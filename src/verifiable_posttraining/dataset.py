"""Tier A: deterministic pilot tasks and family-level split validation."""

from __future__ import annotations

import hashlib
import json
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping

from .schemas import Split, Task, TaskKind
from .synthetic_db import PILOT_PRODUCTS, PILOT_REGIONS, PILOT_SALES_ROWS, SALES_SCHEMA


class DatasetValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class FamilySpec:
    family_id: str
    kind: TaskKind
    build: Callable[[int, Split, random.Random], Task]


def _stable_seed(seed: int, namespace: str) -> int:
    digest = hashlib.sha256(f"{seed}:{namespace}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def select_task_window_per_kind(
    tasks: Iterable[Task],
    *,
    offset_per_kind: int = 0,
    limit_per_kind: int = 0,
) -> tuple[Task, ...]:
    """Select a deterministic, disjoint positional window within each task kind.

    The input order is part of the frozen dataset protocol. An offset is applied
    independently to each kind so paired search conditions can be expanded
    without silently reusing the first batch. A zero limit means all remaining
    tasks after the offset.
    """

    if offset_per_kind < 0:
        raise ValueError("offset_per_kind must be non-negative")
    if limit_per_kind < 0:
        raise ValueError("limit_per_kind must be non-negative")
    task_list = list(tasks)
    selected: list[Task] = []
    for kind in (TaskKind.NO_TOOL, TaskKind.CALCULATOR, TaskKind.SQL):
        matching = [task for task in task_list if task.kind is kind]
        stop = offset_per_kind + limit_per_kind if limit_per_kind else None
        selected.extend(matching[offset_per_kind:stop])
    return tuple(selected)


def assign_family_splits(
    family_ids: Iterable[str],
    *,
    seed: int,
) -> dict[str, Split]:
    """Assign sorted unique families to an exact 2/1/1 split per group."""

    families = sorted(set(family_ids))
    if len(families) < 4:
        raise ValueError("at least four families are required for a 2/1/1 split")
    rng = random.Random(seed)
    rng.shuffle(families)
    train_count = len(families) // 2
    remaining = len(families) - train_count
    validation_count = remaining // 2
    mapping: dict[str, Split] = {}
    for index, family_id in enumerate(families):
        if index < train_count:
            split = Split.TRAIN
        elif index < train_count + validation_count:
            split = Split.VALIDATION
        else:
            split = Split.TEST
        mapping[family_id] = split
    return mapping


def _numeric_truth(
    value: float | int,
    *,
    tolerance: float = 1e-6,
) -> dict[str, float | str]:
    return {"type": "number", "value": value, "tolerance": tolerance}


def _task(
    *,
    family_id: str,
    index: int,
    kind: TaskKind,
    split: Split,
    prompt: str,
    value: float | int,
    tolerance: float = 1e-6,
    reference_expression: str | None = None,
    reference_query: str | None = None,
) -> Task:
    metadata: dict[str, object] = {"generator_index": index, "synthetic": True}
    if reference_expression is not None:
        metadata["reference_expression"] = reference_expression
    if reference_query is not None:
        metadata["reference_query"] = reference_query
        metadata["database_fixture"] = "pilot_sales_v1"
    allowed_tools = () if kind is TaskKind.NO_TOOL else (kind.value,)
    return Task(
        task_id=f"{family_id}-{index:03d}",
        family_id=family_id,
        kind=kind,
        split=split,
        prompt=prompt,
        allowed_tools=allowed_tools,
        ground_truth=_numeric_truth(value, tolerance=tolerance),
        metadata=metadata,
    )


def _build_direct_add(index: int, split: Split, rng: random.Random) -> Task:
    del rng
    left, right = 101 + index * 7, 13 + index * 3
    return _task(
        family_id="direct-add-v1",
        index=index,
        kind=TaskKind.NO_TOOL,
        split=split,
        prompt=f"Answer directly without tools: what is {left} + {right}?",
        value=left + right,
    )


