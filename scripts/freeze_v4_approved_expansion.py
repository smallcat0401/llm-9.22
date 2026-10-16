"""Freeze approved V4 task candidates and build their combined train pool."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

from verifiable_posttraining.dataset import validate_task_dataset, write_tasks_jsonl
from verifiable_posttraining.public_seed_expansion import (
    build_approved_public_seed_expansion,
)
from verifiable_posttraining.seed_expansion import (
    build_approved_self_written_seed_expansion,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-written-output",
        type=Path,
        default=Path(
            "data/generated/v4_seed_derived_self_written_approved_v1.jsonl"
        ),
    )
    parser.add_argument(
        "--public-output",
        type=Path,
        default=Path("data/generated/v4_public_seed_relations_approved_v1.jsonl"),
    )
    parser.add_argument(
        "--public-manifest",
        type=Path,
        default=Path(
            "artifacts/dataset_manifests/"
            "v4_public_seed_relations_approved_v1.json"
        ),
    )
    parser.add_argument(
        "--combined-output",
        type=Path,
        default=Path("data/generated/v4_train_task_candidates_approved_v1.jsonl"),
    )
    parser.add_argument(
        "--combined-manifest",
        type=Path,
        default=Path(
            "artifacts/dataset_manifests/"
            "v4_train_task_candidates_approved_v1.json"
        ),
    )
    parser.add_argument("--public-approved-on", default="2026-10-06")
    parser.add_argument("--self-written-approved-on", default="2026-10-05")
    args = parser.parse_args(argv)

    self_written = build_approved_self_written_seed_expansion(
        approved_on=args.self_written_approved_on
    )
    public = build_approved_public_seed_expansion(
        approved_on=args.public_approved_on
    )
    combined = (*self_written, *public)
    validate_task_dataset(combined)

    write_tasks_jsonl(self_written, args.self_written_output)
    write_tasks_jsonl(public, args.public_output)
    write_tasks_jsonl(combined, args.combined_output)

    public_manifest: dict[str, Any] = {
        "dataset": "v4_public_seed_relations_approved_v1",
        "status": "owner_approved_task_candidates",
        "is_sft_dataset": False,
        "contains_trajectory_data": False,
        "requires_verified_trajectories_before_sft": True,
        "owner_approval_date": args.public_approved_on,
        "review_artifact": "docs/V4_PUBLIC_SEED_RELATIONS_AUDIT_ZH.md",
        "count": len(public),
        "family_count": len({task.family_id for task in public}),
        "family_counts": dict(Counter(task.family_id for task in public)),
        "output": str(args.public_output),
        "output_sha256": _sha256(args.public_output),
    }
    _write_manifest(args.public_manifest, public_manifest)

    combined_manifest: dict[str, Any] = {
        "dataset": "v4_train_task_candidates_approved_v1",
        "status": "owner_approved_task_candidates",
        "is_sft_dataset": False,
        "contains_trajectory_data": False,
        "requires_verified_trajectories_before_sft": True,
        "count": len(combined),
        "family_count": len({task.family_id for task in combined}),
        "split_counts": dict(Counter(task.split.value for task in combined)),
        "kind_counts": dict(Counter(task.kind.value for task in combined)),
        "component_counts": {
            "self_written_seed_derived": len(self_written),
            "public_relation_synthetic_tables": len(public),
        },
        "components": [
            {
                "dataset": "v4_seed_derived_self_written_approved_v1",
                "output": str(args.self_written_output),
                "sha256": _sha256(args.self_written_output),
                "count": len(self_written),
            },
            {
                "dataset": "v4_public_seed_relations_approved_v1",
                "output": str(args.public_output),
                "sha256": public_manifest["output_sha256"],
                "count": len(public),
            },
        ],
        "family_counts": dict(Counter(task.family_id for task in combined)),
        "output": str(args.combined_output),
        "output_sha256": _sha256(args.combined_output),
    }
    _write_manifest(args.combined_manifest, combined_manifest)

    print(json.dumps({
        "public": public_manifest,
        "combined": combined_manifest,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
