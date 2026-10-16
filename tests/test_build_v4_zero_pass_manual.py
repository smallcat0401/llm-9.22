from __future__ import annotations

import copy
import unittest

from scripts.build_v4_zero_pass_manual import (
    EXCLUDED_TASK_IDS,
    MANUAL_EXPRESSIONS,
    _zero_pass_ids,
    build_manual_record,
)
from verifiable_posttraining.schemas import Split, Task, TaskKind
from verifiable_posttraining.sft_data import build_sft_example


class V4ManualZeroPassTests(unittest.TestCase):
    def setUp(self) -> None:
        self.task = Task(
            task_id="train-example",
            family_id="train-family",
            kind=TaskKind.CALCULATOR,
            split=Split.TRAIN,
            prompt="What is 2 + 3?",
            allowed_tools=("calculator",),
            ground_truth={"type": "number", "value": 5, "tolerance": 0},
            metadata={
                "training_eligible": True,
                "answer_decimal_places": None,
                "ground_truth_display": "5",
            },
        )

    def test_explicit_programs_exclude_exactly_four_questionable_tasks(self) -> None:
        self.assertEqual(len(MANUAL_EXPRESSIONS), 41)
        self.assertEqual(len(EXCLUDED_TASK_IDS), 4)
        self.assertFalse(EXCLUDED_TASK_IDS & set(MANUAL_EXPRESSIONS))

    def test_manual_program_replays_into_valid_sft_messages(self) -> None:
        record = build_manual_record(self.task, "2 + 3")
        self.assertTrue(record["verification"]["passed"])
        self.assertEqual(record["trajectory"]["steps"][0]["observation"]["content"], {"value": 5})
        self.assertFalse(record["provenance"]["search_discovered"])
        example = build_sft_example(record)
        self.assertEqual([message["role"] for message in example["messages"]], [
            "system", "user", "assistant", "tool", "assistant",
        ])

    def test_rejects_wrong_program_and_non_train_task(self) -> None:
        with self.assertRaisesRegex(ValueError, "differs from displayed GT"):
            build_manual_record(self.task, "2 + 4")
        validation = Task.from_dict({**self.task.to_dict(), "split": "validation"})
        with self.assertRaisesRegex(ValueError, "train task"):
            build_manual_record(validation, "2 + 3")

    def test_zero_pass_requires_eight_unique_samples(self) -> None:
        records = [
            {
                "task": self.task.to_dict(),
                "search": {"sample_index": index},
                "rollout": {"task_success": False},
            }
            for index in range(8)
        ]
        self.assertEqual(_zero_pass_ids(records, (self.task,)), {self.task.task_id})
        success = copy.deepcopy(records)
        success[7]["rollout"]["task_success"] = True
        self.assertEqual(_zero_pass_ids(success, (self.task,)), set())
        duplicate = copy.deepcopy(records)
        duplicate[7]["search"]["sample_index"] = 0
        with self.assertRaisesRegex(ValueError, "duplicate or invalid"):
            _zero_pass_ids(duplicate, (self.task,))


if __name__ == "__main__":
    unittest.main()