def _build_direct_subtract(index: int, split: Split, rng: random.Random) -> Task:
    del rng
    left, right = 500 + index * 11, 17 + index * 2
    return _task(
        family_id="direct-subtract-v1",
        index=index,
        kind=TaskKind.NO_TOOL,
        split=split,
        prompt=f"Answer directly without tools: what is {left} - {right}?",
        value=left - right,
    )


def _build_direct_multiply(index: int, split: Split, rng: random.Random) -> Task:
    del rng
    left, right = 3 + index, 4 + index % 9
    return _task(
        family_id="direct-multiply-v1",
        index=index,
        kind=TaskKind.NO_TOOL,
        split=split,
        prompt=f"Answer directly without tools: what is {left} multiplied by {right}?",
        value=left * right,
    )


def _build_direct_percent(index: int, split: Split, rng: random.Random) -> Task:
    del rng
    total, selected = 80 + index * 20, 8 + index * 2
    value = selected / total * 100
    return _task(
        family_id="direct-percent-v1",
        index=index,
        kind=TaskKind.NO_TOOL,
        split=split,
        prompt=(
            f"Answer directly without tools: {selected} of {total} items were selected. "
            "What percentage was selected?"
        ),
        value=value,
    )


def _build_calculator_revenue(index: int, split: Split, rng: random.Random) -> Task:
    del rng
    units, price = 17 + index * 2, round(3.25 + index * 0.4, 2)
    expression = f"{units} * {price}"
    return _task(
        family_id="calculator-revenue-v1",
        index=index,
        kind=TaskKind.CALCULATOR,
        split=split,
        prompt=f"Use the calculator: compute revenue for {units} units at {price} each.",
        value=units * price,
        reference_expression=expression,
    )


def _build_calculator_change(index: int, split: Split, rng: random.Random) -> Task:
    del rng
    old, new = 40 + index * 3, 50 + index * 5
    expression = f"({new} - {old}) / {old} * 100"
    return _task(
        family_id="calculator-percent-change-v1",
        index=index,
        kind=TaskKind.CALCULATOR,
        split=split,
        prompt=(
            f"Use the calculator: what is the percentage change from {old} to {new}? "
            "You may round the final percentage to two decimal places."
        ),
        value=(new - old) / old * 100,
        # A correctly rounded two-decimal answer differs from the exact value
        # by at most 0.005 percentage points.  The old global 1e-6 tolerance
        # incorrectly rejected conventional answers such as 27.91%.
        tolerance=0.005,
        reference_expression=expression,
    )


def _build_calculator_average(index: int, split: Split, rng: random.Random) -> Task:
    del rng
    values = (10 + index, 20 + index * 2, 30 + index * 3)
    expression = f"({values[0]} + {values[1]} + {values[2]}) / 3"
    return _task(
        family_id="calculator-average-v1",
        index=index,
        kind=TaskKind.CALCULATOR,
        split=split,
        prompt=f"Use the calculator: find the mean of {values[0]}, {values[1]}, and {values[2]}.",
        value=sum(values) / 3,
        reference_expression=expression,
    )


def _build_calculator_discount(index: int, split: Split, rng: random.Random) -> Task:
    del rng
    price, discount = 75 + index * 6, 5 + index % 6 * 5
    expression = f"{price} * (1 - {discount} / 100)"
    return _task(
        family_id="calculator-discount-v1",
        index=index,
        kind=TaskKind.CALCULATOR,
        split=split,
        prompt=(
            f"Use the calculator: compute the final price of {price} after a "
            f"{discount}% discount."
        ),
        value=price * (1 - discount / 100),
        reference_expression=expression,
    )


def _sql_combinations(rng: random.Random) -> list[tuple[str, str]]:
    del rng
    combinations = [
        (region, f"2026-{month:02d}")
        for region in PILOT_REGIONS
        for month in range(1, 13)
    ]
    return combinations


