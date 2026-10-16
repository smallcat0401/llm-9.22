"""Tier A: freeze the reviewed V3 validation and test tasks.

The builders below are intentionally explicit.  They preserve the reviewed
seed wording, vary only the numeric parameters, replay every hidden reference
expression, and keep validation/test families disjoint.  Public questions are
copied from the reviewed audit without rewriting their English text.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Callable, Iterable, Sequence

from .dataset import validate_task_dataset
from .schemas import Split, Task, TaskKind
from .tools.calculator import calculator
from .v3_eval_seed import EvalSeedCandidate, build_v3_eval_seed_candidates
from .verifier import verify_numeric_answer


Builder = Callable[[int], tuple[str, str, bool]]


def _money(value: int | float) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _tiered_commission(i: int) -> tuple[str, str, bool]:
    base, threshold = 420 + 80 * i, 4000 + 2000 * i
    low = 3 - 0.5 * (i % 2)
    high = 5 - (i % 2)
    charge, sales = 35 + 13 * i, 6800 + 2400 * i
    prompt = (
        f"A sales representative receives a ${base} base payment. The first "
        f"${threshold:,} of sales earns {low:g}% commission and sales above "
        f"${threshold:,} earn {high:g}%. After a fixed ${charge} platform charge, "
        f"what is the representative's pay when total sales are ${sales:,}?"
    )
    expression = (
        f"{base}+{threshold}*{low}/100+({sales}-{threshold})*{high}/100-{charge}"
    )
    return prompt, expression, False


def _restricted_grant(i: int) -> tuple[str, str, bool]:
    cycle, odd = divmod(i, 2)
    if not odd:
        staff, hours, rate = 18 + 2 * cycle, 6 + cycle % 2, 22 + cycle
        materials, venue = 1450 + 110 * cycle, 620 + 40 * cycle
        grant, donor = 18 + cycle, 120 + 20 * cycle
        subject = "An event uses"
    else:
        staff, hours, rate = 14 + 2 * cycle, 5 + cycle % 2, 28 + cycle
        materials, venue = 980 + 120 * cycle, 540 + 45 * cycle
        grant, donor = 22 - cycle, 150 + 20 * cycle
        subject = "A workshop uses"
    prompt = (
        f"{subject} {staff} staff for {hours} hours at ${rate} per hour, "
        f"${materials:,} of materials, and a ${venue} venue. A grant covers "
        f"{grant}% of the combined labor and material costs; it does not cover "
        f"the venue. A separate donor contributes ${donor}. How much must the "
        "organizers still pay? Round to two decimals."
    )
    expression = (
        f"{staff}*{hours}*{rate}+{materials}+{venue}-"
        f"({staff}*{hours}*{rate}+{materials})*{grant}/100-{donor}"
    )
    return prompt, expression, True


def _fixed_basket_change(i: int) -> tuple[str, str, bool]:
    cycle, odd = divmod(i, 2)
    if not odd:
        qa, qb = 12 + cycle, 7 + cycle
        old_a, old_b = 8 + 0.5 * cycle, 15 + cycle
        new_a, new_b, delivery = old_a + 1.2, old_b - 0.5, 20 + 2 * cycle
    else:
        qa, qb = 9 + cycle, 11 + cycle
        old_a, old_b = 12 + 0.5 * cycle, 7.5 + 0.5 * cycle
        new_a, new_b, delivery = old_a - 0.6, old_b + 0.6, 16 + 2 * cycle
    prompt = (
        f"A fixed basket contains {qa} units of product A and {qb} units of product B. "
        f"A cost ${old_a:.2f} and B cost ${old_b:.2f} last year; this year they "
        f"cost ${new_a:.2f} and ${new_b:.2f}. A ${delivery} delivery charge applies "
        "in both years. What is the percentage change in the basket's total cost? "
        "Round to two decimals."
    )
    old = f"({qa}*{old_a}+{qb}*{old_b}+{delivery})"
    new = f"({qa}*{new_a}+{qb}*{new_b}+{delivery})"
    return prompt, f"({new}-{old})/{old}*100", True


def _rework_yield(i: int) -> tuple[str, str, bool]:
    cycle, odd = divmod(i, 2)
    if not odd:
        lines, each, rejected, recovered = 5, 240 + 60 * cycle, 8, "3/4"
        recovered_words = "three quarters"
    else:
        lines, each, rejected, recovered = 4, 350 + 25 * cycle, 6, "2/3"
        recovered_words = "two thirds"
    prompt = (
        f"{lines} production lines each make {each} units. Initial inspection rejects "
        f"{rejected}% of all units, but rework recovers {recovered_words} of the "
        "rejected units. How many sellable units remain?"
    )
    total = f"{lines}*{each}"
    return prompt, f"{total}*(1-{rejected}/100)+{total}*{rejected}/100*({recovered})", False


def _subscription_overage(i: int) -> tuple[str, str, bool]:
    cycle, odd = divmod(i, 2)
    if not odd:
        base, included, used, rate, tax, rental = 45 + 3*cycle, 300 + 50*cycle, 460 + 75*cycle, 0.12 + 0.01*cycle, 6 + cycle, 8 + cycle
    else:
        base, included, used, rate, tax, rental = 52 + 3*cycle, 400 + 50*cycle, 575 + 75*cycle, 0.09 + 0.01*cycle, 7 + cycle, 10 + cycle
    prompt = (
        f"A monthly data plan costs ${base} and includes {included} GB. Extra usage "
        f"costs ${rate:.2f} per GB. A customer uses {used} GB. A {tax}% service tax "
        f"applies to the plan and overage charges, while a ${rental} equipment rental "
        "is added after tax. What is the final bill? Round to two decimals."
    )
    return prompt, f"({base}+({used}-{included})*{rate})*(1+{tax}/100)+{rental}", True


def _route_cost(i: int) -> tuple[str, str, bool]:
    cycle, odd = divmod(i, 2)
    if not odd:
        highway, hmpg, city, cmpg = 180 + 30*cycle, 30, 120 + 24*cycle, 24
        price, toll, voucher = 3.8 + 0.1*cycle, 18 + 2*cycle, 10 + cycle
    else:
        highway, hmpg, city, cmpg = 210 + 35*cycle, 35, 96 + 24*cycle, 24
        price, toll, voucher = 4.1 + 0.1*cycle, 22 + 2*cycle, 12 + cycle
    prompt = (
        f"A delivery van travels {highway} miles on highways at {hmpg} miles per "
        f"gallon and {city} miles in cities at {cmpg} miles per gallon. Fuel costs "
        f"${price:.2f} per gallon. The route also has a ${toll} toll, and a ${voucher} "
        "travel voucher is applied to the total. What is the trip's net cost?"
    )
    return prompt, f"({highway}/{hmpg}+{city}/{cmpg})*{price}+{toll}-{voucher}", False


def _partial_refund(i: int) -> tuple[str, str, bool]:
    cycle, odd = divmod(i, 2)
    if not odd:
        qa, pa, qb, pb = 3 + cycle, 40 + 5*cycle, 2 + cycle, 65 + 5*cycle
        discount, delivery, refund = 15, 12 + cycle, 80
    else:
        qa, pa, qb, pb = 2 + cycle, 55 + 5*cycle, 3 + cycle, 30 + 5*cycle
        discount, delivery, refund = 20, 9 + cycle, 75
    factor = f"(1-{discount}/100)"
    prompt = (
        f"A customer buys {qa} items at ${pa} each and {qb} items at ${pb} each "
        f"during a {discount}%-off sale, plus a nonrefundable ${delivery} delivery "
        f"charge. The customer returns one ${pb} item but receives only {refund}% of "
        "that item's discounted price because of a restocking fee. What is the "
        "customer's final net payment? Round to two decimals."
    )
    expression = f"({qa}*{pa}+{qb}*{pb})*{factor}+{delivery}-{pb}*{factor}*{refund}/100"
    return prompt, expression, True


def _bonus_deduction(i: int) -> tuple[str, str, bool]:
    cycle, odd = divmod(i, 2)
    if not odd:
        regular, overtime, rate = 38, 7 + cycle, 24 + cycle
        bonus, tax, insurance = 6 + cycle, 18, 42 + 3*cycle
    else:
        regular, overtime, rate = 40, 5 + cycle, 27 + cycle
        bonus, tax, insurance = 8 + cycle, 20, 55 + 3*cycle
    prompt = (
        f"An employee works {regular} regular hours and {overtime} overtime hours at "
        f"${rate} per hour. Overtime pays 1.5 times the regular rate. A performance "
        f"bonus equals {bonus}% of regular-hour wages. After {tax}% tax on all gross "
        f"pay, a fixed ${insurance} insurance deduction is taken. What is take-home "
        "pay? Round to two decimals."
    )
    expression = (
        f"({regular}*{rate}+{overtime}*{rate}*1.5+{regular}*{rate}*{bonus}/100)"
        f"*(1-{tax}/100)-{insurance}"
    )
    return prompt, expression, True


_SYNTHETIC_BUILDERS: tuple[tuple[str, Split, Builder], ...] = (
    ("v3-eval-val-tiered-commission-v1", Split.VALIDATION, _tiered_commission),
    ("v3-eval-val-restricted-grant-v1", Split.VALIDATION, _restricted_grant),
    ("v3-eval-val-fixed-basket-change-v1", Split.VALIDATION, _fixed_basket_change),
    ("v3-eval-val-rework-yield-v1", Split.VALIDATION, _rework_yield),
    ("v3-eval-test-subscription-overage-v1", Split.TEST, _subscription_overage),
    ("v3-eval-test-route-cost-v1", Split.TEST, _route_cost),
    ("v3-eval-test-partial-refund-v1", Split.TEST, _partial_refund),
    ("v3-eval-test-bonus-deduction-v1", Split.TEST, _bonus_deduction),
)


def _task_from_synthetic(family: str, split: Split, builder: Builder, index: int) -> Task:
    problem, expression, round_two = builder(index)
    replayed = calculator(expression)
    value = _money(replayed) if round_two else replayed
    tolerance = 0.005 if round_two else 1e-6
    task = Task(
        task_id=f"{family}-{index:03d}", family_id=family,
        kind=TaskKind.CALCULATOR, split=split,
        prompt=("Use the calculator to solve this quantitative reasoning problem. "
                f"Return the final number.\n\n{problem}"),
        allowed_tools=("calculator",),
        ground_truth={"type": "number", "value": value, "tolerance": tolerance},
        metadata={
            "synthetic": True, "evaluation_only": True,
            "dataset_version": "v3_evaluation_v1", "generator_index": index,
            "reference_expression": expression,
            "seed_audit": "v3_eval_seed_audit_v0",
        },
    )
    if not verify_numeric_answer(replayed, task.ground_truth).passed:
        raise ValueError(f"synthetic reference replay failed: {task.task_id}")
    return task


def _task_from_public(candidate: EvalSeedCandidate) -> Task:
    split = Split(candidate.proposed_split)
    task = Task(
        task_id=candidate.candidate_id,
        family_id=candidate.family_id,
        kind=TaskKind.CALCULATOR,
        split=split,
        prompt=("Solve this problem. The calculator tool is available for arithmetic. "
                f"Return the final number.\n\n{candidate.prompt_en}"),
        allowed_tools=("calculator",),
        ground_truth={
            "type": "number", "value": candidate.ground_truth,
            "tolerance": candidate.tolerance,
        },
        metadata={
            "evaluation_only": True, "dataset_version": "v3_evaluation_v1",
            "source_dataset": candidate.source_dataset,
            "source_split": candidate.source_split,
            "source_index": candidate.source_index,
            "reference_expression": candidate.reference_expression,
            "seed_audit": "v3_eval_seed_audit_v0",
        },
    )
    replayed = calculator(candidate.reference_expression)
    if not verify_numeric_answer(replayed, task.ground_truth).passed:
        raise ValueError(f"public reference replay failed: {task.task_id}")
    return task


def build_v3_evaluation_tasks(
    *,
    gsm8k_train_path: str | Path,
    gsm8k_test_path: str | Path,
    exclusion_artifacts: Sequence[str | Path] = (),
    training_family_ids: Iterable[str] = (),
    examples_per_synthetic_family: int = 8,
) -> tuple[Task, ...]:
    if examples_per_synthetic_family < 2:
        raise ValueError("at least two examples per synthetic family are required")
    tasks = [
        _task_from_synthetic(family, split, builder, index)
        for family, split, builder in _SYNTHETIC_BUILDERS
        for index in range(examples_per_synthetic_family)
    ]
    audited = build_v3_eval_seed_candidates(
        gsm8k_train_path=gsm8k_train_path,
        gsm8k_test_path=gsm8k_test_path,
        exclusion_artifacts=exclusion_artifacts,
    )
    tasks.extend(_task_from_public(row) for row in audited if row.source_type == "public")
    validate_task_dataset(tasks)

    evaluation_families = {task.family_id for task in tasks}
    overlap = evaluation_families & {str(value) for value in training_family_ids}
    if overlap:
        raise ValueError(f"training/evaluation family overlap: {sorted(overlap)}")
    if any(task.split is Split.TRAIN for task in tasks):
        raise ValueError("V3 evaluation tasks must never use the train split")
    return tuple(tasks)
