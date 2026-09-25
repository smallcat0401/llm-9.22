import json
from pathlib import Path
import tempfile
import unittest
from dataclasses import replace

from verifiable_posttraining.dataset import (
    DatasetValidationError,
    dataset_summary,
    generate_pilot_tasks,
    load_tasks_jsonl,
    select_task_window_per_kind,
    validate_task_dataset,
    write_tasks_jsonl,
)
from verifiable_posttraining.schemas import Split, TaskKind, ToolCall
from verifiable_posttraining.synthetic_db import create_pilot_sales_connection
from verifiable_posttraining.tools import ReadOnlySQLiteTool
from verifiable_posttraining.tools.calculator import evaluate_expression
from verifiable_posttraining.verifier import verify_numeric_answer


class PilotDatasetTests(unittest.TestCase):
    def test_per_kind_windows_are_deterministic_and_disjoint(self) -> None:
        tasks = generate_pilot_tasks(seed=7, examples_per_family=3)
        first = select_task_window_per_kind(tasks, limit_per_kind=2)
        second = select_task_window_per_kind(
            tasks, offset_per_kind=2, limit_per_kind=2
        )

        self.assertEqual(len(first), 6)
        self.assertEqual(len(second), 6)
        self.assertTrue({task.task_id for task in first}.isdisjoint(
            task.task_id for task in second
        ))
        self.assertEqual(
            second,
            select_task_window_per_kind(
                tasks, offset_per_kind=2, limit_per_kind=2
            ),
        )

    def test_per_kind_window_rejects_negative_bounds(self) -> None:
        tasks = generate_pilot_tasks(seed=7, examples_per_family=1)
        with self.assertRaisesRegex(ValueError, "offset_per_kind"):
            select_task_window_per_kind(tasks, offset_per_kind=-1)
        with self.assertRaisesRegex(ValueError, "limit_per_kind"):
            select_task_window_per_kind(tasks, limit_per_kind=-1)

    def test_default_dataset_has_300_tasks_and_12_families(self) -> None:
        tasks = generate_pilot_tasks(seed=7)
        summary = dataset_summary(tasks)
        self.assertEqual(summary["tasks"], 300)
        self.assertEqual(summary["families"], 12)
        self.assertEqual(
            summary["by_split"],
            {"train": 150, "validation": 75, "test": 75},
        )
        self.assertEqual(
            summary["by_kind"],
            {"no_tool": 100, "calculator": 100, "sql": 100},
        )

    def test_generation_is_deterministic(self) -> None:
        first = generate_pilot_tasks(seed=19)
        second = generate_pilot_tasks(seed=19)
        first_json = json.dumps([task.to_dict() for task in first], sort_keys=True)
        second_json = json.dumps([task.to_dict() for task in second], sort_keys=True)
        self.assertEqual(first_json, second_json)

    def test_prompts_are_unique_within_each_family(self) -> None:
        tasks = generate_pilot_tasks(seed=7)

        for family_id in {task.family_id for task in tasks}:
            prompts = [task.prompt for task in tasks if task.family_id == family_id]
            self.assertEqual(len(prompts), len(set(prompts)), family_id)

    def test_reference_programs_match_numeric_ground_truth(self) -> None:
        tasks = generate_pilot_tasks(seed=7)
        connection = create_pilot_sales_connection()
        sql_tool = ReadOnlySQLiteTool(connection, allowed_tables={"sales"})
        try:
            for task in tasks:
                if task.kind is TaskKind.CALCULATOR:
                    actual = evaluate_expression(task.metadata["reference_expression"])
                elif task.kind is TaskKind.SQL:
                    observation = sql_tool(
                        ToolCall(
                            call_id=task.task_id,
                            name="sql",
                            arguments={"query": task.metadata["reference_query"]},
                        )
                    )
                    self.assertTrue(observation.ok, task.task_id)
                    actual = observation.content["rows"][0][0]
                else:
                    actual = task.ground_truth["value"]

                result = verify_numeric_answer(actual, task.ground_truth)
                self.assertTrue(result.passed, task.task_id)
        finally:
            connection.close()

    def test_jsonl_round_trip_preserves_tasks(self) -> None:
        tasks = generate_pilot_tasks(seed=7, examples_per_family=2)
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "pilot.jsonl"
            write_tasks_jsonl(tasks, path)
            restored = load_tasks_jsonl(path)

        self.assertEqual(restored, tasks)

    def test_each_kind_has_families_in_every_split(self) -> None:
        tasks = generate_pilot_tasks(seed=7)
        observed = {
            kind: {task.split for task in tasks if task.kind is kind}
            for kind in (TaskKind.NO_TOOL, TaskKind.CALCULATOR, TaskKind.SQL)
        }
        for splits in observed.values():
            self.assertEqual(splits, {Split.TRAIN, Split.VALIDATION, Split.TEST})

    def test_family_leakage_is_rejected(self) -> None:
        tasks = list(generate_pilot_tasks(seed=7, examples_per_family=2))
        family_id = tasks[0].family_id
        matching_index = next(
            index
            for index, task in enumerate(tasks[1:], start=1)
            if task.family_id == family_id
        )
        replacement_split = (
            Split.TEST if tasks[matching_index].split is not Split.TEST else Split.TRAIN
        )
        tasks[matching_index] = replace(tasks[matching_index], split=replacement_split)
        with self.assertRaisesRegex(DatasetValidationError, "multiple splits"):
            validate_task_dataset(tasks)

    def test_duplicate_task_id_is_rejected(self) -> None:
        tasks = list(generate_pilot_tasks(seed=7, examples_per_family=1))
        tasks[1] = replace(tasks[1], task_id=tasks[0].task_id)
        with self.assertRaisesRegex(DatasetValidationError, "duplicate task_id"):
            validate_task_dataset(tasks)


if __name__ == "__main__":
    unittest.main()
