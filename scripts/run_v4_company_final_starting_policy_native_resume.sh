#!/usr/bin/env bash
# Resume only the native starting-policy control after the v1 CLI rejected a missing adapter.

set -euo pipefail

export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}src"
CACHE_DIR="${HF_HUB_CACHE:-/data/huggingface-cache}"
MODEL_ID="${MODEL_ID:-Qwen2/Qwen3.5-4B}"
TEST_DATA="data/generated/v4_test_v1.jsonl"
EVAL_ROOT="outputs/eval/v4_final_starting_policy_test_seed937"
LOG_DIR="outputs/logs/v4_final_starting_policy_test_seed937"
CUSTOM_DIR="$EVAL_ROOT/starting-policy-custom"
NATIVE_DIR="$EVAL_ROOT/starting-policy-native"
CUSTOM_ARTIFACT="artifacts/metrics/qwen3_5_4b_v4_final_starting_policy_custom_test_seed937.json"
NATIVE_ARTIFACT="artifacts/metrics/qwen3_5_4b_v4_final_starting_policy_native_test_seed937.json"
RESULT_ARCHIVE="v4_4b_final_starting_policy_test_results_seed937.tar.gz"

if [[ ! -f "$CUSTOM_DIR/metrics.json" || ! -f "$CUSTOM_DIR/records.jsonl" || ! -f "$CUSTOM_ARTIFACT" ]]; then
  echo "The completed custom starting-policy result is missing; refusing to resume." >&2
  exit 1
fi
if [[ "$(wc -l < "$CUSTOM_DIR/records.jsonl")" -ne 72 ]]; then
  echo "The existing custom result does not contain exactly 72 records." >&2
  exit 1
fi
if [[ -e "$NATIVE_DIR" || -e "$NATIVE_ARTIFACT" || -e "$RESULT_ARCHIVE" ]]; then
  echo "A native result or final archive already exists; refusing to overwrite or rerun." >&2
  exit 1
fi

echo "== Recheck frozen input hashes =="
sha256sum -c v4_4b_final_starting_policy_test_bundle_v1.data.sha256

echo "== Verify the corrected native evaluator =="
python -m unittest tests.test_native_tool_evaluation 2>&1 \
  | tee "$LOG_DIR/native-resume-tests.log"

echo "== Resume only: starting policy native-tool frozen diagnostic =="
python -m verifiable_posttraining.native_tool_evaluation \
  --model-id "$MODEL_ID" \
  --cache-dir "$CACHE_DIR" \
  --load-in-4bit \
  --dataset "$TEST_DATA" \
  --split test \
  --output-dir "$NATIVE_DIR" \
  --metrics-artifact "$NATIVE_ARTIFACT" \
  --run-id qwen3.5-4b-v4-final-starting-policy-native-test-seed937 \
  --seed 937 \
  --max-new-tokens 128 2>&1 | tee "$LOG_DIR/starting-policy-native-test.log"

nvidia-smi | tee "$LOG_DIR/nvidia-smi-after-resume.txt"

echo "== Package the preserved custom result plus the new native result =="
tar -czf "$RESULT_ARCHIVE" \
  "$EVAL_ROOT" \
  "$LOG_DIR" \
  "$CUSTOM_ARTIFACT" \
  "$NATIVE_ARTIFACT" \
  docs/V4_FINAL_STARTING_POLICY_TEST_ADDENDUM_ZH.md

echo "Resume completed. Return $RESULT_ARCHIVE."
echo "The existing custom run was preserved and was not rerun."

