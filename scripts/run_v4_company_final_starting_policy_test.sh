#!/usr/bin/env bash
# Tier C orchestration for the post-hoc frozen-test starting-policy control.

set -euo pipefail

export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}src"
CACHE_DIR="${HF_HUB_CACHE:-/data/huggingface-cache}"
MODEL_ID="${MODEL_ID:-Qwen2/Qwen3.5-4B}"
TEST_DATA="data/generated/v4_test_v1.jsonl"
EVAL_ROOT="outputs/eval/v4_final_starting_policy_test_seed937"
LOG_DIR="outputs/logs/v4_final_starting_policy_test_seed937"
RESULT_ARCHIVE="v4_4b_final_starting_policy_test_results_seed937.tar.gz"

if [[ -e "$EVAL_ROOT" || -e "$LOG_DIR" || -e "$RESULT_ARCHIVE" ]]; then
  echo "Refusing to overwrite an existing starting-policy final-test result." >&2
  exit 1
fi

mkdir -p "$LOG_DIR" "$EVAL_ROOT"

echo "== Frozen input hashes =="
sha256sum -c v4_4b_final_starting_policy_test_bundle_v1.data.sha256

echo "== GPU, environment, and actual path =="
nvidia-smi | tee "$LOG_DIR/nvidia-smi-before.txt"
python -m pip freeze > "$LOG_DIR/pip-freeze.txt"
printf 'MODEL_ID=%s\nCACHE_DIR=%s\nTEST_DATA=%s\nADAPTER=NONE\n' \
  "$MODEL_ID" "$CACHE_DIR" "$TEST_DATA" \
  | tee "$LOG_DIR/runtime-paths.txt"

echo "== Focused CPU evaluator invariants =="
python -m unittest \
  tests.test_evaluation \
  tests.test_metrics \
  tests.test_native_tool_evaluation \
  tests.test_model_protocol \
  tests.test_verifier 2>&1 | tee "$LOG_DIR/cpu-tests.log"

echo "== Starting policy: custom-protocol frozen test =="
python -m verifiable_posttraining.cli baseline-eval \
  --model-id "$MODEL_ID" \
  --cache-dir "$CACHE_DIR" \
  --load-in-4bit \
  --dataset "$TEST_DATA" \
  --split test \
  --kind calculator \
  --output-dir "$EVAL_ROOT/starting-policy-custom" \
  --metrics-artifact artifacts/metrics/qwen3_5_4b_v4_final_starting_policy_custom_test_seed937.json \
  --run-id qwen3.5-4b-v4-final-starting-policy-custom-test-seed937 \
  --seed 937 \
  --max-new-tokens 256 \
  --max-model-turns 3 \
  --max-tool-calls 2 2>&1 | tee "$LOG_DIR/starting-policy-custom-test.log"

echo "== Starting policy: native-tool frozen diagnostic =="
python -m verifiable_posttraining.native_tool_evaluation \
  --model-id "$MODEL_ID" \
  --cache-dir "$CACHE_DIR" \
  --load-in-4bit \
  --dataset "$TEST_DATA" \
  --split test \
  --output-dir "$EVAL_ROOT/starting-policy-native" \
  --metrics-artifact artifacts/metrics/qwen3_5_4b_v4_final_starting_policy_native_test_seed937.json \
  --run-id qwen3.5-4b-v4-final-starting-policy-native-test-seed937 \
  --seed 937 \
  --max-new-tokens 128 2>&1 | tee "$LOG_DIR/starting-policy-native-test.log"

nvidia-smi | tee "$LOG_DIR/nvidia-smi-after.txt"

echo "== Package starting-policy metrics, records, and logs =="
tar -czf "$RESULT_ARCHIVE" \
  "$EVAL_ROOT" \
  "$LOG_DIR" \
  artifacts/metrics/qwen3_5_4b_v4_final_starting_policy_custom_test_seed937.json \
  artifacts/metrics/qwen3_5_4b_v4_final_starting_policy_native_test_seed937.json \
  docs/V4_FINAL_STARTING_POLICY_TEST_ADDENDUM_ZH.md

echo "Starting-policy control completed. Return $RESULT_ARCHIVE."
echo "Do not train, tune, edit the test, or rerun selected failures."

