from __future__ import annotations

import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from scripts.freeze_v4_test import main
from verifiable_posttraining.dataset import load_tasks_jsonl
from verifiable_posttraining.schemas import Split


ROOT = Path(__file__).resolve().parents[1]


class V4TestFreezeTests(unittest.TestCase):
    def test_freeze_preserves_v3_and_approves_one_per_parent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "test.jsonl"
            manifest = Path(directory) / "manifest.json"
            argv = ["--output", str(output), "--manifest", str(manifest)]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(argv), 0)
                self.assertEqual(main(argv), 0)

            prior = load_tasks_jsonl(ROOT / "data/generated/v3_test_v1.jsonl")
            frozen = load_tasks_jsonl(output)
            self.assertEqual(len(frozen), 72)
            self.assertEqual(frozen[:36], prior)
            self.assertEqual(Counter(task.family_id for task in frozen), Counter({
                family: 16 if "public" not in family else 2
                for family in {task.family_id for task in prior}
            }))
            self.assertEqual(
                {task.metadata["parent_test_task_id"] for task in frozen[36:]},
                {task.task_id for task in prior},
            )
            self.assertTrue(all(task.split is Split.TEST for task in frozen))
            self.assertTrue(all(task.metadata["review_status"] == "owner_approved"
                                for task in frozen[36:]))
            self.assertTrue(all(task.metadata["training_eligible"] is False
                                for task in frozen[36:]))
            self.assertEqual(json.loads(manifest.read_text(encoding="utf-8"))["count"], 72)

    def test_rejects_hash_change_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            audit_manifest = json.loads((ROOT / (
                "artifacts/dataset_manifests/v4_test_extension_audit_v1.json"
            )).read_text(encoding="utf-8"))
            audit_manifest["output_sha256"] = "0" * 64
            bad_manifest = Path(directory) / "bad_audit_manifest.json"
            bad_manifest.write_text(json.dumps(audit_manifest), encoding="utf-8")
            output = Path(directory) / "must_not_exist.jsonl"
            with self.assertRaisesRegex(ValueError, "input hash mismatch"):
                main([
                    "--extension-manifest", str(bad_manifest),
                    "--output", str(output),
                    "--manifest", str(Path(directory) / "manifest.json"),
                ])
            self.assertFalse(output.exists())

    def test_rejects_incorrect_gt_even_with_updated_input_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = ROOT / "data/review/v4_test_extension_audit_v1.jsonl"
            lines = source.read_text(encoding="utf-8").splitlines()
            changed = json.loads(lines[0])
            changed["ground_truth"]["value"] += 1
            lines[0] = json.dumps(changed, sort_keys=True)
            bad_extension = Path(directory) / "bad_extension.jsonl"
            bad_extension.write_text("\n".join(lines) + "\n", encoding="utf-8")
            audit_manifest = json.loads((ROOT / (
                "artifacts/dataset_manifests/v4_test_extension_audit_v1.json"
            )).read_text(encoding="utf-8"))
            audit_manifest["output_sha256"] = hashlib.sha256(bad_extension.read_bytes()).hexdigest()
            bad_manifest = Path(directory) / "bad_audit_manifest.json"
            bad_manifest.write_text(json.dumps(audit_manifest), encoding="utf-8")
            output = Path(directory) / "must_not_exist.jsonl"
            with self.assertRaisesRegex(ValueError, "reference expression disagrees with GT"):
                main([
                    "--extension", str(bad_extension),
                    "--extension-manifest", str(bad_manifest),
                    "--output", str(output),
                    "--manifest", str(Path(directory) / "manifest.json"),
                ])
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
