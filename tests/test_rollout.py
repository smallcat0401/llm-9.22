import unittest
from collections.abc import Sequence

from verifiable_posttraining.prompting import ChatMessage
from verifiable_posttraining.rollout import run_episode
from verifiable_posttraining.schemas import Split, Task, TaskKind
from verifiable_posttraining.tools import execute_calculator


def calculator_task() -> Task:
    return Task(
        task_id="percent-rollout-001",
        family_id="percentage-calculator-v1",
        kind=TaskKind.CALCULATOR,
        split=Split.TEST,
        prompt="A group has 40 items and 10 are selected. What percentage is selected?",
        allowed_tools=("calculator",),
        ground_truth={"type": "number", "value": 25.0, "tolerance": 1e-6},
    )


class ScriptedPolicy:
    def __init__(self, outputs: list[str]) -> None:
        self._outputs = iter(outputs)
        self.seeds: list[int] = []
        self.histories: list[tuple[ChatMessage, ...]] = []

    def generate(self, messages: Sequence[ChatMessage], *, seed: int) -> str:
        self.seeds.append(seed)
        self.histories.append(tuple(messages))
        return next(self._outputs)


class RolloutTests(unittest.TestCase):
    def test_two_turn_tool_episode_succeeds(self) -> None:
        policy = ScriptedPolicy(
            [
                '{"type":"tool_call","name":"calculator",'
                '"arguments":{"expression":"10 / 40 * 100"}}',
                '{"type":"final","answer":"25%"}',
            ]
        )
        result = run_episode(
            calculator_task(),
            policy,
            {"calculator": execute_calculator},
            trajectory_id="trajectory-1",
            model_id="scripted-policy",
            seed=100,
        )
        self.assertTrue(result.task_success)
        self.assertEqual(result.termination_reason, "final_answer")
        self.assertEqual(policy.seeds, [100, 101])
        self.assertEqual(policy.histories[1][-1].role, "tool")
        self.assertEqual(len(result.episode.trajectory.steps), 1)
        self.assertEqual(result.episode.trajectory.steps[0].tool_call.call_id, "call-1")

    def test_protocol_error_terminates_without_false_success(self) -> None:
        policy = ScriptedPolicy(["25"])
        result = run_episode(
            calculator_task(),
            policy,
            {"calculator": execute_calculator},
            trajectory_id="trajectory-1",
            model_id="scripted-policy",
            seed=7,
        )
        self.assertTrue(result.episode.verification.passed)
        self.assertFalse(result.task_success)
        self.assertEqual(result.termination_reason, "protocol_error")
        self.assertEqual(result.protocol_error, "invalid_envelope")

    def test_wrong_final_answer_is_not_success(self) -> None:
        policy = ScriptedPolicy(['{"type":"final","answer":30}'])
        result = run_episode(
            calculator_task(),
            policy,
            {"calculator": execute_calculator},
            trajectory_id="trajectory-1",
            model_id="scripted-policy",
            seed=7,
        )
        self.assertFalse(result.task_success)
        self.assertEqual(result.episode.verification.error_code, "wrong_answer")

    def test_turn_limit_terminates_tool_loop(self) -> None:
        policy = ScriptedPolicy(
            [
                '{"type":"tool_call","call_id":"call-1","name":"calculator",'
                '"arguments":{"expression":"1 + 1"}}'
            ]
        )
        result = run_episode(
            calculator_task(),
            policy,
            {"calculator": execute_calculator},
            trajectory_id="trajectory-1",
            model_id="scripted-policy",
            seed=7,
            max_model_turns=1,
        )
        self.assertFalse(result.task_success)
        self.assertEqual(result.termination_reason, "max_model_turns")
        self.assertEqual(len(result.episode.trajectory.steps), 1)


if __name__ == "__main__":
    unittest.main()
