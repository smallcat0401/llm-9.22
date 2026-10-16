#!/usr/bin/env bash
# Inference-only V4 reward-variance probe.  This script never updates the model.

set -euo pipefail

export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}src"
CACHE_DIR="${HF_HUB_CACHE:-/data/huggingface-cache}"
MODEL_ID="${MODEL_ID:-Qwen2/Qwen3.5-4B}"
ADAPTER_PATH="${ADAPTER_PATH:-outputs/sft/qwen3_5_4b_v4_mixed213_seed113/adapter}"
CONFIG="configs/grpo_qwen3_5_4b_v4_reward_probe_seed719.toml"
LOG_DIR="outputs/logs/v4_grpo_probe"
RESULT_DIR="outputs/grpo_probe/qwen3_5_4b_v4_reward_probe_seed719"
METRICS="artifacts/metrics/qwen3_5_4b_v4_grpo_reward_probe_seed719.json"

mkdir -p "$LOG_DIR"

if [[ ! -d "$ADAPTER_PATH" ]]; then
  echo "Missing epoch-3 adapter: $ADAPTER_PATH" >&2
  echo "Run this package from the existing V4 training workspace, or export ADAPTER_PATH." >&2
  exit 1
fi

echo "== GPU and paths =="
nvidia-smi | tee "$LOG_DIR/nvidia-smi.txt"
printf 'MODEL_ID=%s\nADAPTER_PATH=%s\nCACHE_DIR=%s\n' \
  "$MODEL_ID" "$ADAPTER_PATH" "$CACHE_DIR" | tee "$LOG_DIR/runtime-paths.txt"

echo "== Frozen train-only data hash =="
sha256sum -c v4_4b_grpo_probe_bundle_v1.data.sha256

echo "== Focused CPU tests =="
python -m unittest tests.test_grpo_probe tests.test_reward tests.test_native_tool_evaluation

echo "== Two-task, two-sample inference smoke (no parameter updates) =="
python -m verifiable_posttraining.grpo_probe \
  --config "$CONFIG" \
  --cache-dir "$CACHE_DIR" \
  --model-id "$MODEL_ID" \
  --adapter-path "$ADAPTER_PATH" \
  --task-limit 2 \
  --num-samples 2 \
  --output-dir outputs/grpo_probe/qwen3_5_4b_v4_reward_probe_smoke_seed719 \
  --metrics-path artifacts/metrics/qwen3_5_4b_v4_grpo_reward_probe_smoke_seed719.json \
  2>&1 | tee "$LOG_DIR/smoke.log"

echo "== Full 158-task x 8-sample reward-variance probe =="
python -m verifiable_posttraining.grpo_probe \
  --config "$CONFIG" \
  --cache-dir "$CACHE_DIR" \
  --model-id "$MODEL_ID" \
  --adapter-path "$ADAPTER_PATH" \
  2>&1 | tee "$LOG_DIR/full.log"

echo "== Package probe results for return =="
tar -czf v4_4b_grpo_probe_results_seed719.tar.gz \
  "$RESULT_DIR" \
  "$METRICS" \
  "$LOG_DIR" \
  "$CONFIG"

echo "Probe completed. Return v4_4b_grpo_probe_results_seed719.tar.gz."
echo "No validation/test task was read and no model parameter was updated."
