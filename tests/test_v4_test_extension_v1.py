from __future__ import annotations

import re
import unittest
from collections import Counter
from dataclasses import replace
from pathlib import Path

from scripts.build_v4_test_extension_audit_v1 import _audit_markdown
from verifiable_posttraining.dataset import load_tasks_jsonl, validate_task_dataset
from verifiable_posttraining.schemas import Split
from verifiable_posttraining.tools.calculator import calculator
from verifiable_posttraining.v4_test_extension_v1 import build_v4_test_extension_v1_records
from verifiable_posttraining.verifier import verify_numeric_answer


ROOT = Path(__file__).resolve().parents[1]


class V4TestExtensionV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.originals = load_tasks_jsonl(ROOT / "data/generated/v3_test_v1.jsonl")
        cls.records = build_v4_test_extension_v1_records(cls.originals)

    def test_exactly_one_pending_variant_for_each_parent(self) -> None:
        new = [row.task for row in self.records]
        self.assertEqual(len(new), 36)
        self.assertEqual(
            {task.metadata["parent_test_task_id"] for task in new},
            {task.task_id for task in self.originals},
        )
        self.assertEqual(len({task.task_id for task in new}), 36)
        self.assertEqual(len({task.prompt for task in new}), 36)
        self.assertFalse({task.prompt for task in new} & {task.prompt for task in self.originals})
        self.assertTrue(all(task.split is Split.TEST for task in new))
        self.assertTrue(all(task.metadata["review_status"] == "pending" for task in new))
        self.assertTrue(all(task.metadata["evaluation_only"] for task in new))
        self.assertFalse(any(task.metadata["training_eligible"] for task in new))

    def test_family_and_source_counts(self) -> None:
        new = [row.task for row in self.records]
        counts = Counter(task.family_id for task in (*self.originals, *new))
        self.assertEqual(len((*self.originals, *new)), 72)
        self.assertEqual(sorted(counts.values()), [2, 2, 2, 2, 16, 16, 16, 16])
        groups = Counter(task.metadata["source_group"] for task in new)
        self.assertEqual(groups, {"self_written_extension": 32, "public_seed_derived_synthetic": 4})
        for task in new:
            self.assertTrue(task.metadata["synthetic"])
            self.assertNotIn("source_dataset", task.metadata)
            self.assertNotIn("gsm8k", task.task_id)

    def test_calculator_and_independent_oracle_agree(self) -> None:
        for row in self.records:
            task = row.task
            replayed = calculator(task.metadata["reference_expression"])
            self.assertTrue(verify_numeric_answer(replayed, task.ground_truth).passed, task.task_id)
            self.assertNotIn(task.metadata["reference_expression"], task.prompt)
            self.assertNotIn(row.question_zh, task.prompt)
            params = task.metadata["parameters"]
            if task.family_id.endswith("subscription-overage-v1"):
                self.assertGreater(params["used"], params["included"])
            elif task.family_id.endswith("route-cost-v1"):
                self.assertEqual(params["highway"] % params["highway_mpg"], 0)
                self.assertEqual(params["city"] % params["city_mpg"], 0)
                self.assertLess(params["voucher"], params["toll"] + replayed)
            elif task.family_id.endswith("partial-refund-v1"):
                self.assertGreaterEqual(params["quantity_b"], 2)
                self.assertTrue(0 < params["refund_percent"] < 100)
            elif task.family_id.endswith("bonus-deduction-v1"):
                self.assertGreater(params["overtime_hours"], 0)
                self.assertGreater(float(params["overtime_multiplier"]), 1)

    def test_wording_and_range_are_not_v0_linear_continuation(self) -> None:
        old = {family: [task.ground_truth["value"] for task in self.originals
                        if task.family_id == family]
               for family in {task.family_id for task in self.originals}}
        new_synthetic = [row.task for row in self.records
                         if row.task.metadata["source_group"] == "self_written_extension"]
        above_old_max = sum(task.ground_truth["value"] > max(old[task.family_id])
                            for task in new_synthetic)
        self.assertLess(above_old_max, 10)
        for family in {task.family_id for task in new_synthetic}:
            family_tasks = [task for task in new_synthetic if task.family_id == family]
            normalized = {re.sub(r"\d+(?:\.\d+)?", "<n>", task.prompt)
                          for task in family_tasks}
            self.assertEqual(len(normalized), 4)
            self.assertEqual(Counter(task.metadata["wording_variant"] for task in family_tasks),
                             {1: 2, 2: 2, 3: 2, 4: 2})

    def test_chinese_audit_displays_two_decimal_places(self) -> None:
        audit = _audit_markdown(self.records, self.originals)
        for row in self.records:
            task = row.task
            if "to two decimals" in task.prompt:
                self.assertIn(f"- GT：`{task.ground_truth['value']:.2f}`", audit)
        self.assertIn("GT：`90.50`", audit)
        self.assertIn("GT：`209.20`", audit)

    def test_dataset_split_and_determinism(self) -> None:
        train = load_tasks_jsonl(ROOT / "data/generated/v4_train_tasks_curated_v2.jsonl")
        validation = load_tasks_jsonl(ROOT / "data/generated/v4_validation_v1.jsonl")
        new = tuple(row.task for row in self.records)
        validate_task_dataset((*train, *validation, *self.originals, *new))
        self.assertEqual(self.records, build_v4_test_extension_v1_records(self.originals))

    def test_bad_parent_batch_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "36 distinct"):
            build_v4_test_extension_v1_records(self.originals[:-1])
        changed = (*self.originals[:-1], replace(self.originals[-1], split=Split.VALIDATION))
        with self.assertRaisesRegex(ValueError, "invalid test parent"):
            build_v4_test_extension_v1_records(changed)


if __name__ == "__main__":
    unittest.main()
