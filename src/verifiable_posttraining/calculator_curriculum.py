"""Tier A deterministic multi-step calculator curriculum.

This dataset is a diagnostic synthetic curriculum, not a substitute for the
project's search-distillation branch.  Families are assigned to splits before
examples are generated so no prompt template appears in more than one split.
Reference expressions are stored for replay and may be converted into an
explicit reference-program SFT ablation using the builder below.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Mapping, Sequence

from .dataset import validate_task_dataset
from .native_sft_data import CALCULATOR_TOOL_SCHEMA
from .prompting import build_native_calculator_grpo_messages
from .schemas import Split, Task, TaskKind
from .tools.calculator import calculator
from .verifier import verify_numeric_answer


Builder = Callable[[int], tuple[str, str, float | int]]
BuilderV2 = Callable[[int], tuple[str, str, float | int, float]]


def _shopping_total(i: int) -> tuple[str, str, float | int]:
    boxes, units, price, shipping = 2 + i % 4, 3 + i, 4 + i % 5, 5 + i
    return (
        f"A shop orders {boxes} boxes with {units} items per box. Each item costs "
        f"${price}, and shipping costs ${shipping}. What is the total cost?",
        f"{boxes}*{units}*{price}+{shipping}",
        boxes * units * price + shipping,
    )


def _rate_time_offset(i: int) -> tuple[str, str, float | int]:
    rate, hours, extra = 35 + i * 2, 2 + i % 4, 7 + i
    return (
        f"A vehicle travels at {rate} km/h for {hours} hours, then travels another "
        f"{extra} km. How far does it travel in total?",
        f"{rate}*{hours}+{extra}",
        rate * hours + extra,
    )


def _recipe_scale(i: int) -> tuple[str, str, float | int]:
    base, target, amount = 4, 8 + 4 * (i % 4), 3 + i
    return (
        f"A recipe for {base} servings uses {amount} cups of an ingredient. How many "
        f"cups are needed for {target} servings at the same ratio?",
        f"{amount}*{target}/{base}",
        amount * target / base,
    )


def _discount_then_fee(i: int) -> tuple[str, str, float | int]:
    price, discount, fee = 100 + 20 * i, 10 + 5 * (i % 3), 4 + i
    return (
        f"An item costs ${price}. It receives a {discount}% discount, then a fixed "
        f"${fee} service fee is added. What is the final price?",
        f"{price}*(100-{discount})/100+{fee}",
        price * (100 - discount) / 100 + fee,
    )


def _production_after_rejects(i: int) -> tuple[str, str, float | int]:
    machines, each, rejected = 3 + i % 5, 20 + 3 * i, 4 + i
    return (
        f"There are {machines} machines, and each produces {each} parts. After "
        f"{rejected} defective parts are rejected, how many usable parts remain?",
        f"{machines}*{each}-{rejected}",
        machines * each - rejected,
    )


def _savings_after_purchase(i: int) -> tuple[str, str, float | int]:
    initial, weeks, weekly, purchase = 25 + 2 * i, 3 + i % 4, 8 + i, 10 + i
    return (
        f"A person starts with ${initial}, saves ${weekly} each week for {weeks} "
        f"weeks, then spends ${purchase}. How much remains?",
        f"{initial}+{weekly}*{weeks}-{purchase}",
        initial + weekly * weeks - purchase,
    )


def _event_capacity(i: int) -> tuple[str, str, float | int]:
    rows, seats, reserved, standing = 5 + i % 4, 8 + i, 3 + i, 2 + i % 3
    return (
        f"A hall has {rows} rows with {seats} seats per row. {reserved} seats are "
        f"reserved and {standing} people may stand. How many other people can attend?",
        f"{rows}*{seats}-{reserved}+{standing}",
        rows * seats - reserved + standing,
    )


def _fuel_cost(i: int) -> tuple[str, str, float | int]:
    efficiency, gallons, price = 20 + i, 3 + i % 5, 3 + (i % 4) * 0.5
    distance = efficiency * gallons
    return (
        f"A car travels {distance} miles at {efficiency} miles per gallon. Fuel costs "
        f"${price} per gallon. What is the fuel cost for the trip?",
        f"{distance}/{efficiency}*{price}",
        distance / efficiency * price,
    )


def _inventory_batches(i: int) -> tuple[str, str, float | int]:
    initial, batches, size, sold = 30 + i, 2 + i % 4, 9 + i, 7 + 2 * i
    return (
        f"A warehouse starts with {initial} units, receives {batches} batches of "
        f"{size} units, and sells {sold} units. How many units remain?",
        f"{initial}+{batches}*{size}-{sold}",
        initial + batches * size - sold,
    )


def _two_leg_trip(i: int) -> tuple[str, str, float | int]:
    rate1, time1 = 25 + i, 2 + i % 3
    rate2, time2 = 40 + 2 * i, 1 + i % 4
    return (
        f"A trip has two legs: {time1} hours at {rate1} km/h and {time2} hours at "
        f"{rate2} km/h. What is the total distance?",
        f"{rate1}*{time1}+{rate2}*{time2}",
        rate1 * time1 + rate2 * time2,
    )


_FAMILIES: tuple[tuple[str, Split, Builder], ...] = (
    ("curriculum-shopping-total-v1", Split.TRAIN, _shopping_total),
    ("curriculum-rate-time-offset-v1", Split.TRAIN, _rate_time_offset),
    ("curriculum-recipe-scale-v1", Split.TRAIN, _recipe_scale),
    ("curriculum-discount-fee-v1", Split.TRAIN, _discount_then_fee),
    ("curriculum-production-rejects-v1", Split.TRAIN, _production_after_rejects),
    ("curriculum-savings-purchase-v1", Split.TRAIN, _savings_after_purchase),
    ("curriculum-event-capacity-v1", Split.VALIDATION, _event_capacity),
    ("curriculum-fuel-cost-v1", Split.VALIDATION, _fuel_cost),
    ("curriculum-inventory-batches-v1", Split.TEST, _inventory_batches),
    ("curriculum-two-leg-trip-v1", Split.TEST, _two_leg_trip),
)


def _sales_returns(i: int) -> tuple[str, str, float | int, float]:
    regular, regular_price = 18 + i, 9 + i % 4
    premium, premium_price = 7 + i % 5, 15 + i % 3
    returned, fee = 2 + i % 3, 11 + i
    return (
        f"A store sold {regular} regular items at ${regular_price} each and {premium} "
        f"premium items at ${premium_price} each. Customers returned {returned} regular "
        f"items, and the store also earned a fixed ${fee} service fee. What was net revenue?",
        f"({regular}-{returned})*{regular_price}+{premium}*{premium_price}+{fee}",
        (regular - returned) * regular_price + premium * premium_price + fee,
        1e-6,
    )


def _markup_discount(i: int) -> tuple[str, str, float | int, float]:
    cost, markup, discount = 80 + 20 * i, 25 + 5 * (i % 3), 10 + 5 * (i % 2)
    return (
        f"A product costs ${cost}. Its price is increased by {markup}%, then the marked "
        f"price is discounted by {discount}%. What is the final price? Round to two decimals.",
        f"{cost}*(1+{markup}/100)*(1-{discount}/100)",
        cost * (1 + markup / 100) * (1 - discount / 100),
        0.005,
    )


def _required_final_score(i: int) -> tuple[str, str, float | int, float]:
    scores = (62 + i, 68 + i, 74 + i, 80 + i)
    target = 75 + i
    score_text = ", ".join(str(score) for score in scores)
    return (
        f"Four test scores are {score_text}. What fifth score is needed for an average "
        f"of {target} across all five tests?",
        f"{target}*5-({'+'.join(str(score) for score in scores)})",
        target * 5 - sum(scores),
        1e-6,
    )


def _cartons_after_damage(i: int) -> tuple[str, str, float | int, float]:
    cartons, packs, items = 3 + i % 4, 4 + i % 3, 6 + i
    damaged, samples = 5 + i, 2 + i % 4
    return (
        f"A shipment has {cartons} cartons, {packs} packs per carton, and {items} items "
        f"per pack. After {damaged} damaged items and {samples} sample items are removed, "
        f"how many saleable items remain?",
        f"{cartons}*{packs}*{items}-{damaged}-{samples}",
        cartons * packs * items - damaged - samples,
        1e-6,
    )


def _shared_bill(i: int) -> tuple[str, str, float | int, float]:
    diners, meal, room, nonpaying = 6 + i % 4, 14 + i, 20 + 2 * i, 1 + i % 2
    return (
        f"A group of {diners} people has meals costing ${meal} per person plus a ${room} "
        f"room charge. {nonpaying} guests pay nothing, so the others split the entire bill "
        f"equally. How much does each paying person owe? Round to two decimals.",
        f"({diners}*{meal}+{room})/({diners}-{nonpaying})",
        (diners * meal + room) / (diners - nonpaying),
        0.005,
    )


def _two_year_growth_fee(i: int) -> tuple[str, str, float | int, float]:
    initial, rate, fee = 200 + 25 * i, 5 + i % 4, 8 + i
    return (
        f"An account starts with ${initial}, grows by {rate}% in each of two years, then "
        f"a one-time ${fee} fee is deducted. What is the balance? Round to two decimals.",
        f"{initial}*(1+{rate}/100)*(1+{rate}/100)-{fee}",
        initial * (1 + rate / 100) * (1 + rate / 100) - fee,
        0.005,
    )


def _weighted_grade(i: int) -> tuple[str, str, float | int, float]:
    exam, project, quiz = 70 + i, 80 + i, 60 + i
    return (
        f"A course grade uses an exam worth 50%, a project worth 35%, and a quiz worth "
        f"15%. A student scores {exam}, {project}, and {quiz}. What is the weighted grade?",
        f"{exam}*0.5+{project}*0.35+{quiz}*0.15",
        exam * 0.5 + project * 0.35 + quiz * 0.15,
        1e-6,
    )


def _tank_balance(i: int) -> tuple[str, str, float | int, float]:
    initial, deliveries, each = 100 + 5 * i, 2 + i % 3, 30 + i
    daily, days = 7 + i % 4, 3 + i % 5
    return (
        f"A tank starts with {initial} liters. It receives {deliveries} deliveries of "
        f"{each} liters, then {daily} liters are drained from the tank per day for "
        f"{days} days. A label "
        f"on the tank says its maximum capacity is 1000 liters. How much remains?",
        f"{initial}+{deliveries}*{each}-{daily}*{days}",
        initial + deliveries * each - daily * days,
        1e-6,
    )


def _overtime_take_home(i: int) -> tuple[str, str, float | int, float]:
    regular_hours, overtime = 32 + i % 7, 4 + i % 5
    rate, tax = 14 + i, 10 + 2 * (i % 4)
    return (
        f"A worker earns ${rate} per regular hour and 1.5 times that rate for overtime. "
        f"This week they work {regular_hours} regular hours and {overtime} overtime hours. "
        f"After {tax}% tax on the whole gross pay, what is take-home pay? Round to two decimals.",
        f"({regular_hours}*{rate}+{overtime}*{rate}*1.5)*(1-{tax}/100)",
        (regular_hours * rate + overtime * rate * 1.5) * (1 - tax / 100),
        0.005,
    )


def _mixture_concentration(i: int) -> tuple[str, str, float | int, float]:
    amount1, percent1 = 8 + i, 20 + 5 * (i % 3)
    amount2, percent2 = 5 + i % 6, 50 + 5 * (i % 4)
    return (
        f"A mixture combines {amount1} liters of a {percent1}% solution with {amount2} "
        f"liters of a {percent2}% solution. What percentage of the combined mixture is "
        f"the substance? Round to two decimals.",
        f"({amount1}*{percent1}/100+{amount2}*{percent2}/100)/({amount1}+{amount2})*100",
        (amount1 * percent1 / 100 + amount2 * percent2 / 100) / (amount1 + amount2) * 100,
        0.005,
    )


_FAMILIES_V2: tuple[tuple[str, Split, BuilderV2], ...] = (
    ("curriculum-v2-sales-returns", Split.TRAIN, _sales_returns),
    ("curriculum-v2-markup-discount", Split.TRAIN, _markup_discount),
    ("curriculum-v2-required-score", Split.TRAIN, _required_final_score),
    ("curriculum-v2-cartons-damage", Split.TRAIN, _cartons_after_damage),
    ("curriculum-v2-shared-bill", Split.TRAIN, _shared_bill),
    ("curriculum-v2-growth-fee", Split.TRAIN, _two_year_growth_fee),
    ("curriculum-v2-weighted-grade", Split.VALIDATION, _weighted_grade),
    ("curriculum-v2-tank-drain", Split.VALIDATION, _tank_balance),
    ("curriculum-v2-overtime-take-home", Split.TEST, _overtime_take_home),
    ("curriculum-v2-mixture-concentration", Split.TEST, _mixture_concentration),
)


def generate_calculator_curriculum(*, examples_per_family: int = 12) -> tuple[Task, ...]:
    if examples_per_family <= 0:
        raise ValueError("examples_per_family must be positive")
    tasks = []
    for family_id, split, builder in _FAMILIES:
        for index in range(examples_per_family):
            problem, expression, value = builder(index)
            tasks.append(Task(
                task_id=f"{family_id}-{index:03d}",
                family_id=family_id,
                kind=TaskKind.CALCULATOR,
                split=split,
                prompt=(
                    "Use the calculator to solve this multi-step problem. Return the final "
                    f"number.\n\n{problem}"
                ),
                allowed_tools=("calculator",),
                ground_truth={"type": "number", "value": value, "tolerance": 1e-6},
                metadata={
                    "synthetic": True,
                    "curriculum": "multi_step_calculator_v1",
                    "generator_index": index,
                    "reference_expression": expression,
                },
            ))
    validate_task_dataset(tasks)
    for task in tasks:
        result = calculator(task.metadata["reference_expression"])
        if not verify_numeric_answer(result, task.ground_truth).passed:
            raise ValueError(f"reference expression failed replay: {task.task_id}")
    return tuple(tasks)


def generate_calculator_curriculum_v2(*, examples_per_family: int = 12) -> tuple[Task, ...]:
    if examples_per_family <= 0:
        raise ValueError("examples_per_family must be positive")
    tasks = []
    for family_id, split, builder in _FAMILIES_V2:
        for index in range(examples_per_family):
            problem, expression, value, tolerance = builder(index)
            tasks.append(Task(
                task_id=f"{family_id}-{index:03d}",
                family_id=family_id,
                kind=TaskKind.CALCULATOR,
                split=split,
                prompt=(
                    "Use the calculator to solve this multi-step problem. Return the final "
                    f"number.\n\n{problem}"
                ),
                allowed_tools=("calculator",),
                ground_truth={"type": "number", "value": value, "tolerance": tolerance},
                metadata={
                    "synthetic": True,
                    "curriculum": "multi_step_calculator_v2",
                    "generator_index": index,
                    "reference_expression": expression,
                },
            ))
    validate_task_dataset(tasks)
    for task in tasks:
        result = calculator(task.metadata["reference_expression"])
        if not verify_numeric_answer(result, task.ground_truth).passed:
            raise ValueError(f"reference expression failed replay: {task.task_id}")
    return tuple(tasks)


def _tiered_utility(i: int) -> tuple[str, str, float | int, float]:
    units, threshold = 140 + 10 * i, 100
    base, low_rate, high_rate, credit = 12 + i, 0.18, 0.31, 3 + i % 4
    return (
        f"An electricity bill has a ${base} base charge. The first {threshold} kWh cost "
        f"${low_rate} each and usage above {threshold} kWh costs ${high_rate} each. A "
        f"${credit} credit is then applied. If usage is {units} kWh, what is the bill? "
        "Round to two decimals.",
        f"{base}+{threshold}*{low_rate}+({units}-{threshold})*{high_rate}-{credit}",
        base + threshold * low_rate + (units - threshold) * high_rate - credit,
        0.005,
    )


def _event_net_cost(i: int) -> tuple[str, str, float | int, float]:
    adults, adult_meal = 18 + i, 16 + i % 4
    children, child_meal = 7 + i % 5, 9 + i % 3
    room, sponsor = 80 + 5 * i, 35 + 3 * i
    return (
        f"An event serves {adults} adults at ${adult_meal} each and {children} children "
        f"at ${child_meal} each. The room costs ${room}, and a sponsor contributes "
        f"${sponsor} toward the total. What amount must the organizers still pay?",
        f"{adults}*{adult_meal}+{children}*{child_meal}+{room}-{sponsor}",
        adults * adult_meal + children * child_meal + room - sponsor,
        1e-6,
    )


def _service_tax_tip(i: int) -> tuple[str, str, float | int, float]:
    meals, meal_price = 3 + i % 4, 18 + i
    drinks, drink_price = 2 + i % 3, 5 + i % 2
    tax, tip = 6 + i % 4, 8 + i
    subtotal = meals * meal_price + drinks * drink_price
    return (
        f"A restaurant order has {meals} meals at ${meal_price} each and {drinks} drinks "
        f"at ${drink_price} each. Add {tax}% tax to the subtotal, then add a fixed ${tip} "
        "tip. What is the final bill? Round to two decimals.",
        f"({meals}*{meal_price}+{drinks}*{drink_price})*(1+{tax}/100)+{tip}",
        subtotal * (1 + tax / 100) + tip,
        0.005,
    )


_HOLDOUT_V1: tuple[tuple[str, Split, BuilderV2], ...] = (
    ("holdout-v1-tiered-utility", Split.TEST, _tiered_utility),
    ("holdout-v1-event-net-cost", Split.TEST, _event_net_cost),
    ("holdout-v1-service-tax-tip", Split.TEST, _service_tax_tip),
)


def generate_calculator_holdout_v1(*, examples_per_family: int = 12) -> tuple[Task, ...]:
    """Freeze fresh test-only families; these rows must never enter training."""

    if examples_per_family <= 0:
        raise ValueError("examples_per_family must be positive")
    tasks = []
    for family_id, split, builder in _HOLDOUT_V1:
        for index in range(examples_per_family):
            problem, expression, value, tolerance = builder(index)
            tasks.append(Task(
                task_id=f"{family_id}-{index:03d}", family_id=family_id,
                kind=TaskKind.CALCULATOR, split=split,
                prompt=("Use the calculator to solve this multi-step problem. Return the "
                        f"final number.\n\n{problem}"),
                allowed_tools=("calculator",),
                ground_truth={"type": "number", "value": value, "tolerance": tolerance},
                metadata={
                    "synthetic": True,
                    "curriculum": "calculator_final_holdout_v1",
                    "evaluation_only": True,
                    "generator_index": index,
                    "reference_expression": expression,
                },
            ))
    validate_task_dataset(tasks)
    for task in tasks:
        if not verify_numeric_answer(
            calculator(task.metadata["reference_expression"]), task.ground_truth
        ).passed:
            raise ValueError(f"reference expression failed replay: {task.task_id}")
    return tuple(tasks)


def build_reference_program_sft(tasks: Sequence[Task]) -> tuple[dict[str, Any], ...]:
    """Build an explicit reference-program SFT ablation from train families only."""

    examples = []
    for task in tasks:
        if task.split is not Split.TRAIN:
            continue
        if task.kind is not TaskKind.CALCULATOR or task.allowed_tools != ("calculator",):
            raise ValueError(f"invalid calculator task: {task.task_id}")
        expression = task.metadata.get("reference_expression")
        if not isinstance(expression, str) or not expression.strip():
            raise ValueError(f"missing reference expression: {task.task_id}")
        result = calculator(expression)
        if not verify_numeric_answer(result, task.ground_truth).passed:
            raise ValueError(f"reference expression does not solve task: {task.task_id}")
        messages = [
            message.to_dict() for message in build_native_calculator_grpo_messages(task)
        ]
        messages.extend((
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [{
                    "type": "function",
                    "function": {
                        "name": "calculator",
                        "arguments": {"expression": expression},
                    },
                }],
            },
            {"role": "tool", "name": "calculator", "content": str(result)},
            {
                "role": "assistant",
                "content": json.dumps(
                    {"type": "final", "answer": str(result)},
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
            },
        ))
        examples.append({
            "example_id": f"reference-program-{task.task_id}",
            "messages": messages,
            "tools": [CALCULATOR_TOOL_SCHEMA],
            "metadata": {
                "task_id": task.task_id,
                "family_id": task.family_id,
                "kind": task.kind.value,
                "split": task.split.value,
                "format": "reference-program-native-calculator-v1",
                "provenance": "deterministic_synthetic_reference_expression",
            },
        })
    if not examples:
        raise ValueError("no train examples available")
    return tuple(examples)
