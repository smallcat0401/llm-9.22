"""Freeze owner-approved V4 SFT examples without changing staged candidates.

Tier A: pin reviewed inputs, enforce train-only/family isolation, replay every
new calculator observation, and verify every new final answer against its task.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

from verifiable_posttraining.dataset import load_tasks_jsonl
from verifiable_posttraining.schemas import Split, Task
from verifiable_posttraining.sft_data import write_sft_jsonl
from verifiable_posttraining.tools.calculator import evaluate_expression
from verifiable_posttraining.verifier import verify_numeric_answer


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"manifest must be a JSON object: {path}")
    return value


def _examples(path: Path) -> tuple[dict[str, Any], ...]:
    value = tuple(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
                  if line.strip())
    if not value or any(not isinstance(row, dict) for row in value):
        raise ValueError(f"invalid SFT examples: {path}")
    return value


def _verify_new_example(row: dict[str, Any], task: Task, source: str) -> None:
    metadata = row["metadata"]
    messages = row["messages"]
    if (task.split is not Split.TRAIN or task.metadata.get("training_eligible") is not True
            or metadata.get("family_id") != task.family_id
            or metadata.get("split") != "train"
            or messages[1].get("content") != task.prompt):
        raise ValueError(f"task or prompt mismatch: {task.task_id}")
    expected_status = (
        "pending_semantic_path_review" if source == "v4-search-candidate"
        else "pending_owner_review"
    )
    if metadata.get("review_status") != expected_status:
        raise ValueError(f"unexpected review status: {task.task_id}")
    if source == "v4-search-candidate":
        if metadata.get("search_discovered") is not True or metadata.get(
            "trajectory_source"
        ) != "search-discovered":
            raise ValueError(f"search provenance mismatch: {task.task_id}")
    elif metadata.get("search_discovered") is not False or metadata.get(
        "trajectory_source"
    ) != "v4-zero-pass-assistant-authored-reference-v1":
        raise ValueError(f"reference provenance mismatch: {task.task_id}")

    if len(messages) not in (5, 7) or [m.get("role") for m in messages[:2]] != [
        "system", "user"
    ] or messages[-1].get("role") != "assistant":
        raise ValueError(f"invalid conversation structure: {task.task_id}")
    if source == "v4-manual-zero-pass" and len(messages) != 5:
        raise ValueError(f"unexpected multi-call reference path: {task.task_id}")
    for index in range(2, len(messages) - 1, 2):
        if [messages[index].get("role"), messages[index + 1].get("role")] != [
            "assistant", "tool"
        ]:
            raise ValueError(f"invalid tool exchange: {task.task_id}")
        action = json.loads(messages[index]["content"])
        observation = json.loads(messages[index + 1]["content"])
        if action.get("type") != "tool_call" or action.get("name") != "calculator":
            raise ValueError(f"invalid calculator action: {task.task_id}")
        expected_value = evaluate_expression(action["arguments"]["expression"])
        if (observation.get("ok") is not True or observation.get("error_code") is not None
                or observation.get("call_id") != f"call-{index // 2}"
                or not math.isclose(
                    float(observation["content"]["value"]), float(expected_value),
                    rel_tol=1e-12, abs_tol=1e-8,
                )):
            raise ValueError(f"calculator observation mismatch: {task.task_id}")
    final = json.loads(messages[-1]["content"])
    if final.get("type") != "final" or not verify_numeric_answer(
        final.get("answer"), task.ground_truth
    ).passed:
        raise ValueError(f"final answer mismatch: {task.task_id}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidates", type=Path,
        default=Path("data/review/v4_sft_paths_curated_v1/sft_candidates_213.jsonl"),
    )
    parser.add_argument(
        "--candidate-manifest", type=Path,
        default=Path("artifacts/dataset_manifests/v4_sft_paths_curated_v1.json"),
    )
    parser.add_argument(
        "--train-tasks", type=Path,
        default=Path("data/generated/v4_train_tasks_curated_v2.jsonl"),
    )
    parser.add_argument(
        "--v3-sft", type=Path,
        default=Path("data/generated/v3_mixed_sft_custom_v1.jsonl"),
    )
    parser.add_argument(
        "--v3-manifest", type=Path,
        default=Path("artifacts/dataset_manifests/v3_sft_package_custom_v1.json"),
    )
    parser.add_argument(
        "--validation-manifest", type=Path,
        default=Path("artifacts/dataset_manifests/v4_validation_v1.json"),
    )
    parser.add_argument(
        "--test-manifest", type=Path,
        default=Path("artifacts/dataset_manifests/v4_test_v1.json"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("data/generated/v4_sft_custom_approved_v1.jsonl"),
    )
    parser.add_argument(
        "--manifest", type=Path,
        default=Path("artifacts/dataset_manifests/v4_sft_custom_approved_v1.json"),
    )
    parser.add_argument("--owner-approved-on", default="2026-10-06")
    args = parser.parse_args(argv)

    candidate_manifest = _manifest(args.candidate_manifest)
    v3_manifest = _manifest(args.v3_manifest)
    validation_manifest = _manifest(args.validation_manifest)
    test_manifest = _manifest(args.test_manifest)
    if candidate_manifest.get("count") != 213 or candidate_manifest.get("train_ready") is not False:
        raise ValueError("expected the staged, 213-row candidate manifest")
    if validation_manifest.get("status") != "frozen" or test_manifest.get("status") != "frozen":
        raise ValueError("evaluation manifests must be frozen")
    for path, expected in (
        (args.candidates, candidate_manifest["output_sha256"]),
        (args.train_tasks, candidate_manifest["train_tasks_sha256"]),
        (args.v3_sft, v3_manifest["outputs"]["mixed_sft"]["sha256"]),
    ):
        if _sha256(path) != expected:
            raise ValueError(f"source hash mismatch: {path}")

    candidates = _examples(args.candidates)
    v3_rows = _examples(args.v3_sft)
    tasks = {task.task_id: task for task in load_tasks_jsonl(args.train_tasks)}
    if len(candidates) != 213 or len(v3_rows) != 58 or len(tasks) != 158:
        raise ValueError("unexpected source count")
    validation_families = set(validation_manifest["family_counts"])
    test_families = set(test_manifest["family_counts"])
    if validation_families & test_families:
        raise ValueError("validation and test families overlap")
    old_by_id = {row["metadata"]["task_id"]: row for row in v3_rows}
    approved: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_prompts: set[str] = set()
    sources: Counter[str] = Counter()
    for row in candidates:
        metadata = row["metadata"]
        task_id = metadata["task_id"]
        source = metadata["mixture_source"]
        messages = row["messages"]
        family_id = metadata["family_id"]
        if (task_id in seen_ids or family_id in validation_families | test_families
                or metadata.get("split") != "train"):
            raise ValueError(f"duplicate, non-train, or leaked task: {task_id}")
        seen_ids.add(task_id)
        prompt = messages[1]["content"]
        if prompt in seen_prompts:
            raise ValueError(f"duplicate SFT prompt: {task_id}")
        seen_prompts.add(prompt)
        sources[source] += 1
        if source == "v3-reviewed":
            original = old_by_id.get(task_id)
            if original is None or messages != original["messages"]:
                raise ValueError(f"V3 example differs from reviewed source: {task_id}")
            approved.append(row)
        elif source in {"v4-search-candidate", "v4-manual-zero-pass"}:
            task = tasks.get(task_id)
            if task is None:
                raise ValueError(f"V4 task missing from curated train pool: {task_id}")
            _verify_new_example(row, task, source)
            new_metadata = {
                **metadata,
                "review_status": "owner_approved",
                "owner_approval_date": args.owner_approved_on,
                "dataset_version": "v4_sft_custom_approved_v1",
            }
            if source == "v4-manual-zero-pass":
                new_metadata["authored_by"] = "Codex assistant; owner-approved after path audit"
            approved.append({**row, "metadata": new_metadata})
        else:
            raise ValueError(f"unknown SFT source: {source}")
    if dict(sources) != {
        "v3-reviewed": 58, "v4-search-candidate": 114, "v4-manual-zero-pass": 41
    } or set(old_by_id) - seen_ids:
        raise ValueError("approved set does not preserve the intended three-source mixture")

    if args.output.exists():
        if _examples(args.output) != tuple(approved):
            raise ValueError(f"refusing to overwrite a different frozen file: {args.output}")
    else:
        write_sft_jsonl(approved, args.output)
    manifest: dict[str, Any] = {
        "dataset": "v4_sft_custom_approved_v1",
        "status": "frozen",
        "train_ready": True,
        "owner_approval_date": args.owner_approved_on,
        "owner_review_signal": "owner accepted assistant path audit after excluding one error-first path",
        "count": len(approved),
        "source_counts": dict(sources),
        "inputs": {
            "curated_candidates": str(args.candidates),
            "curated_candidates_sha256": _sha256(args.candidates),
            "v4_train_tasks_sha256": _sha256(args.train_tasks),
            "v3_sft_sha256": _sha256(args.v3_sft),
            "validation_manifest": str(args.validation_manifest),
            "validation_manifest_sha256": _sha256(args.validation_manifest),
            "test_manifest": str(args.test_manifest),
            "test_manifest_sha256": _sha256(args.test_manifest),
        },
        "output": str(args.output),
        "output_sha256": _sha256(args.output),
        "evaluation_limit": "Select checkpoints on validation only; V4 test remains final-only.",
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
