"""Stage assistant-authored calculator trajectories for audited V4 zero-pass tasks.

Tier A: the task IDs and arithmetic programs are explicit below. The script
replays each call in EpisodeEnvironment, checks the final verifier, and keeps
train/validation boundaries. These are reference demonstrations, NOT model
search discoveries and NOT owner-approved training data yet.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import asdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Mapping, Sequence

from verifiable_posttraining.dataset import load_tasks_jsonl
from verifiable_posttraining.environment import EpisodeEnvironment
from verifiable_posttraining.model_protocol import FinalAnswer, parse_model_action
from verifiable_posttraining.schemas import Split, Task, TaskKind, ToolCall
from verifiable_posttraining.sft_data import (
    build_sft_example,
    load_selected_trajectory_records,
    write_sft_jsonl,
    write_trajectory_records_jsonl,
)
from verifiable_posttraining.tools.calculator import execute_calculator


SET_NAME = "v4-zero-pass-assistant-authored-reference-v1"
EXCLUDED_TASK_IDS = frozenset({
    "v4-review-public-midpoint_rate_application-000",
    "v4-review-public-midpoint_rate_application-003",
    "v4-review-public-multi_period_interest-002",
    "v4-review-public-multi_period_interest-004",
})

# These are manually specified, task-specific expressions. Do not populate
# them from metadata.reference_expression: the point is an auditable second
# formulation after reviewing each English prompt and synthetic table.
MANUAL_EXPRESSIONS: Mapping[str, str] = {
    "v4-review-curriculum-v2-sales-returns-003": "(46 - 7) * 13 + 13 * 27 + 8",
    "v4-review-curriculum-v2-sales-returns-006": "(43 - 8) * 12 + 18 * 26 + 41",
    "v4-review-curriculum-v2-sales-returns-010": "(32 - 3) * 24 + 9 * 30 + 6",
    "v4-review-curriculum-v2-sales-returns-013": "(38 - 8) * 10 + 7 * 23 + 34",
    "v4-review-curriculum-v2-required-score-007": "5 * 69.6 - (71 + 59 + 62 + 73)",
    "v4-review-curriculum-v2-required-score-010": "5 * 88.2 - (89 + 92 + 70 + 94)",
    "v4-review-curriculum-v2-required-score-014": "5 * 73.2 - (83 + 61 + 64 + 63)",
    "v4-review-curriculum-v2-required-score-015": "5 * 72.6 - (84 + 60 + 76 + 71)",
    "v4-review-curriculum-v2-cartons-damage-011": "3 * 6 * 9 - 18 - 11",
    "v4-review-curriculum-v2-shared-bill-007": "(12 * 40 + 80) / (12 - 3)",
    "v4-review-curriculum-v2-shared-bill-008": "(14 * 41 + 50) / (14 - 2)",
    "v4-review-curriculum-v2-shared-bill-015": "(8 * 25 + 45) / (8 - 3)",
    "v4-review-public-aggregate_percent_change-000": "((3846 + 2709) - (4421 + 3518)) / (4421 + 3518) * 100",
    "v4-review-public-aggregate_percent_change-001": "((781 + 3316) - (953 + 2763)) / (953 + 2763) * 100",
    "v4-review-public-aggregate_percent_change_with_loss-003": "((734 + 0 + 1100 - 72) - (1137 + 206 + 531 - 206)) / (1137 + 206 + 531 - 206) * 100",
    "v4-review-public-average_growth_rate-000": "((5697 - 7121) / 7121 + (6552 - 5697) / 5697) / 2 * 100",
    "v4-review-public-average_growth_rate-001": "((2754 - 2203) / 2203 + (2479 - 2754) / 2754) / 2 * 100",
    "v4-review-public-average_growth_rate-002": "((4097 - 4820) / 4820 + (3892 - 4097) / 4097) / 2 * 100",
    "v4-review-public-average_growth_rate-003": "((8185 - 7441) / 7441 + (10640 - 8185) / 8185) / 2 * 100",
    "v4-review-public-average_growth_rate-004": "((11271 - 8349) / 8349 + (9017 - 11271) / 11271) / 2 * 100",
    "v4-review-public-average_growth_rate-005": "((7944 - 8635) / 8635 + (9692 - 7944) / 7944) / 2 * 100",
    "v4-review-public-derived_value_percent_change-002": "((1038500 * 34.56) - (865417 * 23.67)) / (865417 * 23.67) * 100",
    "v4-review-public-derived_value_percent_change-004": "((172963 * 76.16) - (262065 * 52.89)) / (262065 * 52.89) * 100",
    "v4-review-public-difference_of_averages-001": "(2069 + 11523) / 2 - (16201 + 12190) / 2",
    "v4-review-public-difference_of_averages-004": "(19112 + 18547) / 2 - (9990 + 12854) / 2",
    "v4-review-public-difference_of_averages-005": "(3202 + 19603) / 2 - (18565 + 1985) / 2",
    "v4-review-public-midpoint_rate_application-002": "232 * (3.39 + 4.68) / 2 / 100",
    "v4-review-public-midpoint_rate_application-004": "198 * (6.39 + 10.07) / 2 / 100",
    "v4-review-public-midpoint_rate_application-005": "285 * (7.37 + 9.79) / 2 / 100",
    "v4-review-public-payout_ratio-000": "58837 * 0.72 / 111691 * 100",
    "v4-review-public-payout_ratio-002": "49938 * 0.31 / 30122 * 100",
    "v4-review-public-payout_ratio-004": "26842 * 1.16 / 62728 * 100",
    "v4-review-public-ratio_of_aggregates-003": "(4027 + 4423) / (6092 + 7872) * 100",
    "v4-review-public-signed_multi_value_average-000": "(0 + 124 - 180 + 168) / 4",
    "v4-review-public-signed_multi_value_average-002": "(-18 - 161 + 0 - 95) / 4",
    "v4-review-public-signed_multi_value_average-004": "(-156 - 59 + 147 + 0) / 4",
    "v4-review-public-signed_multi_value_average-005": "(-65 - 79 + 0 - 101) / 4",
    "v4-review-public-signed_percent_change-001": "(280 - 162) / 162 * 100",
    "v4-review-public-signed_percent_change-003": "(414 - 471) / 471 * 100",
    "v4-review-public-signed_percent_change-004": "(64 - 71) / 71 * 100",
    "v4-review-public-signed_percent_change-005": "(545 - 395) / 395 * 100",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _check_hash(path: Path, expected: str) -> None:
    if _sha256(path) != expected:
        raise ValueError(f"source checksum mismatch: {path}")


def _zero_pass_ids(records: Sequence[Mapping[str, Any]], tasks: Sequence[Task]) -> set[str]:
    """Verify exactly eight indexed candidates per approved task before curating."""

    task_by_id = {task.task_id: task for task in tasks}
    if len(task_by_id) != len(tasks):
        raise ValueError("approved task IDs are not unique")
    samples: dict[str, set[int]] = {task_id: set() for task_id in task_by_id}
    successful: set[str] = set()
    for record in records:
        task = Task.from_dict(record["task"])
        if task.task_id not in task_by_id or task != task_by_id[task.task_id]:
            raise ValueError(f"search candidate differs from approved task: {task.task_id}")
        index = record["search"]["sample_index"]
        if isinstance(index, bool) or not isinstance(index, int) or index in samples[task.task_id]:
            raise ValueError(f"duplicate or invalid sample index: {task.task_id}")
        samples[task.task_id].add(index)
        if record["rollout"].get("task_success") is True:
            successful.add(task.task_id)
    if any(indices != set(range(8)) for indices in samples.values()):
        raise ValueError("search must contain samples 0–7 for every approved task")
    return set(task_by_id) - successful


def _format_final(value: int | float, decimals: int | None) -> str:
    if decimals is None:
        return str(value)
    if not isinstance(decimals, int) or decimals < 0:
        raise ValueError("answer_decimal_places must be a non-negative integer")
    quantum = Decimal(1).scaleb(-decimals)
    return format(
        Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP),
        f".{decimals}f",
    )


def build_manual_record(task: Task, expression: str) -> dict[str, Any]:
    """Execute an explicit program and create an honestly labeled trajectory."""

    if (
        task.split is not Split.TRAIN
        or task.kind is not TaskKind.CALCULATOR
        or task.allowed_tools != ("calculator",)
        or task.metadata.get("training_eligible") is not True
    ):
        raise ValueError(f"manual SFT requires a calculator-only train task: {task.task_id}")
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("manual calculator expression must be nonempty")
    call = ToolCall(call_id="call-1", name="calculator", arguments={"expression": expression})
    environment = EpisodeEnvironment({"calculator": execute_calculator}, max_tool_calls=1)
    environment.reset(task)
    observation = environment.step(call)
    if not observation.ok or not isinstance(observation.content, Mapping):
        raise ValueError(f"manual calculator call failed: {task.task_id}: {observation.error_code}")
    result = observation.content["value"]
    answer = _format_final(result, task.metadata.get("answer_decimal_places"))
    if answer != str(task.metadata.get("ground_truth_display")):
        raise ValueError(f"manual answer differs from displayed GT: {task.task_id}")
    episode = environment.finish(
        answer,
        trajectory_id=f"{SET_NAME}-{task.task_id}",
        model_id="assistant-authored-reference-program",
        seed=0,
        metadata={"trajectory_source": SET_NAME, "seed_not_applicable": True},
    )
    if not episode.verification.passed:
        raise ValueError(f"manual answer failed the verifier: {task.task_id}")
    raw_call = json.dumps(
        {"type": "tool_call", "name": "calculator", "arguments": {"expression": expression}},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    raw_final = json.dumps(
        {"type": "final", "answer": answer}, ensure_ascii=False, separators=(",", ":")
    )
    parsed_call = parse_model_action(raw_call, default_call_id="call-1")
    parsed_final = parse_model_action(raw_final)
    if not isinstance(parsed_call.action, ToolCall) or not isinstance(parsed_final.action, FinalAnswer):
        raise ValueError(f"manual outputs fail action protocol: {task.task_id}")
    return {
        "task": task.to_dict(),
        "trajectory": episode.trajectory.to_dict(),
        "verification": asdict(episode.verification),
        "rollout": {
            "task_success": True,
            "termination_reason": "assistant_authored_reference",
            "protocol_error": None,
        },
        "raw_outputs": [raw_call, raw_final],
        "provenance": {
            "trajectory_source": SET_NAME,
            "search_discovered": False,
            "authored_by": "Codex assistant; pending owner review",
            "source_expression_is_not_model_output": True,
        },
    }


def _verify_unique_examples(rows: Sequence[Mapping[str, Any]]) -> None:
    example_ids: set[str] = set()
    task_ids: set[str] = set()
    prompts: set[str] = set()
    for row in rows:
        example_id = row["example_id"]
        task_id = row["metadata"]["task_id"]
        user = [message["content"] for message in row["messages"] if message["role"] == "user"]
        if len(user) != 1 or example_id in example_ids or task_id in task_ids or user[0] in prompts:
            raise ValueError(f"duplicate or malformed merged SFT problem: {task_id}")
        example_ids.add(example_id)
        task_ids.add(task_id)
        prompts.add(user[0])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, default=Path("data/generated/v4_train_task_candidates_approved_v1.jsonl"))
    parser.add_argument("--tasks-manifest", type=Path, default=Path("artifacts/dataset_manifests/v4_train_task_candidates_approved_v1.json"))
    parser.add_argument("--search-candidates", type=Path, default=Path("outputs/search/qwen3_5_4b_v4_train_best_of_8_seed509/candidates.jsonl"))
    parser.add_argument("--search-package-manifest", type=Path, default=Path("data/review/v4_search_sft_candidates_v0/manifest.json"))
    parser.add_argument("--prior-sft", type=Path, default=Path("data/review/v4_search_sft_candidates_v0/v3_plus_v4_sft_candidates.jsonl"))
    parser.add_argument("--validation", type=Path, default=Path("data/generated/v4_validation_v1.jsonl"))
    parser.add_argument("--curated-tasks", type=Path, default=Path("data/generated/v4_train_tasks_curated_v2.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/review/v4_manual_zero_pass_v1"))
    parser.add_argument("--manifest", type=Path, default=Path("artifacts/dataset_manifests/v4_manual_zero_pass_v1.json"))
    args = parser.parse_args(argv)

    tasks_manifest = _json_object(args.tasks_manifest)
    search_manifest = _json_object(args.search_package_manifest)
    _check_hash(args.tasks, tasks_manifest["output_sha256"])
    _check_hash(args.search_candidates, search_manifest["inputs"]["candidates"]["sha256"])
    _check_hash(args.prior_sft, search_manifest["outputs"]["proposed_combined"]["sha256"])
    _check_hash(args.validation, search_manifest["inputs"]["v4_validation"]["sha256"])
    tasks = load_tasks_jsonl(args.tasks)
    validation = load_tasks_jsonl(args.validation)
    if len(tasks) != 162 or len(validation) != 64:
        raise ValueError("unexpected approved task or frozen validation count")
    if {task.family_id for task in tasks} & {task.family_id for task in validation}:
        raise ValueError("approved training families overlap validation")
    records = load_selected_trajectory_records(args.search_candidates)
    zero_ids = _zero_pass_ids(records, tasks)
    if len(zero_ids) != 45 or zero_ids != EXCLUDED_TASK_IDS | set(MANUAL_EXPRESSIONS):
        raise ValueError("manual program and exclusion IDs must exactly partition 45 zero-pass tasks")
    if EXCLUDED_TASK_IDS & set(MANUAL_EXPRESSIONS):
        raise ValueError("excluded task must not receive a manual trajectory")
    task_by_id = {task.task_id: task for task in tasks}
    curated_tasks = tuple(task for task in tasks if task.task_id not in EXCLUDED_TASK_IDS)
    if len(curated_tasks) != 158:
        raise ValueError("expected exactly 158 curated V4 train tasks")

    manual_records = tuple(
        build_manual_record(task_by_id[task_id], expression)
        for task_id, expression in MANUAL_EXPRESSIONS.items()
    )
    manual_examples = []
    for record in manual_records:
        example = build_sft_example(record)
        example["metadata"].update({
            "trajectory_source": SET_NAME,
            "mixture_source": "v4-manual-zero-pass",
            "search_discovered": False,
            "authored_by": "Codex assistant; pending owner review",
            "review_status": "pending_owner_review",
            "calculator_replay_verified": True,
            "answer_decimals": record["task"]["metadata"].get("answer_decimal_places"),
        })
        manual_examples.append(example)
    prior_examples = load_selected_trajectory_records(args.prior_sft)
    if len(prior_examples) != 173:
        raise ValueError("expected the prior 173-row staged SFT set")
    combined = (*prior_examples, *manual_examples)
    _verify_unique_examples(combined)
    if any(row["metadata"]["task_id"] in EXCLUDED_TASK_IDS for row in combined):
        raise ValueError("excluded V4 task leaked into the staged SFT merge")
    if len(combined) != 214:
        raise ValueError("expected 214 distinct staged SFT examples")

    args.curated_tasks.parent.mkdir(parents=True, exist_ok=True)
    args.curated_tasks.write_text(
        "\n".join(json.dumps(task.to_dict(), ensure_ascii=False, sort_keys=True) for task in curated_tasks) + "\n",
        encoding="utf-8",
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    trajectory_path = args.output_dir / "assistant_authored_trajectories.jsonl"
    manual_sft_path = args.output_dir / "manual_sft_custom.jsonl"
    combined_path = args.output_dir / "v3_v4_search_plus_manual_sft_candidates.jsonl"
    review_path = args.output_dir / "manual_program_review.jsonl"
    write_trajectory_records_jsonl(manual_records, trajectory_path)
    write_sft_jsonl(manual_examples, manual_sft_path)
    write_sft_jsonl(combined, combined_path)
    review_rows = [
        {
            "task_id": record["task"]["task_id"],
            "family_id": record["task"]["family_id"],
            "prompt": record["task"]["prompt"],
            "expression": record["trajectory"]["steps"][0]["tool_call"]["arguments"]["expression"],
            "calculator_value": record["trajectory"]["steps"][0]["observation"]["content"]["value"],
            "final_answer": record["trajectory"]["final_answer"],
            "target_value": record["task"]["ground_truth"]["value"],
            "review_status": "pending_owner_review",
        }
        for record in manual_records
    ]
    review_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in review_rows) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "dataset": SET_NAME,
        "train_ready": False,
        "review_status": "pending_owner_review",
        "original_train_tasks": len(tasks),
        "excluded_task_ids": sorted(EXCLUDED_TASK_IDS),
        "curated_train_tasks": len(curated_tasks),
        "zero_pass_tasks": len(zero_ids),
        "assistant_authored_trajectories": len(manual_records),
        "prior_staged_sft": len(prior_examples),
        "combined_staged_sft": len(combined),
        "by_family": dict(sorted(Counter(record["task"]["family_id"] for record in manual_records).items())),
        "sources": {
            "tasks": {"path": str(args.tasks), "sha256": _sha256(args.tasks)},
            "search_candidates": {"path": str(args.search_candidates), "sha256": _sha256(args.search_candidates)},
            "prior_sft": {"path": str(args.prior_sft), "sha256": _sha256(args.prior_sft)},
            "validation": {"path": str(args.validation), "sha256": _sha256(args.validation)},
        },
        "outputs": {
            "curated_tasks": {"path": str(args.curated_tasks), "sha256": _sha256(args.curated_tasks)},
            "manual_trajectories": {"path": str(trajectory_path), "sha256": _sha256(trajectory_path)},
            "manual_sft": {"path": str(manual_sft_path), "sha256": _sha256(manual_sft_path)},
            "combined_staged_sft": {"path": str(combined_path), "sha256": _sha256(combined_path)},
            "review": {"path": str(review_path), "sha256": _sha256(review_path)},
        },
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
