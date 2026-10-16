"""Build the frozen V4 4B SFT-vs-GRPO final paired-test bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BUNDLE_NAME = "v4_4b_final_ab_test_bundle_v1"
ZIP_PATH = DIST / f"{BUNDLE_NAME}.zip"
SHA_PATH = DIST / f"{BUNDLE_NAME}.sha256"

TEST_DATA_PATH = "data/generated/v4_test_v1.jsonl"
TEST_MANIFEST_PATH = "artifacts/dataset_manifests/v4_test_v1.json"
TEST_DATA_SHA256 = "a0223c4517596007cf40e5cdd30e61e534f5f5dd4855af0f0042d106341be0bc"
TEST_MANIFEST_SHA256 = "699e6d4aa54040294216dfa87849823cf0379fbb108762db8495a0b3fb1c8a1d"

EXPLICIT_FILES = (
    "AGENTS.md",
    "pyproject.toml",
    "requirements-gpu-win-cu128.lock",
    TEST_DATA_PATH,
    TEST_MANIFEST_PATH,
    "docs/V4_FINAL_AB_TEST_PLAN_ZH.md",
    "scripts/run_v4_company_final_ab_test.sh",
    "tests/test_evaluation.py",
    "tests/test_metrics.py",
    "tests/test_native_tool_evaluation.py",
    "tests/test_model_protocol.py",
    "tests/test_verifier.py",
)

IGNORED_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
IGNORED_SUFFIXES = {".pyc", ".pyo", ".safetensors", ".bin", ".pt", ".pth"}

README = """# V4 4B SFT 与 GRPO 最终配对测试包

本包只用于已经冻结的两个 checkpoint 的最终推理评测，不执行任何训练或参数更新：

- A：V4 SFT adapter；
- C：从同一个 A 继续训练得到的正式 GRPO adapter。

包内包含 72 道冻结 V4 test、数据 manifest、评测代码、运行脚本和测试计划。它不包含
train、validation、模型权重、adapter 或缓存。

先核对 ZIP：

```bash
sha256sum -c v4_4b_final_ab_test_bundle_v1.sha256
```

建议解压到新的空目录，然后设置公司电脑上的实际绝对路径：

```bash
unzip v4_4b_final_ab_test_bundle_v1.zip -d v4_4b_final_ab_test_bundle_v1
cd v4_4b_final_ab_test_bundle_v1
export HF_HUB_CACHE=/data/huggingface-cache
export MODEL_ID=/actual/path/to/Qwen3.5-4B
export SFT_ADAPTER_PATH=/actual/path/to/qwen3_5_4b_v4_mixed213_seed113/adapter
export GRPO_ADAPTER_PATH=/actual/path/to/qwen3_5_4b_v4_outcome53_seed727/adapter
bash scripts/run_v4_company_final_ab_test.sh
```

脚本会先验证test哈希与两个adapter权重，再以完全相同的设置依次运行：

1. SFT custom协议主评测；
2. GRPO custom协议主评测；
3. SFT native-tool诊断；
4. GRPO native-tool诊断。

两个checkpoint、两个协议都只能运行一次。禁止训练、修改数据、修改参数、根据中间结果
停止另一组、挑选性重跑失败题或在test后继续调参。完成后返回：

