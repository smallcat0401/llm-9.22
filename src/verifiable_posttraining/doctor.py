"""Dependency-light environment diagnostics for a new development machine."""

from __future__ import annotations

import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
from typing import Any


def _distribution_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _nvidia_smi() -> dict[str, Any]:
    executable = shutil.which("nvidia-smi")
    if executable is None:
        return {"available": False, "reason": "nvidia-smi not found"}

    command = [
        executable,
        "--query-gpu=name,memory.total,driver_version",
        "--format=csv,noheader,nounits",
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)
    if completed.returncode != 0:
        return {
            "available": False,
            "reason": completed.stderr.strip() or f"exit code {completed.returncode}",
        }
    devices = []
    for line in completed.stdout.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) == 3:
            devices.append(
                {"name": parts[0], "memory_mib": parts[1], "driver_version": parts[2]}
            )
    return {"available": True, "devices": devices}


def collect_environment() -> dict[str, Any]:
    packages = {
        name: _distribution_version(name)
        for name in (
            "torch",
            "transformers",
            "trl",
            "peft",
            "accelerate",
            "bitsandbytes",
            "datasets",
        )
    }
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "packages": packages,
        "nvidia_smi": _nvidia_smi(),
    }

    try:
        import torch
    except ImportError:
        report["torch_cuda"] = {"available": False, "reason": "torch not installed"}
    else:
        report["torch_cuda"] = {
            "available": torch.cuda.is_available(),
            "torch_cuda_version": torch.version.cuda,
            "device_count": torch.cuda.device_count(),
            "devices": [
                {
                    "index": index,
                    "name": torch.cuda.get_device_name(index),
                    "capability": list(torch.cuda.get_device_capability(index)),
                }
                for index in range(torch.cuda.device_count())
            ],
        }
    return report


def print_environment() -> None:
    print(json.dumps(collect_environment(), ensure_ascii=False, indent=2))

