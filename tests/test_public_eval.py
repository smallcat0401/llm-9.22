import json
from pathlib import Path
import tempfile
import unittest

from verifiable_posttraining.public_eval import (
    PublicDatasetError,
    build_gsm8k_external_tasks,
    build_gsm8k_search_screen_tasks,
    build_gsm8k_train_validation_tasks,
    extract_gsm8k_final_answer,
    load_gsm8k_jsonl,
    public_dataset_manifest,
)
from verifiable_posttraining.schemas import Split, TaskKind


FIXTURE_RECORDS = (
    {"question": "What is 2 + 3?", "answer": "Add them. #### 5"},
    {"question": "What is 10 / 4?", "answer": "Divide. #### 2.5"},
    {"question": "What is 1,200 - 50?", "answer": "Subtract. #### 1,150"},
)


class GSM8KPublicEvaluationTests(unittest.TestCase):
    def test_final_answer_extraction_uses_only_official_marker(self) -> None:
        self.assertEqual(extract_gsm8k_final_answer("3 then 5 #### 1,250"), 1250)
        self.assertEqual(extract_gsm8k_final_answer("work #### 2.5"), 2.5)
        with self.assertRaisesRegex(PublicDatasetError, "####"):
            extract_gsm8k_final_answer("answer is 5")

    def test_loader_and_subset_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "test.jsonl"
            path.write_text(
                "".join(json.dumps(record) + "\n" for record in FIXTURE_RECORDS),
                encoding="utf-8",
            )
            records = load_gsm8k_jsonl(path)
            first = build_gsm8k_external_tasks(records, sample_size=2, seed=7)
            second = build_gsm8k_external_tasks(records, sample_size=2, seed=7)
            manifest = public_dataset_manifest(
                source_path=path,
                tasks=first,
                sample_size=2,
                seed=7,
            )

        self.assertEqual(first, second)
        self.assertEqual(len(first), 4)
        self.assertEqual(manifest["paired_task_count"], 4)
        self.assertEqual(len(manifest["source_sha256"]), 64)

    def test_each_source_question_gets_two_evaluation_only_conditions(self) -> None:
        records = tuple(
            {"source_index": index, **record}
            for index, record in enumerate(FIXTURE_RECORDS)
        )
        tasks = build_gsm8k_external_tasks(records, sample_size=3, seed=7)

        self.assertEqual({task.split for task in tasks}, {Split.TEST})
        self.assertEqual(
            {task.kind for task in tasks},
            {TaskKind.NO_TOOL, TaskKind.CALCULATOR},
        )
        self.assertTrue(all(task.metadata["external_evaluation_only"] for task in tasks))
        self.assertEqual(len({task.task_id for task in tasks}), 6)

    def test_search_screen_uses_train_only_provenance(self) -> None:
        records = tuple(
            {"source_index": index, **record}
            for index, record in enumerate(FIXTURE_RECORDS)
        )
        tasks = build_gsm8k_search_screen_tasks(records, sample_size=2, seed=71)

        self.assertEqual(len(tasks), 4)
        self.assertEqual({task.split for task in tasks}, {Split.TRAIN})
        self.assertEqual(
            {task.family_id for task in tasks},
            {
                "gsm8k-public-train-no-tool-v1",
                "gsm8k-public-train-calculator-v1",
            },
        )
        self.assertTrue(all(task.metadata["source_split"] == "train" for task in tasks))
        self.assertTrue(all(task.metadata["search_screen"] for task in tasks))
        self.assertTrue(
            all("external_evaluation_only" not in task.metadata for task in tasks)
        )

    def test_search_screen_can_exclude_previous_source_questions(self) -> None:
        records = tuple(
            {"source_index": index, **record}
            for index, record in enumerate(FIXTURE_RECORDS)
        )
        tasks = build_gsm8k_search_screen_tasks(
            records,
            sample_size=2,
            seed=71,
            excluded_source_indices={1},
        )

        selected_indices = {task.metadata["source_index"] for task in tasks}
        self.assertEqual(len(selected_indices), 2)
        self.assertNotIn(1, selected_indices)

    def test_search_screen_rejects_too_many_exclusions(self) -> None:
        records = tuple(
            {"source_index": index, **record}
            for index, record in enumerate(FIXTURE_RECORDS)
        )
        with self.assertRaisesRegex(ValueError, "sample_size exceeds"):
            build_gsm8k_search_screen_tasks(
                records,
                sample_size=2,
                seed=71,
                excluded_source_indices={0, 1},
            )

    def test_train_source_validation_is_held_out_and_paired(self) -> None:
        records = tuple(
            {"source_index": index, **record}
            for index, record in enumerate(FIXTURE_RECORDS)
        )
        tasks = build_gsm8k_train_validation_tasks(
            records,
            sample_size=2,
            seed=131,
            excluded_source_indices={1},
        )

        self.assertEqual(len(tasks), 4)
        self.assertEqual({task.split for task in tasks}, {Split.VALIDATION})
        self.assertTrue(all(task.metadata["validation_only"] for task in tasks))
        self.assertTrue(all(task.metadata["source_split"] == "train" for task in tasks))
        self.assertNotIn(1, {task.metadata["source_index"] for task in tasks})

    def test_loader_rejects_missing_answer_marker_and_duplicate_questions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "bad.jsonl"
            path.write_text(
                '{"question":"q","answer":"5"}\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(PublicDatasetError, "invalid GSM8K answer"):
                load_gsm8k_jsonl(path)

            path.write_text(
                '{"question":"q","answer":"work #### 5"}\n'
                '{"question":"q","answer":"other work #### 6"}\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(PublicDatasetError, "duplicate question"):
                load_gsm8k_jsonl(path)


if __name__ == "__main__":
    unittest.main()
