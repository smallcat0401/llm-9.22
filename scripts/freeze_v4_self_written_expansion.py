"""Freeze the owner-approved V4 self-written seed expansion tasks."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

from verifiable_posttraining.dataset import write_tasks_jsonl
from verifiable_posttraining.seed_expansion import (
    build_approved_self_written_seed_expansion,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/generated/v4_seed_derived_self_written_approved_v1.jsonl"),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(
            "artifacts/dataset_manifests/"
            "v4_seed_derived_self_written_approved_v1.json"
        ),
    )
    parser.add_argument("--approved-on", default="2026-10-05")
    args = parser.parse_args(argv)

    tasks = build_approved_self_written_seed_expansion(approved_on=args.approved_on)
    write_tasks_jsonl(tasks, args.output)
    manifest: dict[str, Any] = {
        "dataset": "v4_seed_derived_self_written_approved_v1",
        "status": "owner_approved_task_candidates",
        "is_sft_dataset": False,
        "requires_verified_trajectories_before_sft": True,
        "owner_approval_date": args.approved_on,
        "review_artifact": "docs/V4_SEED_DERIVED_AUDIT_ZH.md",
        "count": len(tasks),
        "family_counts": dict(Counter(task.family_id for task in tasks)),
        "output": str(args.output),
        "output_sha256": _sha256(args.output),
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
