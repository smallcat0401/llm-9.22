"""Tier A: auditable aggregate metrics for evaluation rollouts."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Iterable, Mapping

from .rollout import RolloutResult
from .schemas import TaskKind


@dataclass(frozen=True, slots=True)
class EvaluationMetrics:
    task_count: int
    task_success_count: int
    task_success_rate: float
    verifier_pass_count: int
    verifier_pass_rate: float
    protocol_error_count: int
    protocol_error_rate: float
    tool_selection_correct_count: int
    tool_selection_accuracy: float
    recorded_tool_call_count: int
    rejected_tool_call_count: int
    failed_tool_call_count: int
    invalid_tool_call_rate: float
    average_recorded_tool_calls: float
    no_tool_task_count: int
    over_tool_task_count: int
    over_tool_rate: float
    success_by_kind: Mapping[str, Mapping[str, int | float]]
    termination_counts: Mapping[str, int]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _safe_rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def compute_evaluation_metrics(
    rollouts: Iterable[RolloutResult],
) -> EvaluationMetrics:
    """Compute outcome and tool-use diagnostics without changing task correctness.

    Task success remains the strict rollout result: a verified final answer that
    also obeyed the action protocol. Tool selection is diagnostic. A tool task
    selects correctly when it calls at least one allowed tool; a no-tool task
    selects correctly only when it makes no tool-call attempt.
    """

    results = list(rollouts)
    if not results:
        raise ValueError("at least one rollout is required")

    task_success_count = sum(result.task_success for result in results)
    verifier_pass_count = sum(result.episode.verification.passed for result in results)
    protocol_error_count = sum(result.protocol_error is not None for result in results)
    recorded_tool_call_count = 0
    rejected_tool_call_count = 0
    failed_tool_call_count = 0
    tool_selection_correct_count = 0
    no_tool_task_count = 0
    over_tool_task_count = 0
    termination_counts: Counter[str] = Counter()
    kind_counts: Counter[str] = Counter()
    kind_successes: Counter[str] = Counter()

    for result in results:
        task = result.episode.task
        trajectory = result.episode.trajectory
        steps = trajectory.steps
        rejected_calls = int(trajectory.metadata.get("rejected_tool_calls", 0))
        recorded_tool_call_count += len(steps)
        rejected_tool_call_count += rejected_calls
        failed_tool_call_count += sum(not step.observation.ok for step in steps)
        termination_counts[result.termination_reason] += 1
        kind_counts[task.kind.value] += 1
        kind_successes[task.kind.value] += int(result.task_success)

        attempted_tool_call = bool(steps) or rejected_calls > 0
        if task.kind is TaskKind.NO_TOOL:
            no_tool_task_count += 1
            if attempted_tool_call:
                over_tool_task_count += 1
            else:
                tool_selection_correct_count += 1
        elif any(step.tool_call.name in task.allowed_tools for step in steps):
            tool_selection_correct_count += 1

    task_count = len(results)
    attempted_tool_call_count = recorded_tool_call_count + rejected_tool_call_count
    invalid_tool_call_count = failed_tool_call_count + rejected_tool_call_count
    success_by_kind = {
        kind: {
            "tasks": count,
            "successes": kind_successes[kind],
            "success_rate": _safe_rate(kind_successes[kind], count),
        }
        for kind, count in sorted(kind_counts.items())
    }
    return EvaluationMetrics(
        task_count=task_count,
        task_success_count=task_success_count,
        task_success_rate=_safe_rate(task_success_count, task_count),
        verifier_pass_count=verifier_pass_count,
        verifier_pass_rate=_safe_rate(verifier_pass_count, task_count),
        protocol_error_count=protocol_error_count,
        protocol_error_rate=_safe_rate(protocol_error_count, task_count),
        tool_selection_correct_count=tool_selection_correct_count,
        tool_selection_accuracy=_safe_rate(tool_selection_correct_count, task_count),
        recorded_tool_call_count=recorded_tool_call_count,
        rejected_tool_call_count=rejected_tool_call_count,
        failed_tool_call_count=failed_tool_call_count,
        invalid_tool_call_rate=_safe_rate(
            invalid_tool_call_count, attempted_tool_call_count
        ),
        average_recorded_tool_calls=recorded_tool_call_count / task_count,
        no_tool_task_count=no_tool_task_count,
        over_tool_task_count=over_tool_task_count,
        over_tool_rate=_safe_rate(over_tool_task_count, no_tool_task_count),
        success_by_kind=success_by_kind,
        termination_counts=dict(sorted(termination_counts.items())),
    )
