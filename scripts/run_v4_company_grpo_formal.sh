#!/usr/bin/env bash
# Tier C orchestration for the frozen V4 4B A-vs-C GRPO experiment.

set -euo pipefail

export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}src"
CACHE_DIR="${HF_HUB_CACHE:-/data/huggingface-cache}"
MODEL_ID="${MODEL_ID:-Qwen2/Qwen3.5-4B}"
SFT_ADAPTER="${SFT_ADAPTER_PATH:-outputs/sft/qwen3_5_4b_v4_mixed213_seed113/adapter}"
GRPO_ADAPTER="outputs/grpo/qwen3_5_4b_v4_outcome53_seed727/adapter"
SMOKE_CONFIG="configs/grpo_qwen3_5_4b_v4_outcome53_smoke_seed727.toml"
FORMAL_CONFIG="configs/grpo_qwen3_5_4b_v4_outcome53_seed727.toml"
VALIDATION="data/generated/v4_validation_v1.jsonl"
LOG_DIR="outputs/logs/v4_grpo_formal_seed727"
EVAL_ROOT="outputs/eval/v4_grpo_validation_seed829"
RESULT_ARCHIVE="v4_4b_grpo_formal_results_seed727.tar.gz"

mkdir -p "$LOG_DIR" "$EVAL_ROOT"

if [[ ! -d "$SFT_ADAPTER" ]]; then
  echo "Missing selected V4 epoch-3 SFT adapter: $SFT_ADAPTER" >&2
  echo "Run from the existing V4 company workspace or export SFT_ADAPTER_PATH." >&2
  exit 1
fi
if [[ -e "$GRPO_ADAPTER" ]]; then
  echo "Refusing to overwrite an existing formal GRPO adapter: $GRPO_ADAPTER" >&2
  exit 1
fi

echo "== GPU, environment, and actual paths =="
nvidia-smi | tee "$LOG_DIR/nvidia-smi-before.txt"
python -m pip freeze > "$LOG_DIR/pip-freeze.txt"
printf 'MODEL_ID=%s\nSFT_ADAPTER=%s\nCACHE_DIR=%s\n' \
  "$MODEL_ID" "$SFT_ADAPTER" "$CACHE_DIR" | tee "$LOG_DIR/runtime-paths.txt"

echo "== Frozen input hashes =="
sha256sum -c v4_4b_grpo_formal_bundle_v2.data.sha256

echo "== Focused CPU invariants =="
python -m unittest \
  tests.test_grpo_training \
  tests.test_reward \
  tests.test_native_tool_evaluation \
  tests.test_model_protocol \
  tests.test_verifier 2>&1 | tee "$LOG_DIR/cpu-tests.log"

echo "== A: SFT custom-protocol validation =="
python -m verifiable_posttraining.cli baseline-eval \
  --model-id "$MODEL_ID" \
  --cache-dir "$CACHE_DIR" \
  --adapter-path "$SFT_ADAPTER" \
  --load-in-4bit \
  --dataset "$VALIDATION" \
  --split validation \
  --kind calculator \
  --output-dir "$EVAL_ROOT/sft-custom" \
  --metrics-artifact artifacts/metrics/qwen3_5_4b_v4_grpo_control_custom_validation_seed829.json \
  --run-id qwen3.5-4b-v4-grpo-control-custom-validation-seed829 \
  --seed 829 \
  --max-new-tokens 256 \
  --max-model-turns 3 \
  --max-tool-calls 2 2>&1 | tee "$LOG_DIR/sft-custom-validation.log"

echo "== A: SFT native-tool validation diagnostic =="
python -m verifiable_posttraining.native_tool_evaluation \
  --model-id "$MODEL_ID" \
  --cache-dir "$CACHE_DIR" \
  --adapter-path "$SFT_ADAPTER" \
  --load-in-4bit \
  --dataset "$VALIDATION" \
  --split validation \
  --output-dir "$EVAL_ROOT/sft-native" \
  --metrics-artifact artifacts/metrics/qwen3_5_4b_v4_grpo_control_native_validation_seed829.json \
  --run-id qwen3.5-4b-v4-grpo-control-native-validation-seed829 \
  --seed 829 \
  --max-new-tokens 128 2>&1 | tee "$LOG_DIR/sft-native-validation.log"

