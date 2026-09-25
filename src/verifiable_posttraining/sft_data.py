"""Build supervised chat examples from strictly verified train trajectories."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .model_protocol import FinalAnswer, parse_model_action
from .prompting import ChatMessage, append_tool_exchange, build_initial_messages
from .schemas import Observation, Split, Task, TaskKind, ToolCall


class SFTDataError(ValueError):
    pass


def _mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SFTDataError(f"{field_name} must be an object")
    return value


def _sequence(value: Any, field_name: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise SFTDataError(f"{field_name} must be an array")
    return value


def build_sft_example(record: Mapping[str, Any]) -> dict[str, Any]:
    """Replay structural invariants and convert one selected rollout to messages."""

    try:
        task = Task.from_dict(_mapping(record["task"], "task"))
        rollout = _mapping(record["rollout"], "rollout")
        verification = _mapping(record["verification"], "verification")
        trajectory = _mapping(record["trajectory"], "trajectory")
        raw_outputs = _sequence(record["raw_outputs"], "raw_outputs")
        steps = _sequence(trajectory["steps"], "trajectory.steps")
    except KeyError as exc:
        raise SFTDataError(f"selected trajectory is missing field {exc.args[0]!r}") from exc
    except (TypeError, ValueError) as exc:
        raise SFTDataError(str(exc)) from exc

    if task.split is not Split.TRAIN:
        raise SFTDataError("SFT examples may only come from the train split")
    if rollout.get("task_success") is not True or verification.get("passed") is not True:
        raise SFTDataError("SFT source trajectory must be a strict verified success")
    if trajectory.get("task_id") != task.task_id:
        raise SFTDataError("trajectory task_id does not match task")
    if len(raw_outputs) != len(steps) + 1:
        raise SFTDataError("successful trajectory must have one final output after tool steps")
    if any(not isinstance(output, str) for output in raw_outputs):
        raise SFTDataError("every raw model output must be a string")

    messages = build_initial_messages(task)
    for index, step_value in enumerate(steps):
        step = _mapping(step_value, f"trajectory.steps[{index}]")
        if step.get("index") != index:
            raise SFTDataError("trajectory step indices must be contiguous")
        call_value = _mapping(step.get("tool_call"), "trajectory step tool_call")
        observation_value = _mapping(
            step.get("observation"), "trajectory step observation"
        )
        parsed = parse_model_action(
            raw_outputs[index],
            default_call_id=f"call-{index + 1}",
        )
        if not parsed.ok or not isinstance(parsed.action, ToolCall):
            raise SFTDataError("pre-final outputs must be valid tool calls")
        try:
            expected_call = ToolCall(
                call_id=call_value["call_id"],
                name=call_value["name"],
                arguments=call_value["arguments"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SFTDataError(f"invalid recorded tool call: {exc}") from exc
        if parsed.action != expected_call:
            raise SFTDataError("raw tool call does not match recorded trajectory")
        try:
            observation = Observation(
                call_id=observation_value["call_id"],
                ok=observation_value["ok"],
                content=observation_value.get("content"),
                error_code=observation_value.get("error_code"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SFTDataError(f"invalid recorded observation: {exc}") from exc
        if observation.call_id != expected_call.call_id:
            raise SFTDataError("tool call and observation call_id must match")
        messages = append_tool_exchange(
            messages,
            raw_model_output=raw_outputs[index],
            observation=observation,
        )

    final_output = raw_outputs[-1]
    parsed_final = parse_model_action(final_output)
    if not parsed_final.ok or not isinstance(parsed_final.action, FinalAnswer):
        raise SFTDataError("last raw output must be a valid final answer")
    if parsed_final.action.answer != trajectory.get("final_answer"):
        raise SFTDataError("raw final answer does not match recorded trajectory")
    messages.append(ChatMessage(role="assistant", content=final_output))

    search = record.get("search", {})
    search_metadata = dict(search) if isinstance(search, Mapping) else {}
    return {
        "example_id": f"sft-{task.task_id}",
        "messages": [message.to_dict() for message in messages],
        "metadata": {
            "task_id": task.task_id,
            "family_id": task.family_id,
            "kind": task.kind.value,
            "split": task.split.value,
            "source_trajectory_id": trajectory.get("trajectory_id"),
            "source_model_id": trajectory.get("model_id"),
            "source_seed": trajectory.get("seed"),
            **search_metadata,
        },
    }


def load_selected_trajectory_records(path: str | Path) -> tuple[Mapping[str, Any], ...]:
    records = []
    for line_number, line in enumerate(
        Path(path).read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SFTDataError(f"invalid JSON at line {line_number}: {exc}") from exc
        if not isinstance(record, Mapping):
            raise SFTDataError(f"record at line {line_number} must be an object")
        records.append(record)
    if not records:
        raise SFTDataError("selected trajectory file must not be empty")
    return tuple(records)


def is_path_aligned_sft_record(record: Mapping[str, Any]) -> bool:
    """Return whether a strict success is also a clean task-appropriate demonstration."""

    try:
        task = Task.from_dict(_mapping(record["task"], "task"))
        rollout = _mapping(record["rollout"], "rollout")
        verification = _mapping(record["verification"], "verification")
        trajectory = _mapping(record["trajectory"], "trajectory")
        steps = _sequence(trajectory["steps"], "trajectory.steps")
    except KeyError as exc:
        raise SFTDataError(f"candidate record is missing field {exc.args[0]!r}") from exc
    except (TypeError, ValueError) as exc:
        raise SFTDataError(str(exc)) from exc

    if task.split is not Split.TRAIN:
        raise SFTDataError("SFT candidate records may only come from the train split")
    if rollout.get("task_success") is not True or verification.get("passed") is not True:
        return False
    trajectory_metadata = _mapping(
        trajectory.get("metadata", {}), "trajectory.metadata"
    )
    try:
        rejected_tool_calls = int(trajectory_metadata.get("rejected_tool_calls", 0))
    except (TypeError, ValueError) as exc:
        raise SFTDataError("rejected_tool_calls must be an integer") from exc
    if rejected_tool_calls != 0:
        return False
    if task.kind is TaskKind.NO_TOOL:
        return len(steps) == 0
    if not steps:
        return False
    for step_value in steps:
        step = _mapping(step_value, "trajectory step")
        call = _mapping(step.get("tool_call"), "trajectory step tool_call")
        observation = _mapping(step.get("observation"), "trajectory step observation")
        if call.get("name") not in task.allowed_tools or observation.get("ok") is not True:
            return False
    return True


def select_path_aligned_sft_records(
    records: Iterable[Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    """Select the first clean aligned success per task, without redefining correctness."""

    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for record in records:
        try:
            task = Task.from_dict(_mapping(record["task"], "task"))
        except KeyError as exc:
            raise SFTDataError(f"candidate record is missing field {exc.args[0]!r}") from exc
        except (TypeError, ValueError) as exc:
            raise SFTDataError(str(exc)) from exc
        if task.split is not Split.TRAIN:
            raise SFTDataError("SFT candidate records may only come from the train split")
        grouped.setdefault(task.task_id, []).append(record)

    if not grouped:
        raise SFTDataError("candidate record collection must not be empty")
    selected = []
    for candidates in grouped.values():
        aligned = next(
            (candidate for candidate in candidates if is_path_aligned_sft_record(candidate)),
            None,
        )
        if aligned is not None:
            selected.append(aligned)
    if not selected:
        raise SFTDataError("no path-aligned strict successes were found")
    return tuple(selected)


def write_trajectory_records_jsonl(
    records: Iterable[Mapping[str, Any]], path: str | Path
) -> None:
    record_list = list(records)
    if not record_list:
        raise SFTDataError("trajectory record collection must not be empty")
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, ensure_ascii=False, sort_keys=True) for record in record_list]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_sft_dataset(records: Iterable[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    examples = []
    seen_example_ids = set()
    for record in records:
        example = build_sft_example(record)
        example_id = example["example_id"]
        if example_id in seen_example_ids:
            raise SFTDataError(f"duplicate SFT example_id: {example_id}")
        seen_example_ids.add(example_id)
        examples.append(example)
    if not examples:
        raise SFTDataError("SFT dataset must not be empty")
    return tuple(examples)


def write_sft_jsonl(examples: Iterable[Mapping[str, Any]], path: str | Path) -> None:
    example_list = list(examples)
    if not example_list:
        raise SFTDataError("SFT dataset must not be empty")
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(example, ensure_ascii=False, sort_keys=True) for example in example_list]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def merge_sft_examples(
    sources: Sequence[tuple[str, Sequence[Mapping[str, Any]]]],
) -> tuple[dict[str, Any], ...]:
    """Merge named SFT sources while preserving auditable provenance.

    Duplicate example identifiers are rejected instead of silently changing
    sampling weights.  Callers that intentionally want oversampling must create
    explicitly named replay copies so the weighting remains visible.
    """

    merged: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for source_name, examples in sources:
        if not isinstance(source_name, str) or not source_name.strip():
            raise SFTDataError("SFT source name must be non-empty")
        for example in examples:
            example_id = example.get("example_id")
            if not isinstance(example_id, str) or not example_id.strip():
                raise SFTDataError("every merged SFT example needs an example_id")
            if example_id in seen_ids:
                raise SFTDataError(f"duplicate SFT example_id: {example_id}")
            seen_ids.add(example_id)
            copied = dict(example)
            metadata = copied.get("metadata")
            if not isinstance(metadata, Mapping):
                raise SFTDataError("every merged SFT example needs metadata")
            copied["metadata"] = {**dict(metadata), "mixture_source": source_name}
            merged.append(copied)
    if not merged:
        raise SFTDataError("merged SFT dataset must not be empty")
    return tuple(merged)


def sft_dataset_summary(examples: Iterable[Mapping[str, Any]]) -> dict[str, object]:
    example_list = list(examples)
    return {
        "examples": len(example_list),
        "by_kind": dict(
            Counter(example["metadata"]["kind"] for example in example_list)
        ),
        "by_family": dict(
            Counter(example["metadata"]["family_id"] for example in example_list)
        ),
        "with_tool_messages": sum(
            any(message["role"] == "tool" for message in example["messages"])
            for example in example_list
        ),
    }
