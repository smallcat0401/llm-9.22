"""Best-of-N search with strict verifier selection and auditable metrics."""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass
from typing import Callable, Iterable, Mapping

from .environment import ToolExecutor
from .rollout import GenerationPolicy, RolloutResult, run_episode
from .schemas import Task

SearchProgressCallback = Callable[[int, int, int, int, RolloutResult, float], None]


def _safe_rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


@dataclass(frozen=True, slots=True)
class TaskSearchResult:
    task: Task
    candidates: tuple[RolloutResult, ...]
    candidate_seeds: tuple[int, ...]
    latency_seconds: tuple[float, ...]
    selected_index: int | None

    def __post_init__(self) -> None:
        size = len(self.candidates)
        if size == 0:
            raise ValueError("a task search result requires candidates")
        if len(self.candidate_seeds) != size or len(self.latency_seconds) != size:
            raise ValueError("candidate results, seeds, and latencies must align")
        if any(result.episode.task.task_id != self.task.task_id for result in self.candidates):
            raise ValueError("all candidates must belong to the task")
        successful_indices = [
            index for index, candidate in enumerate(self.candidates) if candidate.task_success
        ]
        expected_selection = successful_indices[0] if successful_indices else None
        if self.selected_index != expected_selection:
            raise ValueError("selected_index must be the first strictly successful candidate")

    @property
    def selected(self) -> RolloutResult | None:
        return None if self.selected_index is None else self.candidates[self.selected_index]


@dataclass(frozen=True, slots=True)
class SearchMetrics:
    task_count: int
    samples_per_task: int
    candidate_count: int
    verified_candidate_count: int
    verified_candidate_yield: float
    pass_at_1_count: int
    pass_at_1: float
    pass_at_k_count: int
    pass_at_k: float
    absolute_search_gain: float
    pass_at_prefix: Mapping[str, Mapping[str, int | float]]
    mean_verified_candidates_per_task: float
    success_by_kind: Mapping[str, Mapping[str, int | float]]

    def to_dict(self) -> dict[str, object]:
        return {
            "task_count": self.task_count,
            "samples_per_task": self.samples_per_task,
            "candidate_count": self.candidate_count,
            "verified_candidate_count": self.verified_candidate_count,
            "verified_candidate_yield": self.verified_candidate_yield,
            "pass_at_1_count": self.pass_at_1_count,
            "pass_at_1": self.pass_at_1,
            "pass_at_k_count": self.pass_at_k_count,
            "pass_at_k": self.pass_at_k,
            "absolute_search_gain": self.absolute_search_gain,
            "pass_at_prefix": dict(self.pass_at_prefix),
            "mean_verified_candidates_per_task": self.mean_verified_candidates_per_task,
            "success_by_kind": dict(self.success_by_kind),
        }


@dataclass(frozen=True, slots=True)
class SearchRun:
    task_results: tuple[TaskSearchResult, ...]
    metrics: SearchMetrics

    @property
    def selected_rollouts(self) -> tuple[RolloutResult, ...]:
        return tuple(
            result.selected
            for result in self.task_results
            if result.selected is not None
        )


def compute_search_metrics(results: Iterable[TaskSearchResult]) -> SearchMetrics:
    task_results = list(results)
    if not task_results:
        raise ValueError("at least one task search result is required")
    sample_counts = {len(result.candidates) for result in task_results}
    if len(sample_counts) != 1:
        raise ValueError("all task search results must use the same sample count")
    samples_per_task = sample_counts.pop()
    task_count = len(task_results)
    candidate_count = task_count * samples_per_task
    verified_candidate_count = sum(
        candidate.task_success
        for result in task_results
        for candidate in result.candidates
    )
    pass_at_1_count = sum(result.candidates[0].task_success for result in task_results)
    pass_at_k_count = sum(result.selected_index is not None for result in task_results)

    kind_tasks: Counter[str] = Counter()
    kind_pass_1: Counter[str] = Counter()
    kind_pass_k: Counter[str] = Counter()
    for result in task_results:
        kind = result.task.kind.value
        kind_tasks[kind] += 1
        kind_pass_1[kind] += int(result.candidates[0].task_success)
        kind_pass_k[kind] += int(result.selected_index is not None)
    success_by_kind = {
        kind: {
            "tasks": count,
            "pass_at_1_count": kind_pass_1[kind],
            "pass_at_1": _safe_rate(kind_pass_1[kind], count),
            "pass_at_k_count": kind_pass_k[kind],
            "pass_at_k": _safe_rate(kind_pass_k[kind], count),
        }
        for kind, count in sorted(kind_tasks.items())
    }
    pass_at_1 = _safe_rate(pass_at_1_count, task_count)
    pass_at_k = _safe_rate(pass_at_k_count, task_count)
    prefix_sizes = []
    prefix = 1
    while prefix < samples_per_task:
        prefix_sizes.append(prefix)
        prefix *= 2
    prefix_sizes.append(samples_per_task)
    pass_at_prefix = {}
    for prefix_size in prefix_sizes:
        count = sum(
            any(candidate.task_success for candidate in result.candidates[:prefix_size])
            for result in task_results
        )
        pass_at_prefix[str(prefix_size)] = {
            "count": count,
            "rate": _safe_rate(count, task_count),
        }
    return SearchMetrics(
        task_count=task_count,
        samples_per_task=samples_per_task,
        candidate_count=candidate_count,
        verified_candidate_count=verified_candidate_count,
        verified_candidate_yield=_safe_rate(verified_candidate_count, candidate_count),
        pass_at_1_count=pass_at_1_count,
        pass_at_1=pass_at_1,
        pass_at_k_count=pass_at_k_count,
        pass_at_k=pass_at_k,
        absolute_search_gain=pass_at_k - pass_at_1,
        pass_at_prefix=pass_at_prefix,
        mean_verified_candidates_per_task=verified_candidate_count / task_count,
        success_by_kind=success_by_kind,
    )


