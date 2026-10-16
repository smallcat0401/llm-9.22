from __future__ import annotations

import copy
import unittest

from scripts.package_v4_search_sft_candidates import (
    _verify_selected_path,
    _verify_unique_training_problems,
)
from verifiable_posttraining.schemas import Split, Task, TaskKind


class V4SearchPackageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.task = Task(
            task_id="train-calculator-example",
            family_id="train-example-family",
            kind=TaskKind.CALCULATOR,
            split=Split.TRAIN,
            prompt="What is 2 + 3?",
            allowed_tools=("calculator",),
            ground_truth={"type": "number", "value": 5, "tolerance": 1e-6},
            metadata={"training_eligible": True},
        )
        self.record = {
            "task": self.task.to_dict(),
            "rollout": {"task_success": True},
            "trajectory": {
                "steps": [{
                    "tool_call": {
                        "call_id": "call-1", "name": "calculator",
                        "arguments": {"expression": "2+3"},
                    },
                    "observation": {
                        "call_id": "call-1", "ok": True, "content": {"value": 5},
                    },
                }],
                "final_answer": "5",
            },
        }

    def test_accepts_replayed_tool_path(self) -> None:
        _verify_selected_path(self.record, self.task)

    def test_rejects_forged_observation(self) -> None:
        forged = copy.deepcopy(self.record)
        forged["trajectory"]["steps"][0]["observation"]["content"]["value"] = 6
        with self.assertRaisesRegex(ValueError, "replay disagrees"):
            _verify_selected_path(forged, self.task)

    def test_rejects_incorrect_final_answer(self) -> None:
        wrong = copy.deepcopy(self.record)
        wrong["trajectory"]["final_answer"] = "6"
        with self.assertRaisesRegex(ValueError, "final answer fails"):
            _verify_selected_path(wrong, self.task)

    def test_rejects_direct_answer_as_tool_supervision(self) -> None:
        direct = copy.deepcopy(self.record)
        direct["trajectory"]["steps"] = []
        with self.assertRaisesRegex(ValueError, "must execute the tool"):
            _verify_selected_path(direct, self.task)

    def test_rejects_duplicate_training_problem_across_sources(self) -> None:
        first = {
            "metadata": {"task_id": "old-task"},
            "messages": [{"role": "user", "content": "What is 2 + 3?"}],
        }
        second = {
            "metadata": {"task_id": "new-task"},
            "messages": [{"role": "user", "content": "What is 2 + 3?"}],
        }
        with self.assertRaisesRegex(ValueError, "repeat user prompt"):
            _verify_unique_training_problems((first, second))


if __name__ == "__main__":
    unittest.main()