```text
v4_4b_final_ab_test_results_seed937.tar.gz
```
"""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_files() -> list[tuple[Path, str]]:
    collected: dict[str, Path] = {}
    for relative in EXPLICIT_FILES:
        source = ROOT / relative
        if not source.is_file():
            raise FileNotFoundError(source)
        archive_name = (
            "requirements-gpu-cu128.lock"
            if relative == "requirements-gpu-win-cu128.lock"
            else relative
        )
        collected[archive_name] = source
    for source in sorted((ROOT / "src").rglob("*")):
        if (
            source.is_file()
            and not any(part in IGNORED_PARTS for part in source.relative_to(ROOT).parts)
            and source.suffix.lower() not in IGNORED_SUFFIXES
        ):
            collected[source.relative_to(ROOT).as_posix()] = source
    return [(source, name) for name, source in sorted(collected.items())]


def _assert_safe(name: str) -> None:
    normalized = name.replace("\\", "/")
    parts = tuple(part.lower() for part in Path(normalized).parts)
    if normalized.startswith("/") or ".." in parts:
        raise ValueError(f"unsafe archive path: {name}")
    if normalized.startswith("data/") and normalized != TEST_DATA_PATH:
        raise ValueError(f"only the frozen final test data may enter this bundle: {name}")
    if any(part in {".git", ".venv", "outputs", "models", ".cache", "dist"} for part in parts):
        raise ValueError(f"forbidden directory in bundle: {name}")
    if any(part == ".env" or part.endswith((".pem", ".key")) for part in parts):
        raise ValueError(f"possible credential in bundle: {name}")
    if Path(normalized).suffix.lower() in IGNORED_SUFFIXES:
        raise ValueError(f"model/checkpoint file in bundle: {name}")


def _verify_archive(expected_names: set[str]) -> None:
    with zipfile.ZipFile(ZIP_PATH) as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP integrity check failed")
        if set(archive.namelist()) != expected_names:
            raise ValueError("archive members differ from explicit allowlist")
        manifest = json.loads(archive.read("BUNDLE_MANIFEST.json"))
        expected_flags = {
            "final_evaluation": True,
            "model_updates": False,
            "test_included": True,
            "train_included": False,
            "validation_included": False,
        }
        for key, value in expected_flags.items():
            if manifest.get(key) is not value:
                raise ValueError(f"unexpected manifest flag {key}")
        for entry in manifest["files"]:
            payload = archive.read(entry["path"])
            if len(payload) != entry["size_bytes"] or _sha256_bytes(payload) != entry["sha256"]:
                raise ValueError(f"archive entry mismatch: {entry['path']}")


def main() -> int:
    files = _source_files()
    for _, name in files:
        _assert_safe(name)
    expected_hashes = {
        TEST_DATA_PATH: TEST_DATA_SHA256,
        TEST_MANIFEST_PATH: TEST_MANIFEST_SHA256,
    }
    for relative, expected in expected_hashes.items():
        if _sha256_file(ROOT / relative) != expected:
            raise ValueError(f"frozen input hash changed: {relative}")

    data_hashes = "".join(
        f"{digest}  {path}\n" for path, digest in expected_hashes.items()
    ).encode("ascii")
    generated = {
        "FINAL_AB_TEST_README_ZH.md": README.encode("utf-8"),
        f"{BUNDLE_NAME}.data.sha256": data_hashes,
    }
    entries = [
        {"path": name, "size_bytes": source.stat().st_size, "sha256": _sha256_file(source)}
        for source, name in files
    ]
    entries.extend(
        {"path": name, "size_bytes": len(payload), "sha256": _sha256_bytes(payload)}
        for name, payload in generated.items()
    )
    manifest = {
        "bundle": BUNDLE_NAME,
        "purpose": "Frozen V4 4B SFT-vs-GRPO final paired evaluation",
        "final_evaluation": True,
        "model_updates": False,
        "checkpoint_count": 2,
        "test_tasks": 72,
        "test_included": True,
        "train_included": False,
        "validation_included": False,
        "test_runs_per_checkpoint_per_protocol": 1,
        "file_count_excluding_manifest": len(entries),
        "files": entries,
    }
    generated["BUNDLE_MANIFEST.json"] = (
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")

    DIST.mkdir(parents=True, exist_ok=True)
    timestamp = (2026, 10, 8, 0, 0, 0)
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source, name in files:
            info = zipfile.ZipInfo(name, timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, source.read_bytes())
        for name, payload in generated.items():
            _assert_safe(name)
            info = zipfile.ZipInfo(name, timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, payload)

    expected_names = {name for _, name in files} | set(generated)
    _verify_archive(expected_names)
    zip_hash = _sha256_file(ZIP_PATH)
    SHA_PATH.write_text(f"{zip_hash}  {ZIP_PATH.name}\n", encoding="utf-8")
    print(json.dumps({
        "zip": str(ZIP_PATH),
        "sha256": zip_hash,
        "size_bytes": ZIP_PATH.stat().st_size,
        "archive_files": len(expected_names),
        "test_tasks": 72,
        "checkpoint_count": 2,
        "model_updates": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

