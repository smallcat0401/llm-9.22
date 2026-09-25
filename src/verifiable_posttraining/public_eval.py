"""Adapters for frozen, evaluation-only public datasets."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable, Mapping

from .schemas import Split, Task, TaskKind
from .verifier import normalize_numeric_answer


class PublicDatasetError(ValueError):
    pass


def load_gsm8k_jsonl(path: str | Path) -> tuple[Mapping[str, Any], ...]:
    """Load the original OpenAI GSM8K JSONL without an extra dataset library."""

    records = []
    seen_questions = set()
    for line_number, line in enumerate(
        Path(path).read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PublicDatasetError(f"invalid JSON at line {line_number}: {exc}") from exc
        if not isinstance(record, Mapping):
            raise PublicDatasetError(f"record at line {line_number} must be an object")
        question = record.get("question")
        answer = record.get("answer")
        if not isinstance(question, str) or not question.strip():
            raise PublicDatasetError(f"line {line_number} has an invalid question")
        if not isinstance(answer, str) or "####" not in answer:
            raise PublicDatasetError(f"line {line_number} has an invalid GSM8K answer")
        if question in seen_questions:
            raise PublicDatasetError(f"duplicate question at line {line_number}")
        seen_questions.add(question)
        records.append({"source_index": line_number - 1, **record})
    if not records:
        raise PublicDatasetError("GSM8K file must not be empty")
    return tuple(records)


def extract_gsm8k_final_answer(answer: str) -> int | float:
    """Extract only the official answer after GSM8K's final ``####`` marker."""

    if not isinstance(answer, str) or "####" not in answer:
        raise PublicDatasetError("GSM8K answer must contain a #### final marker")
    final_text = answer.rsplit("####", maxsplit=1)[1].strip()
    try:
        value = normalize_numeric_answer(final_text)
    except ValueError as exc:
        raise PublicDatasetError(f"invalid GSM8K final answer: {final_text!r}") from exc
    if value == value.to_integral_value():
        return int(value)
    return float(value)


def _selection_key(record: Mapping[str, Any], seed: int) -> bytes:
    payload = f"{seed}:{record['source_index']}:{record['question']}"
    return hashlib.sha256(payload.encode("utf-8")).digest()


def select_frozen_subset(
    records: Iterable[Mapping[str, Any]],
    *,
    sample_size: int,
    seed: int,
    excluded_source_indices: Iterable[int] = (),
) -> tuple[Mapping[str, Any], ...]:
    excluded = {int(index) for index in excluded_source_indices}
    record_list = [
        record for record in records if int(record["source_index"]) not in excluded
    ]
    if sample_size <= 0:
        raise ValueError("sample_size must be positive")
    if sample_size > len(record_list):
        raise ValueError("sample_size exceeds available records")
    return tuple(sorted(record_list, key=lambda record: _selection_key(record, seed))[:sample_size])


def _numeric_truth(value: int | float) -> dict[str, str | int | float]:
    return {"type": "number", "value": value, "tolerance": 1e-6}


def build_gsm8k_external_tasks(
    records: Iterable[Mapping[str, Any]],
    *,
    sample_size: int = 100,
    seed: int = 7,
) -> tuple[Task, ...]:
    """Create paired no-tool and calculator-enabled tasks from a frozen subset."""

    selected = select_frozen_subset(records, sample_size=sample_size, seed=seed)
    tasks = []
    for record in selected:
        source_index = int(record["source_index"])
        question = str(record["question"]).strip()
        answer = extract_gsm8k_final_answer(str(record["answer"]))
        common_metadata = {
            "source_dataset": "openai/grade-school-math",
            "source_config": "main",
            "source_split": "test",
            "source_index": source_index,
            "external_evaluation_only": True,
            "subset_seed": seed,
        }
        tasks.append(
            Task(
                task_id=f"gsm8k-test-{source_index:04d}-no-tool",
                family_id="gsm8k-external-no-tool-v1",
                kind=TaskKind.NO_TOOL,
                split=Split.TEST,
                prompt=f"Solve this problem without tools. Return the final number.\n\n{question}",
                allowed_tools=(),
                ground_truth=_numeric_truth(answer),
                metadata={**common_metadata, "tool_condition": "no_tool"},
            )
        )
        tasks.append(
            Task(
                task_id=f"gsm8k-test-{source_index:04d}-calculator",
                family_id="gsm8k-external-calculator-v1",
                kind=TaskKind.CALCULATOR,
                split=Split.TEST,
                prompt=(
                    "Solve this problem. The calculator tool is available for arithmetic. "
                    f"Return the final number.\n\n{question}"
                ),
                allowed_tools=("calculator",),
                ground_truth=_numeric_truth(answer),
                metadata={**common_metadata, "tool_condition": "calculator_available"},
            )
        )
    return tuple(tasks)