def _build_sql_region_month_revenue(index: int, split: Split, rng: random.Random) -> Task:
    region, month = _sql_combinations(rng)[index]
    matching = [row for row in PILOT_SALES_ROWS if row[1] == month and row[2] == region]
    value = sum(row[4] * row[5] for row in matching)
    query = (
        "SELECT SUM(units * unit_price) FROM sales "
        f"WHERE region = '{region}' AND month = '{month}'"
    )
    return _task(
        family_id="sql-region-month-revenue-v1",
        index=index,
        kind=TaskKind.SQL,
        split=split,
        prompt=f"Schema:\n{SALES_SCHEMA}\nFind total revenue for region '{region}' in {month}.",
        value=value,
        reference_query=query,
    )


def _build_sql_product_month_units(index: int, split: Split, rng: random.Random) -> Task:
    del rng
    combinations = [
        (product, f"2026-{month:02d}")
        for product in PILOT_PRODUCTS
        for month in range(1, 13)
    ]
    product, month = combinations[index]
    value = sum(
        row[4] for row in PILOT_SALES_ROWS if row[1] == month and row[3] == product
    )
    query = (
        "SELECT SUM(units) FROM sales "
        f"WHERE product = '{product}' AND month = '{month}'"
    )
    return _task(
        family_id="sql-product-month-units-v1",
        index=index,
        kind=TaskKind.SQL,
        split=split,
        prompt=f"Schema:\n{SALES_SCHEMA}\nFind units sold for product '{product}' in {month}.",
        value=value,
        reference_query=query,
    )


def _build_sql_region_product_revenue(index: int, split: Split, rng: random.Random) -> Task:
    del rng
    combinations = [
        (region, product, quarter)
        for region in PILOT_REGIONS
        for product in PILOT_PRODUCTS
        for quarter in range(1, 5)
    ]
    region, product, quarter = combinations[index]
    months = {f"2026-{month:02d}" for month in range((quarter - 1) * 3 + 1, quarter * 3 + 1)}
    value = sum(
        row[4] * row[5]
        for row in PILOT_SALES_ROWS
        if row[1] in months and row[2] == region and row[3] == product
    )
    start_month, end_month = min(months), max(months)
    query = (
        "SELECT SUM(units * unit_price) FROM sales "
        f"WHERE region = '{region}' AND product = '{product}' "
        f"AND month BETWEEN '{start_month}' AND '{end_month}'"
    )
    return _task(
        family_id="sql-region-product-quarter-revenue-v1",
        index=index,
        kind=TaskKind.SQL,
        split=split,
        prompt=(
            f"Schema:\n{SALES_SCHEMA}\nFind Q{quarter} revenue for region '{region}' "
            f"and product '{product}'."
        ),
        value=value,
        reference_query=query,
    )


def _build_sql_region_month_average_price(index: int, split: Split, rng: random.Random) -> Task:
    region, month = _sql_combinations(rng)[index]
    prices = [row[5] for row in PILOT_SALES_ROWS if row[1] == month and row[2] == region]
    value = sum(prices) / len(prices)
    query = (
        "SELECT AVG(unit_price) FROM sales "
        f"WHERE region = '{region}' AND month = '{month}'"
    )
    return _task(
        family_id="sql-region-month-average-price-v1",
        index=index,
        kind=TaskKind.SQL,
        split=split,
        prompt=f"Schema:\n{SALES_SCHEMA}\nFind average unit price for '{region}' in {month}.",
        value=value,
        reference_query=query,
    )


