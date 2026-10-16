from __future__ import annotations

import unittest
from collections import Counter
from fractions import Fraction
from pathlib import Path

from verifiable_posttraining.dataset import load_tasks_jsonl, validate_task_dataset
from verifiable_posttraining.schemas import Split
from verifiable_posttraining.tools.calculator import calculator
from verifiable_posttraining.v4_validation_extension import (
    V4_VALIDATION_PUBLIC_FAMILIES,
    _validate_quantity_constraints,
    build_v4_validation_extension,
)
from verifiable_posttraining.verifier import verify_numeric_answer


ROOT = Path(__file__).resolve().parents[1]


class V4ValidationExtensionTests(unittest.TestCase):
    def test_pending_shape_and_flags(self) -> None:
        tasks = build_v4_validation_extension()
        self.assertEqual(len(tasks), 28)
        self.assertEqual(
            Counter(task.family_id for task in tasks),
            Counter({family: 7 for family in V4_VALIDATION_PUBLIC_FAMILIES}),
        )
        self.assertTrue(all(task.split is Split.VALIDATION for task in tasks))
        self.assertTrue(all(task.metadata["evaluation_only"] for task in tasks))
        self.assertTrue(all(task.metadata["review_status"] == "pending" for task in tasks))
        self.assertFalse(any(task.metadata["training_eligible"] for task in tasks))

    def test_balances_frozen_validation_to_eight_rows_per_family(self) -> None:
        frozen = load_tasks_jsonl(ROOT / "data/generated/v3_validation_v1.jsonl")
        extension = build_v4_validation_extension()
        combined = (*frozen, *extension)
        validate_task_dataset(combined)

        counts = Counter(task.family_id for task in combined)
        self.assertEqual(len(combined), 64)
        self.assertEqual(len(counts), 8)
        self.assertEqual(set(counts.values()), {8})

    def test_families_do_not_overlap_train_or_test(self) -> None:
        extension_families = set(V4_VALIDATION_PUBLIC_FAMILIES)
        train = load_tasks_jsonl(
            ROOT / "data/generated/v4_train_task_candidates_approved_v1.jsonl"
        )
        test = load_tasks_jsonl(ROOT / "data/generated/v3_test_v1.jsonl")
        self.assertFalse(extension_families & {task.family_id for task in train})
        self.assertFalse(extension_families & {task.family_id for task in test})

    def test_reference_program_and_independent_oracle_agree(self) -> None:
        for task in build_v4_validation_extension():
            replayed = calculator(task.metadata["reference_expression"])
            self.assertTrue(verify_numeric_answer(replayed, task.ground_truth).passed)
            params = task.metadata["parameters"]
            if task.family_id.endswith("ratio-allocation-v1"):
                total = Fraction(params["total"])
                a = total * Fraction(*params["a_fraction"])
                c = a * Fraction(*params["c_of_a_fraction"])
                d_ratio, e_ratio = params["d_to_e_ratio"]
                expected = float((total - a - c) * Fraction(d_ratio, d_ratio + e_ratio))
            elif task.family_id.endswith("weighted-demand-v1"):
                portions = sum(
                    Fraction(count) * Fraction(*fraction)
                    for count, fraction in zip(
                        params["counts"], params["portion_fractions"], strict=True
                    )
                )
                expected = float(
                    (portions + params["reserve"]) * params["units_per_portion"]
                )
            elif task.family_id.endswith("population-flow-v1"):
                expected = (
                    params["initial"] * (1 + params["natural_rate"] / 100)
                    - params["annual_out"] * params["years"]
                    + params["annual_in"] * params["years"]
                )
            else:
                lost = sum(
                    rate * hours
                    for rate, hours in zip(
                        params["leak_rates"], params["leak_hours"], strict=True
                    )
                )
                expected = lost - params["refill_rate"] * params["refill_hours"]
            self.assertTrue(
                verify_numeric_answer(expected, task.ground_truth).passed,
                task.task_id,
            )

    def test_generation_is_deterministic_unique_and_not_seed_repetition(self) -> None:
        first = build_v4_validation_extension()
        second = build_v4_validation_extension()
        frozen = load_tasks_jsonl(ROOT / "data/generated/v3_validation_v1.jsonl")
        self.assertEqual(first, second)
        self.assertEqual(len({task.prompt for task in first}), 28)
        self.assertFalse(
            {task.prompt for task in first} & {task.prompt for task in frozen}
        )
        self.assertFalse(
            {task.task_id for task in first} & {task.task_id for task in frozen}
        )

    def test_invalid_variant_count_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly 7"):
            build_v4_validation_extension(variants_per_family=6)

    def test_rejects_impossible_quantity_scenarios(self) -> None:
        tasks = build_v4_validation_extension()
        by_family = {task.family_id: task for task in tasks}

        ratio_id = "v3-eval-val-public-ratio-allocation-v1"
        ratio_params = dict(by_family[ratio_id].metadata["parameters"])
        ratio_params["total"] = 97
        with self.assertRaisesRegex(ValueError, "whole count"):
            _validate_quantity_constraints(ratio_id, ratio_params)

        weighted_id = "v3-eval-val-public-weighted-demand-v1"
        weighted_params = dict(by_family[weighted_id].metadata["parameters"])
        weighted_params["counts"] = (85, *weighted_params["counts"][1:])
        with self.assertRaisesRegex(ValueError, "whole, positive portions"):
            _validate_quantity_constraints(weighted_id, weighted_params)

        tank_id = "v3-eval-val-public-tank-loss-recovery-v1"
        tank_params = dict(by_family[tank_id].metadata["parameters"])
        tank_params["refill_rate"] = 1_000_000
        with self.assertRaisesRegex(ValueError, "neither empty nor overfill"):
            _validate_quantity_constraints(tank_id, tank_params)


if __name__ == "__main__":
    unittest.main()
