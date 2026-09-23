import unittest

from verifiable_posttraining.environment import EpisodeEnvironment, EpisodeStateError
from verifiable_posttraining.schemas import Observation, Split, Task, TaskKind, ToolCall
from verifiable_posttraining.tools import execute_calculator


def calculator_task() -> Task:
    return Task(
        task_id="percent-001",
        family_id="percentage-calculator-v1",
        kind=TaskKind.CALCULATOR,
        split=Split.TEST,
        prompt="A group has 40 items and 10 are selected. What percentage is selected?",
        allowed_tools=("calculator",),
        ground_truth={"type": "number", "value": 25.0, "tolerance": 1e-6},
    )


class EpisodeEnvironmentTests(unittest.TestCase):
    def make_environment(self, *, max_tool_calls: int = 2) -> EpisodeEnvironment:
        return EpisodeEnvironment(
            {"calculator": execute_calculator},
            max_tool_calls=max_tool_calls,
        )

    def test_complete_verified_calculator_episode(self) -> None:
        environment = self.make_environment()
        task = calculator_task()
        environment.reset(task)

        observation = environment.step(
            ToolCall(
                call_id="call-1",
                name="calculator",
                arguments={"expression": "10 / 40 * 100"},
            )
        )
        result = environment.finish(
            "25%",
            trajectory_id="trajectory-1",
            model_id="scripted-policy",
            seed=7,
        )

        self.assertTrue(observation.ok)
        self.assertEqual(observation.content, {"value": 25})
        self.assertTrue(result.verification.passed)
        self.assertEqual(result.trajectory.task_id, task.task_id)
        self.assertEqual(len(result.trajectory.steps), 1)
        self.assertEqual(result.trajectory.steps[0].index, 0)

    def test_no_tool_task_can_finish_directly(self) -> None:
        environment = self.make_environment()
        task = Task(
            task_id="direct-001",
            family_id="direct-arithmetic-v1",
            kind=TaskKind.NO_TOOL,
            split=Split.TEST,
            prompt="What is two plus two?",
            allowed_tools=(),
            ground_truth={"type": "number", "value": 4},
        )
        environment.reset(task)
        result = environment.finish(
            "4",
            trajectory_id="trajectory-direct-1",
            model_id="scripted-policy",
            seed=7,
        )
        self.assertTrue(result.verification.passed)
        self.assertEqual(result.trajectory.steps, ())

    def test_disallowed_tool_is_recorded_as_failed_step(self) -> None:
        environment = self.make_environment()
        environment.reset(calculator_task())
        call = ToolCall(call_id="call-1", name="sql", arguments={"query": "SELECT 1"})
        observation = environment.step(call)
        result = environment.finish(
            "25",
            trajectory_id="trajectory-1",
            model_id="scripted-policy",
            seed=7,
        )
        self.assertFalse(observation.ok)
        self.assertEqual(observation.error_code, "tool_not_allowed")
        self.assertEqual(result.trajectory.steps[0].observation, observation)

    def test_duplicate_call_id_is_rejected_without_corrupting_trajectory(self) -> None:
        environment = self.make_environment()
        environment.reset(calculator_task())
        call = ToolCall(
            call_id="call-1",
            name="calculator",
            arguments={"expression": "10 / 40 * 100"},
        )
        environment.step(call)
        duplicate_observation = environment.step(call)
        result = environment.finish(
            "25",
            trajectory_id="trajectory-1",
            model_id="scripted-policy",
            seed=7,
        )
        self.assertEqual(duplicate_observation.error_code, "duplicate_call_id")
        self.assertEqual(len(result.trajectory.steps), 1)
        self.assertEqual(result.trajectory.metadata["rejected_tool_calls"], 1)

    def test_tool_call_budget_is_enforced(self) -> None:
        environment = self.make_environment(max_tool_calls=0)
        environment.reset(calculator_task())
        observation = environment.step(
            ToolCall(
                call_id="call-1",
                name="calculator",
                arguments={"expression": "1 + 1"},
            )
        )
        result = environment.finish(
            "25",
            trajectory_id="trajectory-1",
            model_id="scripted-policy",
            seed=7,
        )
        self.assertEqual(observation.error_code, "tool_call_limit_exceeded")
        self.assertEqual(result.trajectory.steps, ())
        self.assertEqual(result.trajectory.metadata["rejected_tool_calls"], 1)

    def test_executor_observation_mismatch_becomes_failed_observation(self) -> None:
        def broken_executor(call: ToolCall) -> Observation:
            return Observation(call_id="wrong-id", ok=True, content={"value": 25})

        environment = EpisodeEnvironment({"calculator": broken_executor})
        environment.reset(calculator_task())
        observation = environment.step(
            ToolCall(
                call_id="call-1",
                name="calculator",
                arguments={"expression": "10 / 40 * 100"},
            )
        )
        self.assertEqual(observation.error_code, "observation_mismatch")

    def test_lifecycle_order_is_enforced(self) -> None:
        environment = self.make_environment()
        with self.assertRaisesRegex(EpisodeStateError, "reset"):
            environment.finish(
                "25",
                trajectory_id="trajectory-1",
                model_id="scripted-policy",
                seed=7,
            )

        environment.reset(calculator_task())
        with self.assertRaisesRegex(EpisodeStateError, "cannot reset"):
            environment.reset(calculator_task())

        environment.finish(
            "25",
            trajectory_id="trajectory-1",
            model_id="scripted-policy",
            seed=7,
        )
        with self.assertRaisesRegex(EpisodeStateError, "reset"):
            environment.finish(
                "25",
                trajectory_id="trajectory-2",
                model_id="scripted-policy",
                seed=7,
            )


if __name__ == "__main__":
    unittest.main()
