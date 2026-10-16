from __future__ import annotations

import unittest
from pathlib import Path

from verifiable_posttraining.schemas import Split
from verifiable_posttraining.v3_evaluation import build_v3_evaluation_tasks


ROOT = Path(__file__).resolve().parents[1]


class V3EvaluationTests(unittest.TestCase):
    def _build(self, **kwargs):
        return build_v3_evaluation_tasks(
            gsm8k_train_path=ROOT / "data/external/gsm8k/train.jsonl",
            gsm8k_test_path=ROOT / "data/external/gsm8k/test.jsonl",
            **kwargs,
        )

    def test_frozen_shape_and_split_families(self) -> None:
        tasks = self._build(examples_per_synthetic_family=8)
        self.assertEqual(len(tasks), 72)
        self.assertEqual(sum(task.split is Split.VALIDATION for task in tasks), 36)
        self.assertEqual(sum(task.split is Split.TEST for task in tasks), 36)
        validation = {task.family_id for task in tasks if task.split is Split.VALIDATION}
        test = {task.family_id for task in tasks if task.split is Split.TEST}
        self.assertFalse(validation & test)
        self.assertTrue(all(task.metadata.get("evaluation_only") for task in tasks))

    def test_rejects_training_family_overlap(self) -> None:
        with self.assertRaisesRegex(ValueError, "family overlap"):
            self._build(training_family_ids={"v3-eval-test-route-cost-v1"})

    def test_first_two_rows_per_template_match_reviewed_seeds(self) -> None:
        tasks = self._build(examples_per_synthetic_family=2)
        synthetic = [task for task in tasks if task.metadata.get("synthetic")]
        self.assertEqual(len(synthetic), 16)
        self.assertEqual(
            synthetic[0].ground_truth["value"], 645
        )
        self.assertEqual(
            synthetic[1].ground_truth["value"], 730
        )


if __name__ == "__main__":
    unittest.main()
