"""Build audited V3 reference-program SFT rows for zero-pass train tasks.

These rows are deliberately separate from search-distilled trajectories.  A
human-audited arithmetic expression is executed by the safe local calculator,
and the resulting final answer is checked by the task verifier.  The builder
never invents model output and never admits validation/test tasks.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .dataset import load_tasks_jsonl
from .native_sft_data import CALCULATOR_TOOL_SCHEMA
from .prompting import (
    ChatMessage,
    append_tool_exchange,
    build_initial_messages,
    build_native_calculator_grpo_messages,
)
from .schemas import Observation, Split, Task, TaskKind
from .sft_data import write_sft_jsonl
from .tools.calculator import calculator
from .verifier import verify_numeric_answer


REFERENCE_SET = "v3-zero-pass-reference-program-v2"


class V3ReferenceProgramError(ValueError):
    """The audited task/program pair violates a training-data invariant."""


@dataclass(frozen=True, slots=True)
class ReferenceProgram:
    """One audited calculator expression and its visible answer formatting.

    ``answer_decimals`` is used only when the task expects a rounded answer.
    The arithmetic tool still returns its unrounded result; the assistant's
    final action performs the explicitly recorded display rounding.
    """

    expression: str
    answer_decimals: int | None = None

    def __post_init__(self) -> None:
        if not self.expression.strip():
            raise ValueError("reference expression must be non-empty")
        if self.answer_decimals is not None and self.answer_decimals < 0:
            raise ValueError("answer_decimals must be non-negative")


# These are the reviewed train-only tasks that had no usable Best-of-8 path.
# The mapping is intentionally explicit: changing an expression is a material
# label change and must therefore be visible in code review.
REFERENCE_PROGRAMS: Mapping[str, ReferenceProgram] = {
    "v3-public-244426e00be4-arithmetic": ReferenceProgram(
        "(48694 * 0.351) / 51279 * 100", 2
    ),
    "v3-public-4a29948bb22b-arithmetic": ReferenceProgram(
        "((0.709 * 275) - (0.739 * 225.93)) / (0.739 * 225.93) * 100", 2
    ),
    "v3-public-4b50d974aae5-arithmetic": ReferenceProgram(
        "(((25282320 - 22095416) / 22095416) "
        "+ ((22095416 - 19063121) / 19063121)) / 2 * 100",
        2,
    ),
    "v3-public-4dff5a6c3f03-arithmetic": ReferenceProgram(
        "(10 * 2 + 1) * (25 / 2)"
    ),
    "v3-public-550b417fd1d0-arithmetic": ReferenceProgram(
        "((94.5 + 117.7) - (86.5 + 121.8)) / (86.5 + 121.8) * 100", 2
    ),
    "v3-public-9a63b89ea330-arithmetic": ReferenceProgram(
        "(1496 + (-879)) / 2 - ((-879) + 4764) / 2"
    ),
    "v3-public-aa133d54fab4-arithmetic": ReferenceProgram(
        "(1147976 * 9.67) / (881420 * 6.53)", 2
    ),
    "v3-public-af1f11d98652-arithmetic": ReferenceProgram(
        "(594202 + 550058) / 2 - (405359 + 361922) / 2"
    ),
    "v3-public-c84b259d3bfe-arithmetic": ReferenceProgram(
        "((724.8 + 479.4 + 86.5 + 121.8) "
        "- (655.4 + 445.8 - 168.9 + 105.1 + 202.6)) "
        "/ (655.4 + 445.8 - 168.9 + 105.1 + 202.6) * 100",
        2,
    ),
    "v3-public-fee44b520741-arithmetic": ReferenceProgram(
        "(-80.8 - 566.9 - 582.1 - 330.5 + 81.8) / 5"
    ),
    "v3-gsm8k-train-0858-calculator": ReferenceProgram(
        "(150 * 2 - 2500 * 0.05) / 25"
    ),
    "v3-gsm8k-train-1722-calculator": ReferenceProgram(
        "6 / (3 / 150 + 2 / 200 + 1 / 300)"
    ),
    "v3-gsm8k-train-1945-calculator": ReferenceProgram("20 - 1 - 1 - 1"),
    "v3-gsm8k-train-2623-calculator": ReferenceProgram(
        "10 * 10 * 10 - (8 * 10 * 10 + 3 * 10 + 7)"
    ),
    "v3-gsm8k-train-4479-calculator": ReferenceProgram(
        "50 * 14 - (8 + 3 + 12) * 14 - 21"
    ),
    "v3-gsm8k-train-5124-calculator": ReferenceProgram(
        "(20 * 400) / (80 * 5) + 20 / 4"
    ),
    "v3-gsm8k-train-5186-calculator": ReferenceProgram(
        "((37 - 15 - 8) / 2) + 8 - 3 + 5"
    ),
    "v3-gsm8k-train-7014-calculator": ReferenceProgram("50 - 1 - 12 - 9 + 11"),
    "v3-public-13b99cafff24-arithmetic-revised-v2": ReferenceProgram(
        "(((1074 - 1691) / 1691) + ((1691 - 7680) / 7680)) / 2 * 100", 2
    ),
    "v3-public-776305a10cc6-arithmetic-revised-v2": ReferenceProgram(
        "(((519.7 - 526.9) / 526.9) + ((527.9 - 519.7) / 519.7)) / 2 * 100",
        2,
    ),
    "v3-public-abe2824b6e81-arithmetic-revised-v2": ReferenceProgram(
        "((5.74 + 7.83) / 2) / 100 * 79.9", 1
    ),
    "v3-public-ea79960b2b5e-arithmetic-revised-v2": ReferenceProgram(
        "(801659 * 183.18 + 462629 * 194.65) / (801659 + 462629)", 2
    ),
    "v3-public-f5fdb156cd45-arithmetic-revised-v2": ReferenceProgram(
        "(12980 + 13600) / 2 - (13600 + 14223) / 2"
    ),
    "v3-gsm8k-train-1213-calculator-revised-v2": ReferenceProgram(
        "(75 - 12) - 75 * (1 - 0.20)"
    ),
    "v3-gsm8k-train-2706-calculator-revised-v2": ReferenceProgram("(5 - 2) * 11"),
    "v3-gsm8k-train-5285-calculator-revised-v2": ReferenceProgram(
        "2 * (4 * 40 + 40)"
    ),
}


def _final_answer(result: int | float, program: ReferenceProgram) -> str:
    if program.answer_decimals is None:
        return str(result)
    quantum = Decimal(1).scaleb(-program.answer_decimals)
    rounded = Decimal(str(result)).quantize(quantum, rounding=ROUND_HALF_UP)
    return format(rounded, f".{program.answer_decimals}f")


def _execute_and_verify(
    task: Task,
    program: ReferenceProgram,
) -> tuple[int | float, str]:
    """Enforce the shared split, tool, replay, and outcome invariants."""

    if task.split is not Split.TRAIN:
        raise V3ReferenceProgramError(f"reference SFT requires train split: {task.task_id}")
    if task.kind is not TaskKind.CALCULATOR or task.allowed_tools != ("calculator",):
        raise V3ReferenceProgramError(
            f"reference SFT requires a calculator-only task: {task.task_id}"
        )
    if task.metadata.get("training_eligible") is not True:
        raise V3ReferenceProgramError(f"task is not training-eligible: {task.task_id}")

    result = calculator(program.expression)
    answer = _final_answer(result, program)
    verification = verify_numeric_answer(answer, task.ground_truth)
    if not verification.passed:
        raise V3ReferenceProgramError(
            f"reference program final answer does not solve task: {task.task_id}"
        )
    return result, answer


def _reference_metadata(task: Task, *, format_name: str) -> dict[str, Any]:
    return {
        "task_id": task.task_id,
        "family_id": task.family_id,
        "kind": task.kind.value,
        "split": task.split.value,
        "format": format_name,
        "reference_set": REFERENCE_SET,
        "trajectory_source": "reference-program",
        "search_discovered": False,
        "provenance": "human-audited expression with safe-calculator replay",
        "calculator_replay_verified": True,
    }


def build_reference_program_example(
    task: Task,
    program: ReferenceProgram,
) -> dict[str, Any]:
    """Execute and verify one native-tool reference-program SFT row."""

    result, answer = _execute_and_verify(task, program)

    messages = [message.to_dict() for message in build_native_calculator_grpo_messages(task)]
    messages.extend(
        (
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "type": "function",
                        "function": {
                            "name": "calculator",
                            "arguments": {"expression": program.expression},
                        },
                    }
                ],
            },
            {"role": "tool", "name": "calculator", "content": str(result)},
            {
                "role": "assistant",
                "content": json.dumps(
                    {"type": "final", "answer": answer},
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
            },
        )
    )
    return {
        "example_id": f"v3-reference-program-{task.task_id}",
        "messages": messages,
        "tools": [CALCULATOR_TOOL_SCHEMA],
        "metadata": {
            **_reference_metadata(
                task, format_name="reference-program-native-calculator-v1"
            ),
            "answer_decimals": program.answer_decimals,
        },
    }


def build_reference_program_custom_example(
    task: Task,
    program: ReferenceProgram,
) -> dict[str, Any]:
    """Emit the same verified program using the search runner's JSON protocol."""

    result, answer = _execute_and_verify(task, program)
    raw_call = json.dumps(
        {
            "type": "tool_call",
            "name": "calculator",
            "arguments": {"expression": program.expression},
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    observation = Observation(
        call_id="call-1",
        ok=True,
        content={"value": result},
    )
    messages = append_tool_exchange(
        build_initial_messages(task),
        raw_model_output=raw_call,
        observation=observation,
    )
    messages.append(ChatMessage(
        role="assistant",
        content=json.dumps(
            {"type": "final", "answer": answer},
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    ))
    return {
        "example_id": f"v3-reference-program-custom-{task.task_id}",
        "messages": [message.to_dict() for message in messages],
        "metadata": {
            **_reference_metadata(
                task, format_name="reference-program-custom-protocol-v1"
            ),
            "answer_decimals": program.answer_decimals,
        },
    }


def build_v3_reference_program_sft(tasks: Iterable[Task]) -> tuple[dict[str, Any], ...]:
    """Build the reviewed 26-row V3 reference-program branch.

    The initially ambiguous restricted-stock percentage task is intentionally
    absent: after its rounding wording was corrected, Best-of-8 found a fully
    aligned path, so that revised task belongs to Search-SFT instead.
    """

    task_by_id: dict[str, Task] = {}
    for task in tasks:
        if task.task_id in task_by_id:
            raise V3ReferenceProgramError(f"duplicate task id: {task.task_id}")
        task_by_id[task.task_id] = task
    missing = sorted(set(REFERENCE_PROGRAMS) - set(task_by_id))
    if missing:
        raise V3ReferenceProgramError(f"missing reference-program tasks: {missing}")

    return tuple(
        build_reference_program_example(task_by_id[task_id], program)
        for task_id, program in REFERENCE_PROGRAMS.items()
    )


def build_v3_reference_program_custom_sft(
    tasks: Iterable[Task],
) -> tuple[dict[str, Any], ...]:
    """Build the same 26 programs in the search runner's custom protocol."""

    task_by_id: dict[str, Task] = {}
    for task in tasks:
        if task.task_id in task_by_id:
            raise V3ReferenceProgramError(f"duplicate task id: {task.task_id}")
        task_by_id[task.task_id] = task
    missing = sorted(set(REFERENCE_PROGRAMS) - set(task_by_id))
    if missing:
        raise V3ReferenceProgramError(f"missing reference-program tasks: {missing}")
    return tuple(
        build_reference_program_custom_example(task_by_id[task_id], program)
        for task_id, program in REFERENCE_PROGRAMS.items()
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args(argv)

    tasks = tuple(task for path in args.input for task in load_tasks_jsonl(path))
    examples = build_v3_reference_program_sft(tasks)
    write_sft_jsonl(examples, args.output)
    manifest = {
        "dataset": REFERENCE_SET,
        "purpose": "audited reference-program SFT branch for V3 zero-pass train tasks",
        "trajectory_source": "reference-program",
        "search_discovered": False,
        "example_count": len(examples),
        "task_count": len(examples),
        "inputs": [
            {"path": str(path), "sha256": _sha256(path)} for path in args.input
        ],
        "output_sha256": _sha256(args.output),
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
