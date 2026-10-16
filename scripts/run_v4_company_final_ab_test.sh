#!/usr/bin/env bash
# Tier C orchestration for the frozen V4 final SFT-vs-GRPO paired test.

set -euo pipefail

export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}src"
CACHE_DIR="${HF_HUB_CACHE:-/data/huggingface-cache}"
MODEL_ID="${MODEL_ID:-Qwen2/Qwen3.5-4B}"
SFT_ADAPTER="${SFT_ADAPTER_PATH:-outputs/sft/qwen3_5_4b_v4_mixed213_seed113/adapter}"
GRPO_ADAPTER="${GRPO_ADAPTER_PATH:-outputs/grpo/qwen3_5_4b_v4_outcome53_seed727/adapter}"
TEST_DATA="data/generated/v4_test_v1.jsonl"
EVAL_ROOT="outputs/eval/v4_final_ab_test_seed937"
LOG_DIR="outputs/logs/v4_final_ab_test_seed937"
RESULT_ARCHIVE="v4_4b_final_ab_test_results_seed937.tar.gz"

if [[ -e "$EVAL_ROOT" || -e "$LOG_DIR" || -e "$RESULT_ARCHIVE" ]]; then
  echo "Refusing to overwrite an existing final-test result." >&2
  exit 1
fi
for adapter in "$SFT_ADAPTER" "$GRPO_ADAPTER"; do
  if [[ ! -f "$adapter/adapter_config.json" || ! -f "$adapter/adapter_model.safetensors" ]]; then
    echo "Incomplete adapter: $adapter" >&2
    exit 1
  fi
done

mkdir -p "$LOG_DIR" "$EVAL_ROOT"

echo "== Frozen input hashes =="
sha256sum -c v4_4b_final_ab_test_bundle_v1.data.sha256

echo "== GPU, environment, and actual paths =="
nvidia-smi | tee "$LOG_DIR/nvidia-smi-before.txt"
python -m pip freeze > "$LOG_DIR/pip-freeze.txt"
printf 'MODEL_ID=%s\nSFT_ADAPTER=%s\nGRPO_ADAPTER=%s\nCACHE_DIR=%s\nTEST_DATA=%s\n' \
  "$MODEL_ID" "$SFT_ADAPTER" "$GRPO_ADAPTER" "$CACHE_DIR" "$TEST_DATA" \
  | tee "$LOG_DIR/runtime-paths.txt"

echo "== Focused CPU evaluator invariants =="
python -m unittest \
  tests.test_evaluation \
  tests.test_metrics \
  tests.test_native_tool_evaluation \
  tests.test_model_protocol \
  tests.test_verifier 2>&1 | tee "$LOG_DIR/cpu-tests.log"

echo "== A: SFT custom-protocol final test =="
python -m verifiable_posttraining.cli baseline-eval \
  --model-id "$MODEL_ID" \
  --cache-dir "$CACHE_DIR" \
  --adapter-path "$SFT_ADAPTER" \
  --load-in-4bit \
  --dataset "$TEST_DATA" \
  --split test \
  --kind calculator \
  --output-dir "$EVAL_ROOT/sft-custom" \
  --metrics-artifact artifacts/metrics/qwen3_5_4b_v4_final_sft_custom_test_seed937.json \
  --run-id qwen3.5-4b-v4-final-sft-custom-test-seed937 \
  --seed 937 \
  --max-new-tokens 256 \
  --max-model-turns 3 \
  --max-tool-calls 2 2>&1 | tee "$LOG_DIR/sft-custom-test.log"

echo "== C: GRPO custom-protocol final test =="
python -m verifiable_posttraining.cli baseline-eval \
  --model-id "$MODEL_ID" \
  --cache-dir "$CACHE_DIR" \
  --adapter-path "$GRPO_ADAPTER" \
  --load-in-4bit \
  --dataset "$TEST_DATA" \
  --split test \
  --kind calculator \
  --output-dir "$EVAL_ROOT/grpo-custom" \
  --metrics-artifact artifacts/metrics/qwen3_5_4b_v4_final_grpo_custom_test_seed937.json \
  --run-id qwen3.5-4b-v4-final-grpo-custom-test-seed937 \
  --seed 937 \
  --max-new-tokens 256 \
  --max-model-turns 3 \
  --max-tool-calls 2 2>&1 | tee "$LOG_DIR/grpo-custom-test.log"

echo "== A: SFT native-tool final diagnostic =="
python -m verifiable_posttraining.native_tool_evaluation \
  --model-id "$MODEL_ID" \
  --cache-dir "$CACHE_DIR" \
  --adapter-path "$SFT_ADAPTER" \
  --load-in-4bit \
  --dataset "$TEST_DATA" \
  --split test \
  --output-dir "$EVAL_ROOT/sft-native" \
  --metrics-artifact artifacts/metrics/qwen3_5_4b_v4_final_sft_native_test_seed937.json \
  --run-id qwen3.5-4b-v4-final-sft-native-test-seed937 \
  --seed 937 \
  --max-new-tokens 128 2>&1 | tee "$LOG_DIR/sft-native-test.log"

echo "== C: GRPO native-tool final diagnostic =="
python -m verifiable_posttraining.native_tool_evaluation \
  --model-id "$MODEL_ID" \
  --cache-dir "$CACHE_DIR" \
  --adapter-path "$GRPO_ADAPTER" \
  --load-in-4bit \
  --dataset "$TEST_DATA" \
  --split test \
  --output-dir "$EVAL_ROOT/grpo-native" \
  --metrics-artifact artifacts/metrics/qwen3_5_4b_v4_final_grpo_native_test_seed937.json \
  --run-id qwen3.5-4b-v4-final-grpo-native-test-seed937 \
  --seed 937 \
  --max-new-tokens 128 2>&1 | tee "$LOG_DIR/grpo-native-test.log"

nvidia-smi | tee "$LOG_DIR/nvidia-smi-after.txt"

echo "== Package final paired-test metrics, records, and logs =="
tar -czf "$RESULT_ARCHIVE" \
  "$EVAL_ROOT" \
  "$LOG_DIR" \
  artifacts/metrics/qwen3_5_4b_v4_final_sft_custom_test_seed937.json \
  artifacts/metrics/qwen3_5_4b_v4_final_grpo_custom_test_seed937.json \
  artifacts/metrics/qwen3_5_4b_v4_final_sft_native_test_seed937.json \
  artifacts/metrics/qwen3_5_4b_v4_final_grpo_native_test_seed937.json \
  docs/V4_FINAL_AB_TEST_PLAN_ZH.md

echo "Final paired test completed. Return $RESULT_ARCHIVE."
echo "Do not retrain, tune, edit the test, or rerun selected failures."

