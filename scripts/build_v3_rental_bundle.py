"""Build the minimal V3 4B rental-GPU training bundle.

This is Tier C packaging glue. The explicit allowlist prevents the archive from
silently absorbing the frozen test set, virtual environment, model cache,
checkpoints, credentials, or unrelated user files.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BUNDLE_NAME = "v3_4b_train_validation_bundle_v1"
ZIP_PATH = DIST / f"{BUNDLE_NAME}.zip"
SHA_PATH = DIST / f"{BUNDLE_NAME}.sha256"

EXPLICIT_FILES = (
    "AGENTS.md",
    "README.md",
    "PROJECT_CONTEXT.md",
    "pyproject.toml",
    "requirements-gpu-win-cu128.lock",
    "configs/sft_qwen3_5_4b_v3_local_smoke_seed113.toml",
    "configs/sft_qwen3_5_4b_v3_search32_seed113.toml",
    "configs/sft_qwen3_5_4b_v3_reference26_seed113.toml",
    "configs/sft_qwen3_5_4b_v3_mixed58_seed113.toml",
    "data/generated/v3_search_discovered_sft_custom_v1.jsonl",
    "data/generated/v3_reference_program_sft_custom_v1.jsonl",
    "data/generated/v3_mixed_sft_custom_v1.jsonl",
    "data/generated/v3_validation_v1.jsonl",
    "docs/DATASETS.md",
    "docs/V3_QLORA_PLAN_ZH.md",
    "docs/V3_EVALUATION_PROTOCOL_ZH.md",
    "docs/V3_SFT_PACKAGE_ZH.md",
    "docs/V3_VALIDATION_BASELINE_ZH.md",
    "artifacts/dataset_manifests/v3_sft_package_custom_v1.json",
    "artifacts/dataset_manifests/v3_evaluation_v1.json",
    "artifacts/metrics/qwen3_5_4b_v3_validation_baseline_v1_seed503.json",
    "scripts/build_v3_rental_bundle.py",
    "scripts/run_v3_rental_training.sh",
    "scripts/run_v3_rental_validation.sh",
)

TREE_ROOTS = ("src", "tests")
IGNORED_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
IGNORED_SUFFIXES = {".pyc", ".pyo", ".safetensors", ".bin", ".pt", ".pth"}

RENTAL_README = """# V3 4B rental-GPU bundle

This archive contains training code, the three reviewed SFT branches, the
frozen validation set, configs, tests, and provenance records.

It deliberately does **not** contain the frozen V3 test set, local `.venv`,
model weights, caches, previous outputs, Git history, or credentials.

## Suggested AutoDL layout

Extract this archive under `/root/autodl-tmp/llm-post-training-main` so model
caches, adapters, and logs remain on the data disk.

## Environment

```bash
cd /root/autodl-tmp/llm-post-training-main
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-gpu-cu128.lock
python -m pip install -e .
export HF_HUB_CACHE=/root/autodl-tmp/huggingface-cache
export TORCH_HOME=/root/autodl-tmp/torch-cache
export TRITON_CACHE_DIR=/root/autodl-tmp/triton-cache
hf download Qwen/Qwen3.5-4B --cache-dir "$HF_HUB_CACHE"
python -m unittest discover -s tests
```

The dependency versions mirror the locally measured CUDA 12.8 environment.
The rental host must still pass the one-step smoke test before formal runs.

The simplest controlled execution is:

```bash
bash scripts/run_v3_rental_training.sh
bash scripts/run_v3_rental_validation.sh
```

The first script stops immediately if the smoke test fails. The second refuses
to run unless all nine expected adapters exist and evaluates validation only.

## One-step rental smoke

```bash
python -m verifiable_posttraining.cli sft-train \
  --config configs/sft_qwen3_5_4b_v3_local_smoke_seed113.toml \
  --cache-dir "$HF_HUB_CACHE"
```

## Formal branches

Run every branch from the same untouched Qwen3.5-4B starting policy:

```bash
python -m verifiable_posttraining.cli sft-train \
  --config configs/sft_qwen3_5_4b_v3_search32_seed113.toml \
  --cache-dir "$HF_HUB_CACHE"

python -m verifiable_posttraining.cli sft-train \
  --config configs/sft_qwen3_5_4b_v3_reference26_seed113.toml \
  --cache-dir "$HF_HUB_CACHE"

python -m verifiable_posttraining.cli sft-train \
  --config configs/sft_qwen3_5_4b_v3_mixed58_seed113.toml \
  --cache-dir "$HF_HUB_CACHE"
```

