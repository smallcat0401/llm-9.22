"""Tier A verifiable rewards used by RLVR/GRPO experiments."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .model_protocol import FinalAnswer, parse_model_action
from .verifier import verify_numeric_answer


def completion_text(completion: Any) -> str:
    """Extract one assistant completion without repairing malformed content."""

    if isinstance(completion, str):
        return completion
    if isinstance(completion, Sequence) and not isinstance(completion, (str, bytes)):
        if len(completion) == 1 and isinstance(completion[0], Mapping):
            content = completion[0].get("content")
            if isinstance(content, str):
                return content
    raise ValueError("completion must be text or one assistant chat message")


def final_assistant_text(completion: Any) -> str:
    """Extract the final non-empty assistant content from a multi-turn rollout."""

    if isinstance(completion, str):
        return completion
    if isinstance(completion, Sequence) and not isinstance(completion, (str, bytes)):
        for message in reversed(completion):
            if not isinstance(message, Mapping) or message.get("role") != "assistant":
                continue
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                return content
    raise ValueError("completion must contain a final assistant text message")


def typed_final_rewards(completions: Sequence[Any], **_: Any) -> list[float]:
    """Give 1 only for an exact typed-final action; malformed JSON gets 0."""

    rewards = []
    for completion in completions:
        try:
            parsed = parse_model_action(completion_text(completion))
        except ValueError:
            rewards.append(0.0)
            continue
        rewards.append(float(parsed.ok and isinstance(parsed.action, FinalAnswer)))
    return rewards


def numeric_outcome_rewards(
    completions: Sequence[Any],
    ground_truth: Sequence[Mapping[str, Any]],
    **_: Any,
) -> list[float]:
    """Give 1 only when a typed final answer passes the numeric verifier.

    Format and correctness remain separate reward components so their logs show
    whether optimization is learning the protocol or the task outcome.
    """

    if len(completions) != len(ground_truth):
        raise ValueError("completions and ground_truth must have equal length")
    rewards = []
    for completion, truth in zip(completions, ground_truth, strict=True):
        try:
            parsed = parse_model_action(completion_text(completion))
        except ValueError:
            rewards.append(0.0)
            continue
        if not parsed.ok or not isinstance(parsed.action, FinalAnswer):
            rewards.append(0.0)
            continue
        rewards.append(float(verify_numeric_answer(parsed.action.answer, truth).passed))
    return rewards


def numeric_closeness_rewards(
    completions: Sequence[Any],
    ground_truth: Sequence[Mapping[str, Any]],
    **_: Any,
) -> list[float]:
    """Return bounded partial credit for a valid numeric final answer.

    Exact verifier success remains 1.  A wrong but parseable number receives
    ``1 / (1 + normalized_error)``, where error is normalized by the target's
    magnitude with a floor of 1.  Malformed or non-final actions receive 0.
    This dense component is diagnostic/supporting reward; the binary outcome
    reward remains the primary correctness signal.
    """

    if len(completions) != len(ground_truth):
        raise ValueError("completions and ground_truth must have equal length")
    rewards = []
    for completion, truth in zip(completions, ground_truth, strict=True):
        try:
            parsed = parse_model_action(completion_text(completion))
        except ValueError:
            rewards.append(0.0)
            continue
        if not parsed.ok or not isinstance(parsed.action, FinalAnswer):
            rewards.append(0.0)
            continue
        result = verify_numeric_answer(parsed.action.answer, truth)
        if result.predicted_value is None or result.absolute_error is None:
            rewards.append(0.0)
            continue
        scale = max(abs(result.target_value), 1.0)
        normalized_error = result.absolute_error / scale
        rewards.append(1.0 / (1.0 + normalized_error))
    return rewards


def tool_typed_final_rewards(completions: Sequence[Any], **_: Any) -> list[float]:
    """Give format credit only when the last assistant turn is a typed final."""

    rewards = []
    for completion in completions:
        try:
            parsed = parse_model_action(final_assistant_text(completion))
        except ValueError:
            rewards.append(0.0)
            continue
        rewards.append(float(parsed.ok and isinstance(parsed.action, FinalAnswer)))
    return rewards


def tool_numeric_outcome_rewards(
    completions: Sequence[Any],
    ground_truth: Sequence[Mapping[str, Any]],
    **_: Any,
) -> list[float]:
    """Score the final answer at the end of a native multi-turn tool rollout.

    Qwen's native tool template returns a plain scalar after the tool result,
    while the project's separate protocol asks for a typed-final JSON object.
    Outcome reward accepts either representation; ``tool_typed_final_rewards``
    continues to measure the stricter JSON format independently.
    """

    if len(completions) != len(ground_truth):
        raise ValueError("completions and ground_truth must have equal length")
    rewards = []
    for completion, truth in zip(completions, ground_truth, strict=True):
        try:
            final_text = final_assistant_text(completion)
            parsed = parse_model_action(final_text)
            answer = (
                parsed.action.answer
                if parsed.ok and isinstance(parsed.action, FinalAnswer)
                else final_text
            )
        except ValueError:
            rewards.append(0.0)
            continue
        rewards.append(float(verify_numeric_answer(answer, truth).passed))
    return rewards


def tool_numeric_closeness_rewards(
    completions: Sequence[Any],
    ground_truth: Sequence[Mapping[str, Any]],
    **_: Any,
) -> list[float]:
    """Return bounded numeric partial credit for a multi-turn final answer."""

    if len(completions) != len(ground_truth):
        raise ValueError("completions and ground_truth must have equal length")
    rewards = []
    for completion, truth in zip(completions, ground_truth, strict=True):
        try:
            final_text = final_assistant_text(completion)
            parsed = parse_model_action(final_text)
            answer = (
                parsed.action.answer
                if parsed.ok and isinstance(parsed.action, FinalAnswer)
                else final_text
            )
        except ValueError:
            rewards.append(0.0)
            continue
        result = verify_numeric_answer(answer, truth)
        if result.predicted_value is None or result.absolute_error is None:
            rewards.append(0.0)
            continue
        scale = max(abs(result.target_value), 1.0)
        rewards.append(1.0 / (1.0 + result.absolute_error / scale))
    return rewards


def calculator_trace_rewards(completions: Sequence[Any], **_: Any) -> list[float]:
    """Reward a completed native tool-call -> tool-result -> final sequence.

    Merely mentioning a calculator in text is insufficient.  The rollout must
    contain a structured assistant ``tool_calls`` field, a following tool
    message, and a later assistant text response.
    """

    rewards = []
    for completion in completions:
        if not isinstance(completion, Sequence) or isinstance(completion, (str, bytes)):
            rewards.append(0.0)
            continue
        tool_call_index = next(
            (
                index
                for index, message in enumerate(completion)
                if isinstance(message, Mapping)
                and message.get("role") == "assistant"
                and bool(message.get("tool_calls"))
            ),
            None,
        )
        if tool_call_index is None:
            rewards.append(0.0)
            continue
        tool_result_index = next(
            (
                index
                for index, message in enumerate(completion)
                if index > tool_call_index
                and isinstance(message, Mapping)
                and message.get("role") == "tool"
            ),
            None,
        )
        has_final = any(
            index > (tool_result_index if tool_result_index is not None else len(completion))
            and isinstance(message, Mapping)
            and message.get("role") == "assistant"
            and isinstance(message.get("content"), str)
            and bool(message["content"].strip())
            for index, message in enumerate(completion)
        )
        rewards.append(float(tool_result_index is not None and has_final))
    return rewards


def calculator_result_rewards(
    completions: Sequence[Any],
    ground_truth: Sequence[Mapping[str, Any]],
    **_: Any,
) -> list[float]:
    """Reward only a calculator result that already matches the task target.

    This component attributes correctness before the final answer is produced.
    A syntactically valid but semantically wrong expression receives zero even
    when the calculator executes successfully.  Missing, error, ambiguous, and
    non-numeric tool messages also receive zero.
    """

    if len(completions) != len(ground_truth):
        raise ValueError("completions and ground_truth must have equal length")
    rewards = []
    for completion, truth in zip(completions, ground_truth, strict=True):
        if not isinstance(completion, Sequence) or isinstance(completion, (str, bytes)):
            rewards.append(0.0)
            continue
        tool_content = next(
            (
                message.get("content")
                for message in completion
                if isinstance(message, Mapping) and message.get("role") == "tool"
            ),
            None,
        )
        if tool_content is None:
            rewards.append(0.0)
            continue
        rewards.append(float(verify_numeric_answer(tool_content, truth).passed))
    return rewards
