import hashlib
import json
from pathlib import Path
import unittest
import zipfile

from scripts import build_v4_company_bundle as bundle


class V4CompanyBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        bundle.main()

    def test_bundle_is_complete_and_excludes_frozen_test(self) -> None:
        with zipfile.ZipFile(bundle.ZIP_PATH) as archive:
            names = set(archive.namelist())

            self.assertIn(bundle.TRAIN_PATH, names)
            self.assertIn(bundle.VALIDATION_PATH, names)
            self.assertIn("scripts/run_v4_company_training.sh", names)
            self.assertIn("scripts/run_v4_company_validation.sh", names)
            self.assertIn("RENTAL_BUNDLE_README_ZH.md", names)
            self.assertFalse(any(name.endswith("test_v1.jsonl") for name in names))

            manifest = json.loads(archive.read("BUNDLE_MANIFEST.json"))
            self.assertEqual(manifest["training_examples"], 213)
            self.assertEqual(manifest["validation_tasks"], 64)
            self.assertFalse(manifest["frozen_test_included"])

    def test_outer_checksum_matches_zip(self) -> None:
        expected, filename = bundle.SHA_PATH.read_text(encoding="utf-8").split()
        self.assertEqual(filename, bundle.ZIP_PATH.name)
        self.assertEqual(
            expected,
            hashlib.sha256(bundle.ZIP_PATH.read_bytes()).hexdigest(),
        )

    def test_readme_is_utf8_chinese_and_describes_a_fresh_run(self) -> None:
        with zipfile.ZipFile(bundle.ZIP_PATH) as archive:
            readme = archive.read("RENTAL_BUNDLE_README_ZH.md").decode("utf-8")

        self.assertIn("完整运行包", readme)
        self.assertIn("重新做 QLoRA", readme)
        self.assertIn("不包含 V3/V4 test", readme)


if __name__ == "__main__":
    unittest.main()
