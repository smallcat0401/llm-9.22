"""Build the reviewed 11-task V3 revision screen without mutating frozen V3.

The source tasks are the eleven ambiguous or label-misaligned 0/8 tasks found
in ``v3_seed_screen_v1``.  This module changes only their wording (and one
sign-convention label) according to the Chinese audit.  The resulting tasks
must be searched again before any reference trajectory is written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .dataset import dataset_summary, load_tasks_jsonl, write_tasks_jsonl
from .schemas import Task


REVISION_SET = "v3_zero_pass_revisions_v2"


# Wording defines the requested quantity but deliberately does not include a
# worked formula.  ``ground_truth_value`` is present only where the reviewed
# wording changes the label semantics.
REVISIONS: Mapping[str, Mapping[str, Any]] = {
    "v3-public-13b99cafff24-arithmetic": {
        "question": (
            "What is the arithmetic mean of the two year-on-year percentage "
            "changes in Additions and adjustments for 2017-2018 and 2018-2019? "
            "Return a percentage rounded to two decimal places."
        ),
        "reason": "distinguish percentage-change AAGR from an amount change",
    },
    "v3-public-564f2d6051c0-arithmetic": {
        "question": (
            "What is the arithmetic mean of the two year-on-year percentage "
            "changes in research and development expense for 2017-2018 and "
            "2018-2019? Return a percentage rounded to two decimal places."
        ),
        "reason": "distinguish percentage growth from an amount increase",
    },
    "v3-public-776305a10cc6-arithmetic": {
        "question": (
            "What is the arithmetic mean of the 2017-2018 and 2018-2019 "
            "year-on-year percentage changes in Food Care carrying value? "
            "Return a percentage rounded to two decimal places."
        ),
        "reason": "distinguish arithmetic-mean growth from CAGR",
    },
    "v3-public-993d968c025a-arithmetic": {
        "question": (
            "From the 2017-2018 period to the 2018-2019 period, by how much did "
            "the two-year average revenue change? Report an increase as positive "
            "and a decrease as negative."
        ),
        "reason": "define an amount difference and its direction",
    },
    "v3-public-9f547636b5b4-arithmetic": {
        "question": (
            "Parentheses identify rent expense amounts, and each dash means zero. "
            "What was the average annual rent expense related to build-to-suit "
            "facilities from 2015 through 2019?"
        ),
        "ground_truth_value": 1053.4,
        "reason": "treat an expense amount as a positive magnitude",
    },
    "v3-public-abe2824b6e81-arithmetic": {
        "question": (
            "Interest-rate swap agreements have a notional amount of $79.9 "
            "million and rates ranging from 5.74% to 7.83%. Using the midpoint "
            "of that rate range, what is the estimated annual interest expense "
            "in millions of dollars? Round to one decimal place."
        ),
        "reason": "restore the missing rate range and define rounding",
    },
    "v3-public-ea79960b2b5e-arithmetic": {
        "question": (
            "Taking the number of shares purchased in each month into account, "
            "what was Accenture's share-count-weighted average price per share "
            "across June and July 2019?"
        ),
        "reason": "distinguish a transaction-weighted average from a simple mean",
    },
    "v3-public-f5fdb156cd45-arithmetic": {
        "question": (
            "From the 2017-2018 period to the 2018-2019 period, by how much did "
            "the two-year average net cash flow from operating activities change? "
            "Report an increase as positive and a decrease as negative."
        ),
        "reason": "define direction without embedding the solution procedure",
    },
    "v3-gsm8k-train-1213-calculator": {
        "question": (
            "Lyssa and Precious took an English proficiency exam. Lyssa answered "
            "20% of the items incorrectly. Precious made 12 mistakes. If the exam "
            "had 75 items, how many fewer correct answers did Lyssa get than Precious?"
        ),
        "reason": "align the comparison direction with the positive label",
    },
    "v3-gsm8k-train-2706-calculator": {
        "question": (
            "A leaf is blown forward five feet and then backward two feet by each "
            "swirling gust. After 11 gusts, how many feet ahead of its starting "
            "point is the leaf?"
        ),
        "reason": "ask for net displacement rather than ambiguous distance traveled",
    },
    "v3-gsm8k-train-5285-calculator": {
        "question": (
            "The number of trees in a courtyard is four times the number of stones. "
            "The number of birds in the trees is twice the combined number of trees "
            "and stones. If there are 40 stones, how many birds are in the trees?"
        ),
        "reason": "replace the ambiguous phrase 'three times more than'",
    },
}


def _replace_question(prompt: str, question: str) -> str:
    parts = prompt.split("\n\n")
    if len(parts) < 2:
        raise ValueError("source prompt must contain an instruction and a question")
    parts[1] = question.strip()
    return "\n\n".join(parts)


def build_revised_zero_pass_tasks(tasks: Iterable[Task]) -> tuple[Task, ...]:
    """Select and revise exactly the eleven audited source tasks.

    Invariants:

    * every expected frozen task must be present exactly once;
    * only predeclared training-eligible tasks can enter this re-screen;
    * source family IDs stay unchanged so later split checks still treat each
      revision as the same semantic family as its frozen predecessor;
    * task IDs change, preventing accidental metric/trajectory overwrite.
    """

    by_id: dict[str, Task] = {}
    for task in tasks:
        if task.task_id in by_id:
            raise ValueError(f"duplicate source task id: {task.task_id}")
        by_id[task.task_id] = task

    missing = sorted(set(REVISIONS) - set(by_id))
    if missing:
        raise ValueError(f"missing audited source tasks: {missing}")

    revised = []
    for source_task_id, revision in REVISIONS.items():
        source = by_id[source_task_id]
        if source.metadata.get("training_eligible") is not True:
            raise ValueError(f"revised task is not training-eligible: {source_task_id}")
        ground_truth = dict(source.ground_truth)
        if "ground_truth_value" in revision:
            ground_truth["value"] = revision["ground_truth_value"]
        metadata = dict(source.metadata)
        metadata.update(
            {
                "revision_set": REVISION_SET,
                "revision_of_task_id": source_task_id,
                "revision_reason": revision["reason"],
                "requires_fresh_search": True,
            }
        )
        revised.append(
            replace(
                source,
                task_id=f"{source_task_id}-revised-v2",
                prompt=_replace_question(source.prompt, str(revision["question"])),
                ground_truth=ground_truth,
                metadata=metadata,
            )
        )
    return tuple(revised)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args(argv)

    tasks = build_revised_zero_pass_tasks(load_tasks_jsonl(args.input))
    write_tasks_jsonl(tasks, args.output)
    manifest = {
        "dataset": REVISION_SET,
        "purpose": "wording-corrected Best-of-8 re-screen before trajectory writing",
        "not_sft_data": True,
        "source_dataset": str(args.input),
        "source_sha256": _sha256(args.input),
        "summary": dataset_summary(tasks),
        "revised_task_count": len(tasks),
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
