"""Build a complete V4 4B company-GPU training and validation bundle.

Tier C packaging glue uses an explicit allowlist so frozen test data, model
weights, caches, credentials, prior outputs, and unrelated user files cannot
silently enter the archive.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BUNDLE_NAME = "v4_4b_train_validation_bundle_v1"
ZIP_PATH = DIST / f"{BUNDLE_NAME}.zip"
SHA_PATH = DIST / f"{BUNDLE_NAME}.sha256"

TRAIN_PATH = "data/generated/v4_sft_custom_approved_v1.jsonl"
VALIDATION_PATH = "data/generated/v4_validation_v1.jsonl"
TRAIN_SHA256 = "52c6f559156f3c8655516602e0d4a97431e200539d1bbda5880c890bdef497ad"
VALIDATION_SHA256 = "d62dc47ae7027de67c30521327d5f8afb6b88878ffddfe758843820da9093cf0"

EXPLICIT_FILES = (
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "requirements-gpu-win-cu128.lock",
    "configs/sft_qwen3_5_4b_v4_mixed213_smoke_seed113.toml",
    "configs/sft_qwen3_5_4b_v4_mixed213_seed113.toml",
    TRAIN_PATH,
    VALIDATION_PATH,
    "artifacts/dataset_manifests/v4_sft_custom_approved_v1.json",
    "artifacts/dataset_manifests/v4_validation_v1.json",
    "docs/V4_4B_SFT_PLAN_ZH.md",
    "docs/V4_SFT_PATH_CURATION_ZH.md",
    "scripts/preflight_v4_sft.py",
    "scripts/run_v4_company_training.sh",
    "scripts/run_v4_company_validation.sh",
    "tests/test_calculator.py",
    "tests/test_model_protocol.py",
    "tests/test_sft_training.py",
    "tests/test_verifier.py",
)

IGNORED_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
IGNORED_SUFFIXES = {".pyc", ".pyo", ".safetensors", ".bin", ".pt", ".pth"}

BUNDLE_README = """# V4 4B 公司 GPU 完整运行包

这是一个独立的 V4 训练和 validation 包，不需要覆盖或补丁式修改旧 V3 目录。
建议解压到新目录。它包含 213 条已批准 SFT 数据、64 道冻结 validation、
最新版运行代码、环境锁定文件、冒烟/正式配置、预检与运行脚本。

本包故意不包含 V3/V4 test、模型权重、缓存、旧 adapter、旧输出、Git 历史或凭据。

## 运行含义

训练从同一个 `Qwen/Qwen3.5-4B` instruct 起始策略重新做 QLoRA，不加载 V3
adapter。这不是从随机权重预训练模型。213 条由 58 条 V3 已审轨迹、114 条
V4 搜索轨迹、41 条人工参考轨迹组成；来源标签均保留。

## 解压与校验

```bash
unzip v4_4b_train_validation_bundle_v1.zip -d v4_4b_train_validation_bundle_v1
cd v4_4b_train_validation_bundle_v1
sha256sum -c v4_4b_train_validation_bundle_v1.data.sha256
```

压缩包外层的 `v4_4b_train_validation_bundle_v1.sha256` 用于在解压前校验整个 zip。

## 环境

