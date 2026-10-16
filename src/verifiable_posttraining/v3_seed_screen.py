"""Build the reviewed V3 seed screen before any large-scale generation.

The screen combines three deliberately labelled sources:

* reviewed public finance/table questions from the immutable audit JSONL;
* two deterministic examples from each synthetic calculator-curriculum-v2 family;
* a fresh GSM8K-train subset that excludes every source question used by prior
  search or validation artifacts.

This module creates search inputs, not SFT data.  ``training_eligible`` is
metadata only; a successful rollout still has to pass outcome verification and
later trajectory-quality checks before it can become a training example.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .calculator_curriculum import generate_calculator_curriculum_v2
from .dataset import dataset_summary, validate_task_dataset, write_tasks_jsonl
from .public_eval import (
    extract_gsm8k_final_answer,
    load_gsm8k_jsonl,
    select_frozen_subset,
)
from .schemas import Split, Task, TaskKind


PUBLIC_EXCLUSIONS = {
    "74bc19b4-b4f2-474d-8800-7d645ea59a8f",
    "529497d1-cff1-4784-bc46-2c6a6839ca20",
    "RCL/2009/page_90.pdf-1",
}

# The reviewed A versions retain the source's arithmetic-mean interpretation.
# The B versions ask for CAGR and are no-tool because the bounded calculator
# intentionally does not implement exponentiation or roots.
CAGR_VARIANTS: Mapping[str, tuple[str, float]] = {
    "28b7f2b6-f15a-4390-b42c-310d7e727e14": (
        "What was the compound annual growth rate (CAGR) of total net revenue "
        "from 2017 to 2019? Return a percentage rounded to two decimal places.",
        15.16,
    ),
    "8ade1eac-5a92-41bd-8b03-a74ae2769a6f": (
        "What was the compound annual growth rate (CAGR) of research and "
        "development expense from 2017 to 2019? Return a percentage rounded "
        "to two decimal places.",
        27.75,
    ),
    "072b176c-a53e-4e12-97e6-b129ceb92da9": (
        "What was the compound annual growth rate (CAGR) of additions and "
        "adjustments from 2017 to 2019? Return a percentage rounded to two "
        "decimal places.",
        -62.60,
    ),
    "8fb16496-4bed-4e19-b230-a83de9ee6a59": (
        "What was the compound annual growth rate (CAGR) of Food Care carrying "
        "value from 2017 to 2019? Return a percentage rounded to two decimal places.",
        0.09,
    ),
}

QUESTION_OVERRIDES: Mapping[str, str] = {
    "af742fab-b68a-43ac-bb2b-77ef9f2fdbdf": (
        "Compute the 2018-2019 average income-tax expense minus the 2017-2018 "
        "average income-tax expense. Report a positive result for an increase "
        "and a negative result for a decrease."
    ),
    "27c35832-3665-49c5-98df-e669b51effaf": (
        "Parentheses denote liabilities. Using the absolute liability amounts, "
        "what was the percentage change in unfunded obligations from 2018 to "
        "2019? Report an increase as positive and a decrease as negative."
    ),
    "858940e9-21f1-45db-acf2-21f298e367e5": (
        "Parentheses denote expenses. Using the absolute expense amounts, what "
        "was the percentage change in interest expense from 2017 to 2018? "
        "Report an increase as positive and a decrease as negative."
    ),
    "bc009826-d4f1-4c53-9e3c-0e6349e8b527": (
        "Parentheses denote costs. Using the absolute cost amounts, what was the "
        "percentage change in warranty costs incurred from 2018 to 2019? Report "
        "an increase as positive and a decrease as negative."
    ),
    "a018d9b5-a8ed-4b3d-b4cb-7fdf8692b17c": (
        "For fiscal 2018 and 2019, what is the arithmetic mean of the four "
        "amendment amounts shown for pension benefits and other benefits?"
    ),
    "b11bd2c7-36da-437a-af89-face31263fee": (
        "Treat each dash in the table as zero expense. What is the average rent "
        "expense related to build-to-suit facilities from 2015 through 2019?"
    ),
    "b160a76e-1ecf-4b21-9741-846d837e37f8": (
        "For fiscal 2019, what is the ratio of the total value of RSUs granted "
        "to the total value of RSUs settled?"
    ),
    "7b071ea4-9b6f-42cd-b50b-71f0845d4ce8": (
        "What was the dividend payout ratio for the year ended June 2018? Here, "
        "dividend payout ratio means total common dividends divided by net "
        "income available for dividends."
    ),
    "0ccce335-dd41-498d-938a-cf526b7f6357": (
        "Treat the dash in the table as zero. After aggregating the operating "
        "profit of all listed businesses within each year, what was the "
        "percentage change in total operating profit from 2017 to 2018?"
    ),
    "MRO/2009/page_137.pdf-3": (
        "Using the weighted-average grant-date fair values, what was the "
        "percentage change in the total value of unvested restricted stock "
        "awards from 2008 to 2009? Report an increase as positive and a decrease "
        "as negative."
    ),
    "BLK/2015/page_123.pdf-2": (
        "The 2022 notes pay about $25 million of interest per year in two equal "
        "payments. Payments run from December 1, 2012 through December 1, 2022, "
        "inclusive of both dates. How much total interest is paid, in millions "
        "of dollars?"
    ),
    "IPG/2014/page_37.pdf-1": (
        "Using a combined 2013-and-2014 basis, what percentage of total debt was "
        "long-term debt?"
    ),
}


def _read_jsonl(path: str | Path) -> tuple[Mapping[str, Any], ...]:
    rows = []
    for line_number, line in enumerate(
        Path(path).read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, Mapping):
            raise ValueError(f"JSONL row {line_number} in {path} must be an object")
        rows.append(value)
    return tuple(rows)


def _table_rows(row: Mapping[str, Any]) -> Sequence[Sequence[Any]]:
    context = row.get("context", {})
    if not isinstance(context, Mapping):
        return ()
    table = context.get("table", [])
    if isinstance(table, Mapping):
        table = table.get("table", [])
    if not isinstance(table, list):
        return ()
    return tuple(item for item in table if isinstance(item, list))


def _render_table(rows: Sequence[Sequence[Any]]) -> str:
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    normalized = [
        [str(row[index]) if index < len(row) else "" for index in range(width)]
        for row in rows
    ]

    def render(row: Sequence[str]) -> str:
        return "| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |"

    return "\n".join(
        [render(normalized[0]), render(["---"] * width)]
        + [render(row) for row in normalized[1:]]
    )


def _public_prompt(row: Mapping[str, Any], question: str) -> str:
    parts = [
        "Use the calculator when arithmetic is needed. Return the final number.",
        "",
        question.strip(),
    ]
    table = _render_table(_table_rows(row))
    if table:
        parts.extend(("", "Source table:", table))
    context = row.get("context", {})
    evidence = context.get("gold_evidence", {}) if isinstance(context, Mapping) else {}
    if isinstance(evidence, Mapping) and evidence:
        parts.extend(("", "Relevant source text:"))
        parts.extend(str(value) for value in evidence.values())
    return "\n".join(parts)


def build_reviewed_public_tasks(
    rows: Iterable[Mapping[str, Any]],
) -> tuple[Task, ...]:
    tasks = []
    for row in rows:
        source_id = str(row["source_id"])
        if source_id in PUBLIC_EXCLUSIONS:
            continue
        question = QUESTION_OVERRIDES.get(source_id, str(row["question"]))
        ground_truth = dict(row["ground_truth"])
        # Public answers are generally reported to two decimals (or fewer).
        ground_truth["tolerance"] = 0.005
        common_metadata = {
            "seed_screen_group": "reviewed_public",
            "source_dataset": row["source_dataset"],
            "source_split": row["source_split"],
            "source_id": source_id,
            "relation_family": row["relation_family"],
            "reference_derivation": row["reference_derivation"],
            "review_artifact": "v3_public_seed_audit_v0",
            "training_eligible": True,
        }
        slug = hashlib.sha256(source_id.encode("utf-8")).hexdigest()[:12]
        tasks.append(
            Task(
                task_id=f"v3-public-{slug}-arithmetic",
                family_id=f"v3-public-{row['relation_family']}-v1",
                kind=TaskKind.CALCULATOR,
                split=Split.TRAIN,
                prompt=_public_prompt(row, question),
                allowed_tools=("calculator",),
                ground_truth=ground_truth,
                metadata={**common_metadata, "review_variant": "arithmetic"},
            )
        )
        if source_id in CAGR_VARIANTS:
            cagr_question, cagr_value = CAGR_VARIANTS[source_id]
            tasks.append(
                Task(
                    task_id=f"v3-public-{slug}-cagr",
                    family_id="v3-public-cagr-v1",
                    kind=TaskKind.NO_TOOL,
                    split=Split.TRAIN,
                    prompt=_public_prompt(row, cagr_question).replace(
                        "Use the calculator when arithmetic is needed.",
                        "Solve without tools.",
                    ),
                    allowed_tools=(),
                    ground_truth={
                        "type": "number",
                        "value": cagr_value,
                        "tolerance": 0.005,
                    },
                    metadata={
                        **common_metadata,
                        "review_variant": "cagr",
                        "training_eligible": False,
                        "diagnostic_only_reason": "bounded calculator has no root operator",
                    },
                )
            )
    if len(tasks) != 31:
        raise ValueError(f"expected 31 reviewed public variants, found {len(tasks)}")
    return tuple(tasks)


def build_self_written_tasks() -> tuple[Task, ...]:
    tasks = []
    for task in generate_calculator_curriculum_v2(examples_per_family=2):
        historical_split = task.split
        metadata = dict(task.metadata)
        metadata.update(
            {
                "seed_screen_group": "self_written_v2",
                "historical_split": historical_split.value,
                "training_eligible": historical_split is Split.TRAIN,
            }
        )
        if historical_split is not Split.TRAIN:
            metadata["diagnostic_only_reason"] = (
                "historical validation/test family must not become training data"
            )
        tasks.append(
            replace(
                task,
                task_id=f"v3-screen-{task.task_id}",
                split=Split.TRAIN,
                metadata=metadata,
            )
        )
    if len(tasks) != 20:
        raise ValueError(f"expected 20 self-written seeds, found {len(tasks)}")
    return tuple(tasks)


def excluded_gsm8k_indices(paths: Iterable[str | Path]) -> set[int]:
    excluded: set[int] = set()
    for path in paths:
        for row in _read_jsonl(path):
            task = row.get("task", row)
            if not isinstance(task, Mapping):
                continue
            metadata = task.get("metadata", {})
            if not isinstance(metadata, Mapping):
                continue
            if metadata.get("source_dataset") == "openai/grade-school-math":
                source_index = metadata.get("source_index")
                if source_index is not None:
                    excluded.add(int(source_index))
    return excluded


def build_fresh_gsm8k_tasks(
    records: Iterable[Mapping[str, Any]],
    *,
    excluded_source_indices: Iterable[int],
    sample_size: int = 20,
    seed: int = 211,
) -> tuple[Task, ...]:
    selected = select_frozen_subset(
        records,
        sample_size=sample_size,
        seed=seed,
        excluded_source_indices=excluded_source_indices,
    )
    tasks = []
    for record in selected:
        source_index = int(record["source_index"])
        answer = extract_gsm8k_final_answer(str(record["answer"]))
        tasks.append(
            Task(
                task_id=f"v3-gsm8k-train-{source_index:04d}-calculator",
                family_id="v3-gsm8k-public-train-calculator-v1",
                kind=TaskKind.CALCULATOR,
                split=Split.TRAIN,
                prompt=(
                    "Solve this problem. The calculator tool is available for arithmetic. "
                    "Return the final number.\n\n"
                    f"{str(record['question']).strip()}"
                ),
                allowed_tools=("calculator",),
                ground_truth={"type": "number", "value": answer, "tolerance": 1e-6},
                metadata={
                    "seed_screen_group": "fresh_gsm8k_train",
                    "source_dataset": "openai/grade-school-math",
                    "source_split": "train",
                    "source_index": source_index,
                    "subset_seed": seed,
                    "training_eligible": True,
                },
            )
        )
    return tuple(tasks)


def build_v3_seed_screen(
    *,
    public_rows: Iterable[Mapping[str, Any]],
    gsm8k_records: Iterable[Mapping[str, Any]],
    excluded_source_indices: Iterable[int],
    gsm8k_seed: int = 211,
) -> tuple[Task, ...]:
    tasks = (
        *build_reviewed_public_tasks(public_rows),
        *build_self_written_tasks(),
        *build_fresh_gsm8k_tasks(
            gsm8k_records,
            excluded_source_indices=excluded_source_indices,
            seed=gsm8k_seed,
        ),
    )
    validate_task_dataset(tasks)
    if len(tasks) != 71:
        raise ValueError(f"expected 71 V3 seed-screen tasks, found {len(tasks)}")
    return tuple(tasks)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-audit", required=True, type=Path)
    parser.add_argument("--gsm8k-train", required=True, type=Path)
    parser.add_argument("--exclude-artifact", action="append", default=[], type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--gsm8k-seed", type=int, default=211)
    args = parser.parse_args(argv)

    excluded = excluded_gsm8k_indices(args.exclude_artifact)
    tasks = build_v3_seed_screen(
        public_rows=_read_jsonl(args.public_audit),
        gsm8k_records=load_gsm8k_jsonl(args.gsm8k_train),
        excluded_source_indices=excluded,
        gsm8k_seed=args.gsm8k_seed,
    )
    write_tasks_jsonl(tasks, args.output)
    manifest = {
        "dataset": "v3_seed_screen_v1",
        "purpose": "pre-generation starting-policy search-gap screen",
        "not_sft_data": True,
        "gsm8k_subset_seed": args.gsm8k_seed,
        "prior_gsm8k_source_indices_excluded": len(excluded),
        "summary": dataset_summary(tasks),
        "by_group": {
            group: sum(task.metadata.get("seed_screen_group") == group for task in tasks)
            for group in (
                "reviewed_public",
                "self_written_v2",
                "fresh_gsm8k_train",
            )
        },
        "training_eligible": sum(
            task.metadata.get("training_eligible") is True for task in tasks
        ),
        "diagnostic_only": sum(
            task.metadata.get("training_eligible") is False for task in tasks
        ),
        "source_files": {
            "public_audit": str(args.public_audit),
            "public_audit_sha256": _sha256(args.public_audit),
            "gsm8k_train": str(args.gsm8k_train),
            "gsm8k_train_sha256": _sha256(args.gsm8k_train),
            "excluded_artifacts": [str(path) for path in args.exclude_artifact],
        },
        "output_sha256": _sha256(args.output),
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
