"""Freeze the train-only V4 GRPO prompts selected by measured outcome variance.

Tier A invariants live here rather than in the training framework:

* selection uses only the completed train-only probe, never validation/test;
* a task is eligible iff its eight-sample group has both correct and incorrect
  verified final outcomes (``nonzero_outcome_reward_variance``);
* the frozen rows are byte-stable projections of the reviewed V4 train pool;
* train, validation, and test family IDs remain disjoint;
* an existing frozen output is never silently replaced with different data.

The probe is diagnostic inference.  Freezing its eligible prompt IDs does not
claim that GRPO training ran or improved a model.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

from verifiable_posttraining.dataset import (
    load_tasks_jsonl,
    validate_task_dataset,
    write_tasks_jsonl,
)
from verifiable_posttraining.schemas import Split, TaskKind


SOURCE_DATASET_SHA256 = (
    "d24a0b360ce7c771d31e05782eabf863a86f43aa349def19a5c0a84ec6423c96"
)
PROBE_METRICS_SHA256 = (
    "b99f35a5f757799c1729f9803940ad2ef66118e33d765bed244ceab2ede02ece"
)
EXPECTED_SOURCE_TASKS = 158
EXPECTED_EPISODES = 1264
EXPECTED_TOTAL_VARIANCE_TASKS = 58
EXPECTED_OUTCOME_VARIANCE_TASKS = 53
EXPECTED_ALL_CORRECT_TASKS = 103
EXPECTED_ALL_INCORRECT_TASKS = 2
EXPECTED_FAMILIES = 16


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_hash(path: Path, expected: str) -> None:
    actual = _sha256(path)
    if actual != expected:
        raise ValueError(f"input hash mismatch for {path}: {actual} != {expected}")


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON document must be an object: {path}")
    return value


def _selected_probe_rows(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    if (
        metrics.get("status") != "completed"
        or metrics.get("split") != "train"
        or metrics.get("inference_only") is not True
        or metrics.get("model_parameters_updated") is not False
        or metrics.get("dataset_sha256") != SOURCE_DATASET_SHA256
    ):
        raise ValueError("probe was not a completed train-only inference run")

    summary = metrics.get("summary")
    if not isinstance(summary, dict):
        raise ValueError("probe metrics have no summary object")
    expected = {
        "task_count": EXPECTED_SOURCE_TASKS,
        "episode_count": EXPECTED_EPISODES,
        "nonzero_total_reward_variance_task_count": EXPECTED_TOTAL_VARIANCE_TASKS,
        "nonzero_outcome_reward_variance_task_count": EXPECTED_OUTCOME_VARIANCE_TASKS,
        "all_outcomes_correct_task_count": EXPECTED_ALL_CORRECT_TASKS,
        "all_outcomes_incorrect_task_count": EXPECTED_ALL_INCORRECT_TASKS,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            raise ValueError(f"unexpected probe summary {key}: {summary.get(key)!r}")

    task_rows = summary.get("tasks")
    if not isinstance(task_rows, list) or len(task_rows) != EXPECTED_SOURCE_TASKS:
        raise ValueError("probe task summaries are missing or incomplete")
    selected = [
        row for row in task_rows
        if isinstance(row, dict) and row.get("nonzero_outcome_reward_variance") is True
    ]
    if len(selected) != EXPECTED_OUTCOME_VARIANCE_TASKS:
        raise ValueError("probe outcome-variance selection count changed")
    if any(not 0 < row.get("outcome_successes", -1) < row.get("samples", -1)
           for row in selected):
        raise ValueError("selected group does not contain both correct and incorrect outcomes")
    task_ids = [row.get("task_id") for row in selected]
    if any(not isinstance(task_id, str) or not task_id for task_id in task_ids):
        raise ValueError("selected probe row has no task ID")
    if len(set(task_ids)) != len(task_ids):
        raise ValueError("probe selection contains duplicate task IDs")
    return selected


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("data/generated/v4_train_tasks_curated_v2.jsonl"),
    )
    parser.add_argument(
        "--probe-metrics",
        type=Path,
        default=Path(
            "artifacts/metrics/qwen3_5_4b_v4_grpo_reward_probe_seed719.json"
        ),
    )
    parser.add_argument(
        "--validation",
        type=Path,
        default=Path("data/generated/v4_validation_v1.jsonl"),
    )
    parser.add_argument(
        "--test",
        type=Path,
        default=Path("data/generated/v4_test_v1.jsonl"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "data/generated/v4_grpo_train_outcome_variance_seed719_v1.jsonl"
        ),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(
            "artifacts/dataset_manifests/"
            "v4_grpo_train_outcome_variance_seed719_v1.json"
        ),
    )
    parser.add_argument("--frozen-on", default="2026-10-08")
    args = parser.parse_args(argv)

    _require_hash(args.source, SOURCE_DATASET_SHA256)
    _require_hash(args.probe_metrics, PROBE_METRICS_SHA256)
    metrics = _read_object(args.probe_metrics)
    selected_probe_rows = _selected_probe_rows(metrics)
    selected_ids = {row["task_id"] for row in selected_probe_rows}

    source = load_tasks_jsonl(args.source)
    validation = load_tasks_jsonl(args.validation)
    test = load_tasks_jsonl(args.test)
    if len(source) != EXPECTED_SOURCE_TASKS:
        raise ValueError("unexpected V4 curated train count")
    source_by_id = {task.task_id: task for task in source}
    if len(source_by_id) != len(source):
        raise ValueError("source train pool contains duplicate task IDs")
    missing = selected_ids - set(source_by_id)
    if missing:
        raise ValueError(f"probe selected unknown task IDs: {sorted(missing)}")

    frozen = tuple(task for task in source if task.task_id in selected_ids)
    if len(frozen) != EXPECTED_OUTCOME_VARIANCE_TASKS:
        raise ValueError("frozen GRPO task count changed")
    if any(
        task.split is not Split.TRAIN
        or task.kind is not TaskKind.CALCULATOR
        or task.allowed_tools != ("calculator",)
        or task.metadata.get("training_eligible") is not True
        for task in frozen
    ):
        raise ValueError("frozen GRPO prompts must be calculator-only eligible train tasks")

    frozen_families = {task.family_id for task in frozen}
    validation_families = {task.family_id for task in validation}
    test_families = {task.family_id for task in test}
    if len(frozen_families) != EXPECTED_FAMILIES:
        raise ValueError("unexpected number of represented GRPO train families")
    if frozen_families & validation_families or frozen_families & test_families:
        raise ValueError("GRPO train families overlap validation or test")
    validate_task_dataset((*frozen, *validation, *test))

    if args.output.exists():
        if load_tasks_jsonl(args.output) != frozen:
            raise ValueError(f"refusing to overwrite a different frozen file: {args.output}")
    else:
        write_tasks_jsonl(frozen, args.output)

    probe_by_id = {row["task_id"]: row for row in selected_probe_rows}
    outcome_histogram = Counter(
        int(probe_by_id[task.task_id]["outcome_successes"]) for task in frozen
    )
    family_counts = Counter(task.family_id for task in frozen)
    total_only_ids = sorted(
        row["task_id"]
        for row in metrics["summary"]["tasks"]
        if row.get("nonzero_total_reward_variance") is True
        and row.get("nonzero_outcome_reward_variance") is not True
    )
    if len(total_only_ids) != EXPECTED_TOTAL_VARIANCE_TASKS - EXPECTED_OUTCOME_VARIANCE_TASKS:
        raise ValueError("unexpected total-only reward-variance exclusion count")

    manifest: dict[str, Any] = {
        "dataset": "v4_grpo_train_outcome_variance_seed719_v1",
        "status": "frozen",
        "frozen_on": args.frozen_on,
        "split": "train",
        "training_eligible": True,
        "evaluation_only": False,
        "learning_tier": "A - must hand-write selection and split-leakage invariants",
        "selection_rule": (
            "include every reviewed V4 train task whose eight-sample seed-719 probe "
            "has nonzero verified numeric-outcome reward variance; apply no family cap"
        ),
        "count": len(frozen),
        "family_count": len(family_counts),
        "family_counts": dict(family_counts),
        "outcome_successes_of_8_histogram": {
            str(key): outcome_histogram[key] for key in sorted(outcome_histogram)
        },
        "probe_summary": {
            "source_tasks": EXPECTED_SOURCE_TASKS,
            "episodes": EXPECTED_EPISODES,
            "samples_per_task": 8,
            "all_outcomes_correct_tasks": EXPECTED_ALL_CORRECT_TASKS,
            "all_outcomes_incorrect_tasks": EXPECTED_ALL_INCORRECT_TASKS,
            "nonzero_total_reward_variance_tasks": EXPECTED_TOTAL_VARIANCE_TASKS,
            "nonzero_outcome_reward_variance_tasks": EXPECTED_OUTCOME_VARIANCE_TASKS,
            "excluded_total_only_variance_task_ids": total_only_ids,
        },
        "inputs": {
            "source_train": args.source.as_posix(),
            "source_train_sha256": _sha256(args.source),
            "probe_metrics": args.probe_metrics.as_posix(),
            "probe_metrics_sha256": _sha256(args.probe_metrics),
            "validation": args.validation.as_posix(),
            "validation_sha256": _sha256(args.validation),
            "test": args.test.as_posix(),
            "test_sha256": _sha256(args.test),
        },
        "frozen_task_ids": [task.task_id for task in frozen],
        "output": args.output.as_posix(),
        "output_sha256": _sha256(args.output),
        "interpretation_limits": [
            "This is a train-prompt selection from one stochastic probe seed, not an evaluation result.",
            "Freezing prompts is not a GRPO run and does not demonstrate model improvement.",
            "Two zero-of-eight tasks are excluded because numeric-outcome reward had no positive group member.",
            "Three eight-of-eight tasks with only auxiliary/format variance are excluded.",
            "The 53 prompts are weakness-weighted and not family-balanced; report validation/test macro-family metrics.",
        ],
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
