"""Check the approved V4 SFT hash and tokenize every selected example, no GPU/model load."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Sequence

from verifiable_posttraining.sft_training import (
    encode_assistant_only_example,
    load_sft_examples,
    load_sft_training_config,
    select_balanced_examples,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", default="configs/sft_qwen3_5_4b_v4_mixed213_seed113.toml"
    )
    parser.add_argument(
        "--manifest", type=Path,
        default=Path("artifacts/dataset_manifests/v4_sft_custom_approved_v1.json"),
    )
    parser.add_argument("--cache-dir")
    args = parser.parse_args(argv)
    config = load_sft_training_config(args.config)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("status") != "frozen" or manifest.get("train_ready") is not True:
        raise ValueError("training dataset is not approved and frozen")
    path = Path(config.dataset_path)
    if str(path).replace("\\", "/") != manifest["output"].replace("\\", "/"):
        raise ValueError("config dataset path differs from approved manifest")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != manifest["output_sha256"]:
        raise ValueError("approved SFT dataset hash mismatch")
    examples = load_sft_examples(path)
    if len(examples) != manifest["count"]:
        raise ValueError("approved SFT row count mismatch")
    selected = select_balanced_examples(examples, limit=config.sample_count, seed=config.seed)
    if len(selected) != config.sample_count:
        raise ValueError("training configuration does not select the requested row count")

    from transformers import AutoProcessor

    processor = AutoProcessor.from_pretrained(
        config.model_id, cache_dir=args.cache_dir, local_files_only=True
    )
    encoded = [
        encode_assistant_only_example(
            processor.tokenizer, example, max_length=config.max_length
        ) for example in selected
    ]
    result = {
        "config": args.config,
        "dataset_sha256": digest,
        "selected_count": len(selected),
        "max_sequence_tokens": max(len(row["input_ids"]) for row in encoded),
        "min_supervised_tokens": min(
            sum(label != -100 for label in row["labels"]) for row in encoded
        ),
        "model_weights_loaded": False,
        "gpu_training_run": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
