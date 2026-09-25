"""Model-independent chat messages and tool instructions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal, Sequence

from .schemas import Observation, Task, TaskKind

Role = Literal["system", "user", "assistant", "tool"]
PROMPT_PROTOCOL_VERSION = "v3-sql-scalar-aggregate"


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: Role
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


_TOOL_DESCRIPTIONS = {
    "calculator": (
        "calculator: exact bounded arithmetic. Arguments: "
        "an expression using +, -, *, /, and parentheses. "
        'Exact call format: {"type":"tool_call","name":"calculator",'
        '"arguments":{"expression":"1 + 1"}}.'
    ),
    "sql": (
        "sql: read-only queries over the task's documented synthetic tables. "
        "The final answer must be one scalar, not a row list. When multiple rows "
        "contribute to a requested total, count, or average, aggregate them in SQL "
        "with SUM, COUNT, or AVG as appropriate. "
        'Exact call format: {"type":"tool_call","name":"sql",'
        '"arguments":{"query":"SELECT ..."}}.'
    ),
}


def _system_prompt(task: Task) -> str:
    if task.allowed_tools:
        descriptions = "\n".join(
            f"- {_TOOL_DESCRIPTIONS.get(name, f'{name}: available tool')}"
            for name in task.allowed_tools
        )
    else:
        descriptions = "- No tools are available. Answer directly."

    return (
        "You solve one task at a time. Emit exactly one complete JSON object and no prose.\n"
        "Choose exactly one action per turn: a tool_call OR a final answer, never both.\n"
        "For a tool_call, the only top-level keys are type, name, and arguments.\n"
        "Never put type, name, or answer inside arguments. Stop after the closing brace.\n"
        "After receiving a tool observation, emit a final action with exactly this shape:\n"
        '{"type":"final","answer":"your answer"}\n'
        "Available tools:\n"
        f"{descriptions}"
    )


def build_initial_messages(task: Task) -> list[ChatMessage]:
    """Create a prompt without exposing ground truth or hidden metadata."""

    return [
        ChatMessage(role="system", content=_system_prompt(task)),
        ChatMessage(role="user", content=task.prompt),
    ]


def build_native_calculator_grpo_messages(task: Task) -> list[ChatMessage]:
    """Build a prompt for TRL's native tool-calling loop.

    The chat template supplies the callable schema.  This prompt specifies the
    behavioral invariant: one calculator call must precede one typed final
    answer.  Ground truth and hidden metadata are never included.
    """

    if task.kind is not TaskKind.CALCULATOR or task.allowed_tools != ("calculator",):
        raise ValueError("native calculator GRPO requires a calculator-only task")
    return [
        ChatMessage(
            role="system",
            content=(
                "Use the provided calculator exactly once before answering. "
                "Issue the tool call using the platform tool-call format. "
                "After receiving the tool result, emit exactly one complete JSON object "
                "and no prose with this shape: "
                '{"type":"final","answer":"your answer"}'
            ),
        ),
        ChatMessage(role="user", content=task.prompt),
    ]


def append_tool_exchange(
    messages: Sequence[ChatMessage],
    *,
    raw_model_output: str,
    observation: Observation,
) -> list[ChatMessage]:
    """Return a new history containing the model action and trusted observation."""

    observation_payload = {
        "call_id": observation.call_id,
        "ok": observation.ok,
        "content": observation.content,
        "error_code": observation.error_code,
    }
    return [
        *messages,
        ChatMessage(role="assistant", content=raw_model_output),
        ChatMessage(
            role="tool",
            content=json.dumps(observation_payload, ensure_ascii=False, sort_keys=True),
        ),
    ]
