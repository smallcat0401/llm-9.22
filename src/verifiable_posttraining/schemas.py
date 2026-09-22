"""Tier A: canonical task and trajectory schemas.

These small schemas deliberately avoid framework-specific message classes. They
are the stable boundary shared by data generation, rollout, replay, and
evaluation. A model adapter may translate them to a framework chat format, but
stored experiment artifacts should remain readable without that framework.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, Mapping


class TaskKind(StrEnum):
    NO_TOOL = "no_tool"
    CALCULATOR = "calculator"
    SQL = "sql"
    SQL_ANALYSIS = "sql_analysis"


class Split(StrEnum):
    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"


def _require_non_empty(name: str, value: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class ToolCall:
    """A model-requested action before the environment executes it."""

    call_id: str
    name: str
    arguments: Mapping[str, Any]

    def __post_init__(self) -> None:
        _require_non_empty("call_id", self.call_id)
        _require_non_empty("name", self.name)
        if not isinstance(self.arguments, Mapping):
            raise TypeError("arguments must be a mapping")


@dataclass(frozen=True, slots=True)
class Observation:
    """The environment result corresponding to exactly one tool call."""

    call_id: str
    ok: bool
    content: Any
    error_code: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty("call_id", self.call_id)
        if self.ok and self.error_code is not None:
            raise ValueError("a successful observation cannot have an error_code")
        if not self.ok and not self.error_code:
            raise ValueError("a failed observation must include an error_code")


@dataclass(frozen=True, slots=True)
class TrajectoryStep:
    """One aligned tool call and environment observation."""

    index: int
    tool_call: ToolCall
    observation: Observation

    def __post_init__(self) -> None:
        if self.index < 0:
            raise ValueError("step index must be non-negative")
        if self.tool_call.call_id != self.observation.call_id:
            raise ValueError("tool call and observation call_id must match")


@dataclass(frozen=True, slots=True)
class Task:
    """A task definition whose hidden answer is never placed in the user prompt."""

    task_id: str
    family_id: str
    kind: TaskKind
    split: Split
    prompt: str
    allowed_tools: tuple[str, ...]
    ground_truth: Mapping[str, Any]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("task_id", self.task_id)
        _require_non_empty("family_id", self.family_id)
        _require_non_empty("prompt", self.prompt)
        if len(set(self.allowed_tools)) != len(self.allowed_tools):
            raise ValueError("allowed_tools must not contain duplicates")
        if self.kind is TaskKind.NO_TOOL and self.allowed_tools:
            raise ValueError("no-tool tasks must not expose tools")
        if not isinstance(self.ground_truth, Mapping):
            raise TypeError("ground_truth must be a mapping")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Task":
        return cls(
            task_id=str(value["task_id"]),
            family_id=str(value["family_id"]),
            kind=TaskKind(value["kind"]),
            split=Split(value["split"]),
            prompt=str(value["prompt"]),
            allowed_tools=tuple(value.get("allowed_tools", ())),
            ground_truth=dict(value["ground_truth"]),
            metadata=dict(value.get("metadata", {})),
        )


@dataclass(frozen=True, slots=True)
class Trajectory:
    """Executed actions and a final answer for one task attempt."""

    trajectory_id: str
    task_id: str
    steps: tuple[TrajectoryStep, ...]
    final_answer: Any
    model_id: str
    seed: int
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty("trajectory_id", self.trajectory_id)
        _require_non_empty("task_id", self.task_id)
        _require_non_empty("model_id", self.model_id)
        expected = tuple(range(len(self.steps)))
        actual = tuple(step.index for step in self.steps)
        if actual != expected:
            raise ValueError("trajectory step indices must be contiguous and start at zero")
        call_ids = tuple(step.tool_call.call_id for step in self.steps)
        if len(set(call_ids)) != len(call_ids):
            raise ValueError("tool call ids must be unique within a trajectory")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def demo_task() -> Task:
    """Return a tiny dependency-free fixture for smoke tests and documentation."""

    return Task(
        task_id="demo-percent-001",
        family_id="percentage-no-tool-v1",
        kind=TaskKind.NO_TOOL,
        split=Split.TEST,
        prompt="A group has 40 items and 10 are selected. What percentage is selected?",
        allowed_tools=(),
        ground_truth={"type": "number", "value": 25.0, "tolerance": 1e-6},
        metadata={"seed": 7, "difficulty": "easy"},
    )

