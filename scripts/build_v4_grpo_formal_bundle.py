"""Build the formal V4 4B GRPO train-and-validation company bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BUNDLE_NAME = "v4_4b_grpo_formal_bundle_v2"
ZIP_PATH = DIST / f"{BUNDLE_NAME}.zip"
SHA_PATH = DIST / f"{BUNDLE_NAME}.sha256"

GRPO_DATA_PATH = "data/generated/v4_grpo_train_outcome_variance_seed719_v1.jsonl"
SFT_DATA_PATH = "data/generated/v4_sft_custom_approved_v1.jsonl"
VALIDATION_PATH = "data/generated/v4_validation_v1.jsonl"
GRPO_DATA_SHA256 = "83962d596d52edad6db84db8d2d6fae7ce81f5ec55b28098f0309cc96f52be9a"
SFT_DATA_SHA256 = "52c6f559156f3c8655516602e0d4a97431e200539d1bbda5880c890bdef497ad"
VALIDATION_SHA256 = "d62dc47ae7027de67c30521327d5f8afb6b88878ffddfe758843820da9093cf0"

EXPLICIT_FILES = (
    "AGENTS.md",
    "pyproject.toml",
    "requirements-gpu-win-cu128.lock",
    "configs/grpo_qwen3_5_4b_v4_outcome53_smoke_seed727.toml",
    "configs/grpo_qwen3_5_4b_v4_outcome53_seed727.toml",
    GRPO_DATA_PATH,
    SFT_DATA_PATH,
    VALIDATION_PATH,
    "artifacts/dataset_manifests/v4_grpo_train_outcome_variance_seed719_v1.json",
    "artifacts/dataset_manifests/v4_sft_custom_approved_v1.json",
    "artifacts/dataset_manifests/v4_validation_v1.json",
    "artifacts/metrics/qwen3_5_4b_v4_grpo_reward_probe_seed719.json",
    "docs/V4_GRPO_TRAIN_FREEZE_ZH.md",
    "docs/V4_4B_GRPO_PLAN_ZH.md",
    "scripts/run_v4_company_grpo_formal.sh",
    "tests/test_grpo_training.py",
    "tests/test_reward.py",
    "tests/test_native_tool_evaluation.py",
    "tests/test_model_protocol.py",
    "tests/test_verifier.py",
)

IGNORED_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
IGNORED_SUFFIXES = {".pyc", ".pyo", ".safetensors", ".bin", ".pt", ".pth"}

README = """# V4 4B 正式 GRPO 公司 GPU 运行包

本包执行预注册的 A（SFT）与 C（SFT+GRPO）对照。它包含 53 道冻结 train
prompt、原 SFT 数据（只用于重叠审计）、64 道冻结 validation、训练代码、配置、测试和
运行脚本。它不包含 V4 test、模型权重、SFT adapter、缓存或历史输出。

必须解压到此前完成 V4 SFT 和 reward probe 的同一个工作目录。默认需要以下 adapter：

```text
outputs/sft/qwen3_5_4b_v4_mixed213_seed113/adapter/
```

先在压缩包外核对整个 ZIP：

```bash
sha256sum -c v4_4b_grpo_formal_bundle_v2.sha256
```

解压并进入工作目录后运行：

```bash
unzip -o v4_4b_grpo_formal_bundle_v2.zip
export HF_HUB_CACHE=/data/huggingface-cache
export MODEL_ID=Qwen2/Qwen3.5-4B
export SFT_ADAPTER_PATH=outputs/sft/qwen3_5_4b_v4_mixed213_seed113/adapter
bash scripts/run_v4_company_grpo_formal.sh
```

若 GPU 由调度器分配，请在执行前设置正确的 `CUDA_VISIBLE_DEVICES`。脚本会依次做：

1. 文件哈希与 CPU 测试；
2. SFT 的 custom/native validation；
3. 2-step 4B GRPO smoke；
4. 53-step 正式 4B GRPO；
5. GRPO 后相同的 custom/native validation；
6. 打包 adapter、指标、records 和日志。

任一步骤 OOM、NaN、报错或 smoke 没有真实参数更新，都应停止并保留日志，不要自行
改变学习率、reward、题目、步数或采样参数。脚本拒绝覆盖已有正式 adapter。

完成后只返回：

```text
v4_4b_grpo_formal_results_seed727.tar.gz
```

不要运行 test。test 不在本包中，只有 validation 选定 A 或 C 后才能另行执行一次。
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
    lowered = normalized.lower()
    parts = tuple(part.lower() for part in Path(normalized).parts)
    if normalized.startswith("/") or ".." in parts:
        raise ValueError(f"unsafe archive path: {name}")
    if lowered.startswith("data/") and "test" in Path(lowered).name:
        raise ValueError(f"frozen test data must not enter bundle: {name}")
    if any(part in {".git", ".venv", "outputs", "models", ".cache", "dist"}
           for part in parts):
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
        if manifest.get("formal_grpo_updates") is not True:
            raise ValueError("formal bundle must explicitly enable GRPO updates")
        if manifest.get("validation_included") is not True:
            raise ValueError("formal bundle must include frozen validation")
        if manifest.get("test_included") is not False:
            raise ValueError("formal bundle must exclude frozen test")
        for entry in manifest["files"]:
            payload = archive.read(entry["path"])
            if len(payload) != entry["size_bytes"] or _sha256_bytes(payload) != entry["sha256"]:
                raise ValueError(f"archive entry mismatch: {entry['path']}")


def main() -> int:
    files = _source_files()
    for _, name in files:
        _assert_safe(name)
    expected_hashes = {
        GRPO_DATA_PATH: GRPO_DATA_SHA256,
        SFT_DATA_PATH: SFT_DATA_SHA256,
        VALIDATION_PATH: VALIDATION_SHA256,
    }
    for relative, expected in expected_hashes.items():
        if _sha256_file(ROOT / relative) != expected:
            raise ValueError(f"frozen input hash changed: {relative}")

    data_hashes = "".join(
        f"{digest}  {path}\n" for path, digest in expected_hashes.items()
    ).encode("ascii")
    generated = {
        "GRPO_FORMAL_README_ZH.md": README.encode("utf-8"),
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
        "purpose": "V4 4B frozen outcome-variance GRPO and A-vs-C validation",
        "formal_grpo_updates": True,
        "starting_adapter_included": False,
        "grpo_train_tasks": 53,
        "sft_overlap_tasks": 51,
        "validation_tasks": 64,
        "validation_included": True,
        "test_included": False,
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
        "grpo_train_tasks": 53,
        "sft_overlap_tasks": 51,
        "validation_tasks": 64,
        "test_included": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
