import unittest
from collections.abc import Sequence

from verifiable_posttraining.prompting import ChatMessage
from verifiable_posttraining.schemas import Split, Task, TaskKind
from verifiable_posttraining.search import assess_search_gate, run_best_of_n


class ScriptedPolicy:
    def __init__(self, outputs: list[str]) -> None:
        self._outputs = iter(outputs)
        self.seeds: list[int] = []

    def generate(self, messages: Sequence[ChatMessage], *, seed: int) -> str:
        del messages
        self.seeds.append(seed)
        return next(self._outputs)


def _task(index: int) -> Task:
    return Task(
        task_id=f"task-{index}",
        family_id="direct-v1",
        kind=TaskKind.NO_TOOL,
        split=Split.TRAIN,
        prompt="Return 2.",
        allowed_tools=(),
        ground_truth={"type": "number", "value": 2, "tolerance": 0},
    )


class BestOfNSearchTests(unittest.TestCase):
    def test_search_selects_first_strict_success_and_computes_pass_at_k(self) -> None:
        policy = ScriptedPolicy(
            [
                "2",
                '{"type":"final","answer":2}',
                '{"type":"final","answer":2}',
                '{"type":"final","answer":0}',
                '{"type":"final","answer":1}',
                '{"type":"final","answer":3}',
            ]
        )
        progress = []
        search = run_best_of_n(
            [_task(1), _task(2)],
            policy,
            {},
            samples_per_task=3,
            run_id="search",
            model_id="scripted",
            seed=7,
            on_candidate=lambda completed, total, task_index, sample_index, result, latency: (
                progress.append(
                    (completed, total, task_index, sample_index, result.task_success, latency >= 0)
                )
            ),
        )

        self.assertEqual(policy.seeds, [7, 107, 207, 100007, 100107, 100207])
        self.assertEqual(search.task_results[0].selected_index, 1)
        self.assertIsNone(search.task_results[1].selected_index)
        self.assertEqual(len(search.selected_rollouts), 1)
        self.assertEqual(search.metrics.candidate_count, 6)
        self.assertEqual(search.metrics.verified_candidate_count, 2)
        self.assertEqual(search.metrics.pass_at_1, 0.0)
        self.assertEqual(search.metrics.pass_at_k, 0.5)
        self.assertEqual(search.metrics.absolute_search_gain, 0.5)
        self.assertEqual(search.metrics.pass_at_prefix["1"]["count"], 0)
        self.assertEqual(search.metrics.pass_at_prefix["2"]["count"], 1)
        self.assertEqual(search.metrics.pass_at_prefix["3"]["count"], 1)
        gate = assess_search_gate(
            search.metrics,
            min_absolute_gain=0.25,
            min_verified_tasks=1,
        )
        self.assertTrue(gate["passed"])
        self.assertEqual(len(progress), 6)

    def test_invalid_search_inputs_are_rejected(self) -> None:
        policy = ScriptedPolicy([])
        with self.assertRaisesRegex(ValueError, "at least one task"):
            run_best_of_n(
                [],
                policy,
                {},
                samples_per_task=2,
                run_id="search",
                model_id="scripted",
                seed=7,
            )
        with self.assertRaisesRegex(ValueError, "min_absolute_gain"):
            assess_search_gate(
                run_best_of_n(
                    [_task(1)],
                    ScriptedPolicy(['{"type":"final","answer":2}']),
                    {},
                    samples_per_task=1,
                    run_id="gate",
                    model_id="scripted",
                    seed=7,
                ).metrics,
                min_absolute_gain=1.1,
                min_verified_tasks=1,
            )
        with self.assertRaisesRegex(ValueError, "samples_per_task must be positive"):
            run_best_of_n(
                [_task(1)],
                policy,
                {},
                samples_per_task=0,
                run_id="search",
                model_id="scripted",
                seed=7,
            )


if __name__ == "__main__":
    unittest.main()
