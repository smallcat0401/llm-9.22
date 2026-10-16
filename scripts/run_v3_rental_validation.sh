#!/usr/bin/env bash
# Tier C orchestration: evaluate all nine formal adapters on validation only.

set -euo pipefail

CACHE_DIR="${HF_HUB_CACHE:-/root/autodl-tmp/huggingface-cache}"
MODEL_ID="Qwen/Qwen3.5-4B"
DATASET="data/generated/v3_validation_v1.jsonl"

LABELS=(
  "search32-epoch1"
  "search32-epoch2"
  "search32-epoch3"
  "reference26-epoch1"
  "reference26-epoch2"
  "reference26-epoch3"
  "mixed58-epoch1"
  "mixed58-epoch2"
  "mixed58-epoch3"
)

ADAPTERS=(
  "outputs/sft/qwen3_5_4b_v3_search32_seed113/adapter-step-32"
  "outputs/sft/qwen3_5_4b_v3_search32_seed113/adapter-step-64"
  "outputs/sft/qwen3_5_4b_v3_search32_seed113/adapter"
  "outputs/sft/qwen3_5_4b_v3_reference26_seed113/adapter-step-26"
  "outputs/sft/qwen3_5_4b_v3_reference26_seed113/adapter-step-52"
  "outputs/sft/qwen3_5_4b_v3_reference26_seed113/adapter"
  "outputs/sft/qwen3_5_4b_v3_mixed58_seed113/adapter-step-58"
  "outputs/sft/qwen3_5_4b_v3_mixed58_seed113/adapter-step-116"
  "outputs/sft/qwen3_5_4b_v3_mixed58_seed113/adapter"
)

for adapter in "${ADAPTERS[@]}"; do
  if [[ ! -d "$adapter" ]]; then
    echo "Missing expected adapter: $adapter" >&2
    exit 1
  fi
done

for index in "${!LABELS[@]}"; do
  label="${LABELS[$index]}"
  adapter="${ADAPTERS[$index]}"
  echo "== validation: ${label} =="
  python -m verifiable_posttraining.cli baseline-eval \
    --model-id "$MODEL_ID" \
    --cache-dir "$CACHE_DIR" \
    --adapter-path "$adapter" \
    --load-in-4bit \
    --dataset "$DATASET" \
    --split validation \
    --kind calculator \
    --output-dir "outputs/eval/qwen3_5_4b_v3_validation_${label}_seed503" \
    --metrics-artifact "artifacts/metrics/qwen3_5_4b_v3_validation_${label}_seed503.json" \
    --run-id "qwen3.5-4b-v3-validation-${label}-seed503" \
    --seed 503 \
    --max-new-tokens 256 \
    --max-model-turns 3 \
    --max-tool-calls 2
done

echo "All nine validation runs completed. The frozen test set is not in this bundle."
