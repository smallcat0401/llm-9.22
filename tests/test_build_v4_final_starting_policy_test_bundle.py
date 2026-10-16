import hashlib
import json
import unittest
import zipfile

from scripts import build_v4_final_starting_policy_test_bundle as bundle


class V4FinalStartingPolicyTestBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        bundle.main()

    def test_bundle_contains_only_frozen_test_data_and_no_weights(self) -> None:
        with zipfile.ZipFile(bundle.ZIP_PATH) as archive:
            names = set(archive.namelist())
            manifest = json.loads(archive.read("BUNDLE_MANIFEST.json"))

        self.assertIn(bundle.TEST_DATA_PATH, names)
        self.assertIn(bundle.TEST_MANIFEST_PATH, names)
        self.assertIn("scripts/run_v4_company_final_starting_policy_test.sh", names)
        self.assertFalse(any(name.startswith("data/") and name != bundle.TEST_DATA_PATH for name in names))
        self.assertFalse(any(name.endswith((".safetensors", ".bin", ".pt", ".pth")) for name in names))
        self.assertTrue(manifest["final_evaluation_addendum"])
        self.assertTrue(manifest["post_hoc_baseline_addendum"])
        self.assertFalse(manifest["model_updates"])
        self.assertFalse(manifest["adapter_loaded"])
        self.assertEqual(manifest["checkpoint_count"], 1)
        self.assertEqual(manifest["test_tasks"], 72)
        self.assertTrue(manifest["test_included"])
        self.assertFalse(manifest["train_included"])
        self.assertFalse(manifest["validation_included"])

    def test_run_script_has_one_matched_starting_policy_evaluation_per_protocol(self) -> None:
        with zipfile.ZipFile(bundle.ZIP_PATH) as archive:
            script = archive.read(
                "scripts/run_v4_company_final_starting_policy_test.sh"
            ).decode("utf-8")

        self.assertEqual(script.count("baseline-eval"), 1)
        self.assertEqual(
            script.count("python -m verifiable_posttraining.native_tool_evaluation"),
            1,
        )
        self.assertEqual(script.count("--seed 937"), 2)
        self.assertEqual(script.count("--split test"), 2)
        self.assertNotIn("--adapter-path", script)
        self.assertNotIn("SFT_ADAPTER", script)
        self.assertNotIn("GRPO_ADAPTER", script)

    def test_outer_checksum_matches_zip(self) -> None:
        expected, filename = bundle.SHA_PATH.read_text(encoding="utf-8").split()
        self.assertEqual(filename, bundle.ZIP_PATH.name)
        self.assertEqual(expected, hashlib.sha256(bundle.ZIP_PATH.read_bytes()).hexdigest())

    def test_readme_discloses_post_hoc_control_and_return_archive(self) -> None:
        with zipfile.ZipFile(bundle.ZIP_PATH) as archive:
            readme = archive.read(
                "FINAL_STARTING_POLICY_TEST_README_ZH.md"
            ).decode("utf-8")

        self.assertIn("未加载任何 adapter", readme)
        self.assertIn("看到 SFT/GRPO test 结果后补充", readme)
        self.assertIn("不得据此继续训练", readme)
        self.assertIn(
            "v4_4b_final_starting_policy_test_results_seed937.tar.gz", readme
        )


if __name__ == "__main__":
    unittest.main()

