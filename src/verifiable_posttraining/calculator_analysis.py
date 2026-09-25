"""Tier A calculator failure attribution for saved evaluation records.

The classifier never treats a successful tool invocation as proof of task
correctness.  It separately checks whether the tool result matches the task
ground truth and whether the final answer preserves that correct result.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from enum import Enum
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .dataset import load_tasks_jsonl
from .schemas import Task
from .verifier import normalize_numeric_answer, verify_numeric_answer


class CalculatorFailureCategory(str, Enum):
    SUCCESS = "success"
    NO_TOOL_CALL = "no_tool_call"
    TOOL_EXECUTION_FAILED = "tool_execution_failed"
    WRONG_TOOL_RESULT = "wrong_tool_result"
    INVALID_FINAL = "invalid_final"
    CORRECT_TOOL_RESULT_BAD_FINAL = "correct_tool_result_bad_final"
    PROTOCOL_ERROR = "protocol_error"


@dataclass(frozen=True, slots=True)
class CalculatorRecordAnalysis:
    task_id: str
    family_id: str
    category: CalculatorFailureCategory
    expression: str | None
    tool_value: float | None
    predicted_value: float | None
    target_value: float


def _number_or_none(value: Any) -> float | None:
    try:
        return float(normalize_numeric_answer(value))
    except ValueError:
        return None


def _native_expression(messages: Sequence[Any]) -> str | None:
    for message in messages:
        if not isinstance(message, Mapping):
            continue
        calls = message.get("tool_calls")
        if not isinstance(calls, list) or len(calls) != 1:
            continue
        call = calls[0]
        if not isinstance(call, Mapping):
            continue
        function = call.get("function")
        if not isinstance(function, Mapping):
            continue
        arguments = function.get("arguments")
        if isinstance(arguments, Mapping) and isinstance(arguments.get("expression"), str):
            return arguments["expression"]
    return None


def _native_tool_content(messages: Sequence[Any]) -> Any:
    for message in messages:
        if isinstance(message, Mapping) and message.get("role") == "tool":
            return message.get("content")
    return None


def analyze_native_record(
    record: Mapping[str, Any],
    task: Task,
) -> CalculatorRecordAnalysis:
    """Classify one native-tool record using the current task verifier."""

    messages = record.get("messages", [])
    if not isinstance(messages, Sequence) or isinstance(messages, (str, bytes)):
        messages = []
    expression = _native_expression(messages)
    tool_value = _number_or_none(_native_tool_content(messages))
    predicted_value = _number_or_none(record.get("verification", {}).get("predicted_value"))
    target_value = float(task.ground_truth["value"])

    if not record.get("tool_called"):
        category = CalculatorFailureCategory.NO_TOOL_CALL
    elif not record.get("tool_succeeded") or tool_value is None:
        category = CalculatorFailureCategory.TOOL_EXECUTION_FAILED
    elif not verify_numeric_answer(tool_value, task.ground_truth).passed:
        category = CalculatorFailureCategory.WRONG_TOOL_RESULT
    elif predicted_value is None:
        category = CalculatorFailureCategory.INVALID_FINAL
    elif verify_numeric_answer(predicted_value, task.ground_truth).passed:
        category = CalculatorFailureCategory.SUCCESS
    else:
        category = CalculatorFailureCategory.CORRECT_TOOL_RESULT_BAD_FINAL

    return CalculatorRecordAnalysis(
        task_id=task.task_id,
        family_id=task.family_id,
        category=category,
        expression=expression,
        tool_value=tool_value,
        predicted_value=predicted_value,
        target_value=target_value,
    )


def analyze_trajectory_record(record: Mapping[str, Any]) -> CalculatorRecordAnalysis:
    """Classify one custom-protocol trajectory record with embedded task data."""

    task = Task.from_dict(record["task"])
    trajectory = record.get("trajectory", {})
    steps = trajectory.get("steps", []) if isinstance(trajectory, Mapping) else []
    step = steps[0] if isinstance(steps, list) and steps else None
    expression = None
    tool_value = None
    if isinstance(step, Mapping):
        call = step.get("tool_call", {})
        arguments = call.get("arguments", {}) if isinstance(call, Mapping) else {}
        if isinstance(arguments, Mapping) and isinstance(arguments.get("expression"), str):
            expression = arguments["expression"]
        observation = step.get("observation", {})
        if isinstance(observation, Mapping) and observation.get("ok"):
            content = observation.get("content", {})
            if isinstance(content, Mapping):
                tool_value = _number_or_none(content.get("value"))

    verification = record.get("verification", {})
    predicted_value = _number_or_none(
        verification.get("predicted_value") if isinstance(verification, Mapping) else None
    )
    target_value = float(task.ground_truth["value"])
    rollout = record.get("rollout", {})

    if isinstance(rollout, Mapping) and rollout.get("protocol_error"):
        category = CalculatorFailureCategory.PROTOCOL_ERROR
    elif not step:
        category = CalculatorFailureCategory.NO_TOOL_CALL
    elif tool_value is None:
        category = CalculatorFailureCategory.TOOL_EXECUTION_FAILED
    elif not verify_numeric_answer(tool_value, task.ground_truth).passed:
        category = CalculatorFailureCategory.WRONG_TOOL_RESULT
    elif predicted_value is None:
        category = CalculatorFailureCategory.INVALID_FINAL
    elif verify_numeric_answer(predicted_value, task.ground_truth).passed:
        category = CalculatorFailureCategory.SUCCESS
    else:
        category = CalculatorFailureCategory.CORRECT_TOOL_RESULT_BAD_FINAL

    return CalculatorRecordAnalysis(
        task_id=task.task_id,
        family_id=task.family_id,
        category=category,
        expression=expression,
        tool_value=tool_value,
        predicted_value=predicted_value,
        target_value=target_value,
    )


def summarize_analyses(
    analyses: Sequence[CalculatorRecordAnalysis],
) -> dict[str, Any]:
    counts = {category.value: 0 for category in CalculatorFailureCategory}
    for analysis in analyses:
        counts[analysis.category.value] += 1
    by_family: dict[str, dict[str, Any]] = {}
    for analysis in analyses:
        family = by_family.setdefault(
            analysis.family_id,
            {
                "record_count": 0,
                "category_counts": {
                    category.value: 0 for category in CalculatorFailureCategory
                },
            },
        )
        family["record_count"] += 1
        family["category_counts"][analysis.category.value] += 1
    return {
        "record_count": len(analyses),
        "category_counts": counts,
        "by_family": by_family,
        "records": [
            {**asdict(analysis), "category": analysis.category.value}
            for analysis in analyses
        ],
    }


def _read_jsonl(path: Path) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("native", "trajectory"), required=True)
    parser.add_argument("--records", required=True)
    parser.add_argument("--tasks")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)

    records = _read_jsonl(Path(args.records))
    if args.format == "native":
        if not args.tasks:
            parser.error("--tasks is required for native records")
        tasks = {task.task_id: task for task in load_tasks_jsonl(args.tasks)}
        analyses = tuple(analyze_native_record(record, tasks[record["task_id"]]) for record in records)
    else:
        # Paired external evaluations also contain a no-tool control for every
        # problem.  Exclude those controls from calculator failure attribution;
        # their lack of a tool call is expected behavior, not a failure.
        calculator_records = tuple(
            record
            for record in records
            if isinstance(record.get("task"), Mapping)
            and record["task"].get("kind") == "calculator"
        )
        analyses = tuple(
            analyze_trajectory_record(record) for record in calculator_records
        )

    report = summarize_analyses(analyses)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
