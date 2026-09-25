"""Small command-line entry point for repository smoke checks."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import time
from typing import Sequence

from .doctor import print_environment
from .calculator_curriculum import (
    build_reference_program_sft,
    generate_calculator_holdout_v1,
    generate_calculator_curriculum,
    generate_calculator_curriculum_v2,
)
from .dataset import (
    dataset_summary,
    generate_pilot_tasks,
    load_tasks_jsonl,
    select_task_window_per_kind,
    write_tasks_jsonl,
)
from .environment import ToolExecutor
from .evaluation import evaluate_tasks, rollout_record
from .grpo_training import load_grpo_smoke_config, run_grpo_smoke
from .native_sft_data import build_native_calculator_sft_dataset
from .prompting import PROMPT_PROTOCOL_VERSION, ChatMessage
from .public_eval import (
    build_gsm8k_external_tasks,
    build_gsm8k_search_screen_tasks,
    build_gsm8k_train_validation_tasks,
    load_gsm8k_jsonl,
    public_dataset_manifest,
)
from .rollout import run_episode
from .schemas import Split, Task, TaskKind, demo_task
from .search import assess_search_gate, run_best_of_n
from .sft_data import (
    build_sft_dataset,
    is_path_aligned_sft_record,
    merge_sft_examples,
    load_selected_trajectory_records,
    select_path_aligned_sft_records,
    sft_dataset_summary,
    write_trajectory_records_jsonl,
    write_sft_jsonl,
)
from .sft_training import load_sft_examples, load_sft_training_config, run_qlora_sft
from .synthetic_db import (
    SALES_SCHEMA,
    create_pilot_sales_connection,
    create_sales_connection,
)
from .tools import ReadOnlySQLiteTool, execute_calculator
from .transformers_backend import GenerationSettings, TransformersPolicy


def _schema_demo() -> None:
    original = demo_task()
    payload = original.to_dict()
    restored = Task.from_dict(payload)
    if original != restored:
        raise RuntimeError("task JSON round trip changed the task")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


class _ScriptedPolicy:
    def __init__(self, outputs: Sequence[str]) -> None:
        self._outputs = iter(outputs)

    def generate(self, messages: Sequence[ChatMessage], *, seed: int) -> str:
        del messages, seed
        return next(self._outputs)


def _episode_demo() -> None:
    task = Task(
        task_id="demo-calculator-001",
        family_id="percentage-calculator-v1",
        kind=TaskKind.CALCULATOR,
        split=Split.TEST,
        prompt="A group has 40 items and 10 are selected. What percentage is selected?",
        allowed_tools=("calculator",),
        ground_truth={"type": "number", "value": 25.0, "tolerance": 1e-6},
        metadata={"source": "scripted-demo"},
    )
    policy = _ScriptedPolicy(
        (
            '{"type":"tool_call","call_id":"call-1","name":"calculator",'
            '"arguments":{"expression":"10 / 40 * 100"}}',
            '{"type":"final","answer":"25%"}',
        )
    )
    rollout = run_episode(
        task,
        policy,
        {"calculator": execute_calculator},
        trajectory_id="demo-trajectory-001",
        model_id="scripted-policy",
        seed=7,
    )
    result = rollout.episode
    print(
        json.dumps(
            {
                "task": result.task.to_dict(),
                "trajectory": result.trajectory.to_dict(),
                "verification": asdict(result.verification),
                "rollout": {
                    "termination_reason": rollout.termination_reason,
                    "protocol_error": rollout.protocol_error,
                    "task_success": rollout.task_success,
                    "turns": len(rollout.raw_outputs),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _model_smoke(
    model_id: str,
    cache_dir: str | None,
    max_new_tokens: int,
    load_in_4bit: bool,
) -> None:
    policy = TransformersPolicy.from_pretrained(
        model_id,
        cache_dir=cache_dir,
        local_files_only=True,
        load_in_4bit=load_in_4bit,
        settings=GenerationSettings(max_new_tokens=max_new_tokens),
    )
    messages = [
        ChatMessage(
            role="system",
            content=(
                "Emit exactly one JSON object and no prose. "
                'Use {"type":"final","answer":"your answer"}.'
            ),
        ),
        ChatMessage(role="user", content="What is 17 plus 25?"),
    ]
    print(policy.generate(messages, seed=7))


def _model_episode(
    model_id: str,
    cache_dir: str | None,
    max_new_tokens: int,
    max_model_turns: int,
    load_in_4bit: bool,
) -> None:
    task = Task(
        task_id="real-model-calculator-001",
        family_id="revenue-calculator-v1",
        kind=TaskKind.CALCULATOR,
        split=Split.TEST,
        prompt=(
            "Use the calculator tool to compute the total revenue from selling "
            "37 items at 24.5 currency units each. Then return the final numeric answer."
        ),
        allowed_tools=("calculator",),
        ground_truth={"type": "number", "value": 906.5, "tolerance": 1e-6},
        metadata={"source": "local-model-smoke"},
    )
    _run_local_model_episode(
        task,
        {"calculator": execute_calculator},
        trajectory_id="real-model-trajectory-001",
        model_id=model_id,
        cache_dir=cache_dir,
        max_new_tokens=max_new_tokens,
        max_model_turns=max_model_turns,
        load_in_4bit=load_in_4bit,
    )


def _model_sql_episode(
    model_id: str,
    cache_dir: str | None,
    max_new_tokens: int,
    max_model_turns: int,
    load_in_4bit: bool,
) -> None:
    connection = create_sales_connection()
    try:
        sql_tool = ReadOnlySQLiteTool(connection, allowed_tables={"sales"})
        task = Task(
            task_id="real-model-sql-001",
            family_id="sales-aggregation-sql-v1",
            kind=TaskKind.SQL,
            split=Split.TEST,
            prompt=(
                f"Use the sql tool and this schema:\n{SALES_SCHEMA}\n"
                "Compute total revenue for region 'north', where revenue is "
                "SUM(units * unit_price). Return the final numeric answer."
            ),
            allowed_tools=("sql",),
            ground_truth={"type": "number", "value": 97.5, "tolerance": 1e-6},
            metadata={"source": "synthetic-sql-smoke"},
        )
        _run_local_model_episode(
            task,
            {"sql": sql_tool},
            trajectory_id="real-model-sql-trajectory-001",
            model_id=model_id,
            cache_dir=cache_dir,
            max_new_tokens=max_new_tokens,
            max_model_turns=max_model_turns,
            load_in_4bit=load_in_4bit,
        )
    finally:
        connection.close()


def _run_local_model_episode(
    task: Task,
    tool_executors: dict[str, ToolExecutor],
    *,
    trajectory_id: str,
    model_id: str,
    cache_dir: str | None,
    max_new_tokens: int,
    max_model_turns: int,
    load_in_4bit: bool,
) -> None:
    import torch

    load_started = time.perf_counter()
    policy = TransformersPolicy.from_pretrained(
        model_id,
        cache_dir=cache_dir,
        local_files_only=True,
        load_in_4bit=load_in_4bit,
        settings=GenerationSettings(max_new_tokens=max_new_tokens),
    )
    load_seconds = time.perf_counter() - load_started

    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
        baseline_memory = torch.cuda.memory_allocated()
    else:
        baseline_memory = 0

    rollout_started = time.perf_counter()
    rollout = run_episode(
        task,
        policy,
        tool_executors,
        trajectory_id=trajectory_id,
        model_id=model_id,
        seed=7,
        max_model_turns=max_model_turns,
        max_tool_calls=2,
    )
    rollout_seconds = time.perf_counter() - rollout_started
    peak_memory = torch.cuda.max_memory_allocated() if torch.cuda.is_available() else 0

    print(
        json.dumps(
            {
                "task": task.to_dict(),
                "raw_outputs": list(rollout.raw_outputs),
                "trajectory": rollout.episode.trajectory.to_dict(),
                "verification": asdict(rollout.episode.verification),
                "rollout": {
                    "termination_reason": rollout.termination_reason,
                    "protocol_error": rollout.protocol_error,
                    "task_success": rollout.task_success,
                    "turns": len(rollout.raw_outputs),
                },
                "runtime": {
                    "load_seconds": round(load_seconds, 3),
                    "rollout_seconds": round(rollout_seconds, 3),
                    "cuda_baseline_memory_mib": round(baseline_memory / 1024**2, 1),
                    "cuda_peak_memory_mib": round(peak_memory / 1024**2, 1),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _add_model_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--model-id", default="Qwen/Qwen3.5-0.8B")
    parser.add_argument("--cache-dir")
    parser.add_argument("--max-new-tokens", type=int, default=128)
    parser.add_argument(
        "--load-in-4bit",
        action="store_true",
        help="load model weights with bitsandbytes NF4 for memory-constrained inference",
    )


def _generate_pilot(output: str, seed: int, examples_per_family: int) -> None:
    tasks = generate_pilot_tasks(seed=seed, examples_per_family=examples_per_family)
    write_tasks_jsonl(tasks, Path(output))
    print(json.dumps(dataset_summary(tasks), ensure_ascii=False, indent=2))


def _baseline_eval(args: argparse.Namespace) -> None:
    import torch

    tasks = list(load_tasks_jsonl(args.dataset))
    selected_splits = {Split(value) for value in args.split}
    selected_kinds = (
        {TaskKind(value) for value in args.kind}
        if args.kind
        else {TaskKind.NO_TOOL, TaskKind.CALCULATOR, TaskKind.SQL}
    )
    tasks = [
        task
        for task in tasks
        if task.split in selected_splits and task.kind in selected_kinds
    ]
    if args.limit_per_kind:
        tasks = list(
            select_task_window_per_kind(tasks, limit_per_kind=args.limit_per_kind)
        )
    if not tasks:
        raise ValueError("task filters selected no evaluation tasks")
    evaluated_kinds = {task.kind for task in tasks}

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    records_path = output_dir / "records.jsonl"
    metrics_path = output_dir / "metrics.json"

    load_started = time.perf_counter()
    policy = TransformersPolicy.from_pretrained(
        args.model_id,
        cache_dir=args.cache_dir,
        adapter_path=args.adapter_path,
        local_files_only=True,
        load_in_4bit=args.load_in_4bit,
        settings=GenerationSettings(max_new_tokens=args.max_new_tokens),
    )
    load_seconds = time.perf_counter() - load_started
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    connection = create_pilot_sales_connection()
    try:
        sql_tool = ReadOnlySQLiteTool(connection, allowed_tables={"sales"})
        evaluation_started = time.perf_counter()
        with records_path.open("w", encoding="utf-8", newline="\n") as records_file:

            def save_progress(completed, total, rollout, latency) -> None:
                record = rollout_record(rollout, latency_seconds=latency)
                records_file.write(
                    json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
                )
                records_file.flush()
                print(
                    f"[{completed}/{total}] {rollout.episode.task.task_id}: "
                    f"success={rollout.task_success} latency={latency:.2f}s"
                )

            evaluation = evaluate_tasks(
                tasks,
                policy,
                {"calculator": execute_calculator, "sql": sql_tool},
                run_id=args.run_id,
                model_id=args.model_id,
                seed=args.seed,
                max_model_turns=args.max_model_turns,
                max_tool_calls=args.max_tool_calls,
                on_result=save_progress,
            )
        evaluation_seconds = time.perf_counter() - evaluation_started
    finally:
        connection.close()

    peak_memory = torch.cuda.max_memory_allocated() if torch.cuda.is_available() else 0
    report = {
        "config": {
            "run_id": args.run_id,
            "model_id": args.model_id,
            "adapter_path": args.adapter_path,
            "load_in_4bit": args.load_in_4bit,
            "prompt_protocol_version": PROMPT_PROTOCOL_VERSION,
            "dataset": args.dataset,
            "splits": sorted(split.value for split in selected_splits),
            "kinds": sorted(kind.value for kind in evaluated_kinds),
            "seed": args.seed,
            "max_new_tokens": args.max_new_tokens,
            "max_model_turns": args.max_model_turns,
            "max_tool_calls": args.max_tool_calls,
        },
        "runtime": {
            "load_seconds": round(load_seconds, 3),
            "evaluation_seconds": round(evaluation_seconds, 3),
            "average_episode_seconds": round(
                sum(evaluation.latency_seconds) / len(evaluation.latency_seconds), 3
            ),
            "cuda_peak_memory_mib": round(peak_memory / 1024**2, 1),
        },
        "metrics": evaluation.metrics.to_dict(),
    }
    metrics_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if args.metrics_artifact:
        artifact_path = Path(args.metrics_artifact)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


def _search_eval(args: argparse.Namespace) -> None:
    import torch

    tasks = list(load_tasks_jsonl(args.dataset))
    selected_splits = {Split(value) for value in args.split}
    selected_kinds = (
        {TaskKind(value) for value in args.kind}
        if args.kind
        else {TaskKind.NO_TOOL, TaskKind.CALCULATOR, TaskKind.SQL}
    )
    tasks = [
        task
        for task in tasks
        if task.split in selected_splits and task.kind in selected_kinds
    ]
    if args.offset_per_kind or args.limit_per_kind:
        tasks = list(
            select_task_window_per_kind(
                tasks,
                offset_per_kind=args.offset_per_kind,
                limit_per_kind=args.limit_per_kind,
            )
        )
    if not tasks:
        raise ValueError("task filters selected no search tasks")
    evaluated_kinds = {task.kind for task in tasks}

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    candidates_path = output_dir / "candidates.jsonl"
    selected_path = output_dir / "verified_trajectories.jsonl"
    metrics_path = output_dir / "metrics.json"

    load_started = time.perf_counter()
    policy = TransformersPolicy.from_pretrained(
        args.model_id,
        cache_dir=args.cache_dir,
        adapter_path=args.adapter_path,
        local_files_only=True,
        load_in_4bit=args.load_in_4bit,
        settings=GenerationSettings(
            max_new_tokens=args.max_new_tokens,
            do_sample=True,
            temperature=args.temperature,
            top_p=args.top_p,
            top_k=args.top_k,
        ),
    )
    load_seconds = time.perf_counter() - load_started
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    connection = create_pilot_sales_connection()
    try:
        sql_tool = ReadOnlySQLiteTool(connection, allowed_tables={"sales"})
        search_started = time.perf_counter()
        with candidates_path.open("w", encoding="utf-8", newline="\n") as candidate_file:

            def save_candidate(
                completed,
                total,
                task_index,
                sample_index,
                rollout,
                latency,
            ) -> None:
                record = rollout_record(rollout, latency_seconds=latency)
                record["search"] = {
                    "task_index": task_index,
                    "sample_index": sample_index,
                }
                candidate_file.write(
                    json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
                )
                candidate_file.flush()
                print(
                    f"[{completed}/{total}] {rollout.episode.task.task_id} "
                    f"sample={sample_index}: success={rollout.task_success} "
                    f"latency={latency:.2f}s"
                )

            search = run_best_of_n(
                tasks,
                policy,
                {"calculator": execute_calculator, "sql": sql_tool},
                samples_per_task=args.samples_per_task,
                run_id=args.run_id,
                model_id=args.model_id,
                seed=args.seed,
                max_model_turns=args.max_model_turns,
                max_tool_calls=args.max_tool_calls,
                on_candidate=save_candidate,
            )
        search_seconds = time.perf_counter() - search_started
    finally:
        connection.close()

    with selected_path.open("w", encoding="utf-8", newline="\n") as selected_file:
        for task_result in search.task_results:
            if task_result.selected is None or task_result.selected_index is None:
                continue
            record = rollout_record(
                task_result.selected,
                latency_seconds=task_result.latency_seconds[task_result.selected_index],
            )
            record["search"] = {
                "selected_sample_index": task_result.selected_index,
                "candidate_seed": task_result.candidate_seeds[task_result.selected_index],
                "selection_rule": "first_strict_task_success",
            }
            selected_file.write(
                json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
            )

    peak_memory = torch.cuda.max_memory_allocated() if torch.cuda.is_available() else 0
    all_latencies = [
        latency
        for task_result in search.task_results
        for latency in task_result.latency_seconds
    ]
    report = {
        "config": {
            "run_id": args.run_id,
            "model_id": args.model_id,
            "adapter_path": args.adapter_path,
            "load_in_4bit": args.load_in_4bit,
            "prompt_protocol_version": PROMPT_PROTOCOL_VERSION,
            "dataset": args.dataset,
            "splits": sorted(split.value for split in selected_splits),
            "kinds": sorted(kind.value for kind in evaluated_kinds),
            "seed": args.seed,
            "samples_per_task": args.samples_per_task,
            "offset_per_kind": args.offset_per_kind,
            "limit_per_kind": args.limit_per_kind,
            "max_new_tokens": args.max_new_tokens,
            "max_model_turns": args.max_model_turns,
            "max_tool_calls": args.max_tool_calls,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "top_k": args.top_k,
        },
        "runtime": {
            "load_seconds": round(load_seconds, 3),
            "search_seconds": round(search_seconds, 3),
            "average_candidate_seconds": round(sum(all_latencies) / len(all_latencies), 3),
            "cuda_peak_memory_mib": round(peak_memory / 1024**2, 1),
        },
        "metrics": search.metrics.to_dict(),
        "search_gate": assess_search_gate(
            search.metrics,
            min_absolute_gain=args.min_search_gain,
            min_verified_tasks=args.min_verified_tasks,
        ),
    }
    metrics_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


def _build_sft_data(input_path: str, output_path: str) -> None:
    records = load_selected_trajectory_records(input_path)
    examples = build_sft_dataset(records)
    write_sft_jsonl(examples, output_path)
    print(json.dumps(sft_dataset_summary(examples), ensure_ascii=False, indent=2))


def _build_native_calculator_sft_data(
    input_path: str, tasks_path: str, output_path: str
) -> None:
    sources = load_sft_examples(input_path)
    tasks = load_tasks_jsonl(tasks_path)
    examples = build_native_calculator_sft_dataset(sources, tasks)
    write_sft_jsonl(examples, output_path)
    print(json.dumps(sft_dataset_summary(examples), ensure_ascii=False, indent=2))


def _generate_calculator_curriculum(args: argparse.Namespace) -> None:
    generators = {
        "v1": generate_calculator_curriculum,
        "v2": generate_calculator_curriculum_v2,
        "holdout-v1": generate_calculator_holdout_v1,
    }
    generator = generators[args.version]
    tasks = generator(
        examples_per_family=args.examples_per_family
    )
    write_tasks_jsonl(tasks, args.output)
    print(json.dumps(dataset_summary(tasks), ensure_ascii=False, indent=2))


def _build_reference_program_sft(args: argparse.Namespace) -> None:
    tasks = load_tasks_jsonl(args.tasks)
    examples = build_reference_program_sft(tasks)
    write_sft_jsonl(examples, args.output)
    print(json.dumps(sft_dataset_summary(examples), ensure_ascii=False, indent=2))


def _merge_sft_data(args: argparse.Namespace) -> None:
    sources = []
    for specification in args.input:
        if "=" not in specification:
            raise ValueError("each --input must use NAME=PATH")
        name, path = specification.split("=", 1)
        sources.append((name, load_sft_examples(path)))
    examples = merge_sft_examples(tuple(sources))
    write_sft_jsonl(examples, args.output)
    summary = sft_dataset_summary(examples)
    summary["by_mixture_source"] = {
        name: sum(row["metadata"]["mixture_source"] == name for row in examples)
        for name, _ in sources
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def _build_public_eval(args: argparse.Namespace) -> None:
    records = load_gsm8k_jsonl(args.source)
    tasks = build_gsm8k_external_tasks(
        records,
        sample_size=args.sample_size,
        seed=args.seed,
    )
    write_tasks_jsonl(tasks, args.output)
    manifest = public_dataset_manifest(
        source_path=args.source,
        tasks=tasks,
        sample_size=args.sample_size,
        seed=args.seed,
    )
    manifest_path = Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


def _excluded_train_source_indices(task_paths: Sequence[str]) -> set[int]:
    excluded_source_indices: set[int] = set()
    for task_path in task_paths:
        for task in load_tasks_jsonl(task_path):
            if task.metadata.get("source_split") != "train":
                raise ValueError("excluded search-screen tasks must come from train")
            if "source_index" not in task.metadata:
                raise ValueError("excluded search-screen task is missing source_index")
            excluded_source_indices.add(int(task.metadata["source_index"]))
    return excluded_source_indices


def _build_public_search_screen(args: argparse.Namespace) -> None:
    records = load_gsm8k_jsonl(args.source)
    excluded_source_indices = _excluded_train_source_indices(args.exclude_tasks)
    tasks = build_gsm8k_search_screen_tasks(
        records,
        sample_size=args.sample_size,
        seed=args.seed,
        excluded_source_indices=excluded_source_indices,
    )
    write_tasks_jsonl(tasks, args.output)
    summary = dataset_summary(tasks)
    summary["excluded_source_questions"] = len(excluded_source_indices)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def _build_public_validation(args: argparse.Namespace) -> None:
    records = load_gsm8k_jsonl(args.source)
    excluded_source_indices = _excluded_train_source_indices(args.exclude_tasks)
    tasks = build_gsm8k_train_validation_tasks(
        records,
        sample_size=args.sample_size,
        seed=args.seed,
        excluded_source_indices=excluded_source_indices,
    )
    write_tasks_jsonl(tasks, args.output)
    summary = dataset_summary(tasks)
    summary["excluded_source_questions"] = len(excluded_source_indices)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def _curate_sft_data(args: argparse.Namespace) -> None:
    candidates = load_selected_trajectory_records(args.candidates)
    strict_successes = [
        record
        for record in candidates
        if record.get("rollout", {}).get("task_success") is True
        and record.get("verification", {}).get("passed") is True
    ]
    aligned_successes = [
        record for record in strict_successes if is_path_aligned_sft_record(record)
    ]
    selected = select_path_aligned_sft_records(candidates)
    write_trajectory_records_jsonl(selected, args.selected_output)
    examples = build_sft_dataset(selected)
    write_sft_jsonl(examples, args.output)
    summary = {
        "candidate_records": len(candidates),
        "strict_success_candidates": len(strict_successes),
        "path_aligned_success_candidates": len(aligned_successes),
        "selected_examples": len(examples),
        **sft_dataset_summary(examples),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vpt")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor", help="print Python, package, and NVIDIA GPU information")
    subparsers.add_parser("schema-demo", help="validate and print a minimal task fixture")
    subparsers.add_parser("episode-demo", help="run one scripted calculator episode")
    model_smoke = subparsers.add_parser(
        "model-smoke",
        help="run one local-only generation with a downloaded Transformers model",
    )
    _add_model_arguments(model_smoke)
    model_episode = subparsers.add_parser(
        "model-episode",
        help="run one local-only calculator episode with a downloaded model",
    )
    _add_model_arguments(model_episode)
    model_episode.add_argument("--max-model-turns", type=int, default=3)
    model_sql_episode = subparsers.add_parser(
        "model-sql-episode",
        help="run one local-only SQL episode with a downloaded model",
    )
    _add_model_arguments(model_sql_episode)
    model_sql_episode.add_argument("--max-model-turns", type=int, default=3)
    generate_pilot = subparsers.add_parser(
        "generate-pilot",
        help="generate deterministic family-split pilot tasks as JSONL",
    )
    generate_pilot.add_argument("--output", default="data/generated/pilot_tasks.jsonl")
    generate_pilot.add_argument("--seed", type=int, default=7)
    generate_pilot.add_argument("--examples-per-family", type=int, default=25)
    baseline_eval = subparsers.add_parser(
        "baseline-eval",
        help="run local-only pass@1 evaluation and save records plus metrics",
    )
    _add_model_arguments(baseline_eval)
    baseline_eval.add_argument(
        "--adapter-path", help="optional local PEFT adapter to evaluate"
    )
    baseline_eval.add_argument(
        "--metrics-artifact", help="optional second path for the final metrics report"
    )
    baseline_eval.add_argument("--dataset", default="data/generated/pilot_tasks.jsonl")
    baseline_eval.add_argument(
        "--output-dir", default="outputs/baseline/qwen3_5_0_8b_test_seed7"
    )
    baseline_eval.add_argument("--run-id", default="qwen3.5-0.8b-baseline-seed7")
    baseline_eval.add_argument(
        "--split",
        action="append",
        choices=[split.value for split in Split],
        default=None,
    )
    baseline_eval.add_argument(
        "--kind",
        action="append",
        choices=[kind.value for kind in TaskKind if kind is not TaskKind.SQL_ANALYSIS],
    )
    baseline_eval.add_argument("--limit-per-kind", type=int, default=0)
    baseline_eval.add_argument("--seed", type=int, default=7)
    baseline_eval.add_argument("--max-model-turns", type=int, default=3)
    baseline_eval.add_argument("--max-tool-calls", type=int, default=2)
    search_eval = subparsers.add_parser(
        "search-eval",
        help="run sampled Best-of-N search and save verifier-selected trajectories",
    )
    _add_model_arguments(search_eval)
    search_eval.add_argument(
        "--adapter-path", help="optional local PEFT adapter to sample from"
    )
    search_eval.set_defaults(max_new_tokens=256)
    search_eval.add_argument("--dataset", default="data/generated/pilot_tasks.jsonl")
    search_eval.add_argument(
        "--output-dir", default="outputs/search/qwen3_5_0_8b_train_best_of_4_seed7"
    )
    search_eval.add_argument("--run-id", default="qwen3.5-0.8b-train-best-of-4-seed7")
    search_eval.add_argument(
        "--split",
        action="append",
        choices=[split.value for split in Split],
        default=None,
    )
    search_eval.add_argument(
        "--kind",
        action="append",
        choices=[kind.value for kind in TaskKind if kind is not TaskKind.SQL_ANALYSIS],
    )
    search_eval.add_argument("--limit-per-kind", type=int, default=0)
    search_eval.add_argument(
        "--offset-per-kind",
        type=int,
        default=0,
        help="skip this many filtered tasks independently within each task kind",
    )
    search_eval.add_argument("--samples-per-task", type=int, default=4)
    search_eval.add_argument("--seed", type=int, default=7)
    search_eval.add_argument("--max-model-turns", type=int, default=3)
    search_eval.add_argument("--max-tool-calls", type=int, default=2)
    search_eval.add_argument("--temperature", type=float, default=0.7)
    search_eval.add_argument("--top-p", type=float, default=0.9)
    search_eval.add_argument("--top-k", type=int, default=20)
    search_eval.add_argument("--min-search-gain", type=float, default=0.10)
    search_eval.add_argument("--min-verified-tasks", type=int, default=25)
    build_sft = subparsers.add_parser(
        "build-sft-data",
        help="validate selected train trajectories and convert them to SFT JSONL",
    )
    build_sft.add_argument(
        "--input",
        default=(
            "outputs/search/qwen3_5_0_8b_train_best_of_4_seed7/"
            "verified_trajectories.jsonl"
        ),
    )
    build_sft.add_argument("--output", default="data/generated/sft_train_seed7.jsonl")
    build_native_sft = subparsers.add_parser(
        "build-native-calculator-sft-data",
        help="replay verified calculator rows into native structured tool-call SFT data",
    )
    build_native_sft.add_argument(
        "--input", default="data/generated/sft_train_path_aligned_seed7.jsonl"
    )
    build_native_sft.add_argument(
        "--tasks", default="data/generated/pilot_tasks.jsonl"
    )
    build_native_sft.add_argument(
        "--output", default="data/generated/sft_native_calculator_seed7.jsonl"
    )
    calculator_curriculum = subparsers.add_parser(
        "generate-calculator-curriculum",
        help="generate a family-isolated multi-step calculator curriculum",
    )
    calculator_curriculum.add_argument(
        "--output", default="data/generated/calculator_curriculum_v1.jsonl"
    )
    calculator_curriculum.add_argument("--examples-per-family", type=int, default=12)
    calculator_curriculum.add_argument(
        "--version", choices=("v1", "v2", "holdout-v1"), default="v1"
    )
    reference_sft = subparsers.add_parser(
        "build-reference-calculator-sft-data",
        help="build a train-only reference-program native calculator SFT ablation",
    )
    reference_sft.add_argument(
        "--tasks", default="data/generated/calculator_curriculum_v1.jsonl"
    )
    reference_sft.add_argument(
        "--output", default="data/generated/sft_calculator_curriculum_reference_v1.jsonl"
    )
    merge_sft = subparsers.add_parser(
        "merge-sft-data",
        help="merge named SFT sources with unique IDs and explicit provenance",
    )
    merge_sft.add_argument(
        "--input", action="append", required=True, help="named source in NAME=PATH form"
    )
    merge_sft.add_argument("--output", required=True)
    build_public_eval = subparsers.add_parser(
        "build-public-eval",
        help="freeze paired evaluation-only tasks from the official GSM8K test JSONL",
    )
    build_public_eval.add_argument(
        "--source", default="data/external/gsm8k/test.jsonl"
    )
    build_public_eval.add_argument(
        "--output", default="data/generated/gsm8k_external_eval_seed7.jsonl"
    )
    build_public_eval.add_argument(
        "--manifest",
        default="artifacts/dataset_manifests/gsm8k_external_eval_seed7.json",
    )
    build_public_eval.add_argument("--sample-size", type=int, default=100)
    build_public_eval.add_argument("--seed", type=int, default=7)
    build_public_screen = subparsers.add_parser(
        "build-public-search-screen",
        help="build train-only paired search-gap tasks from official GSM8K train JSONL",
    )
    build_public_screen.add_argument(
        "--source", default="data/external/gsm8k/train.jsonl"
    )
    build_public_screen.add_argument(
        "--output", default="data/generated/gsm8k_search_screen_seed71.jsonl"
    )
    build_public_screen.add_argument("--sample-size", type=int, default=100)
    build_public_screen.add_argument("--seed", type=int, default=71)
    build_public_screen.add_argument(
        "--exclude-tasks",
        action="append",
        default=[],
        help="train-only task JSONL whose source indices must not be sampled",
    )
    build_public_validation = subparsers.add_parser(
        "build-public-validation",
        help="freeze held-out validation tasks from unused GSM8K train sources",
    )
    build_public_validation.add_argument(
        "--source", default="data/external/gsm8k/train.jsonl"
    )
    build_public_validation.add_argument(
        "--output", default="data/generated/gsm8k_train_validation_seed131.jsonl"
    )
    build_public_validation.add_argument("--sample-size", type=int, default=50)
    build_public_validation.add_argument("--seed", type=int, default=131)
    build_public_validation.add_argument(
        "--exclude-tasks", action="append", default=[], required=True
    )
    curate_sft = subparsers.add_parser(
        "curate-sft-data",
        help="select one clean path-aligned strict success per train task",
    )
    curate_sft.add_argument(
        "--candidates",
        default=(
            "outputs/search/qwen3_5_0_8b_train_best_of_4_seed7/"
            "candidates.jsonl"
        ),
    )
    curate_sft.add_argument(
        "--selected-output",
        default="data/generated/sft_path_aligned_records_seed7.jsonl",
    )
    curate_sft.add_argument(
        "--output", default="data/generated/sft_train_path_aligned_seed7.jsonl"
    )
    sft_overfit = subparsers.add_parser(
        "sft-overfit-smoke",
        help="run a local-only QLoRA overfit check on a balanced verified subset",
    )
    sft_overfit.add_argument("--config", default="configs/sft_tiny_overfit.toml")
    sft_overfit.add_argument("--cache-dir")
    sft_train = subparsers.add_parser(
        "sft-train",
        help="run local-only QLoRA SFT from a machine-readable config",
    )
    sft_train.add_argument("--config", default="configs/sft_full_seed7.toml")
    sft_train.add_argument("--cache-dir")
    grpo_smoke = subparsers.add_parser(
        "grpo-smoke",
        help="run a minimal local QLoRA GRPO update with verifiable rewards",
    )
    grpo_smoke.add_argument("--config", default="configs/grpo_smoke.toml")
    grpo_smoke.add_argument("--cache-dir")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        print_environment()
    elif args.command == "schema-demo":
        _schema_demo()
    elif args.command == "episode-demo":
        _episode_demo()
    elif args.command == "model-smoke":
        _model_smoke(
            args.model_id,
            args.cache_dir,
            args.max_new_tokens,
            args.load_in_4bit,
        )
    elif args.command == "model-episode":
        _model_episode(
            args.model_id,
            args.cache_dir,
            args.max_new_tokens,
            args.max_model_turns,
            args.load_in_4bit,
        )
    elif args.command == "model-sql-episode":
        _model_sql_episode(
            args.model_id,
            args.cache_dir,
            args.max_new_tokens,
            args.max_model_turns,
            args.load_in_4bit,
        )
    elif args.command == "generate-pilot":
        _generate_pilot(args.output, args.seed, args.examples_per_family)
    elif args.command == "baseline-eval":
        if args.split is None:
            args.split = [Split.TEST.value]
        if args.limit_per_kind < 0:
            raise ValueError("limit-per-kind must be non-negative")
        _baseline_eval(args)
    elif args.command == "search-eval":
        if args.split is None:
            args.split = [Split.TRAIN.value]
        if args.limit_per_kind < 0:
            raise ValueError("limit-per-kind must be non-negative")
        if args.offset_per_kind < 0:
            raise ValueError("offset-per-kind must be non-negative")
        if args.samples_per_task <= 0:
            raise ValueError("samples-per-task must be positive")
        if not 0 <= args.min_search_gain <= 1:
            raise ValueError("min-search-gain must be in [0, 1]")
        if args.min_verified_tasks <= 0:
            raise ValueError("min-verified-tasks must be positive")
        _search_eval(args)
    elif args.command == "build-sft-data":
        _build_sft_data(args.input, args.output)
    elif args.command == "build-native-calculator-sft-data":
        _build_native_calculator_sft_data(args.input, args.tasks, args.output)
    elif args.command == "generate-calculator-curriculum":
        _generate_calculator_curriculum(args)
    elif args.command == "build-reference-calculator-sft-data":
        _build_reference_program_sft(args)
    elif args.command == "merge-sft-data":
        _merge_sft_data(args)
    elif args.command == "build-public-eval":
        _build_public_eval(args)
    elif args.command == "build-public-search-screen":
        _build_public_search_screen(args)
    elif args.command == "build-public-validation":
        _build_public_validation(args)
    elif args.command == "curate-sft-data":
        _curate_sft_data(args)
    elif args.command in {"sft-overfit-smoke", "sft-train"}:
        config = load_sft_training_config(args.config)
        metrics = run_qlora_sft(config, cache_dir=args.cache_dir)
        print(
            json.dumps(
                {
                    "run_id": metrics["run_id"],
                    "initial_loss": metrics["initial_loss"],
                    "final_loss": metrics["final_loss"],
                    "loss_reduction_fraction": metrics["loss_reduction_fraction"],
                    "trainable_parameters": metrics["trainable_parameters"],
                    "peak_cuda_memory_mib": metrics["peak_cuda_memory_mib"],
                    "elapsed_seconds": metrics["elapsed_seconds"],
                    "adapter_dir": config.output_dir,
                    "metrics_path": config.metrics_path,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.command == "grpo-smoke":
        config = load_grpo_smoke_config(args.config)
        metrics = run_grpo_smoke(config, cache_dir=args.cache_dir)
        print(
            json.dumps(
                {
                    "run_id": metrics["run_id"],
                    "changed_trainable_tensors": metrics["changed_trainable_tensors"],
                    "max_parameter_delta": metrics["max_parameter_delta"],
                    "peak_cuda_memory_mib": metrics["peak_cuda_memory_mib"],
                    "elapsed_seconds": metrics["elapsed_seconds"],
                    "adapter_dir": config.output_dir,
                    "metrics_path": config.metrics_path,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:  # pragma: no cover - argparse prevents this path.
        raise AssertionError(f"unexpected command: {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