def build_gsm8k_search_screen_tasks(
    records: Iterable[Mapping[str, Any]],
    *,
    sample_size: int = 100,
    seed: int = 71,
    excluded_source_indices: Iterable[int] = (),
) -> tuple[Task, ...]:
    """Create train-only paired tasks for measuring a model's search gap.

    This builder must only receive the official GSM8K ``train`` source.  The
    resulting rows may be searched and later used for trajectory SFT, unlike
    :func:`build_gsm8k_external_tasks`, whose test rows are evaluation-only.
    The source split remains explicit in every record so train/test provenance
    cannot be silently mixed.
    """

    selected = select_frozen_subset(
        records,
        sample_size=sample_size,
        seed=seed,
        excluded_source_indices=excluded_source_indices,
    )
    tasks = []
    for record in selected:
        source_index = int(record["source_index"])
        question = str(record["question"]).strip()
        answer = extract_gsm8k_final_answer(str(record["answer"]))
        common_metadata = {
            "source_dataset": "openai/grade-school-math",
            "source_config": "main",
            "source_split": "train",
            "source_index": source_index,
            "search_screen": True,
            "subset_seed": seed,
        }
        tasks.append(
            Task(
                task_id=f"gsm8k-train-{source_index:04d}-no-tool",
                family_id="gsm8k-public-train-no-tool-v1",
                kind=TaskKind.NO_TOOL,
                split=Split.TRAIN,
                prompt=f"Solve this problem without tools. Return the final number.\n\n{question}",
                allowed_tools=(),
                ground_truth=_numeric_truth(answer),
                metadata={**common_metadata, "tool_condition": "no_tool"},
            )
        )
        tasks.append(
            Task(
                task_id=f"gsm8k-train-{source_index:04d}-calculator",
                family_id="gsm8k-public-train-calculator-v1",
                kind=TaskKind.CALCULATOR,
                split=Split.TRAIN,
                prompt=(
                    "Solve this problem. The calculator tool is available for arithmetic. "
                    f"Return the final number.\n\n{question}"
                ),
                allowed_tools=("calculator",),
                ground_truth=_numeric_truth(answer),
                metadata={**common_metadata, "tool_condition": "calculator_available"},
            )
        )
    return tuple(tasks)


def build_gsm8k_train_validation_tasks(
    records: Iterable[Mapping[str, Any]],
    *,
    sample_size: int = 50,
    seed: int = 131,
    excluded_source_indices: Iterable[int] = (),
) -> tuple[Task, ...]:
    """Freeze held-out validation tasks from GSM8K train-source questions.

    Exclusions are source-question indices, not condition-specific task IDs.
    This keeps both paired conditions out whenever a source question contributed
    to search or SFT.
    """

    search_tasks = build_gsm8k_search_screen_tasks(
        records,
        sample_size=sample_size,
        seed=seed,
        excluded_source_indices=excluded_source_indices,
    )
    validation_tasks = []
    for task in search_tasks:
        source_index = int(task.metadata["source_index"])
        condition = task.kind.value
        metadata = dict(task.metadata)
        metadata.pop("search_screen", None)
        metadata["validation_only"] = True
        validation_tasks.append(
            replace(
                task,
                task_id=f"gsm8k-train-validation-{source_index:04d}-{condition}",
                family_id=f"gsm8k-public-validation-{condition}-v1",
                split=Split.VALIDATION,
                metadata=metadata,
            )
        )
    return tuple(validation_tasks)


def public_dataset_manifest(
    *,
    source_path: str | Path,
    tasks: Iterable[Task],
    sample_size: int,
    seed: int,
) -> dict[str, Any]:
    source = Path(source_path)
    source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    task_list = list(tasks)
    source_indices = sorted({int(task.metadata["source_index"]) for task in task_list})
    return {
        "dataset": "GSM8K",
        "upstream": "openai/grade-school-math",
        "license": "MIT",
        "source_split": "test",
        "evaluation_only": True,
        "source_sha256": source_sha256,
        "subset_seed": seed,
        "source_example_count": sample_size,
        "paired_task_count": len(task_list),
        "source_indices": source_indices,
    }
