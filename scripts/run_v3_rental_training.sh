#!/usr/bin/env bash
# Tier C orchestration: run the preregistered smoke and three V3 SFT branches.

set -euo pipefail

CACHE_DIR="${HF_HUB_CACHE:-/root/autodl-tmp/huggingface-cache}"
LOG_DIR="outputs/logs/v3_rental"
mkdir -p "$LOG_DIR"

echo "== GPU =="
nvidia-smi
echo "== CPU tests =="
python -m unittest discover -s tests

run_sft() {
  local label="$1"
  local config="$2"
  echo "== ${label} =="
  python -m verifiable_posttraining.cli sft-train \
    --config "$config" \
    --cache-dir "$CACHE_DIR" 2>&1 | tee "$LOG_DIR/${label}.log"
}

# The shell exits here on any load, encoding, loss, OOM, or serialization error.
run_sft "local-smoke" "configs/sft_qwen3_5_4b_v3_local_smoke_seed113.toml"

# Each command reloads the untouched starting policy; no branch continues from
# another branch's adapter.
run_sft "search32" "configs/sft_qwen3_5_4b_v3_search32_seed113.toml"
run_sft "reference26" "configs/sft_qwen3_5_4b_v3_reference26_seed113.toml"
run_sft "mixed58" "configs/sft_qwen3_5_4b_v3_mixed58_seed113.toml"

echo "All three formal branches completed. Do not run the frozen test set."
