"""Tier B: deterministic sequential evaluation over canonical tasks."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Callable, Iterable, Mapping

from .environment import ToolExecutor
from .metrics import EvaluationMetrics, compute_evaluation_metrics
from .rollout import GenerationPolicy, RolloutResult, run_episode
from .schemas import Task

ProgressCallback = Callable[[int, int, RolloutResult, float], None]


@dataclass(frozen=True, slots=True)
class EvaluationRun:
    rollouts: tuple[RolloutResult, ...]
    latency_seconds: tuple[float, ...]
    metrics: EvaluationMetrics

    def __post_init__(self) -> None:
        if len(self.rollouts) != len(self.latency_seconds):
            raise ValueError("rollouts and latency_seconds must align")

    def to_dict(self) -> dict[str, object]:
        records = [
            rollout_record(rollout, latency_seconds=latency)
            for rollout, latency in zip(self.rollouts, self.latency_seconds, strict=True)
        ]
        return {"metrics": self.metrics.to_dict(), "records": records}


def rollout_record(result: RolloutResult, *, latency_seconds: float) -> dict[str, object]:
    """Serialize all evidence needed to audit one scored completion."""

    return {
        "task": result.episode.task.to_dict(),
        "raw_outputs": list(result.raw_outputs),
        "trajectory": result.episode.trajectory.to_dict(),
        "verification": asdict(result.episode.verification),
        "rollout": {
            "termination_reason": result.termination_reason,
            "protocol_error": result.protocol_error,
            "task_success": result.task_success,
        },
        "runtime": {"latency_seconds": round(latency_seconds, 6)},
    }


def evaluate_tasks(
    tasks: Iterable[Task],
    policy: GenerationPolicy,
    tool_executors: Mapping[str, ToolExecutor],
    *,
    run_id: str,
    model_id: str,
    seed: int,
    max_model_turns: int = 3,
    max_tool_calls: int = 2,
    on_result: ProgressCallback | None = None,
) -> EvaluationRun:
    """Evaluate tasks in their supplied order with stable per-task seeds."""

    task_list = list(tasks)
    if not task_list:
        raise ValueError("at least one task is required")
    if not run_id.strip():
        raise ValueError("run_id must be non-empty")
    if len({task.task_id for task in task_list}) != len(task_list):
        raise ValueError("evaluation task ids must be unique")

    rollouts = []
    latencies = []
    total = len(task_list)
    for index, task in enumerate(task_list):
        task_seed = seed + index * 100
        started = time.perf_counter()
        rollout = run_episode(
            task,
            policy,
            dict(tool_executors),
            trajectory_id=f"{run_id}-{task.task_id}",
            model_id=model_id,
            seed=task_seed,
            max_model_turns=max_model_turns,
            max_tool_calls=max_tool_calls,
        )
        latency = time.perf_counter() - started
        rollouts.append(rollout)
        latencies.append(latency)
        if on_result is not None:
            on_result(index + 1, total, rollout, latency)

    frozen_rollouts = tuple(rollouts)
    return EvaluationRun(
        rollouts=frozen_rollouts,
        latency_seconds=tuple(latencies),
        metrics=compute_evaluation_metrics(frozen_rollouts),
    )
