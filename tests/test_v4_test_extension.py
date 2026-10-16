from __future__ import annotations

import unittest
from collections import Counter
from dataclasses import replace
from pathlib import Path

from verifiable_posttraining.dataset import load_tasks_jsonl, validate_task_dataset
from verifiable_posttraining.schemas import Split
from verifiable_posttraining.tools.calculator import calculator
from verifiable_posttraining.v4_test_extension import build_v4_test_extension_records
from verifiable_posttraining.verifier import verify_numeric_answer


ROOT = Path(__file__).resolve().parents[1]


class V4TestExtensionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.originals = load_tasks_jsonl(ROOT / "data/generated/v3_test_v1.jsonl")
        cls.records = build_v4_test_extension_records(cls.originals)

    def test_one_pending_extension_per_frozen_parent(self) -> None:
        original_ids = {task.task_id for task in self.originals}
        new = [record.task for record in self.records]
        self.assertEqual(len(new), 36)
        self.assertEqual({task.metadata["parent_test_task_id"] for task in new}, original_ids)
        self.assertEqual(len({task.prompt for task in new}), 36)
        self.assertFalse({task.prompt for task in new} & {task.prompt for task in self.originals})
        self.assertTrue(all(task.split is Split.TEST for task in new))
        self.assertTrue(all(task.metadata["review_status"] == "pending" for task in new))
        self.assertTrue(all(task.metadata["evaluation_only"] for task in new))
        self.assertFalse(any(task.metadata["training_eligible"] for task in new))

    def test_combined_counts_and_provenance(self) -> None:
        new = [record.task for record in self.records]
        self.assertEqual(len((*self.originals, *new)), 72)
        counts = Counter(task.family_id for task in (*self.originals, *new))
        self.assertEqual(len(counts), 8)
        self.assertEqual(sorted(counts.values()), [2, 2, 2, 2, 16, 16, 16, 16])
        groups = Counter(task.metadata["source_group"] for task in new)
        self.assertEqual(groups, {"self_written_extension": 32, "public_seed_derived_synthetic": 4})
        self.assertTrue(all(task.metadata["synthetic"] for task in new))
        self.assertTrue(all("source_dataset" not in task.metadata for task in new))

    def test_reference_replay_and_independent_oracle(self) -> None:
        for record in self.records:
            task = record.task
            replayed = calculator(task.metadata["reference_expression"])
            self.assertTrue(verify_numeric_answer(replayed, task.ground_truth).passed, task.task_id)
            self.assertNotRegex(task.metadata["reference_expression"], r"\d+\.\d{7,}")
            self.assertNotIn(task.metadata["reference_expression"], task.prompt)
            self.assertNotIn(record.question_zh, task.prompt)

    def test_family_split_leakage_and_determinism(self) -> None:
        new = tuple(record.task for record in self.records)
        train = load_tasks_jsonl(ROOT / "data/generated/v4_train_tasks_curated_v2.jsonl")
        validation = load_tasks_jsonl(ROOT / "data/generated/v4_validation_v1.jsonl")
        validate_task_dataset((*train, *validation, *self.originals, *new))
        self.assertEqual(self.records, build_v4_test_extension_records(self.originals))

    def test_rejects_modified_parent_batch(self) -> None:
        with self.assertRaisesRegex(ValueError, "36 distinct"):
            build_v4_test_extension_records(self.originals[:-1])
        modified = (*self.originals[:-1], replace(self.originals[-1], split=Split.VALIDATION))
        with self.assertRaisesRegex(ValueError, "invalid frozen test parent"):
            build_v4_test_extension_records(modified)


if __name__ == "__main__":
    unittest.main()
