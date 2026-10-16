import unittest
from collections import Counter

from verifiable_posttraining.schemas import Split
from verifiable_posttraining.seed_expansion import (
    AUDITED_SELF_WRITTEN_SEED_FAMILIES,
    build_approved_self_written_seed_expansion,
    build_self_written_seed_expansion,
)
from verifiable_posttraining.tools.calculator import calculator
from verifiable_posttraining.verifier import verify_numeric_answer


class SeedExpansionTests(unittest.TestCase):
    def test_expands_only_audited_train_seed_families(self) -> None:
        tasks = build_self_written_seed_expansion(variants_per_family=3)
        self.assertEqual(len(tasks), 18)
        self.assertEqual(
            Counter(task.family_id for task in tasks),
            Counter({family: 3 for family in AUDITED_SELF_WRITTEN_SEED_FAMILIES}),
        )
        self.assertTrue(all(task.split is Split.TRAIN for task in tasks))

    def test_parent_rows_are_not_duplicated_and_provenance_is_recorded(self) -> None:
        tasks = build_self_written_seed_expansion(variants_per_family=3)
        for task in tasks:
            self.assertGreaterEqual(task.metadata["generator_index"], 2)
            self.assertEqual(task.metadata["review_status"], "pending")
            self.assertFalse(task.metadata["training_eligible"])
            self.assertEqual(task.metadata["parent_family_id"], task.family_id)
            self.assertEqual(len(task.metadata["parent_seed_task_ids"]), 2)

    def test_every_candidate_replays_to_ground_truth(self) -> None:
        for task in build_self_written_seed_expansion(variants_per_family=3):
            result = calculator(task.metadata["reference_expression"])
            self.assertTrue(verify_numeric_answer(result, task.ground_truth).passed)

    def test_required_scores_are_realistic(self) -> None:
        tasks = build_self_written_seed_expansion()
        required_scores = [
            task.metadata["reference_result"]
            for task in tasks
            if task.family_id == "curriculum-v2-required-score"
        ]
        self.assertTrue(required_scores)
        self.assertTrue(all(0 <= score <= 100 for score in required_scores))

    def test_two_decimal_tasks_have_rounded_targets_and_display_values(self) -> None:
        tasks = build_self_written_seed_expansion()
        rounded_tasks = [
            task for task in tasks if task.metadata["answer_decimal_places"] == 2
        ]
        self.assertTrue(rounded_tasks)
        for task in rounded_tasks:
            display = task.metadata["ground_truth_display"]
            self.assertRegex(display, r"^-?\d+\.\d{2}$")
            self.assertEqual(float(display), task.ground_truth["value"])

    def test_generation_is_deterministic_and_has_no_duplicate_prompts(self) -> None:
        first = build_self_written_seed_expansion()
        second = build_self_written_seed_expansion()
        self.assertEqual(first, second)
        self.assertEqual(len({task.prompt for task in first}), len(first))

    def test_invalid_counts_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "variants_per_family"):
            build_self_written_seed_expansion(variants_per_family=0)
        with self.assertRaisesRegex(ValueError, "parent_examples_per_family"):
            build_self_written_seed_expansion(parent_examples_per_family=0)

    def test_owner_approved_copy_is_training_eligible_but_not_an_sft_file(self) -> None:
        tasks = build_approved_self_written_seed_expansion()
        self.assertEqual(len(tasks), 84)
        self.assertTrue(all(task.metadata["review_status"] == "approved" for task in tasks))
        self.assertTrue(all(task.metadata["training_eligible"] for task in tasks))
        self.assertTrue(all(task.metadata["owner_approval_date"] == "2026-10-05" for task in tasks))


if __name__ == "__main__":
    unittest.main()
