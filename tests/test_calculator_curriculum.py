import unittest

from verifiable_posttraining.calculator_curriculum import (
    build_reference_program_sft,
    generate_calculator_curriculum,
    generate_calculator_curriculum_v2,
    generate_calculator_holdout_v1,
)
from verifiable_posttraining.schemas import Split
from verifiable_posttraining.tools.calculator import calculator
from verifiable_posttraining.verifier import verify_numeric_answer


class CalculatorCurriculumTests(unittest.TestCase):
    def test_family_split_counts_and_isolation(self) -> None:
        tasks = generate_calculator_curriculum(examples_per_family=3)
        self.assertEqual(len(tasks), 30)
        counts = {split: sum(task.split is split for task in tasks) for split in Split}
        self.assertEqual(counts, {Split.TRAIN: 18, Split.VALIDATION: 6, Split.TEST: 6})
        for family in {task.family_id for task in tasks}:
            self.assertEqual(len({task.split for task in tasks if task.family_id == family}), 1)

    def test_every_reference_expression_solves_its_task(self) -> None:
        for task in generate_calculator_curriculum(examples_per_family=3):
            result = calculator(task.metadata["reference_expression"])
            self.assertTrue(verify_numeric_answer(result, task.ground_truth).passed)

    def test_reference_program_sft_uses_train_only(self) -> None:
        examples = build_reference_program_sft(
            generate_calculator_curriculum(examples_per_family=2)
        )
        self.assertEqual(len(examples), 12)
        self.assertTrue(all(row["metadata"]["split"] == "train" for row in examples))
        self.assertTrue(all(row["messages"][2].get("tool_calls") for row in examples))
        self.assertTrue(all(len(row["tools"]) == 1 for row in examples))

    def test_v2_is_family_isolated_and_reference_verified(self) -> None:
        tasks = generate_calculator_curriculum_v2(examples_per_family=2)
        self.assertEqual(len(tasks), 20)
        self.assertEqual(sum(task.split is Split.TRAIN for task in tasks), 12)
        self.assertEqual(sum(task.split is Split.VALIDATION for task in tasks), 4)
        self.assertEqual(sum(task.split is Split.TEST for task in tasks), 4)
        for task in tasks:
            result = calculator(task.metadata["reference_expression"])
            self.assertTrue(verify_numeric_answer(result, task.ground_truth).passed)
        tank_tasks = [task for task in tasks if task.family_id == "curriculum-v2-tank-drain"]
        self.assertTrue(tank_tasks)
        self.assertTrue(all("drained from the tank" in task.prompt for task in tank_tasks))

    def test_final_holdout_is_test_only_and_evaluation_only(self) -> None:
        tasks = generate_calculator_holdout_v1(examples_per_family=2)
        self.assertEqual(len(tasks), 6)
        self.assertTrue(all(task.split is Split.TEST for task in tasks))
        self.assertTrue(all(task.metadata["evaluation_only"] for task in tasks))
        with self.assertRaisesRegex(ValueError, "no train examples"):
            build_reference_program_sft(tasks)


if __name__ == "__main__":
    unittest.main()
