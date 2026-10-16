import hashlib
import json
import unittest
import zipfile

from scripts import build_v4_final_starting_policy_native_hotfix as hotfix


class V4FinalStartingPolicyNativeHotfixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        hotfix.main()

    def test_hotfix_is_minimal_and_contains_no_data_or_weights(self) -> None:
        with zipfile.ZipFile(hotfix.ZIP_PATH) as archive:
            names = set(archive.namelist())
            manifest = json.loads(archive.read("HOTFIX_MANIFEST.json"))

        self.assertIn("src/verifiable_posttraining/native_tool_evaluation.py", names)
        self.assertIn(
            "scripts/run_v4_company_final_starting_policy_native_resume.sh", names
        )
        self.assertFalse(any(name.startswith("data/") for name in names))
        self.assertFalse(any(name.endswith((".safetensors", ".bin", ".pt", ".pth")) for name in names))
        self.assertFalse(manifest["model_updates"])
        self.assertFalse(manifest["custom_rerun"])
        self.assertEqual(manifest["native_runs"], 1)
        self.assertFalse(manifest["adapter_required"])

    def test_resume_script_preserves_custom_and_runs_native_once(self) -> None:
        with zipfile.ZipFile(hotfix.ZIP_PATH) as archive:
            script = archive.read(
                "scripts/run_v4_company_final_starting_policy_native_resume.sh"
            ).decode("utf-8")

        self.assertIn('wc -l < "$CUSTOM_DIR/records.jsonl"', script)
        self.assertEqual(
            script.count("python -m verifiable_posttraining.native_tool_evaluation"),
            1,
        )
        self.assertNotIn("baseline-eval", script)
        self.assertNotIn("--adapter-path", script)
        self.assertIn("refusing to overwrite or rerun", script)

    def test_outer_checksum_matches_zip(self) -> None:
        expected, filename = hotfix.SHA_PATH.read_text(encoding="utf-8").split()
        self.assertEqual(filename, hotfix.ZIP_PATH.name)
        self.assertEqual(expected, hashlib.sha256(hotfix.ZIP_PATH.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()

