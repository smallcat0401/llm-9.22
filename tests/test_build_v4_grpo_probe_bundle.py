import hashlib
import json
import unittest
import zipfile

from scripts import build_v4_grpo_probe_bundle as bundle


class V4GRPOProbeBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        bundle.main()

    def test_bundle_contains_only_train_probe_material(self) -> None:
        with zipfile.ZipFile(bundle.ZIP_PATH) as archive:
            names = set(archive.namelist())
            manifest = json.loads(archive.read("BUNDLE_MANIFEST.json"))

        self.assertIn(bundle.DATA_PATH, names)
        self.assertIn("src/verifiable_posttraining/grpo_probe.py", names)
        self.assertIn("scripts/run_v4_company_grpo_probe.sh", names)
        self.assertTrue(manifest["inference_only"])
        self.assertFalse(manifest["model_updates"])
        self.assertFalse(manifest["validation_included"])
        self.assertFalse(manifest["test_included"])
        self.assertFalse(any(name.startswith("data/") and "validation" in name for name in names))
        self.assertFalse(any(name.endswith("test_v1.jsonl") for name in names))

    def test_outer_checksum_matches_zip(self) -> None:
        expected, filename = bundle.SHA_PATH.read_text(encoding="utf-8").split()
        self.assertEqual(filename, bundle.ZIP_PATH.name)
        self.assertEqual(expected, hashlib.sha256(bundle.ZIP_PATH.read_bytes()).hexdigest())

    def test_readme_is_utf8_and_requires_existing_epoch3_adapter(self) -> None:
        with zipfile.ZipFile(bundle.ZIP_PATH) as archive:
            readme = archive.read("GRPO_PROBE_README_ZH.md").decode("utf-8")

        self.assertIn("同一个项目根目录", readme)
        self.assertIn("不会反向传播", readme)
        self.assertIn("不要运行validation/test", readme)


if __name__ == "__main__":
    unittest.main()
