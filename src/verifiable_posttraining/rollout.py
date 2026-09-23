"""Model-independent multi-turn rollout runner."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from .environment import EpisodeEnvironment, EpisodeResult, ToolExecutor
from .model_protocol import FinalAnswer, parse_model_action
from .prompting import ChatMessage, append_tool_exchange, build_initial_messages
from .schemas import Task, ToolCall


class GenerationPolicy(Protocol):
    def generate(self, messages: Sequence[ChatMessage], *, seed: int) -> str:
        """Generate exactly one raw model action."""


@dataclass(frozen=True, slots=True)
class RolloutResult:
    episode: EpisodeResult
    raw_outputs: tuple[str, ...]
    termination_reason: str
    protocol_error: str | None
    task_success: bool


def run_episode(
    task: Task,
    policy: GenerationPolicy,
    tool_executors: dict[str, ToolExecutor],
    *,
    trajectory_id: str,
    model_id: str,
    seed: int,
    max_model_turns: int = 6,
    max_tool_calls: int = 4,
) -> RolloutResult:
    """Run one policy until a final answer, protocol error, or turn limit."""

    if max_model_turns <= 0:
        raise ValueError("max_model_turns must be positive")

    environment = EpisodeEnvironment(tool_executors, max_tool_calls=max_tool_calls)
    environment.reset(task)
    messages = build_initial_messages(task)
    raw_outputs: list[str] = []

    for turn_index in range(max_model_turns):
        raw_output = policy.generate(messages, seed=seed + turn_index)
        raw_outputs.append(raw_output)
        parsed = parse_model_action(
            raw_output,
            default_call_id=f"call-{turn_index + 1}",
        )

        if not parsed.ok:
            episode = environment.finish(
                raw_output,
                trajectory_id=trajectory_id,
                model_id=model_id,
                seed=seed,
                metadata={
                    "termination_reason": "protocol_error",
                    "protocol_error": parsed.error_code,
                },
            )
            return RolloutResult(
                episode=episode,
                raw_outputs=tuple(raw_outputs),
                termination_reason="protocol_error",
                protocol_error=parsed.error_code,
                task_success=False,
            )

        action = parsed.action
        if isinstance(action, ToolCall):
            observation = environment.step(action)
            messages = append_tool_exchange(
                messages,
                raw_model_output=raw_output,
                observation=observation,
            )
            continue

        if isinstance(action, FinalAnswer):
            episode = environment.finish(
                action.answer,
                trajectory_id=trajectory_id,
                model_id=model_id,
                seed=seed,
                metadata={"termination_reason": "final_answer"},
            )
            return RolloutResult(
                episode=episode,
                raw_outputs=tuple(raw_outputs),
                termination_reason="final_answer",
                protocol_error=None,
                task_success=episode.verification.passed,
            )

        raise AssertionError(f"unexpected parsed action: {action!r}")

    episode = environment.finish(
        None,
        trajectory_id=trajectory_id,
        model_id=model_id,
        seed=seed,
        metadata={"termination_reason": "max_model_turns"},
    )
    return RolloutResult(
        episode=episode,
        raw_outputs=tuple(raw_outputs),
        termination_reason="max_model_turns",
        protocol_error=None,
        task_success=False,
    )
