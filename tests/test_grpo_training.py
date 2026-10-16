import json
import hashlib
from pathlib import Path
import tempfile
import unittest

from verifiable_posttraining.dataset import generate_pilot_tasks, write_tasks_jsonl
from verifiable_posttraining.grpo_training import GRPOSmokeConfig, build_grpo_smoke_rows
from verifiable_posttraining.schemas import Split, TaskKind


def _config(
    root: Path,
    *,
    task_ids: tuple[str, ...],
    allow_sft_task_overlap: bool = False,
    expected_sft_overlap_count: int | None = None,
) -> GRPOSmokeConfig:
    return GRPOSmokeConfig(
        run_id="test",
        model_id="test/model",
        adapter_path="adapter",
        dataset_path=str(root / "tasks.jsonl"),
        sft_dataset_path=str(root / "sft.jsonl"),
        output_dir=str(root / "output"),
        metrics_path=str(root / "metrics.json"),
        prompt_count=len(task_ids),
        task_ids=task_ids,
        allow_sft_task_overlap=allow_sft_task_overlap,
        expected_dataset_sha256=(
            hashlib.sha256((root / "tasks.jsonl").read_bytes()).hexdigest()
            if allow_sft_task_overlap
            else ""
        ),
        expected_sft_overlap_count=expected_sft_overlap_count,
    )


class GRPOTrainingTests(unittest.TestCase):
    def test_explicit_curriculum_preserves_order(self) -> None:
        tasks = generate_pilot_tasks(seed=7, examples_per_family=3)
        eligible = [
            task
            for task in tasks
            if task.split is Split.TRAIN and task.kind is TaskKind.NO_TOOL
        ]
        selected_ids = (eligible[1].task_id, eligible[0].task_id)
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            write_tasks_jsonl(tasks, root / "tasks.jsonl")
            (root / "sft.jsonl").write_text(
                json.dumps({"metadata": {"task_id": eligible[2].task_id}}) + "\n",
                encoding="utf-8",
            )
            rows = build_grpo_smoke_rows(_config(root, task_ids=selected_ids))

        self.assertEqual(tuple(row["task_id"] for row in rows), selected_ids)

    def test_explicit_curriculum_rejects_sft_task(self) -> None:
        tasks = generate_pilot_tasks(seed=7, examples_per_family=3)
        task = next(
            item
            for item in tasks
            if item.split is Split.TRAIN and item.kind is TaskKind.NO_TOOL
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            write_tasks_jsonl(tasks, root / "tasks.jsonl")
            (root / "sft.jsonl").write_text(
                json.dumps({"metadata": {"task_id": task.task_id}}) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "already in SFT"):
                build_grpo_smoke_rows(_config(root, task_ids=(task.task_id,)))

    def test_pinned_formal_curriculum_can_explicitly_reuse_sft_prompt(self) -> None:
        tasks = generate_pilot_tasks(seed=7, examples_per_family=3)
        task = next(
            item
            for item in tasks
            if item.split is Split.TRAIN and item.kind is TaskKind.NO_TOOL
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            task_path = root / "tasks.jsonl"
            write_tasks_jsonl(tasks, task_path)
            (root / "sft.jsonl").write_text(
                json.dumps({"metadata": {"task_id": task.task_id}}) + "\n",
                encoding="utf-8",
            )
            rows = build_grpo_smoke_rows(_config(
                root,
                task_ids=(task.task_id,),
                allow_sft_task_overlap=True,
                expected_sft_overlap_count=1,
            ))

        self.assertEqual([row["task_id"] for row in rows], [task.task_id])

    def test_sft_overlap_requires_pinned_dataset(self) -> None:
        with self.assertRaisesRegex(ValueError, "frozen dataset hash"):
            GRPOSmokeConfig(
                run_id="test",
                model_id="test/model",
                adapter_path="adapter",
                dataset_path="tasks.jsonl",
                sft_dataset_path="sft.jsonl",
                output_dir="output",
                metrics_path="metrics.json",
                allow_sft_task_overlap=True,
            )

    def test_curriculum_ids_must_match_prompt_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "length must equal prompt_count"):
            GRPOSmokeConfig(
                run_id="test",
                model_id="test/model",
                adapter_path="adapter",
                dataset_path="tasks.jsonl",
                sft_dataset_path="sft.jsonl",
                output_dir="output",
                metrics_path="metrics.json",
                prompt_count=2,
                task_ids=("one",),
            )

    def test_calculator_kind_requires_native_tool_loop(self) -> None:
        with self.assertRaisesRegex(ValueError, "enable_calculator_tool"):
            GRPOSmokeConfig(
                run_id="test",
                model_id="test/model",
                adapter_path="adapter",
                dataset_path="tasks.jsonl",
                sft_dataset_path="sft.jsonl",
                output_dir="output",
                metrics_path="metrics.json",
                task_kind="calculator",
            )


if __name__ == "__main__":
    unittest.main()
