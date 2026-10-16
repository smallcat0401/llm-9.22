"""Probe train-only calculator prompts for usable 4B GRPO reward variance.

This is an inference-only diagnostic.  It samples the frozen SFT policy,
executes the trusted calculator, applies the same component weights planned
for GRPO, and records per-prompt reward variance.  It never updates model
parameters and never reads validation or test tasks.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
import hashlib
import json
from pathlib import Path
import statistics
import time
import tomllib
from typing import Any, Mapping, Sequence

from .dataset import load_tasks_jsonl
from .native_tool_evaluation import (
    NativeToolEpisodeResult,
    TransformersNativeToolPolicy,
    evaluate_native_calculator,
)
from .schemas import Split, Task, TaskKind
from .transformers_backend import GenerationSettings, TransformersPolicy


@dataclass(frozen=True, slots=True)
class GRPORewardProbeConfig:
    run_id: str
    model_id: str
    adapter_path: str
    dataset_path: str
    expected_dataset_sha256: str
    expected_task_count: int
    output_dir: str
    metrics_path: str
    seed: int = 719
    num_samples: int = 8
    max_new_tokens: int = 128
    temperature: float = 1.4
    top_p: float = 0.97
    outcome_reward_weight: float = 1.0
    closeness_reward_weight: float = 0.25
    format_reward_weight: float = 0.1
    tool_trace_reward_weight: float = 0.05
    tool_result_reward_weight: float = 0.5

    def __post_init__(self) -> None:
        if self.expected_task_count <= 0 or self.num_samples <= 1:
            raise ValueError("expected_task_count must be positive and num_samples must exceed one")
        if self.max_new_tokens <= 0 or self.temperature <= 0:
            raise ValueError("max_new_tokens and temperature must be positive")
        if not 0 < self.top_p <= 1:
            raise ValueError("top_p must be in (0, 1]")
        weights = (
            self.outcome_reward_weight,
            self.closeness_reward_weight,
            self.format_reward_weight,
            self.tool_trace_reward_weight,
            self.tool_result_reward_weight,
        )
        if self.outcome_reward_weight <= 0 or any(weight < 0 for weight in weights):
            raise ValueError("outcome reward must be positive and all rewards non-negative")
        digest = self.expected_dataset_sha256.lower()
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise ValueError("expected_dataset_sha256 must be a SHA-256 hex digest")


def load_grpo_reward_probe_config(path: str | Path) -> GRPORewardProbeConfig:
    payload = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    section = payload.get("probe")
    if not isinstance(section, Mapping):
        raise ValueError("config must contain a [probe] table")
    return GRPORewardProbeConfig(**dict(section))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _completed_tool_trace(result: NativeToolEpisodeResult) -> bool:
    tool_index = next(
        (index for index, message in enumerate(result.messages) if message.get("role") == "tool"),
        None,
    )
    if tool_index is None:
        return False
    return any(
        index > tool_index
        and message.get("role") == "assistant"
        and isinstance(message.get("content"), str)
        and bool(message["content"].strip())
        for index, message in enumerate(result.messages)
    )


def reward_probe_record(
    result: NativeToolEpisodeResult,
    task: Task,
    *,
    sample_index: int,
    config: GRPORewardProbeConfig,
) -> dict[str, Any]:
    """Convert one episode into auditable reward components.

    These components mirror the formal calculator GRPO rewards: verified final
    outcome, bounded numeric closeness, typed final, completed tool trace, and
    a calculator result that independently matches ground truth.
    """

    verification = result.verification
    if verification.predicted_value is None or verification.absolute_error is None:
        closeness = 0.0
    else:
        scale = max(abs(verification.target_value), 1.0)
        closeness = 1.0 / (1.0 + verification.absolute_error / scale)
    components = {
        "numeric_outcome": float(verification.passed),
        "numeric_closeness": closeness,
        "typed_final": float(result.typed_final),
        "calculator_trace": float(_completed_tool_trace(result)),
        "calculator_result": float(
            result.tool_result_verification is not None
            and result.tool_result_verification.passed
        ),
    }
    total = (
        components["numeric_outcome"] * config.outcome_reward_weight
        + components["numeric_closeness"] * config.closeness_reward_weight
        + components["typed_final"] * config.format_reward_weight
        + components["calculator_trace"] * config.tool_trace_reward_weight
        + components["calculator_result"] * config.tool_result_reward_weight
    )
    return {
        "task_id": task.task_id,
        "family_id": task.family_id,
        "sample_index": sample_index,
        "reward": total,
        "reward_components": components,
        "tool_called": result.tool_called,
        "tool_succeeded": result.tool_succeeded,
        "typed_final": result.typed_final,
        "task_success": result.task_success,
        "tool_result_verification": (
            asdict(result.tool_result_verification)
            if result.tool_result_verification is not None
            else None
        ),
        "verification": asdict(result.verification),
        "messages": list(result.messages),
    }


def summarize_probe_records(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_task: dict[str, list[Mapping[str, Any]]] = {}
    for record in records:
        by_task.setdefault(str(record["task_id"]), []).append(record)
    task_summaries = []
    for task_id, group in sorted(by_task.items()):
        rewards = [float(record["reward"]) for record in group]
        outcomes = [float(record["reward_components"]["numeric_outcome"]) for record in group]
        family_id = str(group[0]["family_id"])
        total_variance = max(rewards) - min(rewards) > 1e-12
        outcome_variance = max(outcomes) - min(outcomes) > 1e-12
        task_summaries.append({
            "task_id": task_id,
            "family_id": family_id,
            "samples": len(group),
            "reward_mean": statistics.fmean(rewards),
            "reward_std_population": statistics.pstdev(rewards),
            "reward_min": min(rewards),
            "reward_max": max(rewards),
            "nonzero_total_reward_variance": total_variance,
            "nonzero_outcome_reward_variance": outcome_variance,
            "outcome_successes": int(sum(outcomes)),
            "strict_task_successes": sum(bool(record["task_success"]) for record in group),
        })
    family_summaries = []
    families = sorted({summary["family_id"] for summary in task_summaries})
    for family_id in families:
        group = [summary for summary in task_summaries if summary["family_id"] == family_id]
        family_summaries.append({
            "family_id": family_id,
            "tasks": len(group),
            "nonzero_total_reward_variance_tasks": sum(
                summary["nonzero_total_reward_variance"] for summary in group
            ),
            "nonzero_outcome_reward_variance_tasks": sum(
                summary["nonzero_outcome_reward_variance"] for summary in group
            ),
            "outcome_successful_episodes": sum(summary["outcome_successes"] for summary in group),
            "episodes": sum(summary["samples"] for summary in group),
        })
    return {
        "task_count": len(task_summaries),
        "episode_count": len(records),
        "nonzero_total_reward_variance_task_count": sum(
            summary["nonzero_total_reward_variance"] for summary in task_summaries
        ),
        "nonzero_outcome_reward_variance_task_count": sum(
            summary["nonzero_outcome_reward_variance"] for summary in task_summaries
        ),
        "all_outcomes_correct_task_count": sum(
            summary["outcome_successes"] == summary["samples"] for summary in task_summaries
        ),
        "all_outcomes_incorrect_task_count": sum(
            summary["outcome_successes"] == 0 for summary in task_summaries
        ),
        "candidate_task_ids": [
            summary["task_id"]
            for summary in task_summaries
            if summary["nonzero_total_reward_variance"]
        ],
        "families": family_summaries,
        "tasks": task_summaries,
    }


def run_grpo_reward_probe(
    config: GRPORewardProbeConfig,
    *,
    cache_dir: str | None = None,
    task_limit: int | None = None,
) -> dict[str, Any]:
    dataset_path = Path(config.dataset_path)
    actual_hash = _sha256(dataset_path)
    if actual_hash != config.expected_dataset_sha256.lower():
        raise ValueError("GRPO probe dataset hash changed")
    tasks = tuple(
        task
        for task in load_tasks_jsonl(dataset_path)
        if task.split is Split.TRAIN and task.kind is TaskKind.CALCULATOR
    )
    if len(tasks) != config.expected_task_count:
        raise ValueError(
            f"expected {config.expected_task_count} train calculator tasks, found {len(tasks)}"
        )
    if task_limit is not None:
        if task_limit <= 0:
            raise ValueError("task_limit must be positive")
        tasks = tasks[:task_limit]

    started = time.perf_counter()
    base_policy = TransformersPolicy.from_pretrained(
        config.model_id,
        cache_dir=cache_dir,
        adapter_path=config.adapter_path,
        local_files_only=True,
        settings=GenerationSettings(max_new_tokens=config.max_new_tokens),
    )
    load_seconds = time.perf_counter() - started
    policy = TransformersNativeToolPolicy(
        base_policy,
        do_sample=True,
        temperature=config.temperature,
        top_p=config.top_p,
    )
    evaluation_started = time.perf_counter()
    results = evaluate_native_calculator(
        tasks,
        policy,
        seed=config.seed,
        num_samples=config.num_samples,
    )
    evaluation_seconds = time.perf_counter() - evaluation_started

    records = []
    task_by_id = {task.task_id: task for task in tasks}
    sample_counts: dict[str, int] = {}
    for result in results:
        sample_index = sample_counts.get(result.task_id, 0)
        sample_counts[result.task_id] = sample_index + 1
        records.append(
            reward_probe_record(
                result,
                task_by_id[result.task_id],
                sample_index=sample_index,
                config=config,
            )
        )
    if any(count != config.num_samples for count in sample_counts.values()):
        raise RuntimeError("probe did not produce the configured samples for every task")

    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "records.jsonl").open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    with (output_dir / "generation_traces.jsonl").open(
        "w", encoding="utf-8", newline="\n"
    ) as stream:
        for trace in policy.generation_traces:
            stream.write(json.dumps(trace, ensure_ascii=False, sort_keys=True) + "\n")

    summary = summarize_probe_records(records)
    report = {
        "status": "completed",
        "inference_only": True,
        "model_parameters_updated": False,
        "split": "train",
        "dataset_sha256": actual_hash,
        "load_seconds": load_seconds,
        "evaluation_seconds": evaluation_seconds,
        "config": asdict(config),
        "summary": summary,
    }
    (output_dir / "metrics.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    metrics_path = Path(config.metrics_path)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": report["status"],
        "inference_only": report["inference_only"],
        "task_count": summary["task_count"],
        "episode_count": summary["episode_count"],
        "nonzero_total_reward_variance_task_count": summary[
            "nonzero_total_reward_variance_task_count"
        ],
        "nonzero_outcome_reward_variance_task_count": summary[
            "nonzero_outcome_reward_variance_task_count"
        ],
        "evaluation_seconds": evaluation_seconds,
        "output_dir": str(output_dir),
        "metrics_path": str(metrics_path),
    }, ensure_ascii=False, indent=2))
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--cache-dir")
    parser.add_argument("--model-id")
    parser.add_argument("--adapter-path")
    parser.add_argument("--task-limit", type=int)
    parser.add_argument("--num-samples", type=int)
    parser.add_argument("--output-dir")
    parser.add_argument("--metrics-path")
    args = parser.parse_args(argv)

    config = load_grpo_reward_probe_config(args.config)
    overrides = {
        "model_id": args.model_id,
        "adapter_path": args.adapter_path,
        "num_samples": args.num_samples,
        "output_dir": args.output_dir,
        "metrics_path": args.metrics_path,
    }
    config = replace(
        config,
        **{name: value for name, value in overrides.items() if value is not None},
    )
    run_grpo_reward_probe(config, cache_dir=args.cache_dir, task_limit=args.task_limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
