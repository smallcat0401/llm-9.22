from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from scripts.freeze_v4_validation import main
from verifiable_posttraining.dataset import load_tasks_jsonl
from verifiable_posttraining.schemas import Split


ROOT = Path(__file__).resolve().parents[1]


class V4ValidationFreezeTests(unittest.TestCase):
    def test_freeze_preserves_v3_rows_and_approves_only_extension(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "validation.jsonl"
            manifest = Path(directory) / "manifest.json"
            argv = ["--output", str(output), "--manifest", str(manifest)]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(argv), 0)
                self.assertEqual(main(argv), 0)

            prior = load_tasks_jsonl(ROOT / "data/generated/v3_validation_v1.jsonl")
            frozen = load_tasks_jsonl(output)
            self.assertEqual(len(frozen), 64)
            self.assertEqual(frozen[:36], prior)
            self.assertEqual(set(Counter(task.family_id for task in frozen).values()), {8})
            self.assertTrue(all(task.split is Split.VALIDATION for task in frozen))
            self.assertTrue(all(task.metadata["review_status"] == "owner_approved"
                                for task in frozen[36:]))
            self.assertTrue(all(task.metadata["training_eligible"] is False
                                for task in frozen[36:]))
            self.assertEqual(json.loads(manifest.read_text(encoding="utf-8"))["count"], 64)

    def test_rejects_modified_review_input_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bad_manifest = Path(directory) / "bad_audit_manifest.json"
            value = json.loads((
                ROOT / "artifacts/dataset_manifests/"
                "v4_validation_public_extension_audit_v0.json"
            ).read_text(encoding="utf-8"))
            value["output_sha256"] = "0" * 64
            bad_manifest.write_text(json.dumps(value), encoding="utf-8")
            output = Path(directory) / "must_not_exist.jsonl"
            with self.assertRaisesRegex(ValueError, "input hash mismatch"):
                main([
                    "--extension-manifest", str(bad_manifest),
                    "--output", str(output),
                    "--manifest", str(Path(directory) / "manifest.json"),
                ])
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
