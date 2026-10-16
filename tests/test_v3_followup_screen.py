from pathlib import Path
import unittest

from verifiable_posttraining.dataset import load_tasks_jsonl
from verifiable_posttraining.v3_followup_screen import (
    REVISED_TASK_ID,
    SOURCE_TASK_ID,
    build_rounding_followup_task,
)


ROOT = Path(__file__).resolve().parents[1]


class V3FollowupScreenTests(unittest.TestCase):
    def test_rounding_revision_is_explicit_and_preserves_source(self) -> None:
        tasks = load_tasks_jsonl(ROOT / "data/generated/v3_seed_screen_v1.jsonl")
        source = next(task for task in tasks if task.task_id == SOURCE_TASK_ID)
        revised = build_rounding_followup_task(tasks)

        self.assertEqual(revised.task_id, REVISED_TASK_ID)
        self.assertIn("Round the percentage to one decimal place.", revised.prompt)
        self.assertEqual(revised.ground_truth, source.ground_truth)
        self.assertEqual(revised.family_id, source.family_id)
        self.assertEqual(revised.metadata["revision_of_task_id"], source.task_id)
        self.assertNotEqual(revised.task_id, source.task_id)

    def test_missing_source_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly one source task"):
            build_rounding_followup_task(())


if __name__ == "__main__":
    unittest.main()
