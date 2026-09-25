import unittest
from collections.abc import Sequence

from verifiable_posttraining.metrics import compute_evaluation_metrics
from verifiable_posttraining.prompting import ChatMessage
from verifiable_posttraining.rollout import run_episode
from verifiable_posttraining.schemas import Split, Task, TaskKind
from verifiable_posttraining.tools import execute_calculator


class ScriptedPolicy:
    def __init__(self, outputs: list[str]) -> None:
        self._outputs = iter(outputs)

    def generate(self, messages: Sequence[ChatMessage], *, seed: int) -> str:
        del messages, seed
        return next(self._outputs)


def _task(task_id: str, kind: TaskKind) -> Task:
    return Task(
        task_id=task_id,
        family_id=f"{kind.value}-family",
        kind=kind,
        split=Split.TEST,
        prompt="Return 2.",
        allowed_tools=() if kind is TaskKind.NO_TOOL else ("calculator",),
        ground_truth={"type": "number", "value": 2, "tolerance": 0},
    )


def _run(task: Task, outputs: list[str]):
    return run_episode(
        task,
        ScriptedPolicy(outputs),
        {"calculator": execute_calculator},
        trajectory_id=f"trajectory-{task.task_id}",
        model_id="scripted",
        seed=7,
    )


class EvaluationMetricsTests(unittest.TestCase):
    def test_empty_input_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one rollout"):
            compute_evaluation_metrics([])

    def test_outcome_protocol_and_tool_metrics_are_kept_separate(self) -> None:
        no_tool_success = _run(
            _task("no-tool-success", TaskKind.NO_TOOL),
            ['{"type":"final","answer":2}'],
        )
        calculator_success = _run(
            _task("calculator-success", TaskKind.CALCULATOR),
            [
                '{"type":"tool_call","name":"calculator",'
                '"arguments":{"expression":"1 + 1"}}',
                '{"type":"final","answer":2}',
            ],
        )
        over_tool = _run(
            _task("no-tool-over-tool", TaskKind.NO_TOOL),
            [
                '{"type":"tool_call","name":"calculator",'
                '"arguments":{"expression":"1 + 1"}}',
                '{"type":"final","answer":2}',
            ],
        )
        malformed_but_numeric = _run(
            _task("malformed", TaskKind.CALCULATOR),
            ["2"],
        )

        metrics = compute_evaluation_metrics(
            [no_tool_success, calculator_success, over_tool, malformed_but_numeric]
        )

        self.assertEqual(metrics.task_count, 4)
        self.assertEqual(metrics.task_success_count, 3)
        self.assertEqual(metrics.verifier_pass_count, 4)
        self.assertEqual(metrics.protocol_error_count, 1)
        self.assertEqual(metrics.tool_selection_correct_count, 2)
        self.assertEqual(metrics.recorded_tool_call_count, 2)
        self.assertEqual(metrics.failed_tool_call_count, 1)
        self.assertEqual(metrics.invalid_tool_call_rate, 0.5)
        self.assertEqual(metrics.no_tool_task_count, 2)
        self.assertEqual(metrics.over_tool_task_count, 1)
        self.assertEqual(metrics.over_tool_rate, 0.5)
        self.assertEqual(metrics.success_by_kind["calculator"]["success_rate"], 0.5)


if __name__ == "__main__":
    unittest.main()