优先复用公司机器此前已跑通 V3 的 Python 3.11、CUDA 12.8、Transformers、
PEFT 和 bitsandbytes 环境。若确需重建：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-gpu-cu128.lock
python -m pip install -e .
```

设置官方 Qwen3.5-4B 文件所在的 Hugging Face cache。默认脚本使用
`/data/huggingface-cache`；路径不同则先设置：

```bash
export HF_HUB_CACHE=/actual/path/to/huggingface-cache
export PYTHONPATH=src
```

如果公司机器上的官方模型只以普通本地目录存在，而不是 HF cache 结构，请先把
两个 TOML 中的 `model_id` 同步改成同一个绝对目录，并把修改后的配置随结果返还。
不要给冒烟和正式训练使用不同起始权重。

## 顺序

```bash
bash scripts/run_v4_company_training.sh
bash scripts/run_v4_company_validation.sh
```

第一个脚本依次执行数据哈希、重点 CPU 测试、全部 213 条 tokenizer 预检、4 条
冒烟、正式三轮 SFT。任何一步报错即停止。第二个脚本评估起始策略以及 epoch
1/2/3 三个 adapter，只使用 validation。

不要自行调整学习率、训练步数、LoRA 参数或数据。如果出现 OOM、样本超长、
NaN/Inf、路径或依赖错误，停止并保留日志。

## 返还结果

请打包返还：

- `artifacts/metrics/`
- `outputs/logs/v4_company/`
- `outputs/eval/v4_validation_seed613/`
- `outputs/sft/qwen3_5_4b_v4_mixed213_seed113/`
- 实际使用的两个 TOML 配置及 `pip freeze`、`nvidia-smi` 输出

不要运行 test；test 不在包里。checkpoint 只能根据 validation 按
`docs/V4_4B_SFT_PLAN_ZH.md` 的预注册规则选择。
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
    source_root = ROOT / "src"
    for source in sorted(source_root.rglob("*")):
        if (source.is_file()
                and not any(part in IGNORED_PARTS for part in source.relative_to(ROOT).parts)
                and source.suffix.lower() not in IGNORED_SUFFIXES):
            collected[source.relative_to(ROOT).as_posix()] = source
    return [(source, name) for name, source in sorted(collected.items())]


def _assert_safe(name: str) -> None:
    normalized = name.replace("\\", "/")
    lowered = normalized.lower()
    parts = tuple(part.lower() for part in Path(normalized).parts)
    if normalized.startswith("/") or ".." in parts:
        raise ValueError(f"unsafe archive path: {name}")
    if lowered in {
        "data/generated/v3_test_v1.jsonl", "data/generated/v4_test_v1.jsonl"
    } or "/test_v1.jsonl" in lowered:
        raise ValueError(f"frozen test data must not enter bundle: {name}")
    if any(part in {".git", ".venv", "outputs", "models", ".cache", "dist"}
           for part in parts):
        raise ValueError(f"forbidden directory in bundle: {name}")
    if any(part == ".env" or part.endswith((".pem", ".key")) for part in parts):
        raise ValueError(f"possible credential in bundle: {name}")
    if Path(normalized).suffix.lower() in IGNORED_SUFFIXES:
        raise ValueError(f"model/checkpoint file in bundle: {name}")


def _verify_archive(expected_names: set[str]) -> None:
    with zipfile.ZipFile(ZIP_PATH, "r") as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP integrity check failed")
        if set(archive.namelist()) != expected_names:
            raise ValueError("archive members differ from explicit allowlist")
        manifest = json.loads(archive.read("BUNDLE_MANIFEST.json"))
        if manifest.get("frozen_test_included") is not False:
            raise ValueError("manifest must exclude frozen test")
        for entry in manifest["files"]:
            payload = archive.read(entry["path"])
            if len(payload) != entry["size_bytes"] or _sha256_bytes(payload) != entry["sha256"]:
                raise ValueError(f"archive entry mismatch: {entry['path']}")
        data_hashes = archive.read(f"{BUNDLE_NAME}.data.sha256").decode("ascii")
        if f"{TRAIN_SHA256}  {TRAIN_PATH}" not in data_hashes:
            raise ValueError("training data hash missing from bundle")
        if f"{VALIDATION_SHA256}  {VALIDATION_PATH}" not in data_hashes:
            raise ValueError("validation hash missing from bundle")


def main() -> int:
    files = _source_files()
    for _, name in files:
        _assert_safe(name)
    if _sha256_file(ROOT / TRAIN_PATH) != TRAIN_SHA256:
        raise ValueError("approved training data hash changed")
    if _sha256_file(ROOT / VALIDATION_PATH) != VALIDATION_SHA256:
        raise ValueError("frozen validation hash changed")

    data_hashes = (
        f"{TRAIN_SHA256}  {TRAIN_PATH}\n"
        f"{VALIDATION_SHA256}  {VALIDATION_PATH}\n"
    ).encode("ascii")
    generated = {
        "RENTAL_BUNDLE_README_ZH.md": BUNDLE_README.encode("utf-8"),
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
        "purpose": "V4 4B QLoRA SFT from starting policy and validation only",
        "frozen_test_included": False,
        "training_examples": 213,
        "validation_tasks": 64,
        "file_count_excluding_manifest": len(entries),
        "files": entries,
    }
    generated["BUNDLE_MANIFEST.json"] = (
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")

    DIST.mkdir(parents=True, exist_ok=True)
    timestamp = (2026, 10, 6, 0, 0, 0)
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
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

    expected = {name for _, name in files} | set(generated)
    _verify_archive(expected)
    zip_hash = _sha256_file(ZIP_PATH)
    SHA_PATH.write_text(f"{zip_hash}  {ZIP_PATH.name}\n", encoding="utf-8")
    print(json.dumps({
        "zip": str(ZIP_PATH),
        "sha256": zip_hash,
        "size_bytes": ZIP_PATH.stat().st_size,
        "archive_files": len(expected),
        "training_examples": 213,
        "validation_tasks": 64,
        "frozen_test_included": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
