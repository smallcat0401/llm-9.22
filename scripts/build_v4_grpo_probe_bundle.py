"""Build the train-only V4 4B GRPO reward-variance probe bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BUNDLE_NAME = "v4_4b_grpo_probe_bundle_v1"
ZIP_PATH = DIST / f"{BUNDLE_NAME}.zip"
SHA_PATH = DIST / f"{BUNDLE_NAME}.sha256"
DATA_PATH = "data/generated/v4_train_tasks_curated_v2.jsonl"
DATA_SHA256 = "d24a0b360ce7c771d31e05782eabf863a86f43aa349def19a5c0a84ec6423c96"

EXPLICIT_FILES = (
    "AGENTS.md",
    "pyproject.toml",
    "requirements-gpu-win-cu128.lock",
    "configs/grpo_qwen3_5_4b_v4_reward_probe_seed719.toml",
    DATA_PATH,
    "scripts/run_v4_company_grpo_probe.sh",
    "tests/test_grpo_probe.py",
    "tests/test_reward.py",
    "tests/test_native_tool_evaluation.py",
)

IGNORED_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
IGNORED_SUFFIXES = {".pyc", ".pyo", ".safetensors", ".bin", ".pt", ".pth"}

README = """# V4 4B GRPO reward 方差探测包

这个包只做 **train-only、inference-only** 探测：使用现有 epoch 3 adapter，对158道
审核后的训练题各采样8次，执行可信 calculator，并计算与正式GRPO一致的分项reward和
组内方差。它不会反向传播、不会更新adapter，也不包含或读取validation/test。

## 必须放在哪里

请把ZIP解压到此前完成V4 SFT的**同一个项目根目录**，因为脚本默认读取仍保存在公司机器
上的epoch 3 adapter：

```text
outputs/sft/qwen3_5_4b_v4_mixed213_seed113/adapter/
```

示例：

```bash
cd /path/to/existing/v4-training-workspace
unzip -o /path/to/v4_4b_grpo_probe_bundle_v1.zip
sha256sum -c v4_4b_grpo_probe_bundle_v1.data.sha256
```

## 运行

训练结果记录的模型路径是 `Qwen2/Qwen3.5-4B`，脚本将它作为默认本地路径。如果公司
机器实际路径不同，请显式设置；adapter路径同理：

```bash
export HF_HUB_CACHE=/actual/path/to/huggingface-cache
export MODEL_ID=Qwen2/Qwen3.5-4B
export ADAPTER_PATH=outputs/sft/qwen3_5_4b_v4_mixed213_seed113/adapter
bash scripts/run_v4_company_grpo_probe.sh
```

脚本依次运行CPU测试、2题×2次冒烟以及158题×8次完整探测。完整探测可能需要数小时，
过程中可以看到每道题的tool成功数和严格成功数。任何报错都应停止并保留日志，不要自行
改temperature、reward权重、题目或采样次数。

## 返回

完成后只需返回脚本生成的：

```text
v4_4b_grpo_probe_results_seed719.tar.gz
```

不要运行validation/test，也不要开始正式GRPO。返回探测结果后再冻结family平衡的prompt
清单和正式训练配置。
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
    if (
        "/validation" in lowered
        or "validation_" in lowered
        or "/test" in lowered
        or "test_v1.jsonl" in lowered
    ) and lowered.startswith("data/"):
        raise ValueError(f"evaluation data must not enter probe bundle: {name}")
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
            raise ValueError("archive members differ from allowlist")
        manifest = json.loads(archive.read("BUNDLE_MANIFEST.json"))
        if not manifest.get("inference_only") or manifest.get("model_updates"):
            raise ValueError("probe manifest must prohibit model updates")
        if manifest.get("validation_included") or manifest.get("test_included"):
            raise ValueError("evaluation data entered probe bundle")
        for entry in manifest["files"]:
            payload = archive.read(entry["path"])
            if len(payload) != entry["size_bytes"] or _sha256_bytes(payload) != entry["sha256"]:
                raise ValueError(f"archive entry mismatch: {entry['path']}")


def main() -> int:
    files = _source_files()
    for _, name in files:
        _assert_safe(name)
    if _sha256_file(ROOT / DATA_PATH) != DATA_SHA256:
        raise ValueError("frozen V4 train-only probe data hash changed")

    generated = {
        "GRPO_PROBE_README_ZH.md": README.encode("utf-8"),
        f"{BUNDLE_NAME}.data.sha256": f"{DATA_SHA256}  {DATA_PATH}\n".encode("ascii"),
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
        "purpose": "V4 epoch-3 train-only GRPO reward-variance probe",
        "inference_only": True,
        "model_updates": False,
        "train_tasks": 158,
        "samples_per_task": 8,
        "validation_included": False,
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
        "train_tasks": 158,
        "samples_per_task": 8,
        "validation_included": False,
        "test_included": False,
        "model_updates": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
