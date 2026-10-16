import unittest

from verifiable_posttraining.schemas import Split, TaskKind
from verifiable_posttraining.v3_seed_screen import (
    PUBLIC_EXCLUSIONS,
    build_fresh_gsm8k_tasks,
    build_reviewed_public_tasks,
    build_self_written_tasks,
)


def _public_row(source_id: str, family: str = "family") -> dict:
    return {
        "source_dataset": "TAT-QA",
        "source_split": "train",
        "source_id": source_id,
        "relation_family": family,
        "question": "What is the result?",
        "context": {"table": {"table": [["a", "b"], ["1", "2"]]}},
        "reference_derivation": "1+1",
        "ground_truth": {"type": "number", "value": 2},
    }


class V3SeedScreenTests(unittest.TestCase):
    def test_reviewed_public_split_and_exclusions(self) -> None:
        cagr_ids = (
            "28b7f2b6-f15a-4390-b42c-310d7e727e14",
            "8ade1eac-5a92-41bd-8b03-a74ae2769a6f",
            "072b176c-a53e-4e12-97e6-b129ceb92da9",
            "8fb16496-4bed-4e19-b230-a83de9ee6a59",
        )
        ordinary = [f"ordinary-{index}" for index in range(23)]
        rows = [_public_row(source_id) for source_id in (*cagr_ids, *ordinary)]
        rows.extend(_public_row(source_id) for source_id in PUBLIC_EXCLUSIONS)

        tasks = build_reviewed_public_tasks(rows)

        self.assertEqual(len(tasks), 31)
        self.assertEqual(sum(task.kind is TaskKind.NO_TOOL for task in tasks), 4)
        self.assertEqual(sum(task.kind is TaskKind.CALCULATOR for task in tasks), 27)
        self.assertTrue(all(task.split is Split.TRAIN for task in tasks))
        self.assertTrue(
            all(task.metadata["source_id"] not in PUBLIC_EXCLUSIONS for task in tasks)
        )
        self.assertTrue(
            all(
                not task.metadata["training_eligible"]
                for task in tasks
                if task.kind is TaskKind.NO_TOOL
            )
        )

    def test_self_written_historical_holdouts_stay_diagnostic_only(self) -> None:
        tasks = build_self_written_tasks()

        self.assertEqual(len(tasks), 20)
        self.assertEqual(sum(task.metadata["training_eligible"] for task in tasks), 12)
        self.assertEqual(
            sum(not task.metadata["training_eligible"] for task in tasks), 8
        )
        self.assertTrue(all(task.split is Split.TRAIN for task in tasks))

    def test_fresh_gsm8k_subset_excludes_prior_indices(self) -> None:
        records = tuple(
            {
                "source_index": index,
                "question": f"Question {index}",
                "answer": f"work #### {index}",
            }
            for index in range(30)
        )

        tasks = build_fresh_gsm8k_tasks(
            records,
            excluded_source_indices={0, 1, 2},
            sample_size=20,
            seed=211,
        )

        self.assertEqual(len(tasks), 20)
        self.assertTrue(all(task.kind is TaskKind.CALCULATOR for task in tasks))
        self.assertFalse(
            {0, 1, 2}
            & {int(task.metadata["source_index"]) for task in tasks}
        )


if __name__ == "__main__":
    unittest.main()
