#!/usr/bin/env bash
# Tier C orchestration: evaluate the starting policy and all V4 epoch adapters.

set -euo pipefail

CACHE_DIR="${HF_HUB_CACHE:-/data/huggingface-cache}"
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}src"
CONFIG_MODEL_ID="$(python -c 'import tomllib; print(tomllib.load(open("configs/sft_qwen3_5_4b_v4_mixed213_seed113.toml", "rb"))["sft"]["model_id"])')"
MODEL_ID="${MODEL_ID:-$CONFIG_MODEL_ID}"
DATASET="data/generated/v4_validation_v1.jsonl"
OUTPUT_ROOT="outputs/eval/v4_validation_seed613"
mkdir -p "$OUTPUT_ROOT"

LABELS=("starting-policy" "epoch1" "epoch2" "epoch3")
ADAPTERS=(
  ""
  "outputs/sft/qwen3_5_4b_v4_mixed213_seed113/adapter-step-213"
  "outputs/sft/qwen3_5_4b_v4_mixed213_seed113/adapter-step-426"
  "outputs/sft/qwen3_5_4b_v4_mixed213_seed113/adapter"
)

for index in 1 2 3; do
  if [[ ! -d "${ADAPTERS[$index]}" ]]; then
    echo "Missing expected adapter: ${ADAPTERS[$index]}" >&2
    exit 1
  fi
done

for index in "${!LABELS[@]}"; do
  label="${LABELS[$index]}"
  adapter="${ADAPTERS[$index]}"
  command=(
    python -m verifiable_posttraining.cli baseline-eval
    --model-id "$MODEL_ID"
    --cache-dir "$CACHE_DIR"
    --load-in-4bit
    --dataset "$DATASET"
    --split validation
    --kind calculator
    --output-dir "$OUTPUT_ROOT/$label"
    --metrics-artifact "artifacts/metrics/qwen3_5_4b_v4_validation_${label}_seed613.json"
    --run-id "qwen3.5-4b-v4-validation-${label}-seed613"
    --seed 613
    --max-new-tokens 256
    --max-model-turns 3
    --max-tool-calls 2
  )
  if [[ -n "$adapter" ]]; then
    command+=(--adapter-path "$adapter")
  fi
  echo "== validation: $label =="
  "${command[@]}"
done

echo "Validation completed. Return artifacts/metrics, outputs/eval, outputs/logs, and outputs/sft."
echo "Do not run the frozen test set; it is not included in this bundle."
