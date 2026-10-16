"""Package reviewed V3 Search-SFT, Reference-SFT, and mixed custom data.

The primary package uses one protocol throughout: the JSON action protocol
used by the search runner.  Native structured-tool rows remain a separate
ablation and are never mixed into these files.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .dataset import load_tasks_jsonl
from .schemas import Task
from .sft_data import (
    SFTDataError,
    build_sft_example,
    load_selected_trajectory_records,
    merge_sft_examples,
    sft_dataset_summary,
    write_sft_jsonl,
    write_trajectory_records_jsonl,
)
from .tools.calculator import CalculatorError, calculator
from .v3_reference_program import build_v3_reference_program_custom_sft


PACKAGE_NAME = "v3-reviewed-sft-custom-protocol-v1"
REJECTED_SEED_TASK_IDS = {"v3-gsm8k-train-5655-calculator"}
APPROVED_REVISION_TASK_IDS = {
    "v3-public-564f2d6051c0-arithmetic-revised-v2",
    "v3-public-993d968c025a-arithmetic-revised-v2",
    "v3-public-9f547636b5b4-arithmetic-revised-v2",
}
APPROVED_FOLLOWUP_TASK_IDS = {
    "v3-public-ab005e597c33-arithmetic-rounding-revised-v1"
}


class V3SFTPackageError(ValueError):
    """The reviewed source set cannot be packaged without changing its meaning."""


def _decimal(value: Any, field: str) -> Decimal:
    if isinstance(value, bool):
        raise V3SFTPackageError(f"{field} must be numeric")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise V3SFTPackageError(f"{field} must be numeric") from exc
    if not number.is_finite():
        raise V3SFTPackageError(f"{field} must be finite")
    return number


def _verify_calculator_replay(record: Mapping[str, Any]) -> str:
    """Replay a reviewed search path and return its visible path type."""

    trajectory = record.get("trajectory")
    if not isinstance(trajectory, Mapping):
        raise V3SFTPackageError("search record trajectory must be an object")
    steps = trajectory.get("steps")
    if not isinstance(steps, list):
        raise V3SFTPackageError("search record steps must be an array")
    if not steps:
        return "direct-answer-on-calculator-available-task"
    if len(steps) != 1:
        raise V3SFTPackageError("reviewed V3 tool paths must contain exactly one step")

    step = steps[0]
    call = step.get("tool_call") if isinstance(step, Mapping) else None
    observation = step.get("observation") if isinstance(step, Mapping) else None
    if not isinstance(call, Mapping) or not isinstance(observation, Mapping):
        raise V3SFTPackageError("tool step must contain call and observation objects")
    arguments = call.get("arguments")
    if call.get("name") != "calculator" or not isinstance(arguments, Mapping):
        raise V3SFTPackageError("reviewed V3 tool path must call calculator")
    if set(arguments) != {"expression"} or not isinstance(arguments["expression"], str):
        raise V3SFTPackageError("calculator path must contain exactly one expression")
    if observation.get("ok") is not True:
        raise V3SFTPackageError("reviewed calculator observation must be successful")
    content = observation.get("content")
    if not isinstance(content, Mapping) or "value" not in content:
        raise V3SFTPackageError("calculator observation must contain a value")
    try:
        replayed = calculator(arguments["expression"])
    except CalculatorError as exc:
        raise V3SFTPackageError(f"calculator replay failed: {exc}") from exc
    if _decimal(replayed, "replayed value") != _decimal(content["value"], "observed value"):
        raise V3SFTPackageError("calculator replay does not match stored observation")
    return "tool-assisted"


def select_reviewed_search_records(
    seed_records: Sequence[Mapping[str, Any]],
    revision_records: Sequence[Mapping[str, Any]],
    followup_records: Sequence[Mapping[str, Any]],
) -> tuple[tuple[Mapping[str, Any], str], ...]:
    """Select exactly the 32 owner-reviewed strict-success trajectories."""

    seed = tuple(
        record
        for record in seed_records
        if record.get("task", {}).get("metadata", {}).get("training_eligible") is True
        and record.get("task", {}).get("task_id") not in REJECTED_SEED_TASK_IDS
    )
    if len(seed) != 28:
        raise V3SFTPackageError(f"expected 28 reviewed seed trajectories, found {len(seed)}")

    revision_by_id = {
        record.get("task", {}).get("task_id"): record for record in revision_records
    }
    missing_revisions = sorted(APPROVED_REVISION_TASK_IDS - set(revision_by_id))
    if missing_revisions:
        raise V3SFTPackageError(f"missing approved revision trajectories: {missing_revisions}")
    revision = tuple(revision_by_id[task_id] for task_id in sorted(APPROVED_REVISION_TASK_IDS))

    followup_by_id = {
        record.get("task", {}).get("task_id"): record for record in followup_records
    }
    if set(followup_by_id) != APPROVED_FOLLOWUP_TASK_IDS:
        raise V3SFTPackageError("follow-up trajectory set does not match its approval list")
    followup = tuple(followup_by_id[task_id] for task_id in sorted(APPROVED_FOLLOWUP_TASK_IDS))

    selected = (
        *((record, "v3-seed-best-of-8-v1") for record in seed),
        *((record, "v3-zero-pass-revisions-best-of-8-v2") for record in revision),
        *((record, "v3-rounding-followup-best-of-8-v1") for record in followup),
    )
    task_ids = [record["task"]["task_id"] for record, _ in selected]
    if len(selected) != 32 or len(set(task_ids)) != 32:
        raise V3SFTPackageError("reviewed search package must contain 32 unique tasks")
    return selected


def build_search_sft_examples(
    selected: Sequence[tuple[Mapping[str, Any], str]],
) -> tuple[dict[str, Any], ...]:
    examples = []
    for record, source_run in selected:
        path_type = _verify_calculator_replay(record)
        try:
            example = build_sft_example(record)
        except SFTDataError as exc:
            raise V3SFTPackageError(str(exc)) from exc
        example["metadata"] = {
            **example["metadata"],
            "format": "search-custom-protocol-v1",
            "package": PACKAGE_NAME,
            "trajectory_source": "search-discovered",
            "search_discovered": True,
            "source_run": source_run,
            "path_type": path_type,
            "calculator_replay_verified": path_type == "tool-assisted",
        }
        examples.append(example)
    if sum(row["metadata"]["path_type"] == "tool-assisted" for row in examples) != 27:
        raise V3SFTPackageError("expected 27 tool-assisted search examples")
    if sum(row["metadata"]["path_type"].startswith("direct-answer") for row in examples) != 5:
        raise V3SFTPackageError("expected 5 direct-answer search examples")
    return tuple(examples)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-verified", required=True, type=Path)
    parser.add_argument("--revision-verified", required=True, type=Path)
    parser.add_argument("--followup-verified", required=True, type=Path)
    parser.add_argument("--tasks", action="append", required=True, type=Path)
    parser.add_argument("--selected-output", required=True, type=Path)
    parser.add_argument("--search-output", required=True, type=Path)
    parser.add_argument("--reference-output", required=True, type=Path)
    parser.add_argument("--mixed-output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args(argv)

    selected = select_reviewed_search_records(
        load_selected_trajectory_records(args.seed_verified),
        load_selected_trajectory_records(args.revision_verified),
        load_selected_trajectory_records(args.followup_verified),
    )
    selected_records = []
    for record, source_run in selected:
        copied = dict(record)
        copied["package"] = {
            "name": PACKAGE_NAME,
            "trajectory_source": "search-discovered",
            "source_run": source_run,
        }
        selected_records.append(copied)
    write_trajectory_records_jsonl(selected_records, args.selected_output)

    search_examples = build_search_sft_examples(selected)
    tasks: tuple[Task, ...] = tuple(
        task for path in args.tasks for task in load_tasks_jsonl(path)
    )
    reference_examples = build_v3_reference_program_custom_sft(tasks)
    if len(reference_examples) != 26:
        raise V3SFTPackageError("reference package must contain 26 examples")
    reference_examples = tuple(
        {
            **row,
            "metadata": {**row["metadata"], "package": PACKAGE_NAME},
        }
        for row in reference_examples
    )
    mixed_examples = merge_sft_examples(
        (
            ("search-discovered", search_examples),
            ("reference-program", reference_examples),
        )
    )
    if len(mixed_examples) != 58:
        raise V3SFTPackageError("mixed package must contain 58 examples")

    write_sft_jsonl(search_examples, args.search_output)
    write_sft_jsonl(reference_examples, args.reference_output)
    write_sft_jsonl(mixed_examples, args.mixed_output)

    input_paths = (
        args.seed_verified,
        args.revision_verified,
        args.followup_verified,
        *args.tasks,
    )
    outputs = {
        "selected_trajectories": args.selected_output,
        "search_sft": args.search_output,
        "reference_sft": args.reference_output,
        "mixed_sft": args.mixed_output,
    }
    manifest = {
        "package": PACKAGE_NAME,
        "protocol": "custom-json-actions-v1",
        "inputs": [
            {"path": str(path), "sha256": _sha256(path)} for path in input_paths
        ],
        "search": {
            **sft_dataset_summary(search_examples),
            "tool_assisted": 27,
            "direct_answer": 5,
            "trajectory_source": "search-discovered",
        },
        "reference": {
            **sft_dataset_summary(reference_examples),
            "trajectory_source": "reference-program",
        },
        "mixed": sft_dataset_summary(mixed_examples),
        "outputs": {
            name: {"path": str(path), "sha256": _sha256(path)}
            for name, path in outputs.items()
        },
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
