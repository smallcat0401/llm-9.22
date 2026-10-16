from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from scripts.freeze_v4_sft import _examples, main
from verifiable_posttraining.sft_training import (
    load_sft_training_config,
    select_balanced_examples,
)


ROOT = Path(__file__).resolve().parents[1]


class FreezeV4SFTTests(unittest.TestCase):
    def test_configs_select_approved_rows_from_clean_start(self) -> None:
        examples = _examples(ROOT / "data/generated/v4_sft_custom_approved_v1.jsonl")
        formal = load_sft_training_config(
            ROOT / "configs/sft_qwen3_5_4b_v4_mixed213_seed113.toml"
        )
        smoke = load_sft_training_config(
            ROOT / "configs/sft_qwen3_5_4b_v4_mixed213_smoke_seed113.toml"
        )
        self.assertEqual(formal.sample_count, 213)
        self.assertEqual(formal.max_steps, 3 * 213)
        self.assertEqual(formal.checkpoint_steps, (213, 426))
        self.assertIsNone(formal.adapter_path)
        self.assertEqual(len(select_balanced_examples(
            examples, limit=formal.sample_count, seed=formal.seed
        )), 213)
        self.assertEqual(smoke.sample_count, 4)
        self.assertIsNone(smoke.adapter_path)

    def test_freeze_preserves_messages_and_source_labels(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "sft.jsonl"
            manifest = Path(directory) / "manifest.json"
            argv = ["--output", str(output), "--manifest", str(manifest)]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(argv), 0)
                self.assertEqual(main(argv), 0)

            candidates = _examples(ROOT / (
                "data/review/v4_sft_paths_curated_v1/sft_candidates_213.jsonl"
            ))
            frozen = _examples(output)
            self.assertEqual(len(frozen), 213)
            self.assertEqual([row["messages"] for row in frozen],
                             [row["messages"] for row in candidates])
            self.assertEqual(Counter(row["metadata"]["mixture_source"] for row in frozen), {
                "v3-reviewed": 58,
                "v4-search-candidate": 114,
                "v4-manual-zero-pass": 41,
            })
            self.assertTrue(all(row["metadata"].get("review_status") == "owner_approved"
                                for row in frozen if row["metadata"]["mixture_source"]
                                != "v3-reviewed"))
            self.assertEqual([row for row in frozen if row["metadata"]["mixture_source"]
                              == "v3-reviewed"],
                             [row for row in candidates if row["metadata"]["mixture_source"]
                              == "v3-reviewed"])
            self.assertTrue(json.loads(manifest.read_text(encoding="utf-8"))["train_ready"])

    def test_rejects_changed_candidate_hash_before_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            candidate_manifest = json.loads((ROOT / (
                "artifacts/dataset_manifests/v4_sft_paths_curated_v1.json"
            )).read_text(encoding="utf-8"))
            candidate_manifest["output_sha256"] = "0" * 64
            bad_manifest = Path(directory) / "bad_candidate_manifest.json"
            bad_manifest.write_text(json.dumps(candidate_manifest), encoding="utf-8")
            output = Path(directory) / "must_not_exist.jsonl"
            with self.assertRaisesRegex(ValueError, "source hash mismatch"):
                main([
                    "--candidate-manifest", str(bad_manifest),
                    "--output", str(output),
                    "--manifest", str(Path(directory) / "manifest.json"),
                ])
            self.assertFalse(output.exists())

    def test_rejects_validation_family_leak(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            validation_manifest = json.loads((ROOT / (
                "artifacts/dataset_manifests/v4_validation_v1.json"
            )).read_text(encoding="utf-8"))
            validation_manifest["family_counts"]["curriculum-v2-sales-returns"] = 1
            bad_manifest = Path(directory) / "bad_validation_manifest.json"
            bad_manifest.write_text(json.dumps(validation_manifest), encoding="utf-8")
            output = Path(directory) / "must_not_exist.jsonl"
            with self.assertRaisesRegex(ValueError, "leaked task"):
                main([
                    "--validation-manifest", str(bad_manifest),
                    "--output", str(output),
                    "--manifest", str(Path(directory) / "manifest.json"),
                ])
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