_FAMILIES = (
    FamilySpec("direct-add-v1", TaskKind.NO_TOOL, _build_direct_add),
    FamilySpec("direct-subtract-v1", TaskKind.NO_TOOL, _build_direct_subtract),
    FamilySpec("direct-multiply-v1", TaskKind.NO_TOOL, _build_direct_multiply),
    FamilySpec("direct-percent-v1", TaskKind.NO_TOOL, _build_direct_percent),
    FamilySpec("calculator-revenue-v1", TaskKind.CALCULATOR, _build_calculator_revenue),
    FamilySpec("calculator-percent-change-v1", TaskKind.CALCULATOR, _build_calculator_change),
    FamilySpec("calculator-average-v1", TaskKind.CALCULATOR, _build_calculator_average),
    FamilySpec("calculator-discount-v1", TaskKind.CALCULATOR, _build_calculator_discount),
    FamilySpec("sql-region-month-revenue-v1", TaskKind.SQL, _build_sql_region_month_revenue),
    FamilySpec("sql-product-month-units-v1", TaskKind.SQL, _build_sql_product_month_units),
    FamilySpec(
        "sql-region-product-quarter-revenue-v1",
        TaskKind.SQL,
        _build_sql_region_product_revenue,
    ),
    FamilySpec(
        "sql-region-month-average-price-v1",
        TaskKind.SQL,
        _build_sql_region_month_average_price,
    ),
)


def generate_pilot_tasks(*, seed: int = 7, examples_per_family: int = 25) -> tuple[Task, ...]:
    if not 1 <= examples_per_family <= 25:
        raise ValueError("examples_per_family must be between 1 and 25")

    split_by_family: dict[str, Split] = {}
    families_by_kind: dict[TaskKind, list[str]] = defaultdict(list)
    for family in _FAMILIES:
        families_by_kind[family.kind].append(family.family_id)
    for kind, family_ids in families_by_kind.items():
        split_by_family.update(
            assign_family_splits(
                family_ids,
                seed=_stable_seed(seed, kind.value),
            )
        )

    tasks = []
    for family in _FAMILIES:
        rng = random.Random(_stable_seed(seed, family.family_id))
        split = split_by_family[family.family_id]
        for index in range(examples_per_family):
            tasks.append(family.build(index, split, rng))
    validate_task_dataset(tasks)
    return tuple(tasks)


def _prompt_fingerprint(prompt: str) -> str:
    normalized = " ".join(prompt.casefold().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def validate_task_dataset(tasks: Iterable[Task]) -> None:
    task_list = list(tasks)
    if not task_list:
        raise DatasetValidationError("dataset must not be empty")

    task_ids: set[str] = set()
    family_splits: dict[str, Split] = {}
    prompt_splits: dict[str, Split] = {}
    for task in task_list:
        if task.task_id in task_ids:
            raise DatasetValidationError(f"duplicate task_id: {task.task_id}")
        task_ids.add(task.task_id)

        prior_family_split = family_splits.setdefault(task.family_id, task.split)
        if prior_family_split is not task.split:
            raise DatasetValidationError(
                f"family {task.family_id!r} appears in multiple splits"
            )

        fingerprint = _prompt_fingerprint(task.prompt)
        prior_prompt_split = prompt_splits.setdefault(fingerprint, task.split)
        if prior_prompt_split is not task.split:
            raise DatasetValidationError("identical prompt appears in multiple splits")


def dataset_summary(tasks: Iterable[Task]) -> dict[str, Mapping[str, int] | int]:
    task_list = list(tasks)
    return {
        "tasks": len(task_list),
        "families": len({task.family_id for task in task_list}),
        "by_split": dict(Counter(task.split.value for task in task_list)),
        "by_kind": dict(Counter(task.kind.value for task in task_list)),
    }


def write_tasks_jsonl(tasks: Iterable[Task], path: str | Path) -> None:
    """Validate and write canonical task records as UTF-8 JSONL."""

    task_list = list(tasks)
    validate_task_dataset(task_list)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(task.to_dict(), ensure_ascii=False, sort_keys=True)
        for task in task_list
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_tasks_jsonl(path: str | Path) -> tuple[Task, ...]:
    """Load task records and reject malformed or leakage-prone datasets."""

    tasks = []
    input_path = Path(path)
    for line_number, line in enumerate(
        input_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
            if not isinstance(payload, Mapping):
                raise TypeError("task record must be a JSON object")
            tasks.append(Task.from_dict(payload))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise DatasetValidationError(
                f"invalid task record at line {line_number}: {exc}"
            ) from exc
    validate_task_dataset(tasks)
    return tuple(tasks)
