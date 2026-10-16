from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from scripts.curate_v4_sft_paths import EXCLUDED_TASK_ID, _read_rows, main


ROOT = Path(__file__).resolve().parents[1]


class CurateV4SFTPathsTests(unittest.TestCase):
    def test_excludes_only_rejected_path_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "candidates.jsonl"
            manifest = Path(directory) / "manifest.json"
            argv = ["--output", str(output), "--manifest", str(manifest)]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(argv), 0)
                self.assertEqual(main(argv), 0)

            source = _read_rows(ROOT / (
                "data/review/v4_manual_zero_pass_v1/"
                "v3_v4_search_plus_manual_sft_candidates.jsonl"
            ))
            expected = tuple(row for row in source
                             if row["metadata"]["task_id"] != EXCLUDED_TASK_ID)
            actual = _read_rows(output)
            self.assertEqual(actual, expected)
            self.assertEqual(len(actual), 213)
            self.assertEqual(dict(Counter(row["metadata"]["mixture_source"] for row in actual)), {
                "v3-reviewed": 58,
                "v4-search-candidate": 114,
                "v4-manual-zero-pass": 41,
            })
            self.assertFalse(json.loads(manifest.read_text(encoding="utf-8"))["train_ready"])

    def test_rejects_changed_source_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source_manifest = json.loads((ROOT / (
                "artifacts/dataset_manifests/v4_manual_zero_pass_v1.json"
            )).read_text(encoding="utf-8"))
            source_manifest["outputs"]["combined_staged_sft"]["sha256"] = "0" * 64
            bad_manifest = Path(directory) / "source_manifest.json"
            bad_manifest.write_text(json.dumps(source_manifest), encoding="utf-8")
            output = Path(directory) / "must_not_exist.jsonl"
            with self.assertRaisesRegex(ValueError, "source hash mismatch"):
                main([
                    "--source-manifest", str(bad_manifest),
                    "--output", str(output),
                    "--manifest", str(Path(directory) / "manifest.json"),
                ])
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
