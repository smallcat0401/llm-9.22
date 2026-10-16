import hashlib
import json
import unittest
import zipfile

from scripts import build_v4_grpo_formal_bundle as bundle


class V4GRPOFormalBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        bundle.main()

    def test_bundle_contains_frozen_train_and_validation_but_no_test(self) -> None:
        with zipfile.ZipFile(bundle.ZIP_PATH) as archive:
            names = set(archive.namelist())
            manifest = json.loads(archive.read("BUNDLE_MANIFEST.json"))

        self.assertIn(bundle.GRPO_DATA_PATH, names)
        self.assertIn(bundle.SFT_DATA_PATH, names)
        self.assertIn(bundle.VALIDATION_PATH, names)
        self.assertIn("scripts/run_v4_company_grpo_formal.sh", names)
        self.assertIn("src/verifiable_posttraining/grpo_training.py", names)
        self.assertNotIn("tests/test_freeze_v4_grpo_train.py", names)
        self.assertNotIn("scripts/freeze_v4_grpo_train.py", names)
        self.assertTrue(manifest["formal_grpo_updates"])
        self.assertEqual(manifest["grpo_train_tasks"], 53)
        self.assertEqual(manifest["sft_overlap_tasks"], 51)
        self.assertTrue(manifest["validation_included"])
        self.assertFalse(manifest["test_included"])
        self.assertFalse(any(name.startswith("data/") and "test" in name for name in names))

    def test_outer_checksum_matches_zip(self) -> None:
        expected, filename = bundle.SHA_PATH.read_text(encoding="utf-8").split()
        self.assertEqual(filename, bundle.ZIP_PATH.name)
        self.assertEqual(expected, hashlib.sha256(bundle.ZIP_PATH.read_bytes()).hexdigest())

    def test_readme_is_utf8_and_keeps_test_sealed(self) -> None:
        with zipfile.ZipFile(bundle.ZIP_PATH) as archive:
            readme = archive.read("GRPO_FORMAL_README_ZH.md").decode("utf-8")

        self.assertIn("正式 GRPO", readme)
        self.assertIn("不要运行 test", readme)
        self.assertIn("v4_4b_grpo_formal_bundle_v2.zip", readme)
        self.assertIn("v4_4b_grpo_formal_results_seed727.tar.gz", readme)


if __name__ == "__main__":
    unittest.main()
