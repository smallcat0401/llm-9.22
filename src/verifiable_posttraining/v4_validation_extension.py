"""Tier A candidates that balance the four public V3 validation families.

The frozen V3 validation set has eight family IDs: four self-written families
with eight rows each and four public families with one row each.  This module
creates seven new synthetic rows for each public family so a later, separately
approved V4 validation set can contain eight rows per family.

These outputs are audit candidates only.  They remain evaluation-only,
pending, and ineligible for training until explicitly approved and frozen.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Callable

from .dataset import validate_task_dataset
from .schemas import Split, Task, TaskKind
from .tools.calculator import calculator
from .verifier import verify_numeric_answer


V4_VALIDATION_PUBLIC_FAMILIES: dict[str, str] = {
    "v3-eval-val-public-ratio-allocation-v1": "v3-eval-val-gsm8k-6154",
    "v3-eval-val-public-weighted-demand-v1": "v3-eval-val-gsm8k-0839",
    "v3-eval-val-public-population-flow-v1": "v3-eval-val-gsm8k-4495",
    "v3-eval-val-public-tank-loss-recovery-v1": "v3-eval-val-gsm8k-4967",
}


@dataclass(frozen=True, slots=True)
class ValidationExtensionRecord:
    task: Task
    question_zh: str


@dataclass(frozen=True, slots=True)
class _Variant:
    question_en: str
    question_zh: str
    expression: str
    parameters: dict[str, Any]
    subtype: str


_Builder = Callable[[random.Random, int], _Variant]


def _rng_for(seed: int, family_id: str, index: int) -> random.Random:
    material = f"{seed}:{family_id}:{index}".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(material).digest()[:8], "big"))


_FRACTION_EN = {
    (1, 2): "one half",
    (1, 3): "one third",
    (1, 4): "one quarter",
    (2, 5): "two fifths",
}

_FRACTION_ZH = {
    (1, 2): "二分之一",
    (1, 3): "三分之一",
    (1, 4): "四分之一",
    (2, 5): "五分之二",
}


def _ratio_allocation(_: random.Random, index: int) -> _Variant:
    configs = (
        (96, 1, 2, 1, 2, 3, 1),
        (120, 1, 3, 1, 2, 2, 1),
        (144, 1, 2, 1, 3, 3, 1),
        (180, 2, 5, 1, 2, 2, 1),
        (200, 1, 4, 1, 2, 3, 2),
        (210, 2, 5, 1, 2, 3, 1),
        (240, 1, 3, 1, 4, 4, 3),
    )
    total, a_num, a_den, c_num, c_den, d_ratio, e_ratio = configs[index]
    a_fraction_en = _FRACTION_EN[(a_num, a_den)]
    a_fraction_zh = _FRACTION_ZH[(a_num, a_den)]
    c_fraction_en = _FRACTION_EN[(c_num, c_den)]
    c_fraction_zh = _FRACTION_ZH[(c_num, c_den)]
    questions = (
        (
            f"A catalog contains {total} records. Category A contains {a_fraction_en} of all "
            f"records, and category C contains {c_fraction_en} as many records as category A. "
            f"All remaining records are assigned to D and E in a {d_ratio}:{e_ratio} ratio. "
            "How many records are assigned to D?",
            f"一个目录共有 {total} 条记录。A类占全部记录的{a_fraction_zh}，C类记录数是A类的"
            f"{c_fraction_zh}。其余记录按 {d_ratio}:{e_ratio} 分给D类和E类。D类有多少条记录？",
        ),
        (
            f"A warehouse labels {total} packages with A, C, D, or E. A labels account for "
            f"{a_fraction_en} of all packages, while C has {c_fraction_en} the number of A. "
            f"The rest are split between D and E in the ratio {d_ratio}:{e_ratio}. How many "
            "packages receive label D?",
            f"仓库要给 {total} 个包裹标记A、C、D或E。A类占全部包裹的{a_fraction_zh}，C类数量"
            f"是A类的{c_fraction_zh}。剩余包裹按 {d_ratio}:{e_ratio} 分到D类和E类。D类有多少个？",
        ),
    )
    question_en, question_zh = questions[index % 2]
    a_expression = f"{total}*{a_num}/{a_den}"
    c_expression = f"({a_expression})*{c_num}/{c_den}"
    remainder = f"({total}-({a_expression})-({c_expression}))"
    expression = f"{remainder}*{d_ratio}/({d_ratio}+{e_ratio})"
    return _Variant(
        question_en,
        question_zh,
        expression,
        {
            "total": total,
            "a_fraction": (a_num, a_den),
            "c_of_a_fraction": (c_num, c_den),
            "d_to_e_ratio": (d_ratio, e_ratio),
        },
        "nested_remainder_ratio_allocation",
    )


def _weighted_demand(rng: random.Random, index: int) -> _Variant:
    profiles = (
        ((1, 2), (1, 1), (3, 2), (2, 1)),
        ((1, 2), (1, 1), (2, 1), (3, 2)),
        ((1, 1), (3, 2), (2, 1), (1, 2)),
    )
    weights = profiles[index % len(profiles)]
    counts = tuple(2 * rng.randint(12, 70) for _ in range(4))
    reserve = rng.randint(8, 30)
    units_per_portion = rng.randint(2, 5)
    portion_en = {
        (1, 2): "half a portion",
        (1, 1): "one portion",
        (3, 2): "one and a half portions",
        (2, 1): "two portions",
    }
    portion_zh = {
        (1, 2): "半份",
        (1, 1): "1份",
        (3, 2): "1.5份",
        (2, 1): "2份",
    }
    groups_en = ("Group A", "Group B", "Group C", "Group D")
    groups_zh = ("A组", "B组", "C组", "D组")
    details_en = ", ".join(
        f"{counts[i]} people in {groups_en[i]} need {portion_en[weights[i]]} each"
        for i in range(4)
    )
    details_zh = "，".join(
        f"{groups_zh[i]}有{counts[i]}人且每人需要{portion_zh[weights[i]]}"
        for i in range(4)
    )
    questions = (
        (
            f"For a catered event, {details_en}. The organizer adds {reserve} extra portions. "
            f"Each portion uses {units_per_portion} ingredient units. How many ingredient "
            "units are required in total?",
            f"一场餐饮活动中，{details_zh}。主办方另准备 {reserve} 份备用餐。每份需要 "
            f"{units_per_portion} 个原料单位。总共需要多少个原料单位？",
        ),
        (
            f"A meal service has the following demand: {details_en}. After including a buffer "
            f"of {reserve} portions, it uses {units_per_portion} supply units per portion. "
            "Find the total number of supply units needed.",
            f"某供餐服务的需求为：{details_zh}。再加入 {reserve} 份缓冲量后，每份消耗 "
            f"{units_per_portion} 个供应单位。共需多少个供应单位？",
        ),
    )
    question_en, question_zh = questions[index % 2]
    weighted_terms = "+".join(
        f"{counts[i]}*{weights[i][0]}/{weights[i][1]}" for i in range(4)
    )
    expression = f"(({weighted_terms})+{reserve})*{units_per_portion}"
    return _Variant(
        question_en,
        question_zh,
        expression,
        {
            "counts": counts,
            "portion_fractions": weights,
            "reserve": reserve,
            "units_per_portion": units_per_portion,
        },
        "weighted_group_demand_with_buffer",
    )


def _population_flow(rng: random.Random, index: int) -> _Variant:
    initial = 10_000 * rng.randint(4, 20)
    years = rng.randint(4, 12)
    natural_rate = rng.choice((8, 12, 15, 18, 20, 25, 30))
    annual_out = 100 * rng.randint(5, 30)
    annual_in = 100 * rng.randint(5, 35)
    questions = (
        (
            f"A region starts with {initial:,} residents. Over the next {years} years, births "
            f"and deaths together produce a net natural increase equal to {natural_rate}% of "
            f"the initial population. During each of those years, {annual_out:,} residents "
            f"move out and {annual_in:,} move in. What is the population after {years} years?",
            f"某地区初始有 {initial:,} 名居民。在随后 {years} 年内，出生与死亡合计带来的自然"
            f"净增长等于初始人口的 {natural_rate}%。这 {years} 年中每年有 {annual_out:,} 人迁出、"
            f"{annual_in:,} 人迁入。{years} 年后人口是多少？",
        ),
        (
            f"The initial population of a district is {initial:,}. Across a {years}-year period, "
            f"its total natural growth is {natural_rate}% of that initial population. Net "
            f"migration is determined by {annual_in:,} arrivals and {annual_out:,} departures "
            "per year. Find the population at the end of the period.",
            f"某行政区初始人口为 {initial:,}。在 {years} 年期间，自然增长总量等于初始人口的 "
            f"{natural_rate}%；每年迁入 {annual_in:,} 人、迁出 {annual_out:,} 人。期末人口是多少？",
        ),
    )
    question_en, question_zh = questions[index % 2]
    expression = (
        f"{initial}*(1+{natural_rate}/100)-{annual_out}*{years}+{annual_in}*{years}"
    )
    return _Variant(
        question_en,
        question_zh,
        expression,
        {
            "initial": initial,
            "years": years,
            "natural_rate": natural_rate,
            "annual_out": annual_out,
            "annual_in": annual_in,
        },
        "period_growth_plus_repeated_population_flows",
    )


def _tank_loss_recovery(_: random.Random, index: int) -> _Variant:
    configs = (
        (500_000, 25_000, 4, 12_000, 5, 30_000, 3),
        (600_000, 30_000, 5, 8_000, 6, 40_000, 4),
        (400_000, 18_000, 6, 7_000, 8, 25_000, 4),
        (750_000, 40_000, 4, 15_000, 6, 50_000, 3),
        (300_000, 20_000, 3, 9_000, 5, 15_000, 4),
        (900_000, 45_000, 5, 20_000, 4, 60_000, 4),
        (650_000, 32_000, 6, 11_000, 7, 42_000, 5),
    )
    capacity, leak1, hours1, leak2, hours2, refill, refill_hours = configs[index]
    vessels = (("storage tank", "储罐"), ("reservoir", "蓄水池"), ("fuel tank", "燃料罐"))
    vessel_en, vessel_zh = vessels[index % len(vessels)]
    questions = (
        (
            f"A {capacity:,}-gallon {vessel_en} is initially full. It leaks at {leak1:,} "
            f"gallons per hour for {hours1} hours, then at {leak2:,} gallons per hour for "
            f"{hours2} more hours. After repair, it is refilled at {refill:,} gallons per hour "
            f"for {refill_hours} hours. How many gallons short of full is it?",
            f"一个容量为 {capacity:,} 加仑且初始装满的{vessel_zh}，先以每小时 {leak1:,} 加仑漏失 "
            f"{hours1} 小时，再以每小时 {leak2:,} 加仑漏失 {hours2} 小时。修复后以每小时 "
            f"{refill:,} 加仑补充 {refill_hours} 小时。距离重新装满还差多少加仑？",
        ),
        (
            f"An initially full {vessel_en} holds {capacity:,} gallons. Two leaks remove "
            f"{leak1:,} gallons per hour for {hours1} hours and then {leak2:,} gallons per hour "
            f"for {hours2} hours. A later refill adds {refill:,} gallons per hour for "
            f"{refill_hours} hours. What volume is still needed to reach capacity?",
            f"一个初始装满的{vessel_zh}容量为 {capacity:,} 加仑。两阶段分别以每小时 {leak1:,} 加仑"
            f"漏失 {hours1} 小时、每小时 {leak2:,} 加仑漏失 {hours2} 小时，之后又以每小时 "
            f"{refill:,} 加仑补充 {refill_hours} 小时。还需补充多少加仑才能达到容量？",
        ),
    )
    question_en, question_zh = questions[index % 2]
    expression = (
        f"{capacity}-({capacity}-{leak1}*{hours1}-{leak2}*{hours2}+"
        f"{refill}*{refill_hours})"
    )
    return _Variant(
        question_en,
        question_zh,
        expression,
        {
            "capacity": capacity,
            "leak_rates": (leak1, leak2),
            "leak_hours": (hours1, hours2),
            "refill_rate": refill,
            "refill_hours": refill_hours,
            "vessel": vessel_en,
        },
        "two_stage_loss_then_partial_recovery",
    )


_BUILDERS: dict[str, _Builder] = {
    "v3-eval-val-public-ratio-allocation-v1": _ratio_allocation,
    "v3-eval-val-public-weighted-demand-v1": _weighted_demand,
    "v3-eval-val-public-population-flow-v1": _population_flow,
    "v3-eval-val-public-tank-loss-recovery-v1": _tank_loss_recovery,
}


def _independent_expected(family_id: str, parameters: dict[str, Any]) -> float:
    if family_id == "v3-eval-val-public-ratio-allocation-v1":
        total = Fraction(parameters["total"])
        a = total * Fraction(*parameters["a_fraction"])
        c = a * Fraction(*parameters["c_of_a_fraction"])
        d_ratio, e_ratio = parameters["d_to_e_ratio"]
        return float((total - a - c) * Fraction(d_ratio, d_ratio + e_ratio))
    if family_id == "v3-eval-val-public-weighted-demand-v1":
        portions = sum(
            Fraction(count) * Fraction(*fraction)
            for count, fraction in zip(
                parameters["counts"], parameters["portion_fractions"], strict=True
            )
        )
        return float(
            (portions + parameters["reserve"]) * parameters["units_per_portion"]
        )
    if family_id == "v3-eval-val-public-population-flow-v1":
        return float(
            parameters["initial"] * (1 + parameters["natural_rate"] / 100)
            - parameters["annual_out"] * parameters["years"]
            + parameters["annual_in"] * parameters["years"]
        )
    if family_id == "v3-eval-val-public-tank-loss-recovery-v1":
        lost = sum(
            rate * hours
            for rate, hours in zip(
                parameters["leak_rates"], parameters["leak_hours"], strict=True
            )
        )
        return float(lost - parameters["refill_rate"] * parameters["refill_hours"])
    raise ValueError(f"unsupported validation extension family: {family_id}")


def _validate_quantity_constraints(family_id: str, parameters: dict[str, Any]) -> None:
    """Reject fractional people/packages and physically impossible tank states."""

    if family_id == "v3-eval-val-public-ratio-allocation-v1":
        total = Fraction(parameters["total"])
        a = total * Fraction(*parameters["a_fraction"])
        c = a * Fraction(*parameters["c_of_a_fraction"])
        d_ratio, e_ratio = parameters["d_to_e_ratio"]
        if d_ratio <= 0 or e_ratio <= 0:
            raise ValueError("allocation ratio must be positive")
        d = (total - a - c) * Fraction(d_ratio, d_ratio + e_ratio)
        e = total - a - c - d
        if any(value <= 0 or value.denominator != 1 for value in (a, c, d, e)):
            raise ValueError("allocation must give each category a positive whole count")
        return

    if family_id == "v3-eval-val-public-weighted-demand-v1":
        portions = sum(
            Fraction(count) * Fraction(*weight)
            for count, weight in zip(
                parameters["counts"], parameters["portion_fractions"], strict=True
            )
        )
        if (
            any(count <= 0 for count in parameters["counts"])
            or portions <= 0
            or portions.denominator != 1
            or parameters["reserve"] <= 0
            or parameters["units_per_portion"] <= 0
        ):
            raise ValueError("weighted demand must have whole, positive portions")
        return

    if family_id == "v3-eval-val-public-population-flow-v1":
        if (
            parameters["initial"] <= 0
            or parameters["years"] <= 0
            or parameters["annual_in"] < 0
            or parameters["annual_out"] < 0
            or _independent_expected(family_id, parameters) <= 0
        ):
            raise ValueError("population must remain positive")
        return

    if family_id == "v3-eval-val-public-tank-loss-recovery-v1":
        lost = sum(
            rate * hours
            for rate, hours in zip(
                parameters["leak_rates"], parameters["leak_hours"], strict=True
            )
        )
        refilled = parameters["refill_rate"] * parameters["refill_hours"]
        if not 0 < refilled < lost < parameters["capacity"]:
            raise ValueError("tank must neither empty nor overfill during the scenario")
        return

    raise ValueError(f"unsupported validation extension family: {family_id}")


def build_v4_validation_extension_records(
    *, variants_per_family: int = 7, seed: int = 509
) -> tuple[ValidationExtensionRecord, ...]:
    if variants_per_family != 7:
        raise ValueError("V4 validation extension requires exactly 7 variants per family")

    records = []
    seen_prompts: set[str] = set()
    for family_id, builder in _BUILDERS.items():
        for index in range(variants_per_family):
            variant = builder(_rng_for(seed, family_id, index), index)
            prompt = (
                "Use the calculator to solve this quantitative reasoning problem. "
                f"Return the final number.\n\n{variant.question_en}"
            )
            if prompt in seen_prompts:
                raise ValueError(f"duplicate V4 validation prompt: {family_id}-{index}")
            seen_prompts.add(prompt)
            _validate_quantity_constraints(family_id, variant.parameters)
            replayed = calculator(variant.expression)
            expected = _independent_expected(family_id, variant.parameters)
            ground_truth = {"type": "number", "value": replayed, "tolerance": 1e-6}
            if not verify_numeric_answer(expected, ground_truth).passed:
                raise ValueError(f"independent oracle mismatch: {family_id}-{index}")
            slug = family_id.removeprefix("v3-eval-val-public-").removesuffix("-v1")
            task = Task(
                task_id=f"v4-review-val-{slug}-{index + 1:03d}",
                family_id=family_id,
                kind=TaskKind.CALCULATOR,
                split=Split.VALIDATION,
                prompt=prompt,
                allowed_tools=("calculator",),
                ground_truth=ground_truth,
                metadata={
                    "synthetic": True,
                    "evaluation_only": True,
                    "training_eligible": False,
                    "review_status": "pending",
                    "dataset_version": "v4_validation_public_extension_audit_v0",
                    "expansion_seed": seed,
                    "generator_index": index + 1,
                    "parent_family_id": family_id,
                    "parent_seed_task_id": V4_VALIDATION_PUBLIC_FAMILIES[family_id],
                    "relation_subtype": variant.subtype,
                    "parameters": variant.parameters,
                    "reference_expression": variant.expression,
                    "reference_result": replayed,
                    "review_artifact": "docs/V4_VALIDATION_EXTENSION_AUDIT_ZH.md",
                },
            )
            records.append(ValidationExtensionRecord(task, variant.question_zh))

    if len(records) != 28:
        raise ValueError(f"expected 28 V4 validation extension rows, found {len(records)}")
    validate_task_dataset(record.task for record in records)
    return tuple(records)


def build_v4_validation_extension(
    *, variants_per_family: int = 7, seed: int = 509
) -> tuple[Task, ...]:
    return tuple(
        record.task
        for record in build_v4_validation_extension_records(
            variants_per_family=variants_per_family,
            seed=seed,
        )
    )
