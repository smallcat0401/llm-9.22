"""Tier A builders for expanding already-audited seed-task families.

Expansion is deliberately separated from training-data emission. Every task
returned here is a review candidate: it keeps the quantitative relation of an
audited seed family, receives fresh deterministic parameters and wording, and
must pass calculator replay before it can be shown to a reviewer.

Invariants:

* only the six historical TRAIN families are expanded;
* historical validation/test families never become training candidates;
* seed indices 0 and 1 are parents, not duplicated candidates;
* independently sampled parameters avoid simple monotonic number sequences;
* requested two-decimal answers are stored with explicit display metadata;
* every candidate records its parent family and parent task ids;
* candidates remain ineligible for training until human review is recorded.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import replace
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Callable

from .dataset import validate_task_dataset
from .schemas import Split, Task, TaskKind
from .tools.calculator import calculator
from .verifier import verify_numeric_answer


AUDITED_SELF_WRITTEN_SEED_FAMILIES: tuple[str, ...] = (
    "curriculum-v2-sales-returns",
    "curriculum-v2-markup-discount",
    "curriculum-v2-required-score",
    "curriculum-v2-cartons-damage",
    "curriculum-v2-shared-bill",
    "curriculum-v2-growth-fee",
)

_Builder = Callable[[random.Random, int], tuple[str, str, dict[str, Any], int | None]]


def _rng_for(seed: int, family_id: str, variant_index: int) -> random.Random:
    material = f"{seed}:{family_id}:{variant_index}".encode("utf-8")
    stable_seed = int.from_bytes(hashlib.sha256(material).digest()[:8], "big")
    return random.Random(stable_seed)


def _sales_returns(
    rng: random.Random, surface: int
) -> tuple[str, str, dict[str, Any], int | None]:
    regular = rng.randint(18, 60)
    regular_price = rng.randint(7, 24)
    premium = rng.randint(6, 25)
    premium_price = regular_price + rng.randint(4, 15)
    returned = rng.randint(1, min(8, regular - 1))
    fee = rng.randint(5, 45)
    parameters = {
        "regular": regular,
        "regular_price": regular_price,
        "premium": premium,
        "premium_price": premium_price,
        "returned": returned,
        "fee": fee,
    }
    regular_return_label = f"{returned} regular {'item' if returned == 1 else 'items'}"
    standard_return_label = (
        f"{returned} standard {'product' if returned == 1 else 'products'}"
    )
    basic_return_label = f"{returned} basic {'unit' if returned == 1 else 'units'}"
    prompts = (
        f"A store sold {regular} regular items at ${regular_price} each and {premium} "
        f"premium items at ${premium_price} each. Customers returned {regular_return_label} "
        f"for full refunds, and the store earned a fixed ${fee} service fee. What "
        "was net revenue?",
        f"An online seller sold and shipped {regular} standard products at ${regular_price} "
        f"each and {premium} deluxe products at ${premium_price} each. It fully "
        f"refunded {standard_return_label} and also collected a fixed ${fee} handling "
        "fee. Find the seller's net revenue.",
        f"A market booth recorded sales of {regular} basic units at ${regular_price} apiece "
        f"and {premium} upgraded units at ${premium_price} apiece. Later, {basic_return_label} "
        f"{'was' if returned == 1 else 'were'} returned for full refunds. Including a "
        f"separate ${fee} service payment, "
        "what revenue remained?",
    )
    expression = (
        f"({regular}-{returned})*{regular_price}+{premium}*{premium_price}+{fee}"
    )
    return prompts[surface % len(prompts)], expression, parameters, None


def _markup_discount(
    rng: random.Random, surface: int
) -> tuple[str, str, dict[str, Any], int | None]:
    cost = rng.randrange(75, 601, 5)
    markup = rng.choice((12, 18, 25, 32, 40))
    discount = rng.choice((7, 10, 15, 20, 25))
    parameters = {"cost": cost, "markup": markup, "discount": discount}
    prompts = (
        f"A product costs ${cost}. Its price is increased by {markup}%, then the marked "
        f"price is discounted by {discount}%. What is the final price? Round to two decimals.",
        f"A retailer sets the list price of a ${cost} item by adding {markup}% to the cost. "
        f"During a sale, the list price is reduced by {discount}%. Find the sale price, "
        "rounded to two decimals.",
        f"Equipment with a starting price of ${cost} is first marked up by {markup}%. A "
        f"{discount}% discount is then applied to that marked price. What amount is paid? "
        "Round to two decimals.",
    )
    expression = f"{cost}*(1+{markup}/100)*(1-{discount}/100)"
    return prompts[surface % len(prompts)], expression, parameters, 2


def _required_final_score(
    rng: random.Random, surface: int
) -> tuple[str, str, dict[str, Any], int | None]:
    scores = [rng.randint(58, 94) for _ in range(4)]
    required = rng.randint(65, 99)
    target = Decimal(sum(scores) + required) / Decimal(5)
    target_text = format(target.normalize(), "f")
    parameters = {
        "scores": tuple(scores),
        "required": required,
        "target": target_text,
    }
    score_text = ", ".join(str(score) for score in scores)
    prompts = (
        f"Four test scores are {score_text}. What fifth score is needed for an average "
        f"of {target_text} across all five tests?",
        f"A student's first four quiz scores are {score_text}. To finish with a five-quiz "
        f"average of {target_text}, what score must the student earn on the last quiz?",
        f"Four equally weighted assessments produced scores of {score_text}. Determine the "
        f"fifth assessment score required to make the overall average {target_text}.",
    )
    expression = f"{target_text}*5-({'+'.join(str(score) for score in scores)})"
    return prompts[surface % len(prompts)], expression, parameters, None


def _cartons_after_damage(
    rng: random.Random, surface: int
) -> tuple[str, str, dict[str, Any], int | None]:
    cartons = rng.randint(3, 9)
    packs = rng.randint(4, 10)
    items = rng.randint(6, 24)
    damaged = rng.randint(4, 25)
    samples = rng.randint(2, 12)
    parameters = {
        "cartons": cartons,
        "packs": packs,
        "items": items,
        "damaged": damaged,
        "samples": samples,
    }
    prompts = (
        f"A shipment has {cartons} cartons, {packs} packs per carton, and {items} items "
        f"per pack. After {damaged} damaged items and {samples} sample items are removed, "
        "how many saleable items remain?",
        f"A warehouse receives {cartons} crates. Each crate contains {packs} boxes with "
        f"{items} components in each box. Inspectors discard {damaged} damaged components, "
        f"and {samples} more are retained as samples. How many components can be sold?",
        f"An order contains {cartons} outer cases, each holding {packs} inner packs of "
        f"{items} units. Before sale, {damaged} defective units and {samples} demonstration "
        "units are removed. Find the number of units left for sale.",
    )
    expression = f"{cartons}*{packs}*{items}-{damaged}-{samples}"
    return prompts[surface % len(prompts)], expression, parameters, None


def _shared_bill(
    rng: random.Random, surface: int
) -> tuple[str, str, dict[str, Any], int | None]:
    diners = rng.randint(6, 14)
    meal = rng.randint(15, 45)
    room = rng.randrange(20, 101, 5)
    nonpaying = rng.randint(1, min(3, diners - 2))
    parameters = {
        "diners": diners,
        "meal": meal,
        "room": room,
        "nonpaying": nonpaying,
    }
    guest_label = f"{nonpaying} {'guest' if nonpaying == 1 else 'guests'}"
    invited_guest_label = (
        f"{nonpaying} invited {'guest' if nonpaying == 1 else 'guests'}"
    )
    attendee_label = f"{nonpaying} {'attendee' if nonpaying == 1 else 'attendees'}"
    prompts = (
        f"A group of {diners} people has meals costing ${meal} per person plus a ${room} "
        f"room charge. {guest_label} {'pays' if nonpaying == 1 else 'pay'} nothing, so the "
        "others split the entire bill "
        "equally. How much does each paying person owe? Round to two decimals.",
        f"At a team dinner for {diners} people, food costs ${meal} for each attendee and a "
        f"private room costs ${room}. The group covers the total cost for "
        f"{invited_guest_label}, while everyone else divides the full bill equally. What "
        "does each payer "
        "owe? Round to two decimals.",
        f"A banquet serves {diners} attendees at ${meal} per person and adds a fixed ${room} "
        f"venue charge. Because {attendee_label} "
        f"{'is' if nonpaying == 1 else 'are'} not charged, the remaining "
        "attendees share every cost equally. Find each paying attendee's share to two decimals.",
    )
    expression = f"({diners}*{meal}+{room})/({diners}-{nonpaying})"
    return prompts[surface % len(prompts)], expression, parameters, 2


def _growth_fee(
    rng: random.Random, surface: int
) -> tuple[str, str, dict[str, Any], int | None]:
    initial = rng.randrange(200, 1501, 25)
    rate1 = rng.randint(3, 12)
    rate2 = rng.randint(3, 12)
    fee = rng.randint(8, 60)
    parameters = {"initial": initial, "rate1": rate1, "rate2": rate2, "fee": fee}
    prompts = (
        f"An account starts with ${initial}, grows by {rate1}% in the first year and "
        f"{rate2}% in the second year, then a one-time ${fee} fee is deducted. What is "
        "the balance? Round to two decimals.",
        f"A fund initially contains ${initial}. It increases by {rate1}% during year one "
        f"and by {rate2}% during year two. After both increases, an administration charge "
        f"of ${fee} is removed. Find the final balance to two decimals.",
        f"An investment of ${initial} earns {rate1}% in its first year. The resulting "
        f"balance then earns {rate2}% in the next year, after which a fixed ${fee} charge "
        "is paid. What amount remains? Round to two decimals.",
    )
    expression = f"{initial}*(1+{rate1}/100)*(1+{rate2}/100)-{fee}"
    return prompts[surface % len(prompts)], expression, parameters, 2


_BUILDERS: dict[str, _Builder] = {
    "curriculum-v2-sales-returns": _sales_returns,
    "curriculum-v2-markup-discount": _markup_discount,
    "curriculum-v2-required-score": _required_final_score,
    "curriculum-v2-cartons-damage": _cartons_after_damage,
    "curriculum-v2-shared-bill": _shared_bill,
    "curriculum-v2-growth-fee": _growth_fee,
}


def _rounded_result(result: int | float, decimal_places: int | None) -> tuple[int | float, str]:
    if decimal_places is None:
        return result, str(result)
    quantum = Decimal(1).scaleb(-decimal_places)
    rounded = Decimal(str(result)).quantize(quantum, rounding=ROUND_HALF_UP)
    return float(rounded), f"{rounded:.{decimal_places}f}"


def build_self_written_seed_expansion(
    *,
    variants_per_family: int = 14,
    parent_examples_per_family: int = 2,
    seed: int = 401,
) -> tuple[Task, ...]:
    """Create review-only variants derived from the audited V3 seed families.

    The two default parent examples are the exact generator indices used by the
    V3 seed screen. New variants begin at index 2, so the expansion does not
    silently duplicate either parent task.

    Failure cases are rejected instead of being written out: non-positive
    counts, duplicate prompts/expressions, impossible required scores, or any
    reference expression that disagrees with the hidden ground truth.
    """

    if variants_per_family <= 0:
        raise ValueError("variants_per_family must be positive")
    if parent_examples_per_family <= 0:
        raise ValueError("parent_examples_per_family must be positive")

    candidates: list[Task] = []
    seen_prompts: set[str] = set()
    seen_expressions: set[tuple[str, str]] = set()
    for family_id in AUDITED_SELF_WRITTEN_SEED_FAMILIES:
        builder = _BUILDERS[family_id]
        parent_task_ids = tuple(
            f"v3-screen-{family_id}-{index:03d}"
            for index in range(parent_examples_per_family)
        )
        for offset in range(variants_per_family):
            variant_index = parent_examples_per_family + offset
            rng = _rng_for(seed, family_id, variant_index)
            surface_variant = rng.randrange(3)
            problem, expression, parameters, decimal_places = builder(rng, surface_variant)
            result = calculator(expression)
            target, target_display = _rounded_result(result, decimal_places)
            tolerance = 0.005 if decimal_places == 2 else 1e-6

            if problem in seen_prompts:
                raise ValueError(f"duplicate expanded prompt: {family_id}-{variant_index:03d}")
            expression_key = (family_id, expression)
            if expression_key in seen_expressions:
                raise ValueError(
                    f"duplicate expanded expression: {family_id}-{variant_index:03d}"
                )
            if family_id == "curriculum-v2-required-score" and not 0 <= result <= 100:
                raise ValueError(f"required score is outside 0..100: {result}")
            seen_prompts.add(problem)
            seen_expressions.add(expression_key)

            metadata: dict[str, Any] = {
                "synthetic": True,
                "curriculum": "v4_seed_derived_self_written_v1",
                "generator_index": variant_index,
                "expansion_seed": seed,
                "surface_variant": surface_variant,
                "parameters": parameters,
                "reference_expression": expression,
                "reference_result": result,
                "ground_truth_display": target_display,
                "answer_decimal_places": decimal_places,
                "expansion_version": "v4_seed_derived_self_written_v1",
                "expansion_kind": "relation_preserving_parameter_and_language_variation",
                "derived_from_audited_seed_family": True,
                "parent_family_id": family_id,
                "parent_seed_task_ids": parent_task_ids,
                "parent_generator_indices": tuple(range(parent_examples_per_family)),
                "review_status": "pending",
                "training_eligible": False,
            }
            task = Task(
                task_id=f"v4-review-{family_id}-{variant_index:03d}",
                family_id=family_id,
                kind=TaskKind.CALCULATOR,
                split=Split.TRAIN,
                prompt=(
                    "Use the calculator to solve this multi-step problem. Return the final "
                    f"number.\n\n{problem}"
                ),
                allowed_tools=("calculator",),
                ground_truth={"type": "number", "value": target, "tolerance": tolerance},
                metadata=metadata,
            )
            if not verify_numeric_answer(result, task.ground_truth).passed:
                raise ValueError(f"reference replay failed: {task.task_id}")
            candidates.append(task)

    expected_count = len(AUDITED_SELF_WRITTEN_SEED_FAMILIES) * variants_per_family
    if len(candidates) != expected_count:
        raise ValueError(
            f"expected {expected_count} seed-derived candidates, found {len(candidates)}"
        )
    validate_task_dataset(candidates)
    return tuple(candidates)


def build_approved_self_written_seed_expansion(
    *,
    variants_per_family: int = 14,
    parent_examples_per_family: int = 2,
    seed: int = 401,
    approved_on: str = "2026-10-05",
) -> tuple[Task, ...]:
    """Freeze the owner-approved review candidates as training-eligible tasks.

    Approval changes metadata only. It does not manufacture SFT trajectories;
    these tasks still need verified search or reference-program trajectories
    before they can enter a supervised training file.
    """

    if not approved_on.strip():
        raise ValueError("approved_on must be non-empty")
    approved = []
    for task in build_self_written_seed_expansion(
        variants_per_family=variants_per_family,
        parent_examples_per_family=parent_examples_per_family,
        seed=seed,
    ):
        metadata = dict(task.metadata)
        metadata.update(
            {
                "review_status": "approved",
                "training_eligible": True,
                "owner_approval_date": approved_on,
                "review_artifact": "docs/V4_SEED_DERIVED_AUDIT_ZH.md",
                "approval_scope": "all_84_self_written_seed_expansion_tasks",
            }
        )
        approved.append(replace(task, metadata=metadata))
    validate_task_dataset(approved)
    return tuple(approved)
