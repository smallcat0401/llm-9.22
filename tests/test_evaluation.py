import unittest
from collections.abc import Sequence

from verifiable_posttraining.evaluation import evaluate_tasks
from verifiable_posttraining.prompting import ChatMessage
from verifiable_posttraining.schemas import Split, Task, TaskKind


class SeedRecordingPolicy:
    def __init__(self) -> None:
        self.seeds: list[int] = []

    def generate(self, messages: Sequence[ChatMessage], *, seed: int) -> str:
        del messages
        self.seeds.append(seed)
        return '{"type":"final","answer":2}'


def _task(index: int) -> Task:
    return Task(
        task_id=f"task-{index}",
        family_id="direct-v1",
        kind=TaskKind.NO_TOOL,
        split=Split.TEST,
        prompt="Return 2.",
        allowed_tools=(),
        ground_truth={"type": "number", "value": 2, "tolerance": 0},
    )


class EvaluationRunnerTests(unittest.TestCase):
    def test_runner_preserves_order_and_uses_stable_task_seeds(self) -> None:
        policy = SeedRecordingPolicy()
        progress = []
        result = evaluate_tasks(
            [_task(1), _task(2)],
            policy,
            {},
            run_id="baseline",
            model_id="scripted",
            seed=7,
            on_result=lambda completed, total, rollout, latency: progress.append(
                (completed, total, rollout.episode.task.task_id, latency >= 0)
            ),
        )

        self.assertEqual(policy.seeds, [7, 107])
        self.assertEqual(
            [rollout.episode.task.task_id for rollout in result.rollouts],
            ["task-1", "task-2"],
        )
        self.assertEqual(result.metrics.task_success_count, 2)
        self.assertEqual(progress, [(1, 2, "task-1", True), (2, 2, "task-2", True)])
        self.assertEqual(len(result.to_dict()["records"]), 2)

    def test_empty_and_duplicate_task_inputs_are_rejected(self) -> None:
        policy = SeedRecordingPolicy()
        with self.assertRaisesRegex(ValueError, "at least one task"):
            evaluate_tasks([], policy, {}, run_id="run", model_id="scripted", seed=7)
        with self.assertRaisesRegex(ValueError, "task ids must be unique"):
            evaluate_tasks(
                [_task(1), _task(1)],
                policy,
                {},
                run_id="run",
                model_id="scripted",
                seed=7,
            )


if __name__ == "__main__":
    unittest.main()
