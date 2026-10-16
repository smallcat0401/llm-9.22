import copy
import unittest

from verifiable_posttraining.v3_sft_package import (
    APPROVED_FOLLOWUP_TASK_IDS,
    APPROVED_REVISION_TASK_IDS,
    V3SFTPackageError,
    _verify_calculator_replay,
    select_reviewed_search_records,
)


def _selection_record(task_id: str) -> dict:
    return {
        "task": {
            "task_id": task_id,
            "metadata": {"training_eligible": True},
        }
    }


def _tool_record(observed_value=2) -> dict:
    return {
        "trajectory": {
            "steps": [
                {
                    "index": 0,
                    "tool_call": {
                        "call_id": "call-1",
                        "name": "calculator",
                        "arguments": {"expression": "1 + 1"},
                    },
                    "observation": {
                        "call_id": "call-1",
                        "ok": True,
                        "content": {"value": observed_value},
                        "error_code": None,
                    },
                }
            ]
        }
    }


class V3SFTPackageTests(unittest.TestCase):
    def test_selection_boundary_is_exactly_32_unique_tasks(self) -> None:
        seed = tuple(_selection_record(f"seed-{index}") for index in range(28))
        revisions = tuple(_selection_record(task_id) for task_id in APPROVED_REVISION_TASK_IDS)
        followup = tuple(_selection_record(task_id) for task_id in APPROVED_FOLLOWUP_TASK_IDS)

        selected = select_reviewed_search_records(seed, revisions, followup)

        self.assertEqual(len(selected), 32)
        self.assertEqual(len({row["task"]["task_id"] for row, _ in selected}), 32)

    def test_missing_approved_revision_is_rejected(self) -> None:
        seed = tuple(_selection_record(f"seed-{index}") for index in range(28))
        revisions = tuple(
            _selection_record(task_id)
            for task_id in tuple(APPROVED_REVISION_TASK_IDS)[:-1]
        )
        followup = tuple(_selection_record(task_id) for task_id in APPROVED_FOLLOWUP_TASK_IDS)

        with self.assertRaisesRegex(V3SFTPackageError, "missing approved revision"):
            select_reviewed_search_records(seed, revisions, followup)

    def test_calculator_observation_is_replayed(self) -> None:
        self.assertEqual(_verify_calculator_replay(_tool_record()), "tool-assisted")

        tampered = copy.deepcopy(_tool_record())
        tampered["trajectory"]["steps"][0]["observation"]["content"]["value"] = 3
        with self.assertRaisesRegex(V3SFTPackageError, "does not match"):
            _verify_calculator_replay(tampered)

    def test_direct_answer_path_is_visible(self) -> None:
        self.assertEqual(
            _verify_calculator_replay({"trajectory": {"steps": []}}),
            "direct-answer-on-calculator-available-task",
        )


if __name__ == "__main__":
    unittest.main()
