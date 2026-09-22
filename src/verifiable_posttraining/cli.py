"""Small command-line entry point for repository smoke checks."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from .doctor import print_environment
from .schemas import Task, demo_task


def _schema_demo() -> None:
    original = demo_task()
    payload = original.to_dict()
    restored = Task.from_dict(payload)
    if original != restored:
        raise RuntimeError("task JSON round trip changed the task")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vpt")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor", help="print Python, package, and NVIDIA GPU information")
    subparsers.add_parser("schema-demo", help="validate and print a minimal task fixture")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        print_environment()
    elif args.command == "schema-demo":
        _schema_demo()
    else:  # pragma: no cover - argparse prevents this path.
        raise AssertionError(f"unexpected command: {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

