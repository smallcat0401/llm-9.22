"""Freeze the owner-approved V4 test extension without changing V3 test."""

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
from verifiable_posttraining.tools.calculator import evaluate_expression
from verifiable_posttraining.verifier import verify_numeric_answer


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
    parser.add_argument("--v3-test", type=Path, default=Path("data/generated/v3_test_v1.jsonl"))
    parser.add_argument(
        "--v3-manifest", type=Path,
        default=Path("artifacts/dataset_manifests/v3_evaluation_v1.json"),
    )
    parser.add_argument(
        "--extension", type=Path,
        default=Path("data/review/v4_test_extension_audit_v1.jsonl"),
    )
    parser.add_argument(
        "--extension-manifest", type=Path,
        default=Path("artifacts/dataset_manifests/v4_test_extension_audit_v1.json"),
    )
    parser.add_argument(
        "--train", type=Path,
        default=Path("data/generated/v4_train_tasks_curated_v2.jsonl"),
    )
    parser.add_argument(
        "--validation", type=Path,
        default=Path("data/generated/v4_validation_v1.jsonl"),
    )
    parser.add_argument(
        "--review-artifact", type=Path,
        default=Path("docs/V4_TEST_EXTENSION_AUDIT_V1_ZH.md"),
    )
    parser.add_argument("--output", type=Path, default=Path("data/generated/v4_test_v1.jsonl"))
    parser.add_argument(
        "--manifest", type=Path,
        default=Path("artifacts/dataset_manifests/v4_test_v1.json"),
    )
    parser.add_argument("--owner-approved-on", default="2026-10-06")
    args = parser.parse_args(argv)

    v3_manifest = _read_manifest(args.v3_manifest)
    extension_manifest = _read_manifest(args.extension_manifest)
    if extension_manifest.get("status") != "pending_owner_review":
        raise ValueError("extension manifest must be the owner-reviewed audit version")
    _require_hash(args.v3_test, v3_manifest["outputs"]["test_sha256"])
    _require_hash(args.v3_test, extension_manifest["input_frozen_test_sha256"])
    _require_hash(args.extension, extension_manifest["output_sha256"])
    _require_hash(args.train, extension_manifest["input_train_sha256"])
    _require_hash(args.validation, extension_manifest["input_validation_sha256"])

    prior = load_tasks_jsonl(args.v3_test)
    extension = load_tasks_jsonl(args.extension)
    train = load_tasks_jsonl(args.train)
    validation = load_tasks_jsonl(args.validation)
    if len(prior) != 36 or len(extension) != 36:
        raise ValueError("V4 test must combine 36 frozen parents with 36 reviewed extensions")
    if {task.family_id for task in prior} != set(v3_manifest["family_ids"]["test"]):
        raise ValueError("V3 test family IDs differ from the frozen manifest")
    if any(task.split is not Split.TEST or task.metadata.get("evaluation_only") is not True
           for task in prior):
        raise ValueError("frozen V3 test has unexpected split or provenance")

    parents = {task.task_id: task for task in prior}
    parent_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    approved = []
    for task in extension:
        parent_id = task.metadata.get("parent_test_task_id")
        parent = parents.get(parent_id)
        source_group = task.metadata.get("source_group")
        if (
            parent is None
            or task.family_id != parent.family_id
            or task.split is not Split.TEST
            or task.kind is not TaskKind.CALCULATOR
            or task.allowed_tools != ("calculator",)
            or task.metadata.get("review_status") != "pending"
            or task.metadata.get("evaluation_only") is not True
            or task.metadata.get("training_eligible") is not False
            or task.metadata.get("synthetic") is not True
            or task.metadata.get("dataset_version") != "v4_test_extension_audit_v1"
            or task.metadata.get("review_artifact") != str(args.review_artifact).replace("\\", "/")
            or source_group not in {"self_written_extension", "public_seed_derived_synthetic"}
        ):
            raise ValueError(f"invalid V4 extension task or provenance: {task.task_id}")
        expression = task.metadata.get("reference_expression")
        if not isinstance(expression, str) or not verify_numeric_answer(
            evaluate_expression(expression), task.ground_truth
        ).passed:
            raise ValueError(f"reference expression disagrees with GT: {task.task_id}")
        parent_counts[parent_id] += 1
        source_counts[source_group] += 1
        approved.append(replace(task, metadata={
            **task.metadata,
            "review_status": "owner_approved",
            "owner_approval_date": args.owner_approved_on,
            "dataset_version": "v4_test_v1",
        }))

    if set(parent_counts) != set(parents) or any(count != 1 for count in parent_counts.values()):
        raise ValueError("V4 extension must contain exactly one row per frozen V3 test task")
    if dict(source_counts) != extension_manifest["new_by_source_group"]:
        raise ValueError("V4 extension source-group counts differ from audit manifest")

    combined = (*prior, *approved)
    validate_task_dataset((*train, *validation, *combined))
    if len({" ".join(task.prompt.casefold().split()) for task in combined}) != 72:
        raise ValueError("V4 test contains duplicate prompts")
    family_counts = dict(sorted(Counter(task.family_id for task in combined).items()))
    if family_counts != extension_manifest["planned_family_counts"]:
        raise ValueError("V4 test family counts differ from audit manifest")
    if any(task.split is not Split.TEST for task in combined):
        raise ValueError("V4 test contains another split")

    if args.output.exists():
        if load_tasks_jsonl(args.output) != combined:
            raise ValueError(f"refusing to overwrite a different frozen file: {args.output}")
    else:
        write_tasks_jsonl(combined, args.output)

    manifest: dict[str, Any] = {
        "dataset": "v4_test_v1",
        "status": "frozen",
        "evaluation_only": True,
        "training_eligible": False,
        "owner_approval_date": args.owner_approved_on,
        "owner_review_signal": "review completed in conversation with no requested edits",
        "review_artifact": str(args.review_artifact),
        "review_artifact_sha256": _sha256(args.review_artifact),
        "count": len(combined),
        "component_counts": {
            "frozen_v3_test": len(prior),
            "approved_v4_extension": len(approved),
        },
        "new_by_source_group": dict(source_counts),
        "family_counts": family_counts,
        "inputs": {
            "v3_test": str(args.v3_test),
            "v3_test_sha256": _sha256(args.v3_test),
            "extension_audit": str(args.extension),
            "extension_audit_sha256": _sha256(args.extension),
            "v4_train": str(args.train),
            "v4_train_sha256": _sha256(args.train),
            "v4_validation": str(args.validation),
            "v4_validation_sha256": _sha256(args.validation),
        },
        "output": str(args.output),
        "output_sha256": _sha256(args.output),
        "interpretation_limit": (
            "Extension tasks share test families with V3 parents; report family and cohort "
            "results separately. Test is for one final evaluation after checkpoint selection."
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
