"""Model-independent chat messages and tool instructions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal, Sequence

from .schemas import Observation, Task

Role = Literal["system", "user", "assistant", "tool"]


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: Role
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


_TOOL_DESCRIPTIONS = {
    "calculator": (
        "calculator: exact bounded arithmetic. Arguments: "
        '{"expression": "an expression using +, -, *, /, and parentheses"}.'
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
        "You solve one task at a time. Emit exactly one JSON object and no prose.\n"
        "To call a tool, emit:\n"
        '{"type":"tool_call","name":"tool name",'
        '"arguments":{}}\n'
        "To finish, emit:\n"
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