Do not upload or evaluate the frozen test set until validation has selected one
checkpoint under the preregistered rule in `docs/V3_QLORA_PLAN_ZH.md`.
"""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tree_files(root_name: str) -> list[Path]:
    root = ROOT / root_name
    if not root.is_dir():
        raise FileNotFoundError(root)
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and not any(part in IGNORED_PARTS for part in path.relative_to(ROOT).parts)
        and path.suffix.lower() not in IGNORED_SUFFIXES
    )


def _collect_files() -> list[tuple[Path, str]]:
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
    for root_name in TREE_ROOTS:
        for source in _tree_files(root_name):
            collected[source.relative_to(ROOT).as_posix()] = source
    return [(source, name) for name, source in sorted(collected.items())]


def _assert_safe_archive_name(name: str) -> None:
    normalized = name.replace("\\", "/")
    parts = tuple(part.lower() for part in Path(normalized).parts)
    if normalized.startswith("/") or ".." in parts:
        raise ValueError(f"unsafe archive path: {name}")
    if normalized == "data/generated/v3_test_v1.jsonl":
        raise ValueError("frozen V3 test set must not enter the rental training bundle")
    if any(part in {".git", ".venv", "outputs", "models", ".cache"} for part in parts):
        raise ValueError(f"forbidden directory in rental bundle: {name}")
    if any(part == ".env" or part.endswith((".pem", ".key")) for part in parts):
        raise ValueError(f"possible credential in rental bundle: {name}")
    if Path(normalized).suffix.lower() in IGNORED_SUFFIXES:
        raise ValueError(f"model/checkpoint file in rental bundle: {name}")


def _verify_archive(expected_names: set[str]) -> None:
    with zipfile.ZipFile(ZIP_PATH, "r") as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise ValueError(f"corrupt ZIP member: {bad_member}")
        actual_names = set(archive.namelist())
        if actual_names != expected_names:
            missing = sorted(expected_names - actual_names)
            unexpected = sorted(actual_names - expected_names)
            raise ValueError(f"archive name mismatch; missing={missing}, unexpected={unexpected}")
        for name in actual_names:
            _assert_safe_archive_name(name)
        manifest = json.loads(archive.read("BUNDLE_MANIFEST.json"))
        if manifest.get("frozen_test_included") is not False:
            raise ValueError("bundle manifest must explicitly exclude the frozen test set")
        for entry in manifest.get("files", []):
            name = entry["path"]
            payload = archive.read(name)
            if len(payload) != entry["size_bytes"]:
                raise ValueError(f"size mismatch for {name}")
            if _sha256_bytes(payload) != entry["sha256"]:
                raise ValueError(f"SHA-256 mismatch for {name}")


def main() -> int:
    files = _collect_files()
    for _, archive_name in files:
        _assert_safe_archive_name(archive_name)

    manifest_files = []
    for source, archive_name in files:
        payload = source.read_bytes()
        manifest_files.append(
            {
                "path": archive_name,
                "size_bytes": len(payload),
                "sha256": _sha256_bytes(payload),
            }
        )
    readme_bytes = RENTAL_README.encode("utf-8")
    manifest_files.append(
        {
            "path": "RENTAL_BUNDLE_README_ZH.md",
            "size_bytes": len(readme_bytes),
            "sha256": _sha256_bytes(readme_bytes),
        }
    )
    manifest = {
        "bundle": BUNDLE_NAME,
        "purpose": "V3 4B QLoRA training and validation only",
        "frozen_test_included": False,
        "file_count_excluding_manifest": len(manifest_files),
        "files": manifest_files,
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode(
        "utf-8"
    )

    DIST.mkdir(parents=True, exist_ok=True)
    timestamp = (2026, 10, 5, 0, 0, 0)
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source, archive_name in files:
            info = zipfile.ZipInfo(archive_name, timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, source.read_bytes())
        for archive_name, payload in (
            ("RENTAL_BUNDLE_README_ZH.md", readme_bytes),
            ("BUNDLE_MANIFEST.json", manifest_bytes),
        ):
            _assert_safe_archive_name(archive_name)
            info = zipfile.ZipInfo(archive_name, timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, payload)

    expected_names = {name for _, name in files}
    expected_names.update({"RENTAL_BUNDLE_README_ZH.md", "BUNDLE_MANIFEST.json"})
    _verify_archive(expected_names)
    zip_sha256 = _sha256_file(ZIP_PATH)
    SHA_PATH.write_text(f"{zip_sha256}  {ZIP_PATH.name}\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "zip": str(ZIP_PATH),
                "sha256": zip_sha256,
                "size_bytes": ZIP_PATH.stat().st_size,
                "archive_files": len(files) + 2,
                "frozen_test_included": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
