"""Build the one-task V3 rounding follow-up screen without mutating V3 v1."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Iterable, Sequence

from .dataset import dataset_summary, load_tasks_jsonl, write_tasks_jsonl
from .schemas import Task


SOURCE_TASK_ID = "v3-public-ab005e597c33-arithmetic"
REVISED_TASK_ID = f"{SOURCE_TASK_ID}-rounding-revised-v1"
REVISION_SET = "v3_rounding_followup_v1"


def build_rounding_followup_task(tasks: Iterable[Task]) -> Task:
    """Create one auditable prompt revision that makes GT rounding explicit."""

    matches = [task for task in tasks if task.task_id == SOURCE_TASK_ID]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one source task {SOURCE_TASK_ID!r}")
    source = matches[0]
    if source.metadata.get("training_eligible") is not True:
        raise ValueError("rounding follow-up source must be training-eligible")

    prompt_parts = source.prompt.split("\n\n")
    if len(prompt_parts) < 2:
        raise ValueError("source prompt must contain an instruction and question")
    prompt_parts[1] = (
        f"{prompt_parts[1].strip()} Round the percentage to one decimal place."
    )
    metadata = dict(source.metadata)
    metadata.update(
        {
            "revision_set": REVISION_SET,
            "revision_of_task_id": SOURCE_TASK_ID,
            "revision_reason": "make the one-decimal ground-truth convention explicit",
            "requires_fresh_search": True,
        }
    )
    return replace(
        source,
        task_id=REVISED_TASK_ID,
        prompt="\n\n".join(prompt_parts),
        metadata=metadata,
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args(argv)

    task = build_rounding_followup_task(load_tasks_jsonl(args.input))
    write_tasks_jsonl((task,), args.output)
    manifest = {
        "dataset": REVISION_SET,
        "purpose": "single-task rounding clarification before SFT attribution",
        "not_sft_data": True,
        "source_dataset": str(args.input),
        "source_sha256": _sha256(args.input),
        "summary": dataset_summary((task,)),
        "output_sha256": _sha256(args.output),
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
