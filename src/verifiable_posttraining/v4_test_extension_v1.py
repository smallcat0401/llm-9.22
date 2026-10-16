"""Tier A: revised test-only variants from the 36 frozen V3 test parents.

The V3 test file and the first pending V4 audit are immutable inputs. This
revision varies numbers without monotonically increasing them, uses several
relation-preserving phrasings per self-written family, and labels variants of
public seeds as synthetic. It does not run a model or approve any task.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Sequence

from .dataset import validate_task_dataset
from .schemas import Split, Task, TaskKind
from .tools.calculator import calculator
from .v4_test_extension import TestExtensionRecord, _public_variant
from .verifier import verify_numeric_answer


def _d(value: int | str) -> Decimal:
    return Decimal(str(value))


def _cents(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


@dataclass(frozen=True, slots=True)
class _Variant:
    question_en: str
    question_zh: str
    expression: str
    expected: float
    tolerance: float
    parameters: dict[str, Any]


# Each tuple is attached to exactly one original row by generator_index. These
# are deliberately not the index-8..15 continuation used by pending audit v0.
_SUBSCRIPTION = (
    (49, 350, 530, "0.11", 7, 9),
    (62, 500, 655, "0.08", 5, 12),
    (39, 250, 420, "0.16", 9, 6),
    (54, 400, 610, "0.10", 6, 11),
    (58, 450, 590, "0.13", 8, 7),
    (43, 300, 485, "0.09", 5, 10),
    (67, 550, 780, "0.14", 9, 12),
    (47, 375, 560, "0.14", 6, 8),
)

_ROUTE = (
    (160, 32, 96, 24, "3.95", 16, 9),
    (270, 30, 144, 24, "4.25", 20, 11),
    (168, 28, 105, 21, "3.70", 24, 8),
    (220, 22, 180, 30, "4.10", 17, 12),
    (195, 39, 128, 32, "3.85", 19, 14),
    (288, 36, 126, 21, "4.40", 27, 10),
    (240, 30, 175, 25, "4.05", 25, 16),
    (315, 35, 160, 20, "4.65", 14, 7),
)

_REFUND = (
    (4, 35, 2, 70, 10, 11, 85),
    (2, 60, 4, 25, 25, 8, 70),
    (5, 32, 3, 54, 15, 9, 90),
    (3, 48, 2, 80, 20, 14, 75),
    (2, 45, 5, 30, 12, 7, 80),
    (4, 52, 2, 68, 18, 10, 65),
    (3, 38, 4, 42, 22, 13, 85),
    (5, 28, 3, 75, 10, 12, 70),
)

_BONUS = (
    (40, 6, 25, 7, 19, 45, "1.5"),
    (37, 9, 29, 5, 21, 38, "1.5"),
    (42, 4, 22, 10, 17, 54, "2"),
    (35, 12, 27, 8, 20, 44, "1.25"),
    (40, 3, 31, 12, 23, 60, "1.5"),
    (38, 8, 24, 6, 16, 49, "2"),
    (36, 10, 26, 9, 22, 32, "1.5"),
    (41, 5, 30, 11, 18, 55, "1.25"),
)


def _subscription_variant(index: int) -> _Variant:
    base, included, used, rate, tax, rental = _SUBSCRIPTION[index]
    # All variants tax the plan plus overage, never the rental.
    en = (
        f"A monthly data plan charges ${base}, covers {included} GB, and costs ${rate} "
          f"per extra GB. Usage is {used} GB. Tax of {tax}% applies to the plan and "
          f"overage charges; an equipment rental fee of ${rental} is added after tax. What is "
        "the final bill? Round to two decimals."
    )
    zh = (f"月度流量套餐费{base}美元，包含{included}GB；超出部分每GB收费{rate}美元。"
          f"本月用了{used}GB。套餐与超额费用加收{tax}%税，之后另加{rental}美元设备租赁费。"
          "最终账单是多少？保留两位小数。")
    if index % 4 == 1:
        en = (f"A customer uses {used} GB on a plan that includes {included} GB for ${base}. "
              f"Additional GB cost ${rate} each. Tax of {tax}% is charged on the base "
              f"plan plus the additional-usage charge, but not on the ${rental} rental "
              "fee. How much is due in total? Round to two decimals.")
        zh = (f"用户在包含{included}GB、套餐费{base}美元的流量方案中用了{used}GB。"
              f"额外流量每GB收费{rate}美元。{tax}%的税只加在套餐费和超额费上，"
              f"{rental}美元设备租赁费不计税。总共应付多少？保留两位小数。")
    elif index % 4 == 2:
        en = (f"For {used} GB of usage, a subscriber pays ${base} for the first "
              f"{included} GB and ${rate} for each GB above that allowance. "
              f"The combined data charges incur {tax}% tax. An additional ${rental} "
              "equipment charge is not taxed. Find the amount payable to two decimals.")
        zh = (f"用户使用了{used}GB流量：前{included}GB按{base}美元套餐费计，"
              f"超出部分每GB为{rate}美元。流量费用合计加收{tax}%税，另有不计税的"
              f"{rental}美元设备费。应付金额是多少？保留两位小数。")
    elif index % 4 == 3:
        en = (f"A bill includes a ${base} plan with {included} GB, plus ${rate} per GB "
              f"for usage beyond the allowance. This month the subscriber used {used} GB. "
              f"Both data charges are subject to {tax}% tax; the ${rental} rental fee "
              "is not. What is the bill? Round to two decimals.")
        zh = (f"账单含{base}美元的{included}GB套餐，超额部分每GB收{rate}美元。"
              f"本月用了{used}GB。套餐费与超额费需缴纳{tax}%税，"
              f"{rental}美元租赁费不计税。账单是多少？保留两位小数。")
    value = (_d(base) + (used - included) * _d(rate)) * (1 + _d(tax)/100) + rental
    expression = f"({base}+({used}-{included})*{rate})*(1+{tax}/100)+{rental}"
    params = dict(base=base, included=included, used=used, rate=rate, tax=tax, rental=rental)
    return _Variant(en, zh, expression, _cents(value), 0.005, params)


def _route_variant(index: int) -> _Variant:
    highway, hmpg, city, cmpg, price, toll, voucher = _ROUTE[index]
    en = (f"A van drives {highway} highway miles at {hmpg} miles per gallon and "
          f"{city} city miles at {cmpg} miles per gallon. Gas costs ${price} per gallon. "
          f"A toll of ${toll} is charged, then a voucher worth ${voucher} is applied. "
          "What is the net cost of the trip?")
    zh = (f"货车在高速公路行驶{highway}英里，每加仑行驶{hmpg}英里；"
          f"市区行驶{city}英里，每加仑行驶{cmpg}英里。油价每加仑{price}美元，"
          f"另付{toll}美元过路费，再抵扣{voucher}美元优惠券。行程净成本是多少？")
    if index % 4 == 1:
        en = (f"Fuel economy is {hmpg} mpg on the highway and {cmpg} mpg in the city. "
              f"A delivery route covers {highway} highway miles and {city} city miles. "
              f"At ${price} per gallon, plus a toll of ${toll} and minus a travel "
              f"credit of ${voucher}, how much does the route cost?")
        zh = (f"送货路线有{highway}英里高速和{city}英里市区路段，"
              f"油耗分别为每加仑{hmpg}英里和{cmpg}英里。每加仑油价{price}美元；"
              f"另加{toll}美元过路费、减去{voucher}美元出行抵扣。路线成本是多少？")
    elif index % 4 == 2:
        en = (f"A driver travels {city} miles in town using one gallon per {cmpg} miles, "
              f"then {highway} miles on the highway using one gallon per {hmpg} miles. "
              f"Fuel is ${price} per gallon. After adding a ${toll} toll and using a "
              f"voucher worth ${voucher} against the total, what is the trip's net cost?")
        zh = (f"司机先在市区行驶{city}英里，每加仑可行驶{cmpg}英里；"
              f"再在高速行驶{highway}英里，每加仑可行驶{hmpg}英里。"
              f"油价每加仑{price}美元，另加{toll}美元过路费，最终用{voucher}美元券抵扣。"
              "行程净成本是多少？")
    elif index % 4 == 3:
        en = (f"A delivery trip has {highway} highway miles ({hmpg} miles per gallon) "
              f"and {city} city miles ({cmpg} miles per gallon). At ${price} per gallon, "
              f"what is the final fuel-and-toll cost after a ${toll} toll and a "
              f"${voucher} credit toward the combined cost?")
        zh = (f"配送行程包括{highway}英里高速路段（每加仑{hmpg}英里）和"
              f"{city}英里市区路段（每加仑{cmpg}英里）。油价每加仑{price}美元，"
              f"另有{toll}美元过路费，总费用再用{voucher}美元抵扣。最终成本是多少？")
    gallons = _d(highway)/hmpg + _d(city)/cmpg
    expression = f"({highway}/{hmpg}+{city}/{cmpg})*{price}+{toll}-{voucher}"
    params = dict(highway=highway, highway_mpg=hmpg, city=city, city_mpg=cmpg,
                  fuel_price=price, toll=toll, voucher=voucher)
    return _Variant(en, zh, expression, float(gallons * _d(price) + toll - voucher), 1e-6, params)


def _refund_variant(index: int) -> _Variant:
    qa, pa, qb, pb, discount, delivery, refund = _REFUND[index]
    en = (f"A shopper buys {qa} items at ${pa} each and {qb} at ${pb} each in a "
          f"{discount}%-off sale, and pays a nonrefundable ${delivery} delivery fee. "
          f"One ${pb} item is returned; only {refund}% of its sale price is refunded "
          "because of a restocking charge. What is the shopper's net payment? "
          "Round to two decimals.")
    zh = (f"顾客在全场优惠{discount}%时买了{qa}件单价{pa}美元的商品、"
          f"{qb}件单价{pb}美元的商品，并支付不退还的{delivery}美元配送费。"
          f"后来退回一件原价{pb}美元的商品，因补货费只退该商品折后价的{refund}%。"
          "顾客最终净付款是多少？保留两位小数。")
    if index % 4 == 1:
        en = (f"With a storewide discount of {discount}%, an order contains {qa} "
              f"units priced ${pa} and {qb} units priced ${pb}. Delivery adds ${delivery} "
              f"and is not refunded. The customer later returns one ${pb} unit and "
              f"receives {refund}% of that unit's discounted price. How much has the "
              "customer paid in the end? Round to two decimals.")
        zh = (f"全场优惠{discount}%时，订单有{qa}件原价{pa}美元的商品和"
              f"{qb}件原价{pb}美元的商品；配送费{delivery}美元不退。随后退回一件"
              f"原价{pb}美元的商品，退款为该件折后价的{refund}%。最终净付多少？"
              "保留两位小数。")
    elif index % 4 == 2:
        en = (f"A {discount}%-off promotion applies to {qa} products at ${pa} and "
              f"{qb} products at ${pb}. A ${delivery} shipping charge cannot be "
              f"recovered. After purchase, one ${pb} product is returned for a refund "
              f"equal to {refund}% of its discounted price. Find the final net spending "
              "to two decimals.")
        zh = (f"{qa}件单价{pa}美元及{qb}件单价{pb}美元的商品均参加优惠{discount}%活动。"
              f"另付不可退的{delivery}美元运费。购买后退回一件原价{pb}美元的商品，"
              f"退款是其折后价的{refund}%。最终净支出是多少？保留两位小数。")
    elif index % 4 == 3:
        en = (f"At {discount}% off, someone purchases {qa} items normally costing "
              f"${pa} apiece and {qb} normally costing ${pb} apiece. The ${delivery} "
              f"delivery charge is nonrefundable. On returning one ${pb} item, the "
              f"buyer gets back {refund}% of its discounted price. What remains paid "
              "overall? Round to two decimals.")
        zh = (f"某人按原价优惠{discount}%购买{qa}件每件{pa}美元的商品和"
              f"{qb}件每件{pb}美元的商品。{delivery}美元配送费不退。"
              f"退回一件原价{pb}美元的商品后，只拿回该件折后价的{refund}%。"
              "最后实际支付多少？保留两位小数。")
    factor = 1 - _d(discount)/100
    value = (qa*pa + qb*pb)*factor + delivery - _d(pb)*factor*refund/100
    expression = (f"({qa}*{pa}+{qb}*{pb})*(1-{discount}/100)+{delivery}"
                  f"-{pb}*(1-{discount}/100)*{refund}/100")
    params = dict(quantity_a=qa, price_a=pa, quantity_b=qb, price_b=pb,
                  discount_percent=discount, delivery=delivery, refund_percent=refund)
    return _Variant(en, zh, expression, _cents(value), 0.005, params)


def _bonus_variant(index: int) -> _Variant:
    regular, overtime, rate, bonus, tax, insurance, multiplier = _BONUS[index]
    en = (f"An employee works {regular} regular hours at ${rate} per hour and "
          f"{overtime} overtime hours at {multiplier} times that rate. A bonus is "
          f"{bonus}% of regular-hour wages. A {tax}% tax is taken from all gross "
          f"earnings; then ${insurance} insurance is deducted. What is take-home pay? "
          "Round to two decimals.")
    zh = (f"员工正常工作{regular}小时，正常时薪{rate}美元；加班{overtime}小时，"
          f"加班时薪是正常时薪的{multiplier}倍。奖金为正常工时工资的{bonus}%。"
          f"全部税前收入先扣{tax}%税，再扣{insurance}美元保险费。"
          "实发工资是多少？保留两位小数。")
    if index % 4 == 1:
        en = (f"Regular pay covers {regular} hours at ${rate} hourly. The worker "
              f"also has {overtime} overtime hours paid at {multiplier} times the "
              f"hourly rate and a bonus of {bonus}% of regular pay. After {tax}% tax "
              f"on the entire gross amount and a further ${insurance} insurance "
              "deduction, what is net pay? Round to two decimals.")
        zh = (f"员工按每小时{rate}美元领取{regular}小时正常工资；"
              f"另有{overtime}小时加班，时薪为正常时薪的{multiplier}倍，"
              f"奖金占正常工资的{bonus}%。全部税前收入扣{tax}%税后，再扣"
              f"{insurance}美元保险费。净工资是多少？保留两位小数。")
    elif index % 4 == 2:
        en = (f"For {regular} normal hours and {overtime} overtime hours, the "
              f"normal hourly wage is ${rate} and overtime pays {multiplier} times "
              f"as much. Add a bonus equal to {bonus}% of wages from normal hours. "
              f"The entire gross pay is subject to {tax}% tax; ${insurance} insurance "
              "is deducted from post-tax pay. "
              "Find take-home pay to two decimals.")
        zh = (f"正常工作{regular}小时、加班{overtime}小时，正常时薪{rate}美元，"
              f"加班时薪为其{multiplier}倍。另加相当于正常工时工资{bonus}%的奖金。"
              f"全部税前收入需缴纳{tax}%税，税后工资还要扣{insurance}美元保险费。"
              "实发工资是多少？保留两位小数。")
    elif index % 4 == 3:
        en = (f"A pay period includes {regular} hours at ${rate}/hour, plus "
              f"{overtime} hours at {multiplier} times the regular rate. The "
              f"performance bonus is {bonus}% of regular-hours pay only. Deduct "
              f"{tax}% tax from the full pre-tax pay and then a fixed ${insurance} "
              "insurance charge. How much is paid out? Round to two decimals.")
        zh = (f"某工资周期正常工作{regular}小时，每小时{rate}美元；"
              f"另加班{overtime}小时，时薪为正常时薪的{multiplier}倍。"
              f"绩效奖只按正常工时工资的{bonus}%算。税前工资整体先扣{tax}%税，"
              f"然后再减固定{insurance}美元保险费。实发多少？保留两位小数。")
    gross = _d(regular)*rate + _d(overtime)*rate*_d(multiplier) + _d(regular)*rate*bonus/100
    value = gross*(1 - _d(tax)/100) - insurance
    expression = (f"({regular}*{rate}+{overtime}*{rate}*{multiplier}"
                  f"+{regular}*{rate}*{bonus}/100)*(1-{tax}/100)-{insurance}")
    params = dict(regular_hours=regular, overtime_hours=overtime, hourly_rate=rate,
                  bonus_percent=bonus, tax_percent=tax, insurance=insurance,
                  overtime_multiplier=multiplier)
    return _Variant(en, zh, expression, _cents(value), 0.005, params)


_BUILDERS = {
    "v3-eval-test-subscription-overage-v1": _subscription_variant,
    "v3-eval-test-route-cost-v1": _route_variant,
    "v3-eval-test-partial-refund-v1": _refund_variant,
    "v3-eval-test-bonus-deduction-v1": _bonus_variant,
}

_PUBLIC_FAMILIES = {
    "v3-eval-test-public-loan-repayment-v1",
    "v3-eval-test-public-bogo-purchase-v1",
    "v3-eval-test-public-delivery-fee-v1",
    "v3-eval-test-public-weighted-test-score-v1",
}


def build_v4_test_extension_v1_records(frozen_test: Sequence[Task]) -> tuple[TestExtensionRecord, ...]:
    """Build pending v1 candidates; reject missing/extra parents and wrong splits."""

    if len(frozen_test) != 36 or len({task.task_id for task in frozen_test}) != 36:
        raise ValueError("expected 36 distinct frozen V3 test tasks")
    counts = Counter(task.family_id for task in frozen_test)
    if counts != {**{family: 8 for family in _BUILDERS},
                  **{family: 1 for family in _PUBLIC_FAMILIES}}:
        raise ValueError("unexpected frozen V3 test family composition")
    records: list[TestExtensionRecord] = []
    for parent in frozen_test:
        if parent.split is not Split.TEST or parent.kind is not TaskKind.CALCULATOR:
            raise ValueError(f"invalid test parent: {parent.task_id}")
        if parent.family_id in _BUILDERS:
            index = parent.metadata.get("generator_index")
            if not isinstance(index, int) or not 0 <= index < 8:
                raise ValueError(f"invalid parent generator index: {parent.task_id}")
            variant = _BUILDERS[parent.family_id](index)
            source_group = "self_written_extension"
            prefix = "Use the calculator to solve this quantitative reasoning problem. "
        else:
            if (parent.family_id not in _PUBLIC_FAMILIES
                    or parent.metadata.get("source_dataset") != "openai/grade-school-math"):
                raise ValueError(f"invalid public-seed parent: {parent.task_id}")
            en, zh, expression, expected, tolerance = _public_variant(parent.family_id)
            variant = _Variant(en, zh, expression, expected, tolerance, {})
            source_group = "public_seed_derived_synthetic"
            prefix = "Solve this problem. The calculator tool is available for arithmetic. "
        truth = {"type": "number", "value": variant.expected, "tolerance": variant.tolerance}
        if not verify_numeric_answer(calculator(variant.expression), truth).passed:
            raise ValueError(f"reference program and independent oracle disagree: {parent.task_id}")
        slug = parent.family_id.removeprefix("v3-eval-test-").removesuffix("-v1")
        index_suffix = parent.metadata.get("generator_index", 0)
        task = Task(
            task_id=f"v4-review-test-synthetic-{slug}-{index_suffix:03d}",
            family_id=parent.family_id,
            kind=TaskKind.CALCULATOR,
            split=Split.TEST,
            prompt=prefix + f"Return the final number.\n\n{variant.question_en}",
            allowed_tools=("calculator",),
            ground_truth=truth,
            metadata={
                "dataset_version": "v4_test_extension_audit_v1",
                "synthetic": True,
                "source_group": source_group,
                "parent_test_task_id": parent.task_id,
                "parent_source_dataset": parent.metadata.get("source_dataset"),
                "parent_source_index": parent.metadata.get("source_index"),
                "evaluation_only": True,
                "training_eligible": False,
                "review_status": "pending",
                "reference_expression": variant.expression,
                "parameters": variant.parameters,
                "wording_variant": (index_suffix % 4) + 1,
                "review_artifact": "docs/V4_TEST_EXTENSION_AUDIT_V1_ZH.md",
            },
        )
        records.append(TestExtensionRecord(task, variant.question_zh))
    if len({record.task.task_id for record in records}) != 36:
        raise ValueError("test extension produced duplicate task IDs")
    if len({record.task.prompt for record in records}) != 36:
        raise ValueError("test extension produced duplicate prompts")
    validate_task_dataset((*frozen_test, *(record.task for record in records)))
    return tuple(records)
