from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from verifiable_posttraining.v3_eval_seed import build_v3_eval_seed_candidates


ROOT = Path(__file__).resolve().parents[1]


class V3EvalSeedTests(unittest.TestCase):
    def test_builds_balanced_pending_disjoint_candidates(self) -> None:
        rows = build_v3_eval_seed_candidates(
            gsm8k_train_path=ROOT / "data/external/gsm8k/train.jsonl",
            gsm8k_test_path=ROOT / "data/external/gsm8k/test.jsonl",
        )
        self.assertEqual(len(rows), 24)
        self.assertEqual(sum(row.proposed_split == "validation" for row in rows), 12)
        self.assertEqual(sum(row.proposed_split == "test" for row in rows), 12)
        self.assertTrue(all(row.review_status == "pending" for row in rows))
        validation_families = {
            row.family_id for row in rows
            if row.source_type == "self_written" and row.proposed_split == "validation"
        }
        test_families = {
            row.family_id for row in rows
            if row.source_type == "self_written" and row.proposed_split == "test"
        }
        self.assertFalse(validation_families & test_families)

    def test_rejects_public_source_seen_in_prior_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "records.jsonl"
            artifact.write_text(json.dumps({
                "task": {"metadata": {"source_split": "train", "source_index": 6154}}
            }) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "already appears"):
                build_v3_eval_seed_candidates(
                    gsm8k_train_path=ROOT / "data/external/gsm8k/train.jsonl",
                    gsm8k_test_path=ROOT / "data/external/gsm8k/test.jsonl",
                    exclusion_artifacts=(artifact,),
                )


if __name__ == "__main__":
    unittest.main()
