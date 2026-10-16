from __future__ import annotations

from collections import Counter
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from scripts.freeze_v4_grpo_train import main
from verifiable_posttraining.dataset import load_tasks_jsonl
from verifiable_posttraining.schemas import Split, TaskKind


ROOT = Path(__file__).resolve().parents[1]


class FreezeV4GRPOTrainTests(unittest.TestCase):
    def test_freeze_selects_only_mixed_verified_outcome_groups(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "grpo.jsonl"
            manifest = Path(directory) / "manifest.json"
            argv = ["--output", str(output), "--manifest", str(manifest)]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(argv), 0)
                self.assertEqual(main(argv), 0)

            tasks = load_tasks_jsonl(output)
            value = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(len(tasks), 53)
            self.assertEqual(len({task.family_id for task in tasks}), 16)
            self.assertEqual(sum(value["family_counts"].values()), 53)
            self.assertEqual(
                value["outcome_successes_of_8_histogram"],
                {"1": 1, "2": 6, "3": 4, "4": 5, "5": 6, "6": 12, "7": 19},
            )
            self.assertTrue(all(task.split is Split.TRAIN for task in tasks))
            self.assertTrue(all(task.kind is TaskKind.CALCULATOR for task in tasks))
            self.assertTrue(all(task.allowed_tools == ("calculator",) for task in tasks))

            validation_families = {
                task.family_id
                for task in load_tasks_jsonl(ROOT / "data/generated/v4_validation_v1.jsonl")
            }
            test_families = {
                task.family_id
                for task in load_tasks_jsonl(ROOT / "data/generated/v4_test_v1.jsonl")
            }
            train_families = {task.family_id for task in tasks}
            self.assertFalse(train_families & validation_families)
            self.assertFalse(train_families & test_families)

    def test_frozen_order_is_source_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "grpo.jsonl"
            manifest = Path(directory) / "manifest.json"
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--output", str(output), "--manifest", str(manifest)])
            tasks = load_tasks_jsonl(output)
            source = load_tasks_jsonl(
                ROOT / "data/generated/v4_train_tasks_curated_v2.jsonl"
            )
            selected = {task.task_id for task in tasks}
            self.assertEqual(
                [task.task_id for task in tasks],
                [task.task_id for task in source if task.task_id in selected],
            )
            counts = Counter(task.family_id for task in tasks)
            self.assertEqual(counts["curriculum-v2-required-score"], 9)
            self.assertEqual(counts["curriculum-v2-shared-bill"], 11)

    def test_rejects_modified_probe_metrics_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bad_metrics = Path(directory) / "metrics.json"
            source = ROOT / (
                "artifacts/metrics/qwen3_5_4b_v4_grpo_reward_probe_seed719.json"
            )
            bad_metrics.write_bytes(source.read_bytes() + b"\n")
            output = Path(directory) / "must_not_exist.jsonl"
            with self.assertRaisesRegex(ValueError, "input hash mismatch"):
                main([
                    "--probe-metrics", str(bad_metrics),
                    "--output", str(output),
                    "--manifest", str(Path(directory) / "manifest.json"),
                ])
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
