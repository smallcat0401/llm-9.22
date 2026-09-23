"""Small command-line entry point for repository smoke checks."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import time
from typing import Sequence

from .doctor import print_environment
from .prompting import ChatMessage
from .rollout import run_episode
from .schemas import Split, Task, TaskKind, demo_task
from .tools import execute_calculator
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


def _model_smoke(model_id: str, cache_dir: str | None, max_new_tokens: int) -> None:
    policy = TransformersPolicy.from_pretrained(
        model_id,
        cache_dir=cache_dir,
        local_files_only=True,
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
) -> None:
    import torch

    load_started = time.perf_counter()
    policy = TransformersPolicy.from_pretrained(
        model_id,
        cache_dir=cache_dir,
        local_files_only=True,
        settings=GenerationSettings(max_new_tokens=max_new_tokens),
    )
    load_seconds = time.perf_counter() - load_started

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

    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
        baseline_memory = torch.cuda.memory_allocated()
    else:
        baseline_memory = 0

    rollout_started = time.perf_counter()
    rollout = run_episode(
        task,
        policy,
        {"calculator": execute_calculator},
        trajectory_id="real-model-trajectory-001",
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
        _model_smoke(args.model_id, args.cache_dir, args.max_new_tokens)
    elif args.command == "model-episode":
        _model_episode(
            args.model_id,
            args.cache_dir,
            args.max_new_tokens,
            args.max_model_turns,
        )
    else:  # pragma: no cover - argparse prevents this path.
        raise AssertionError(f"unexpected command: {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