def assess_search_gate(
    metrics: SearchMetrics,
    *,
    min_absolute_gain: float,
    min_verified_tasks: int,
) -> dict[str, object]:
    """Apply a predeclared go/no-go gate without changing measured metrics."""

    if not 0 <= min_absolute_gain <= 1:
        raise ValueError("min_absolute_gain must be in [0, 1]")
    if min_verified_tasks <= 0:
        raise ValueError("min_verified_tasks must be positive")
    gain_passed = metrics.absolute_search_gain >= min_absolute_gain
    yield_passed = metrics.pass_at_k_count >= min_verified_tasks
    return {
        "passed": gain_passed and yield_passed,
        "min_absolute_gain": min_absolute_gain,
        "observed_absolute_gain": metrics.absolute_search_gain,
        "gain_passed": gain_passed,
        "min_verified_tasks": min_verified_tasks,
        "observed_verified_tasks": metrics.pass_at_k_count,
        "verified_task_count_passed": yield_passed,
        "decision_rule": "continue_to_4b_sft_only_if_all_checks_pass",
    }


def run_best_of_n(
    tasks: Iterable[Task],
    policy: GenerationPolicy,
    tool_executors: Mapping[str, ToolExecutor],
    *,
    samples_per_task: int,
    run_id: str,
    model_id: str,
    seed: int,
    max_model_turns: int = 3,
    max_tool_calls: int = 2,
    on_candidate: SearchProgressCallback | None = None,
) -> SearchRun:
    """Sample N independent trajectories and select the first strict success."""

    task_list = list(tasks)
    if not task_list:
        raise ValueError("at least one task is required")
    if samples_per_task <= 0:
        raise ValueError("samples_per_task must be positive")
    if not run_id.strip():
        raise ValueError("run_id must be non-empty")
    if len({task.task_id for task in task_list}) != len(task_list):
        raise ValueError("search task ids must be unique")

    task_results = []
    total_candidates = len(task_list) * samples_per_task
    completed = 0
    for task_index, task in enumerate(task_list):
        candidates = []
        candidate_seeds = []
        latencies = []
        for sample_index in range(samples_per_task):
            candidate_seed = seed + task_index * 100_000 + sample_index * 100
            started = time.perf_counter()
            candidate = run_episode(
                task,
                policy,
                dict(tool_executors),
                trajectory_id=(
                    f"{run_id}-{task.task_id}-sample-{sample_index:03d}"
                ),
                model_id=model_id,
                seed=candidate_seed,
                max_model_turns=max_model_turns,
                max_tool_calls=max_tool_calls,
            )
            latency = time.perf_counter() - started
            candidates.append(candidate)
            candidate_seeds.append(candidate_seed)
            latencies.append(latency)
            completed += 1
            if on_candidate is not None:
                on_candidate(
                    completed,
                    total_candidates,
                    task_index,
                    sample_index,
                    candidate,
                    latency,
                )

        selected_index = next(
            (
                index
                for index, candidate in enumerate(candidates)
                if candidate.task_success
            ),
            None,
        )
        task_results.append(
            TaskSearchResult(
                task=task,
                candidates=tuple(candidates),
                candidate_seeds=tuple(candidate_seeds),
                latency_seconds=tuple(latencies),
                selected_index=selected_index,
            )
        )

    frozen_results = tuple(task_results)
    return SearchRun(
        task_results=frozen_results,
        metrics=compute_search_metrics(frozen_results),
    )
