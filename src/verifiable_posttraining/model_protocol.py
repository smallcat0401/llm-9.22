"""Tier B protocol with a Tier A boundary for parsing untrusted model output.

The model must emit exactly one JSON object in one of two shapes::

    {"type": "tool_call", "name": "calculator",
     "arguments": {"expression": "10 / 40 * 100"}}

    {"type": "final", "answer": "25%"}

An optional outer ``json`` code fence is accepted.  Prose around the object,
duplicate keys, non-standard JSON constants, and unexpected fields are rejected
so the same text is interpreted identically across evaluation runs.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any

from .schemas import ToolCall

MAX_MODEL_OUTPUT_LENGTH = 10_000
_JSON_FENCE = re.compile(r"```(?:json)?\s*\n?(.*?)\n?```", re.DOTALL | re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class FinalAnswer:
    answer: str | int | float


ModelAction = ToolCall | FinalAnswer


@dataclass(frozen=True, slots=True)
class ActionParseResult:
    """Exactly one of ``action`` or ``error_code`` is populated."""

    action: ModelAction | None = None
    error_code: str | None = None
    message: str | None = None

    def __post_init__(self) -> None:
        if (self.action is None) == (self.error_code is None):
            raise ValueError("parse result must contain exactly one action or error")
        if self.error_code is not None and not self.message:
            raise ValueError("failed parse result requires a message")

    @property
    def ok(self) -> bool:
        return self.action is not None


class _DuplicateKeyError(ValueError):
    pass


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise _DuplicateKeyError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _reject_non_standard_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def _failure(code: str, message: str) -> ActionParseResult:
    return ActionParseResult(error_code=code, message=message)


def _unwrap_optional_fence(text: str) -> str | None:
    if not text.startswith("```"):
        return text
    match = _JSON_FENCE.fullmatch(text)
    if match is None:
        return None
    return match.group(1).strip()


def parse_model_action(
    raw_output: Any,
    *,
    default_call_id: str | None = None,
) -> ActionParseResult:
    """Parse one untrusted model completion into a typed action.

    All expected format failures are returned as data.  The evaluation runner
    can therefore count malformed outputs without aborting the remaining tasks.
    """

    if not isinstance(raw_output, str):
        return _failure("invalid_output_type", "model output must be a string")
    if len(raw_output) > MAX_MODEL_OUTPUT_LENGTH:
        return _failure("output_too_long", "model output exceeds the length limit")
    text = raw_output.strip()
    if not text:
        return _failure("empty_output", "model output must not be empty")

    text = _unwrap_optional_fence(text)
    if text is None:
        return _failure("malformed_json_fence", "JSON code fence must wrap the entire output")

    try:
        payload = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_non_standard_constant,
        )
    except (_DuplicateKeyError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        return _failure("malformed_json", str(exc))

    if not isinstance(payload, dict):
        return _failure("invalid_envelope", "model action must be a JSON object")

    action_type = payload.get("type")
    if action_type == "tool_call":
        required_keys = {"type", "name", "arguments"}
        allowed_keys = required_keys | {"call_id"}
        if not required_keys.issubset(payload) or not set(payload).issubset(allowed_keys):
            return _failure(
                "invalid_tool_call",
                "tool_call requires type, name, and arguments; call_id is optional",
            )
        if not isinstance(payload["arguments"], dict):
            return _failure("invalid_tool_call", "tool arguments must be a JSON object")
        call_id = payload.get("call_id", default_call_id)
        if call_id is None:
            return _failure(
                "invalid_tool_call",
                "tool_call omitted call_id and no deterministic default was provided",
            )
        try:
            call = ToolCall(
                call_id=call_id,
                name=payload["name"],
                arguments=payload["arguments"],
            )
        except (TypeError, ValueError) as exc:
            return _failure("invalid_tool_call", str(exc))
        return ActionParseResult(action=call)

    if action_type == "final":
        if set(payload) != {"type", "answer"}:
            return _failure("invalid_final_answer", "final requires exactly type and answer")
        answer = payload["answer"]
        if isinstance(answer, bool) or not isinstance(answer, (str, int, float)):
            return _failure("invalid_final_answer", "final answer must be a string or number")
        if isinstance(answer, float) and not math.isfinite(answer):
            return _failure("invalid_final_answer", "final answer must be finite")
        return ActionParseResult(action=FinalAnswer(answer=answer))

    return _failure("unknown_action_type", "action type must be 'tool_call' or 'final'")
