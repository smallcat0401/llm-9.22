"""Convert verified calculator trajectories to Qwen-native tool-call SFT rows."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import json
from typing import Any, Iterable, Mapping, Sequence

from .model_protocol import FinalAnswer, parse_model_action
from .prompting import build_native_calculator_grpo_messages
from .schemas import Split, Task, TaskKind, ToolCall
from .tools.calculator import CalculatorError, calculator
from .verifier import verify_numeric_answer


class NativeSFTDataError(ValueError):
    pass


CALCULATOR_TOOL_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Evaluate a bounded arithmetic expression with the safe calculator.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Arithmetic containing only numbers, parentheses, and +, -, *, /.",
                }
            },
            "required": ["expression"],
        },
    },
}


def _decimal(value: Any, field: str) -> Decimal:
    if isinstance(value, bool):
        raise NativeSFTDataError(f"{field} must be numeric")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise NativeSFTDataError(f"{field} must be numeric") from exc
    if not result.is_finite():
        raise NativeSFTDataError(f"{field} must be finite")
    return result


def build_native_calculator_sft_example(
    source: Mapping[str, Any], task: Task
) -> dict[str, Any]:
    """Replay one verified custom-protocol row and emit a native tool conversation.

    Invariants: the source and task are train-only calculator data; exactly one
    successful calculator call is replayed; its expression reproduces the stored
    observation; and the final answer passes the task's outcome verifier.
    """
    metadata = source.get("metadata")
    messages = source.get("messages")
    if not isinstance(metadata, Mapping):
        raise NativeSFTDataError("source metadata must be an object")
    if isinstance(messages, (str, bytes)) or not isinstance(messages, Sequence):
        raise NativeSFTDataError("source messages must be an array")
    if task.split is not Split.TRAIN or task.kind is not TaskKind.CALCULATOR:
        raise NativeSFTDataError("native calculator SFT requires a train calculator task")
    if metadata.get("task_id") != task.task_id or metadata.get("kind") != "calculator":
        raise NativeSFTDataError("source metadata does not match the calculator task")
    if len(messages) != 5 or [m.get("role") for m in messages if isinstance(m, Mapping)] != [
        "system", "user", "assistant", "tool", "assistant"
    ]:
        raise NativeSFTDataError("source must contain one complete calculator exchange")
    if not all(isinstance(message, Mapping) for message in messages):
        raise NativeSFTDataError("every source message must be an object")

    call_text = messages[2].get("content")
    final_text = messages[4].get("content")
    if not isinstance(call_text, str) or not isinstance(final_text, str):
        raise NativeSFTDataError("assistant source messages must contain text")
    parsed_call = parse_model_action(call_text, default_call_id="call-1")
    parsed_final = parse_model_action(final_text)
    if not parsed_call.ok or not isinstance(parsed_call.action, ToolCall):
        raise NativeSFTDataError("source tool call is invalid")
    if parsed_call.action.name != "calculator" or set(parsed_call.action.arguments) != {"expression"}:
        raise NativeSFTDataError("source must call calculator with exactly expression")
    if not parsed_final.ok or not isinstance(parsed_final.action, FinalAnswer):
        raise NativeSFTDataError("source final answer is invalid")
    if not verify_numeric_answer(parsed_final.action.answer, task.ground_truth).passed:
        raise NativeSFTDataError("source final answer does not pass the task verifier")

    try:
        observation = json.loads(messages[3].get("content", ""))
        observed_value = observation["content"]["value"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise NativeSFTDataError("source tool observation is invalid") from exc
    if observation.get("ok") is not True:
        raise NativeSFTDataError("source tool observation must be successful")
    expression = parsed_call.action.arguments["expression"]
    try:
        replayed_value = calculator(expression)
    except CalculatorError as exc:
        raise NativeSFTDataError(f"calculator replay failed: {exc}") from exc
    if _decimal(replayed_value, "replayed result") != _decimal(observed_value, "observed result"):
        raise NativeSFTDataError("calculator replay does not match the stored observation")
    if not verify_numeric_answer(replayed_value, task.ground_truth).passed:
        raise NativeSFTDataError("calculator expression does not solve the task")

    initial = [message.to_dict() for message in build_native_calculator_grpo_messages(task)]
    native_messages = initial + [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "type": "function",
                    "function": {
                        "name": "calculator",
                        "arguments": {"expression": expression},
                    },
                }
            ],
        },
        {"role": "tool", "name": "calculator", "content": str(replayed_value)},
        {"role": "assistant", "content": final_text},
    ]
    return {
        "example_id": f"native-{source.get('example_id', task.task_id)}",
        "messages": native_messages,
        "tools": [CALCULATOR_TOOL_SCHEMA],
        "metadata": {
            **dict(metadata),
            "format": "transformers-native-calculator-v1",
            "source_example_id": source.get("example_id"),
        },
    }


def build_native_calculator_sft_dataset(
    sources: Iterable[Mapping[str, Any]], tasks: Iterable[Task]
) -> tuple[dict[str, Any], ...]:
    task_by_id = {task.task_id: task for task in tasks}
    rows = []
    seen = set()
    for source in sources:
        metadata = source.get("metadata")
        if not isinstance(metadata, Mapping) or metadata.get("kind") != "calculator":
            continue
        task_id = metadata.get("task_id")
        task = task_by_id.get(task_id)
        if task is None:
            raise NativeSFTDataError(f"missing task for source {task_id!r}")
        row = build_native_calculator_sft_example(source, task)
        if row["example_id"] in seen:
            raise NativeSFTDataError(f"duplicate example_id: {row['example_id']}")
        seen.add(row["example_id"])
        rows.append(row)
    if not rows:
        raise NativeSFTDataError("no calculator examples were selected")
    return tuple(rows)
