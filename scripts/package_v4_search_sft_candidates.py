"""Audit V4 search paths and stage V4-only and V3+V4 SFT candidates.

Tier A checks: train-only membership, strict outcome, clean tool path, trusted
calculator replay, source hashes, and validation-family isolation. The staged
new rows still require semantic path review before a training run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Sequence

from verifiable_posttraining.dataset import load_tasks_jsonl
from verifiable_posttraining.schemas import Split, Task, TaskKind
from verifiable_posttraining.sft_data import (
    build_sft_dataset,
    load_selected_trajectory_records,
    merge_sft_examples,
    select_path_aligned_sft_records,
    sft_dataset_summary,
    write_sft_jsonl,
    write_trajectory_records_jsonl,
)
from verifiable_posttraining.tools.calculator import calculator
from verifiable_posttraining.verifier import verify_numeric_answer


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"manifest must be an object: {path}")
    return value


def _require_hash(path: Path, expected: str) -> None:
    if _sha256(path) != expected:
        raise ValueError(f"source hash mismatch: {path}")


def _read_examples(path: Path) -> tuple[dict[str, Any], ...]:
    rows = tuple(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
                 if line.strip())
    if not rows or any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"invalid SFT examples: {path}")
    return rows


def _verify_unique_training_problems(examples: Sequence[Mapping[str, Any]]) -> None:
    """Do not silently upweight an identical task or exact prompt when merging."""

    task_ids: set[str] = set()
    prompts: set[str] = set()
    for example in examples:
        metadata = example.get("metadata")
        messages = example.get("messages")
        if not isinstance(metadata, Mapping) or not isinstance(messages, list):
            raise ValueError("merged SFT example is missing metadata or messages")
        task_id = metadata.get("task_id")
        user_messages = [
            message.get("content") for message in messages
            if isinstance(message, Mapping) and message.get("role") == "user"
        ]
        if not isinstance(task_id, str) or len(user_messages) != 1 or not isinstance(user_messages[0], str):
            raise ValueError("merged SFT example needs one task ID and one user prompt")
        if task_id in task_ids:
            raise ValueError(f"merged SFT examples repeat task ID: {task_id}")
        if user_messages[0] in prompts:
            raise ValueError(f"merged SFT examples repeat user prompt: {task_id}")
        task_ids.add(task_id)
        prompts.add(user_messages[0])


def _verify_selected_path(record: Mapping[str, Any], expected_task: Task) -> None:
    """Replay every recorded calculator observation, including intermediate steps."""

    task = Task.from_dict(record["task"])
    if task != expected_task or task.split is not Split.TRAIN:
        raise ValueError(f"selected task differs from approved train task: {task.task_id}")
    if task.kind is not TaskKind.CALCULATOR or task.metadata.get("training_eligible") is not True:
        raise ValueError(f"selected task is not calculator-train eligible: {task.task_id}")
    if record["rollout"].get("task_success") is not True:
        raise ValueError(f"selected rollout is not a strict success: {task.task_id}")
    steps = record["trajectory"]["steps"]
    if not steps:
        raise ValueError(f"calculator SFT path must execute the tool: {task.task_id}")
    for step in steps:
        call = step["tool_call"]
        observation = step["observation"]
        expression = call.get("arguments", {}).get("expression")
        if (
            call.get("name") != "calculator"
            or not isinstance(expression, str)
            or observation.get("ok") is not True
            or call.get("call_id") != observation.get("call_id")
        ):
            raise ValueError(f"invalid calculator step: {task.task_id}")
        content = observation.get("content")
        if not isinstance(content, Mapping) or "value" not in content:
            raise ValueError(f"missing calculator value: {task.task_id}")
        if Decimal(str(calculator(expression))) != Decimal(str(content["value"])):
            raise ValueError(f"calculator replay disagrees with observation: {task.task_id}")
    if not verify_numeric_answer(
        record["trajectory"]["final_answer"], task.ground_truth
    ).passed:
        raise ValueError(f"final answer fails independent verifier replay: {task.task_id}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--search-dir", type=Path,
        default=Path("outputs/search/qwen3_5_4b_v4_train_best_of_8_seed509"),
    )
    parser.add_argument(
        "--v4-tasks", type=Path,
        default=Path("data/generated/v4_train_task_candidates_approved_v1.jsonl"),
    )
    parser.add_argument(
        "--v4-train-manifest", type=Path,
        default=Path("artifacts/dataset_manifests/v4_train_task_candidates_approved_v1.json"),
    )
    parser.add_argument(
        "--v3-sft", type=Path,
        default=Path("data/generated/v3_mixed_sft_custom_v1.jsonl"),
    )
    parser.add_argument(
        "--v3-sft-manifest", type=Path,
        default=Path("artifacts/dataset_manifests/v3_sft_package_custom_v1.json"),
    )
    parser.add_argument(
        "--validation", type=Path, default=Path("data/generated/v4_validation_v1.jsonl")
    )
    parser.add_argument(
        "--validation-manifest", type=Path,
        default=Path("artifacts/dataset_manifests/v4_validation_v1.json"),
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/review/v4_search_sft_candidates_v0")
    )
    args = parser.parse_args(argv)

    train_manifest = _manifest(args.v4_train_manifest)
    v3_manifest = _manifest(args.v3_sft_manifest)
    val_manifest = _manifest(args.validation_manifest)
    _require_hash(args.v4_tasks, train_manifest["output_sha256"])
    _require_hash(args.v3_sft, v3_manifest["outputs"]["mixed_sft"]["sha256"])
    _require_hash(args.validation, val_manifest["output_sha256"])

    train = load_tasks_jsonl(args.v4_tasks)
    validation = load_tasks_jsonl(args.validation)
    if len(train) != 162 or len(validation) != 64:
        raise ValueError("unexpected frozen V4 train or validation count")
    train_by_id = {task.task_id: task for task in train}
    val_families = {task.family_id for task in validation}
    if {task.family_id for task in train} & val_families:
        raise ValueError("V4 train and validation families overlap")

    candidates_path = args.search_dir / "candidates.jsonl"
    metrics_path = args.search_dir / "metrics.json"
    candidates = load_selected_trajectory_records(candidates_path)
    report = json.loads(metrics_path.read_text(encoding="utf-8"))
    run_id = report["config"]["run_id"]
    samples_per_task = report["config"]["samples_per_task"]
    if (
        report["config"]["model_id"] != "Qwen/Qwen3.5-4B"
        or report["config"]["splits"] != ["train"]
        or report["config"]["kinds"] != ["calculator"]
        or samples_per_task != 8
        or report["metrics"]["task_count"] != len(train)
        or len(candidates) != len(train) * samples_per_task
    ):
        raise ValueError("search report does not describe the full approved V4 run")
    seen_pairs: set[tuple[str, int]] = set()
    by_task: Counter[str] = Counter()
    successes_by_task: Counter[str] = Counter()
    strict_task_ids: set[str] = set()
    first_success_ids: set[str] = set()
    pass_1 = 0
    strict_candidates = 0
    for record in candidates:
        task = Task.from_dict(record["task"])
        if task.task_id not in train_by_id or task != train_by_id[task.task_id]:
            raise ValueError(f"candidate has an unapproved or changed task: {task.task_id}")
        if record["trajectory"]["model_id"] != "Qwen/Qwen3.5-4B":
            raise ValueError(f"candidate model differs from starting policy: {task.task_id}")
        sample = record["search"]["sample_index"]
        if not isinstance(sample, int) or not 0 <= sample < samples_per_task:
            raise ValueError(f"invalid sample index: {task.task_id}")
        pair = (task.task_id, sample)
        if pair in seen_pairs:
            raise ValueError(f"duplicate task/sample candidate: {pair}")
        seen_pairs.add(pair)
        by_task[task.task_id] += 1
        if record["rollout"].get("task_success") is True:
            strict_candidates += 1
            successes_by_task[task.task_id] += 1
            strict_task_ids.add(task.task_id)
            pass_1 += int(sample == 0)
            if sample == 0:
                first_success_ids.add(task.task_id)
    if (
        set(by_task) != set(train_by_id)
        or set(by_task.values()) != {samples_per_task}
        or strict_candidates != report["metrics"]["verified_candidate_count"]
        or len(strict_task_ids) != report["metrics"]["pass_at_k_count"]
        or pass_1 != report["metrics"]["pass_at_1_count"]
    ):
        raise ValueError("candidate records disagree with search metrics")

    selected = select_path_aligned_sft_records(candidates)
    for record in selected:
        task_id = record["task"]["task_id"]
        _verify_selected_path(record, train_by_id[task_id])
    new_examples = build_sft_dataset(selected)
    new_examples = tuple({
        **example,
        "metadata": {
            **example["metadata"],
            "trajectory_source": "search-discovered",
            "search_discovered": True,
            "source_run": run_id,
            "path_type": "tool-assisted",
            "calculator_replay_verified": True,
            "review_status": "pending_semantic_path_review",
        },
    } for example in new_examples)

    old_examples = _read_examples(args.v3_sft)
    if len(old_examples) != 58:
        raise ValueError("expected the 58-row reviewed V3 mixed package")
    for example in old_examples:
        meta = example.get("metadata", {})
        if (
            meta.get("split") != "train"
            or meta.get("kind") != "calculator"
            or meta.get("family_id") in val_families
            or meta.get("mixture_source") not in {"search-discovered", "reference-program"}
        ):
            raise ValueError(f"V3 SFT row is incompatible or leaks validation: {example.get('example_id')}")
    preserved_old = tuple({
        **example,
        "metadata": {
            **example["metadata"],
            "historical_mixture_source": example["metadata"]["mixture_source"],
        },
    } for example in old_examples)
    combined = merge_sft_examples((
        ("v3-reviewed", preserved_old),
        ("v4-search-candidate", new_examples),
    ))
    _verify_unique_training_problems(combined)
    aligned_ids = {record["task"]["task_id"] for record in selected}
    family_summary = {
        family: {
            "tasks": sum(task.family_id == family for task in train),
            "pass_at_1_count": sum(
                task.family_id == family and task.task_id in first_success_ids
                for task in train
            ),
            "pass_at_8_count": sum(
                task.family_id == family and task.task_id in strict_task_ids for task in train
            ),
            "clean_tool_trajectory_tasks": sum(
                task.family_id == family and task.task_id in aligned_ids for task in train
            ),
        }
        for family in sorted({task.family_id for task in train})
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    selected_path = args.output_dir / "selected_tool_trajectories.jsonl"
    new_path = args.output_dir / "v4_new_sft_candidates.jsonl"
    combined_path = args.output_dir / "v3_plus_v4_sft_candidates.jsonl"
    write_trajectory_records_jsonl(selected, selected_path)
    write_sft_jsonl(new_examples, new_path)
    write_sft_jsonl(combined, combined_path)

    manifest = {
        "dataset": "v4_search_sft_candidates_v0",
        "status": "pending_semantic_path_review",
        "protocol": "custom-json-actions-v1",
        "train_ready": False,
        "search": {
            "run_id": run_id,
            "task_count": len(train),
            "candidate_count": len(candidates),
            "strict_successful_candidates": strict_candidates,
            "strict_successful_tasks": len(strict_task_ids),
            "clean_tool_trajectory_tasks": len(selected),
            "strict_success_without_clean_tool_path": len(strict_task_ids) - len(selected),
            "success_count_distribution": dict(sorted(Counter(
                successes_by_task[task.task_id] for task in train
            ).items())),
        },
        "family_summary": family_summary,
        "v3_rows": len(old_examples),
        "v3_search_rows": sum(
            row["metadata"]["historical_mixture_source"] == "search-discovered"
            for row in preserved_old
        ),
        "v3_reference_rows": sum(
            row["metadata"]["historical_mixture_source"] == "reference-program"
            for row in preserved_old
        ),
        "v4_new": sft_dataset_summary(new_examples),
        "proposed_combined": sft_dataset_summary(combined),
        "inputs": {
            "candidates": {"path": str(candidates_path), "sha256": _sha256(candidates_path)},
            "metrics": {"path": str(metrics_path), "sha256": _sha256(metrics_path)},
            "v4_train": {"path": str(args.v4_tasks), "sha256": _sha256(args.v4_tasks)},
            "v3_sft": {"path": str(args.v3_sft), "sha256": _sha256(args.v3_sft)},
            "v4_validation": {"path": str(args.validation), "sha256": _sha256(args.validation)},
        },
        "outputs": {
            "selected": {"path": str(selected_path), "sha256": _sha256(selected_path)},
            "v4_new": {"path": str(new_path), "sha256": _sha256(new_path)},
            "proposed_combined": {"path": str(combined_path), "sha256": _sha256(combined_path)},
        },
    }
    manifest_path = args.output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
