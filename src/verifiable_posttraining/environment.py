"""Tier B: framework-independent task episode lifecycle.

The environment owns tool execution and observations.  A model may request a
tool call, but it must never be allowed to invent the corresponding tool
result.  Expected model mistakes become failed observations; lifecycle misuse
by the calling program raises ``EpisodeStateError`` so implementation bugs are
not silently scored as model failures.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .schemas import Observation, Task, ToolCall, Trajectory, TrajectoryStep
from .verifier import VerificationResult, verify_numeric_answer

ToolExecutor = Callable[[ToolCall], Observation]


class EpisodeStateError(RuntimeError):
    """The caller used reset/step/finish in an invalid order."""


@dataclass(frozen=True, slots=True)
class EpisodeResult:
    task: Task
    trajectory: Trajectory
    verification: VerificationResult


class EpisodeEnvironment:
    """Run one task at a time through reset, tool steps, and final verification.

    Invariants:

    * only tools listed by the task can run;
    * only the environment creates observations;
    * every recorded call and observation shares a call id;
    * recorded step indices are contiguous;
    * a tool-call budget bounds model/environment interaction;
    * finish can happen exactly once per reset.
    """

    def __init__(
        self,
        tool_executors: Mapping[str, ToolExecutor],
        *,
        max_tool_calls: int = 4,
    ) -> None:
        if max_tool_calls < 0:
            raise ValueError("max_tool_calls must be non-negative")
        if any(not name.strip() for name in tool_executors):
            raise ValueError("tool executor names must be non-empty")
        self._tool_executors = dict(tool_executors)
        self._max_tool_calls = max_tool_calls
        self._task: Task | None = None
        self._steps: list[TrajectoryStep] = []
        self._seen_call_ids: set[str] = set()
        self._rejected_call_count = 0
        self._active = False

    def reset(self, task: Task) -> None:
        """Start a new episode after construction or after the prior finish."""

        if self._active:
            raise EpisodeStateError("cannot reset before the active episode is finished")
        self._task = task
        self._steps = []
        self._seen_call_ids = set()
        self._rejected_call_count = 0
        self._active = True

    def step(self, call: ToolCall) -> Observation:
        """Validate and execute one model-requested tool call.

        Rejected calls are returned to the model as failed observations.  Calls
        with duplicate ids or calls beyond the budget are not appended because
        doing so would violate the canonical trajectory schema; their count is
        retained in trajectory metadata when the episode finishes.
        """

        task = self._require_active_task()

        if call.call_id in self._seen_call_ids:
            self._rejected_call_count += 1
            return self._failure(call, "duplicate_call_id", "tool call id was already used")

        if len(self._steps) >= self._max_tool_calls:
            self._rejected_call_count += 1
            return self._failure(
                call,
                "tool_call_limit_exceeded",
                f"at most {self._max_tool_calls} tool calls are allowed",
            )

        self._seen_call_ids.add(call.call_id)
        if call.name not in task.allowed_tools:
            observation = self._failure(
                call,
                "tool_not_allowed",
                f"tool '{call.name}' is not allowed for this task",
            )
        elif call.name not in self._tool_executors:
            observation = self._failure(
                call,
                "tool_unavailable",
                f"tool '{call.name}' has no registered executor",
            )
        else:
            observation = self._execute(call)

        self._steps.append(
            TrajectoryStep(
                index=len(self._steps),
                tool_call=call,
                observation=observation,
            )
        )
        return observation

    def finish(
        self,
        final_answer: Any,
        *,
        trajectory_id: str,
        model_id: str,
        seed: int,
        metadata: Mapping[str, Any] | None = None,
    ) -> EpisodeResult:
        """Close the episode, freeze its trajectory, and verify the outcome."""

        task = self._require_active_task()
        verification = self._verify(task, final_answer)
        trajectory_metadata = dict(metadata or {})
        trajectory_metadata["rejected_tool_calls"] = self._rejected_call_count
        trajectory = Trajectory(
            trajectory_id=trajectory_id,
            task_id=task.task_id,
            steps=tuple(self._steps),
            final_answer=final_answer,
            model_id=model_id,
            seed=seed,
            metadata=trajectory_metadata,
        )
        self._active = False
        return EpisodeResult(task=task, trajectory=trajectory, verification=verification)

    def _require_active_task(self) -> Task:
        if not self._active or self._task is None:
            raise EpisodeStateError("reset must be called before step or finish")
        return self._task

    def _execute(self, call: ToolCall) -> Observation:
        executor = self._tool_executors[call.name]
        try:
            observation = executor(call)
        except Exception:
            # Keep a long evaluation run alive, but do not expose host exception
            # details to the model. Production runners should log the traceback.
            return self._failure(
                call,
                "tool_execution_error",
                "tool executor failed unexpectedly",
            )
        if not isinstance(observation, Observation):
            return self._failure(
                call,
                "invalid_tool_result",
                "tool executor did not return an Observation",
            )
        if observation.call_id != call.call_id:
            return self._failure(
                call,
                "observation_mismatch",
                "tool observation call id did not match the request",
            )
        return observation

    @staticmethod
    def _failure(call: ToolCall, code: str, message: str) -> Observation:
        return Observation(
            call_id=call.call_id,
            ok=False,
            content={"message": message},
            error_code=code,
        )

    @staticmethod
    def _verify(task: Task, final_answer: Any) -> VerificationResult:
        verifier_type = task.ground_truth.get("type")
        if verifier_type == "number":
            return verify_numeric_answer(final_answer, task.ground_truth)
        raise ValueError(f"unsupported ground_truth type: {verifier_type!r}")
