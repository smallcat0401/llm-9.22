#!/usr/bin/env bash
# Tier C orchestration: preflight, smoke, then one formal V4 QLoRA SFT run.

set -euo pipefail

CACHE_DIR="${HF_HUB_CACHE:-/data/huggingface-cache}"
LOG_DIR="outputs/logs/v4_company"
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}src"
mkdir -p "$LOG_DIR"

echo "== GPU =="
nvidia-smi
echo "== Approved data hash =="
sha256sum -c v4_4b_train_validation_bundle_v1.data.sha256
echo "== Focused CPU tests =="
python -m unittest \
  tests.test_calculator \
  tests.test_model_protocol \
  tests.test_sft_training \
  tests.test_verifier

echo "== Full tokenizer preflight (no model weights loaded) =="
python -m scripts.preflight_v4_sft \
  --config configs/sft_qwen3_5_4b_v4_mixed213_seed113.toml \
  --cache-dir "$CACHE_DIR" 2>&1 | tee "$LOG_DIR/preflight.log"

echo "== Four-row, two-microstep smoke =="
python -m verifiable_posttraining.cli sft-train \
  --config configs/sft_qwen3_5_4b_v4_mixed213_smoke_seed113.toml \
  --cache-dir "$CACHE_DIR" 2>&1 | tee "$LOG_DIR/smoke.log"

echo "== Formal 213-row, three-pass SFT from untouched starting policy =="
python -m verifiable_posttraining.cli sft-train \
  --config configs/sft_qwen3_5_4b_v4_mixed213_seed113.toml \
  --cache-dir "$CACHE_DIR" 2>&1 | tee "$LOG_DIR/formal.log"

echo "V4 SFT completed. Run validation next; do not run any test set."
