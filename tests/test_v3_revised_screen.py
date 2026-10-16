import unittest

from verifiable_posttraining.schemas import Split, Task, TaskKind
from verifiable_posttraining.v3_revised_screen import (
    REVISIONS,
    REVISION_SET,
    build_revised_zero_pass_tasks,
)


def _task(task_id: str) -> Task:
    value = -1053.4 if task_id == "v3-public-9f547636b5b4-arithmetic" else 3
    return Task(
        task_id=task_id,
        family_id="shared-source-family",
        kind=TaskKind.CALCULATOR,
        split=Split.TRAIN,
        prompt="Instruction.\n\nOld question.\n\nSource table:\n| a | b |\n|---|---|",
        allowed_tools=("calculator",),
        ground_truth={"type": "number", "value": value, "tolerance": 0.005},
        metadata={"training_eligible": True},
    )


class V3RevisedScreenTests(unittest.TestCase):
    def test_builds_exact_reviewed_revision_set_without_mutating_sources(self) -> None:
        sources = tuple(_task(task_id) for task_id in REVISIONS)

        revised = build_revised_zero_pass_tasks(sources)

        self.assertEqual(len(revised), 11)
        self.assertEqual(len({task.task_id for task in revised}), 11)
        self.assertTrue(all(task.task_id.endswith("-revised-v2") for task in revised))
        self.assertTrue(all(task.family_id == "shared-source-family" for task in revised))
        self.assertTrue(
            all(task.metadata["revision_set"] == REVISION_SET for task in revised)
        )
        self.assertTrue(all(task.metadata["requires_fresh_search"] for task in revised))
        self.assertTrue(all("Source table:" in task.prompt for task in revised))
        self.assertTrue(all(task.prompt != "Old question." for task in revised))
        self.assertTrue(all(task.prompt == "Instruction.\n\nOld question.\n\nSource table:\n| a | b |\n|---|---|" for task in sources))

    def test_owner_decisions_are_encoded_without_worked_steps_in_prompts(self) -> None:
        revised = {
            task.metadata["revision_of_task_id"]: task
            for task in build_revised_zero_pass_tasks(
                _task(task_id) for task_id in REVISIONS
            )
        }

        rent = revised["v3-public-9f547636b5b4-arithmetic"]
        self.assertEqual(rent.ground_truth["value"], 1053.4)
        cash_flow = revised["v3-public-f5fdb156cd45-arithmetic"]
        self.assertIn("by how much", cash_flow.prompt)
        self.assertNotIn("subtract", cash_flow.prompt.lower())
        exam = revised["v3-gsm8k-train-1213-calculator"]
        self.assertIn("how many fewer", exam.prompt.lower())
        self.assertEqual(exam.ground_truth["value"], 3)

    def test_missing_source_task_is_rejected(self) -> None:
        sources = tuple(_task(task_id) for task_id in list(REVISIONS)[:-1])
        with self.assertRaisesRegex(ValueError, "missing audited source tasks"):
            build_revised_zero_pass_tasks(sources)


if __name__ == "__main__":
    unittest.main()
