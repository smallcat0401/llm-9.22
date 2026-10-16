import json
from pathlib import Path
import unittest

from verifiable_posttraining.dataset import load_tasks_jsonl
from verifiable_posttraining.schemas import Split, Task, TaskKind
from verifiable_posttraining.v3_reference_program import (
    REFERENCE_PROGRAMS,
    ReferenceProgram,
    V3ReferenceProgramError,
    build_reference_program_custom_example,
    build_reference_program_example,
    build_v3_reference_program_sft,
)


ROOT = Path(__file__).resolve().parents[1]


def _task(*, split: Split = Split.TRAIN, value: float = 2.33) -> Task:
    return Task(
        task_id="reference-test",
        family_id="reference-family",
        kind=TaskKind.CALCULATOR,
        split=split,
        prompt="Use the calculator. Return the result rounded to two decimals.",
        allowed_tools=("calculator",),
        ground_truth={"type": "number", "value": value, "tolerance": 0.005},
        metadata={"training_eligible": True},
    )


class V3ReferenceProgramTests(unittest.TestCase):
    def test_builds_exact_reviewed_dataset(self) -> None:
        tasks = (
            *load_tasks_jsonl(ROOT / "data/generated/v3_seed_screen_v1.jsonl"),
            *load_tasks_jsonl(ROOT / "data/generated/v3_zero_pass_revisions_v2.jsonl"),
        )
        rows = build_v3_reference_program_sft(tasks)

        self.assertEqual(len(rows), 26)
        self.assertEqual(len(REFERENCE_PROGRAMS), 26)
        self.assertTrue(all(row["metadata"]["split"] == "train" for row in rows))
        self.assertTrue(
            all(row["metadata"]["trajectory_source"] == "reference-program" for row in rows)
        )
        self.assertTrue(all(row["metadata"]["search_discovered"] is False for row in rows))
        self.assertTrue(all(len(row["messages"]) == 5 for row in rows))
        self.assertFalse(
            any(
                row["metadata"]["task_id"] == "v3-public-ab005e597c33-arithmetic"
                for row in rows
            )
        )

    def test_rounding_is_derived_from_replayed_tool_result(self) -> None:
        row = build_reference_program_example(
            _task(), ReferenceProgram("7 / 3", answer_decimals=2)
        )

        self.assertEqual(row["messages"][3]["content"], str(7 / 3))
        self.assertEqual(
            json.loads(row["messages"][4]["content"]),
            {"type": "final", "answer": "2.33"},
        )

    def test_custom_reference_uses_same_json_action_protocol_as_search(self) -> None:
        row = build_reference_program_custom_example(
            _task(), ReferenceProgram("7 / 3", answer_decimals=2)
        )

        self.assertNotIn("tools", row)
        self.assertEqual([message["role"] for message in row["messages"]], [
            "system", "user", "assistant", "tool", "assistant"
        ])
        self.assertEqual(
            json.loads(row["messages"][2]["content"]),
            {
                "type": "tool_call",
                "name": "calculator",
                "arguments": {"expression": "7 / 3"},
            },
        )
        self.assertEqual(
            json.loads(row["messages"][4]["content"]),
            {"type": "final", "answer": "2.33"},
        )
        self.assertEqual(row["metadata"]["trajectory_source"], "reference-program")

    def test_wrong_reference_program_is_rejected(self) -> None:
        with self.assertRaisesRegex(V3ReferenceProgramError, "does not solve"):
            build_reference_program_example(_task(), ReferenceProgram("1 + 1"))

    def test_non_train_task_is_rejected(self) -> None:
        with self.assertRaisesRegex(V3ReferenceProgramError, "train split"):
            build_reference_program_example(
                _task(split=Split.TEST), ReferenceProgram("7 / 3", answer_decimals=2)
            )


if __name__ == "__main__":
    unittest.main()
