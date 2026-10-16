"""Freeze the approved V3 validation and test task files."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from verifiable_posttraining.dataset import write_tasks_jsonl
from verifiable_posttraining.schemas import Split
from verifiable_posttraining.v3_evaluation import build_v3_evaluation_tasks


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _training_families(path: Path) -> set[str]:
    families = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        metadata = row.get("metadata", {}) if isinstance(row, Mapping) else {}
        family = metadata.get("family_id") if isinstance(metadata, Mapping) else None
        if not isinstance(family, str) or not family:
            raise ValueError("every SFT row must expose metadata.family_id")
        families.add(family)
    return families


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gsm8k-train", type=Path, required=True)
    parser.add_argument("--gsm8k-test", type=Path, required=True)
    parser.add_argument("--training-sft", type=Path, required=True)
    parser.add_argument("--exclude-artifact", type=Path, action="append", default=[])
    parser.add_argument("--validation-output", type=Path, required=True)
    parser.add_argument("--test-output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--examples-per-family", type=int, default=8)
    args = parser.parse_args(argv)

    tasks = build_v3_evaluation_tasks(
        gsm8k_train_path=args.gsm8k_train,
        gsm8k_test_path=args.gsm8k_test,
        exclusion_artifacts=args.exclude_artifact,
        training_family_ids=_training_families(args.training_sft),
        examples_per_synthetic_family=args.examples_per_family,
    )
    validation = tuple(task for task in tasks if task.split is Split.VALIDATION)
    test = tuple(task for task in tasks if task.split is Split.TEST)
    write_tasks_jsonl(validation, args.validation_output)
    write_tasks_jsonl(test, args.test_output)
    manifest: dict[str, Any] = {
        "dataset": "v3_evaluation_v1",
        "status": "frozen",
        "evaluation_only": True,
        "seed_audit": "docs/V3_EVAL_SEED_AUDIT_ZH.md",
        "owner_approval_date": "2026-10-05",
        "examples_per_synthetic_family": args.examples_per_family,
        "counts": {
            "validation": len(validation), "test": len(test),
            "by_source": dict(Counter(
                "synthetic" if task.metadata.get("synthetic") else "public"
                for task in tasks
            )),
        },
        "family_ids": {
            "validation": sorted({task.family_id for task in validation}),
            "test": sorted({task.family_id for task in test}),
        },
        "inputs": {
            "training_sft": str(args.training_sft),
            "training_sft_sha256": _sha256(args.training_sft),
            "gsm8k_train_sha256": _sha256(args.gsm8k_train),
            "gsm8k_test_sha256": _sha256(args.gsm8k_test),
            "exclusion_artifacts": [str(path) for path in args.exclude_artifact],
        },
        "outputs": {
            "validation": str(args.validation_output),
            "validation_sha256": _sha256(args.validation_output),
            "test": str(args.test_output),
            "test_sha256": _sha256(args.test_output),
        },
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
