"""Stage a V4 SFT candidate set without one owner-rejected error-first path.

Tier A: require the exact reviewed source, verify the rejected path really has
an incorrect first calculator call, and preserve every other row unchanged.
This is a candidate derivative, not approval to train on the remaining rows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

from verifiable_posttraining.dataset import load_tasks_jsonl
from verifiable_posttraining.sft_data import write_sft_jsonl
from verifiable_posttraining.tools.calculator import evaluate_expression
from verifiable_posttraining.verifier import verify_numeric_answer


EXCLUDED_TASK_ID = "v4-review-curriculum-v2-required-score-002"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"manifest must be a JSON object: {path}")
    return value


def _read_rows(path: Path) -> tuple[dict[str, Any], ...]:
    rows = tuple(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
                 if line.strip())
    if not rows or any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"invalid SFT candidate file: {path}")
    return rows


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", type=Path,
        default=Path("data/review/v4_manual_zero_pass_v1/v3_v4_search_plus_manual_sft_candidates.jsonl"),
    )
    parser.add_argument(
        "--source-manifest", type=Path,
        default=Path("artifacts/dataset_manifests/v4_manual_zero_pass_v1.json"),
    )
    parser.add_argument(
        "--tasks", type=Path, default=Path("data/generated/v4_train_tasks_curated_v2.jsonl"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("data/review/v4_sft_paths_curated_v1/sft_candidates_213.jsonl"),
    )
    parser.add_argument(
        "--manifest", type=Path,
        default=Path("artifacts/dataset_manifests/v4_sft_paths_curated_v1.json"),
    )
    args = parser.parse_args(argv)

    source_manifest = _read_json(args.source_manifest)
    expected_source = source_manifest["outputs"]["combined_staged_sft"]["sha256"]
    expected_tasks = source_manifest["outputs"]["curated_tasks"]["sha256"]
    if _sha256(args.source) != expected_source or _sha256(args.tasks) != expected_tasks:
        raise ValueError("source hash mismatch: refusing to curate changed inputs")

    rows = _read_rows(args.source)
    if len(rows) != 214:
        raise ValueError("expected exactly 214 staged SFT candidates")
    tasks = {task.task_id: task for task in load_tasks_jsonl(args.tasks)}
    matches = [row for row in rows if row.get("metadata", {}).get("task_id") == EXCLUDED_TASK_ID]
    if len(matches) != 1 or EXCLUDED_TASK_ID not in tasks:
        raise ValueError("the rejected task must occur exactly once")
    rejected = matches[0]
    messages = rejected.get("messages", [])
    if len(messages) != 7 or [message.get("role") for message in messages] != [
        "system", "user", "assistant", "tool", "assistant", "tool", "assistant"
    ]:
        raise ValueError("rejected candidate no longer has the audited two-call sequence")
    first_action = json.loads(messages[2]["content"])
    final_action = json.loads(messages[-1]["content"])
    if first_action.get("type") != "tool_call" or first_action.get("name") != "calculator":
        raise ValueError("rejected candidate no longer starts with a calculator call")
    first_value = evaluate_expression(first_action["arguments"]["expression"])
    truth = tasks[EXCLUDED_TASK_ID].ground_truth
    if verify_numeric_answer(first_value, truth).passed or not verify_numeric_answer(
        final_action.get("answer"), truth
    ).passed:
        raise ValueError("rejected candidate no longer has an incorrect first call and correct final")

    curated = tuple(row for row in rows if row["metadata"]["task_id"] != EXCLUDED_TASK_ID)
    ids = [row["metadata"]["task_id"] for row in curated]
    if len(curated) != 213 or len(set(ids)) != 213:
        raise ValueError("curated SFT candidates need 213 unique task IDs")
    source_counts = dict(Counter(row["metadata"].get("mixture_source") for row in curated))
    if source_counts != {
        "v3-reviewed": 58,
        "v4-search-candidate": 114,
        "v4-manual-zero-pass": 41,
    }:
        raise ValueError("unexpected source mixture after exclusion")
    if any(row["metadata"].get("split") != "train" for row in curated):
        raise ValueError("non-train row in curated SFT candidates")

    if args.output.exists():
        if _read_rows(args.output) != curated:
            raise ValueError(f"refusing to overwrite a different candidate file: {args.output}")
    else:
        write_sft_jsonl(curated, args.output)

    manifest: dict[str, Any] = {
        "dataset": "v4_sft_paths_curated_v1",
        "status": "staged_candidate",
        "train_ready": False,
        "source": str(args.source),
        "source_sha256": expected_source,
        "train_tasks": str(args.tasks),
        "train_tasks_sha256": expected_tasks,
        "original_count": len(rows),
        "excluded_task_id": EXCLUDED_TASK_ID,
        "exclusion_reason": "first calculator call uses an incorrect formula before self-correction",
        "owner_decision": "approved exclusion in conversation; other rows not thereby approved for training",
        "count": len(curated),
        "source_counts": source_counts,
        "output": str(args.output),
        "output_sha256": _sha256(args.output),
    }
    serialized = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if args.manifest.exists():
        if args.manifest.read_text(encoding="utf-8") != serialized:
            raise ValueError(f"refusing to overwrite a different manifest: {args.manifest}")
    else:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
