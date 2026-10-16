"""Build a minimal hotfix that resumes only the failed native baseline run."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BUNDLE_NAME = "v4_4b_final_starting_policy_native_hotfix_v1"
ZIP_PATH = DIST / f"{BUNDLE_NAME}.zip"
SHA_PATH = DIST / f"{BUNDLE_NAME}.sha256"

FILES = (
    "src/verifiable_posttraining/native_tool_evaluation.py",
    "tests/test_native_tool_evaluation.py",
    "scripts/run_v4_company_final_starting_policy_native_resume.sh",
    "docs/V4_FINAL_STARTING_POLICY_TEST_ADDENDUM_ZH.md",
)

README = """# 起始策略 native 评测续跑修复

首次补测已经成功完成 custom 的 72 道题，但旧版 native CLI 错误地把 `--adapter-path` 设成必填，因此在 native 开始前退出。

本修复包只做两件事：

1. 让 native 评测在未提供 adapter 时正确加载起始策略；
2. 保留已有 custom 结果，只续跑尚未执行的 native 评测。

请在先前解压并运行过的 `v4_4b_final_starting_policy_test_bundle_v1` 目录中执行：

```bash
unzip -o /path/to/v4_4b_final_starting_policy_native_hotfix_v1.zip -d .
export HF_HUB_CACHE=/data/huggingface-cache
export MODEL_ID=/data/jiang_yiben/models/v4_4b_train_validation_bundle_v1_bk/Qwen2/Qwen3.5-4B
bash scripts/run_v4_company_final_starting_policy_native_resume.sh
```

续跑脚本会先确认已有 custom 结果恰好包含 72 条记录；若 native 结果已经存在则拒绝覆盖。完成后返回：

```text
v4_4b_final_starting_policy_test_results_seed937.tar.gz
```
"""


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def main() -> int:
    entries: dict[str, bytes] = {}
    for relative in FILES:
        source = ROOT / relative
        if not source.is_file():
            raise FileNotFoundError(source)
        entries[relative] = source.read_bytes()
    entries["NATIVE_HOTFIX_README_ZH.md"] = README.encode("utf-8")
    manifest = {
        "bundle": BUNDLE_NAME,
        "purpose": "Resume only the failed starting-policy native evaluation",
        "model_updates": False,
        "custom_rerun": False,
        "native_runs": 1,
        "adapter_required": False,
        "files": [
            {"path": path, "size_bytes": len(payload), "sha256": _sha256(payload)}
            for path, payload in entries.items()
        ],
    }
    entries["HOTFIX_MANIFEST.json"] = (
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")

    DIST.mkdir(parents=True, exist_ok=True)
    timestamp = (2026, 10, 8, 0, 0, 0)
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path, payload in entries.items():
            info = zipfile.ZipInfo(path, timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, payload)

    with zipfile.ZipFile(ZIP_PATH) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != set(entries):
            raise ValueError("hotfix ZIP verification failed")
        for path, payload in entries.items():
            if archive.read(path) != payload:
                raise ValueError(f"hotfix entry mismatch: {path}")

    digest = _sha256(ZIP_PATH.read_bytes())
    SHA_PATH.write_text(f"{digest}  {ZIP_PATH.name}\n", encoding="utf-8")
    print(json.dumps({
        "zip": str(ZIP_PATH),
        "sha256": digest,
        "size_bytes": ZIP_PATH.stat().st_size,
        "archive_files": len(entries),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

