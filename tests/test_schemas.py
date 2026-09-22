import json
import unittest

from verifiable_posttraining.schemas import (
    Observation,
    Split,
    Task,
    TaskKind,
    ToolCall,
    Trajectory,
    TrajectoryStep,
    demo_task,
)


class TaskTests(unittest.TestCase):
    def test_json_round_trip(self) -> None:
        task = demo_task()
        payload = json.loads(json.dumps(task.to_dict()))
        self.assertEqual(task, Task.from_dict(payload))

    def test_no_tool_task_cannot_expose_tools(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not expose tools"):
            Task(
                task_id="bad-task",
                family_id="bad-family",
                kind=TaskKind.NO_TOOL,
                split=Split.TRAIN,
                prompt="Answer directly.",
                allowed_tools=("calculator",),
                ground_truth={"value": 1},
            )

    def test_duplicate_allowed_tools_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicates"):
            Task(
                task_id="bad-task",
                family_id="bad-family",
                kind=TaskKind.CALCULATOR,
                split=Split.TRAIN,
                prompt="Calculate one plus one.",
                allowed_tools=("calculator", "calculator"),
                ground_truth={"value": 2},
            )


class TrajectoryTests(unittest.TestCase):
    def test_call_and_observation_must_align(self) -> None:
        call = ToolCall(call_id="call-1", name="calculator", arguments={"expression": "1+1"})
        observation = Observation(call_id="call-2", ok=True, content={"value": 2})
        with self.assertRaisesRegex(ValueError, "call_id must match"):
            TrajectoryStep(index=0, tool_call=call, observation=observation)

    def test_failed_observation_requires_error_code(self) -> None:
        with self.assertRaisesRegex(ValueError, "must include an error_code"):
            Observation(call_id="call-1", ok=False, content=None)

    def test_steps_must_be_contiguous(self) -> None:
        call = ToolCall(call_id="call-1", name="calculator", arguments={"expression": "1+1"})
        observation = Observation(call_id="call-1", ok=True, content={"value": 2})
        step = TrajectoryStep(index=1, tool_call=call, observation=observation)
        with self.assertRaisesRegex(ValueError, "contiguous"):
            Trajectory(
                trajectory_id="trajectory-1",
                task_id="task-1",
                steps=(step,),
                final_answer="2",
                model_id="debug-model",
                seed=7,
            )


if __name__ == "__main__":
    unittest.main()