echo "== Two-prompt, two-step 4B GRPO smoke =="
python -m verifiable_posttraining.cli grpo-smoke \
  --config "$SMOKE_CONFIG" \
  --cache-dir "$CACHE_DIR" \
  --model-id "$MODEL_ID" \
  --adapter-path "$SFT_ADAPTER" 2>&1 | tee "$LOG_DIR/smoke.log"

echo "== Formal 53-prompt, one-pass 4B GRPO =="
python -m verifiable_posttraining.cli grpo-smoke \
  --config "$FORMAL_CONFIG" \
  --cache-dir "$CACHE_DIR" \
  --model-id "$MODEL_ID" \
  --adapter-path "$SFT_ADAPTER" 2>&1 | tee "$LOG_DIR/formal.log"

echo "== C: post-GRPO custom-protocol validation =="
python -m verifiable_posttraining.cli baseline-eval \
  --model-id "$MODEL_ID" \
  --cache-dir "$CACHE_DIR" \
  --adapter-path "$GRPO_ADAPTER" \
  --load-in-4bit \
  --dataset "$VALIDATION" \
  --split validation \
  --kind calculator \
  --output-dir "$EVAL_ROOT/grpo-custom" \
  --metrics-artifact artifacts/metrics/qwen3_5_4b_v4_grpo_outcome53_custom_validation_seed829.json \
  --run-id qwen3.5-4b-v4-grpo-outcome53-custom-validation-seed829 \
  --seed 829 \
  --max-new-tokens 256 \
  --max-model-turns 3 \
  --max-tool-calls 2 2>&1 | tee "$LOG_DIR/grpo-custom-validation.log"

echo "== C: post-GRPO native-tool validation diagnostic =="
python -m verifiable_posttraining.native_tool_evaluation \
  --model-id "$MODEL_ID" \
  --cache-dir "$CACHE_DIR" \
  --adapter-path "$GRPO_ADAPTER" \
  --load-in-4bit \
  --dataset "$VALIDATION" \
  --split validation \
  --output-dir "$EVAL_ROOT/grpo-native" \
  --metrics-artifact artifacts/metrics/qwen3_5_4b_v4_grpo_outcome53_native_validation_seed829.json \
  --run-id qwen3.5-4b-v4-grpo-outcome53-native-validation-seed829 \
  --seed 829 \
  --max-new-tokens 128 2>&1 | tee "$LOG_DIR/grpo-native-validation.log"

nvidia-smi | tee "$LOG_DIR/nvidia-smi-after.txt"

echo "== Package adapter, metrics, records, logs, and actual configs =="
tar -czf "$RESULT_ARCHIVE" \
  "$GRPO_ADAPTER" \
  "$EVAL_ROOT" \
  "$LOG_DIR" \
  artifacts/metrics/qwen3_5_4b_v4_grpo_outcome53_smoke_seed727.json \
  artifacts/metrics/qwen3_5_4b_v4_grpo_outcome53_seed727.json \
  artifacts/metrics/qwen3_5_4b_v4_grpo_control_custom_validation_seed829.json \
  artifacts/metrics/qwen3_5_4b_v4_grpo_control_native_validation_seed829.json \
  artifacts/metrics/qwen3_5_4b_v4_grpo_outcome53_custom_validation_seed829.json \
  artifacts/metrics/qwen3_5_4b_v4_grpo_outcome53_native_validation_seed829.json \
  "$SMOKE_CONFIG" \
  "$FORMAL_CONFIG"

echo "Formal A-vs-C validation completed. Return $RESULT_ARCHIVE."
echo "Do not run the frozen test set. It is not included in this bundle."
