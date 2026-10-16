"""Freeze the owner-reviewed V4 validation set without changing V3 artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Any, Sequence

from verifiable_posttraining.dataset import (
    load_tasks_jsonl,
    validate_task_dataset,
    write_tasks_jsonl,
)
from verifiable_posttraining.schemas import Split, TaskKind
from verifiable_posttraining.v4_validation_extension import V4_VALIDATION_PUBLIC_FAMILIES


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_hash(path: Path, expected: str) -> None:
    actual = _sha256(path)
    if actual != expected:
        raise ValueError(f"input hash mismatch for {path}: {actual} != {expected}")


def _read_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"manifest must be an object: {path}")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--v3-validation", type=Path, default=Path("data/generated/v3_validation_v1.jsonl")
    )
    parser.add_argument(
        "--v3-manifest", type=Path,
        default=Path("artifacts/dataset_manifests/v3_evaluation_v1.json"),
    )
    parser.add_argument(
        "--extension", type=Path,
        default=Path("data/review/v4_validation_public_extension_audit_v0.jsonl"),
    )
    parser.add_argument(
        "--extension-manifest", type=Path,
        default=Path(
            "artifacts/dataset_manifests/v4_validation_public_extension_audit_v0.json"
        ),
    )
    parser.add_argument(
        "--train", type=Path,
        default=Path("data/generated/v4_train_task_candidates_approved_v1.jsonl"),
    )
    parser.add_argument(
        "--train-manifest", type=Path,
        default=Path(
            "artifacts/dataset_manifests/v4_train_task_candidates_approved_v1.json"
        ),
    )
    parser.add_argument(
        "--output", type=Path, default=Path("data/generated/v4_validation_v1.jsonl")
    )
    parser.add_argument(
        "--manifest", type=Path,
        default=Path("artifacts/dataset_manifests/v4_validation_v1.json"),
    )
    parser.add_argument("--owner-approved-on", default="2026-10-06")
    args = parser.parse_args(argv)

    v3_manifest = _read_manifest(args.v3_manifest)
    extension_manifest = _read_manifest(args.extension_manifest)
    train_manifest = _read_manifest(args.train_manifest)
    _require_hash(args.v3_validation, v3_manifest["outputs"]["validation_sha256"])
    _require_hash(args.extension, extension_manifest["output_sha256"])
    _require_hash(args.train, train_manifest["output_sha256"])
    if extension_manifest.get("status") != "pending_owner_review":
        raise ValueError("extension manifest must be the reviewed audit version")

    prior = load_tasks_jsonl(args.v3_validation)
    extension = load_tasks_jsonl(args.extension)
    train = load_tasks_jsonl(args.train)
    if len(prior) != 36 or len(extension) != 28 or len(train) != 162:
        raise ValueError("unexpected V3 validation, V4 extension, or V4 train count")
    if {task.family_id for task in prior} != set(v3_manifest["family_ids"]["validation"]):
        raise ValueError("V3 validation family IDs differ from the frozen manifest")

    approved = []
    for task in extension:
        if (
            task.split is not Split.VALIDATION
            or task.kind is not TaskKind.CALCULATOR
            or task.family_id not in V4_VALIDATION_PUBLIC_FAMILIES
            or task.metadata.get("parent_seed_task_id")
            != V4_VALIDATION_PUBLIC_FAMILIES[task.family_id]
            or task.metadata.get("review_status") != "pending"
            or task.metadata.get("evaluation_only") is not True
            or task.metadata.get("training_eligible") is not False
        ):
            raise ValueError(f"invalid extension task or provenance: {task.task_id}")
        approved.append(replace(task, metadata={
            **task.metadata,
            "review_status": "owner_approved",
            "owner_approval_date": args.owner_approved_on,
            "dataset_version": "v4_validation_v1",
        }))

    combined = (*prior, *approved)
    validate_task_dataset((*train, *combined))
    if len(combined) != 64 or Counter(task.family_id for task in combined) != Counter({
        family: 8 for family in v3_manifest["family_ids"]["validation"]
    }):
        raise ValueError("V4 validation must have exactly eight rows per family")
    if {task.family_id for task in combined} & set(v3_manifest["family_ids"]["test"]):
        raise ValueError("V4 validation and frozen V3 test families overlap")
    if any(task.split is not Split.VALIDATION for task in combined):
        raise ValueError("V4 validation contains another split")

    if args.output.exists():
        if load_tasks_jsonl(args.output) != combined:
            raise ValueError(f"refusing to overwrite a different frozen file: {args.output}")
    else:
        write_tasks_jsonl(combined, args.output)

    manifest: dict[str, Any] = {
        "dataset": "v4_validation_v1",
        "status": "frozen",
        "evaluation_only": True,
        "training_eligible": False,
        "owner_approval_date": args.owner_approved_on,
        "owner_review_signal": "review completed in conversation with no requested edits",
        "review_artifact": "docs/V4_VALIDATION_EXTENSION_AUDIT_ZH.md",
        "count": len(combined),
        "component_counts": {"frozen_v3_validation": len(prior), "approved_v4_extension": len(approved)},
        "family_counts": dict(Counter(task.family_id for task in combined)),
        "inputs": {
            "v3_validation": str(args.v3_validation),
            "v3_validation_sha256": _sha256(args.v3_validation),
            "extension_audit": str(args.extension),
            "extension_audit_sha256": _sha256(args.extension),
            "v4_train": str(args.train),
            "v4_train_sha256": _sha256(args.train),
            "v3_test_manifest_sha256": v3_manifest["outputs"]["test_sha256"],
        },
        "output": str(args.output),
        "output_sha256": _sha256(args.output),
        "interpretation_limit": (
            "V3 validation rows were already used for model selection; this set is not a fresh holdout"
        ),
    }
    serialized = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if args.manifest.exists():
        if args.manifest.read_text(encoding="utf-8") != serialized:
            raise ValueError(f"refusing to overwrite a different manifest: {args.manifest}")
    else:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
