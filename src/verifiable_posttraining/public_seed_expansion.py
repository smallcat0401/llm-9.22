"""Tier A synthetic expansion of the reviewed public-table relation seeds.

The source tables themselves are not copied or numerically mutated. Each
builder preserves one reviewed quantitative relation and creates a fresh,
clearly synthetic table whose reference expression is replayed locally.

All outputs are review-only. They cannot enter training until the owner audits
the Chinese view and a separate approval artifact marks them eligible.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, replace
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Callable, Sequence

from .dataset import validate_task_dataset
from .schemas import Split, Task, TaskKind
from .tools.calculator import calculator
from .verifier import verify_numeric_answer


PUBLIC_SEED_PARENT_TASKS: dict[str, tuple[str, ...]] = {
    "v3-public-weighted_average-v1": (
        "v3-public-cb26a8ffa95b-arithmetic",
        "v3-public-ea79960b2b5e-arithmetic-revised-v2",
    ),
    "v3-public-aggregate_percent_change-v1": (
        "v3-public-f2f32edba913-arithmetic",
        "v3-public-e511f3abfa5e-arithmetic",
        "v3-public-550b417fd1d0-arithmetic",
    ),
    "v3-public-aggregate_percent_change_with_loss-v1": (
        "v3-public-c84b259d3bfe-arithmetic",
    ),
    "v3-public-average_growth_rate-v1": (
        "v3-public-564f2d6051c0-arithmetic-revised-v2",
        "v3-public-4b50d974aae5-arithmetic",
        "v3-public-13b99cafff24-arithmetic-revised-v2",
        "v3-public-776305a10cc6-arithmetic-revised-v2",
    ),
    "v3-public-derived_value_percent_change-v1": (
        "v3-public-ab005e597c33-arithmetic-rounding-revised-v1",
        "v3-public-4a29948bb22b-arithmetic",
    ),
    "v3-public-difference_of_averages-v1": (
        "v3-public-993d968c025a-arithmetic-revised-v2",
        "v3-public-9a63b89ea330-arithmetic",
        "v3-public-af1f11d98652-arithmetic",
        "v3-public-f5fdb156cd45-arithmetic-revised-v2",
    ),
    "v3-public-midpoint_rate_application-v1": (
        "v3-public-abe2824b6e81-arithmetic-revised-v2",
    ),
    "v3-public-multi_period_interest-v1": (
        "v3-public-4dff5a6c3f03-arithmetic",
    ),
    "v3-public-payout_ratio-v1": (
        "v3-public-244426e00be4-arithmetic",
    ),
    "v3-public-ratio_of_aggregates-v1": (
        "v3-public-7aca02f2885b-arithmetic",
    ),
    "v3-public-ratio_of_derived_values-v1": (
        "v3-public-aa133d54fab4-arithmetic",
    ),
    "v3-public-signed_multi_value_average-v1": (
        "v3-public-42e42100b593-arithmetic",
        "v3-public-9f547636b5b4-arithmetic-revised-v2",
        "v3-public-fee44b520741-arithmetic",
    ),
    "v3-public-signed_percent_change-v1": (
        "v3-public-9d6f397353af-arithmetic",
        "v3-public-2adfb9bf033b-arithmetic",
        "v3-public-aa20ff7068b0-arithmetic",
    ),
}


@dataclass(frozen=True, slots=True)
class PublicExpansionRecord:
    task: Task
    question_zh: str
    table_zh: tuple[tuple[str, ...], ...]


@dataclass(frozen=True, slots=True)
class _Variant:
    question_en: str
    question_zh: str
    table_en: tuple[tuple[str, ...], ...]
    table_zh: tuple[tuple[str, ...], ...]
    expression: str
    decimal_places: int
    parameters: dict[str, Any]
    subtype: str


_Builder = Callable[[random.Random, int], _Variant]


def _rng_for(seed: int, family_id: str, index: int) -> random.Random:
    material = f"{seed}:{family_id}:{index}".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(material).digest()[:8], "big"))


def _render_table(rows: Sequence[Sequence[str]]) -> str:
    def render(row: Sequence[str]) -> str:
        return "| " + " | ".join(str(cell).replace("|", "\\|") for cell in row) + " |"

    return "\n".join(
        [render(rows[0]), render(["---"] * len(rows[0]))]
        + [render(row) for row in rows[1:]]
    )


def _number(value: int | float) -> str:
    if isinstance(value, float):
        return f"{value:,.2f}"
    return f"{value:,}"


def _signed_table_value(value: int) -> str:
    if value < 0:
        return f"({_number(abs(value))})"
    if value == 0:
        return "—"
    return _number(value)


def _sum_expression(values: Sequence[int]) -> str:
    parts = [str(values[0])]
    for value in values[1:]:
        parts.append(f"+{value}" if value >= 0 else str(value))
    return "".join(parts)


def _join_names(names: Sequence[str], *, conjunction: str) -> str:
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} {conjunction} {names[1]}"
    return f"{', '.join(names[:-1])}, {conjunction} {names[-1]}"


def _weighted_average(rng: random.Random, index: int) -> _Variant:
    units = tuple(rng.randint(20_000, 900_000) for _ in range(3))
    price1_cents = rng.randint(2500, 24_000)
    price2_cents = round(price1_cents * rng.randint(75, 125) / 100)
    price3_cents = round(price1_cents * rng.randint(75, 125) / 100)
    prices = (
        price1_cents / 100,
        price2_cents / 100,
        price3_cents / 100,
    )
    selection_plans = ((0, 1), (0, 2), (1, 2), (0, 1, 2), (0, 2), (0, 1, 2))
    selected = selection_plans[index % len(selection_plans)]
    names_en = ("January", "February", "March")
    names_zh = ("一月", "二月", "三月")
    selected_en = _join_names(tuple(names_en[i] for i in selected), conjunction="and")
    selected_zh = "、".join(names_zh[i] for i in selected)
    questions = (
        (
            f"Taking the units purchased in {selected_en} into account, what was the "
            "unit-count-weighted average price across the selected months? Round to two decimals.",
            f"按{selected_zh}的采购数量加权，所选月份的加权平均单价是多少？保留两位小数。",
        ),
        (
            f"Use the {selected_en} purchase counts as weights. Calculate the weighted "
            "average purchase price for those months, rounded to two decimals.",
            f"以{selected_zh}的采购数量作为权重，计算这些月份的加权平均采购价格，保留两位小数。",
        ),
    )
    question_en, question_zh = questions[index % 2]
    table_en = (
        ("Period", "Units purchased", "Average price per unit"),
        *((names_en[i], _number(units[i]), f"${prices[i]:.2f}") for i in range(3)),
    )
    table_zh = (
        ("期间", "采购数量", "平均单价"),
        *((names_zh[i], _number(units[i]), f"${prices[i]:.2f}") for i in range(3)),
    )
    numerator = "+".join(f"{units[i]}*{prices[i]:.2f}" for i in selected)
    denominator = "+".join(str(units[i]) for i in selected)
    expression = f"({numerator})/({denominator})"
    return _Variant(
        question_en,
        question_zh,
        table_en,
        table_zh,
        expression,
        2,
        {
            "units": units,
            "prices": prices,
            "selected_indices": selected,
            "selected_periods": tuple(names_en[i] for i in selected),
        },
        f"{len(selected)}_period_weighted_average",
    )


def _aggregate_percent_change(rng: random.Random, index: int) -> _Variant:
    old = tuple(rng.randint(300, 5000) for _ in range(3))
    new = tuple(round(value * rng.randint(65, 150) / 100) for value in old)
    selection_plans = ((0, 1), (0, 2), (1, 2), (0, 1, 2), (1, 2), (0, 1, 2))
    selected = selection_plans[index % len(selection_plans)]
    labels_en = ("North", "South", "Central")
    labels_zh = ("北区", "南区", "中区")
    selected_en = _join_names(tuple(labels_en[i] for i in selected), conjunction="and")
    selected_zh = "、".join(labels_zh[i] for i in selected)
    questions = (
        (
            f"What was the percentage change in the combined revenue of the {selected_en} "
            "divisions from 2022 to 2023? Round to two decimals.",
            f"{selected_zh}的合计收入从 2022 年到 2023 年变化了百分之多少？保留两位小数。",
        ),
        (
            f"For the {selected_en} divisions taken together, how did revenue change in "
            "percentage terms from 2022 to 2023? Round to two decimals.",
            f"将{selected_zh}作为一个整体，其收入从 2022 年到 2023 年变化了百分之多少？"
            "保留两位小数。",
        ),
    )
    question_en, question_zh = questions[index % 2]
    table_en = (
        ("Division", "2023 revenue", "2022 revenue"),
        *((labels_en[i], _number(new[i]), _number(old[i])) for i in range(3)),
    )
    table_zh = (
        ("部门", "2023 年收入", "2022 年收入"),
        *((labels_zh[i], _number(new[i]), _number(old[i])) for i in range(3)),
    )
    old_expression = "+".join(str(old[i]) for i in selected)
    new_expression = "+".join(str(new[i]) for i in selected)
    expression = f"(({new_expression})-({old_expression}))/({old_expression})*100"
    return _Variant(
        question_en,
        question_zh,
        table_en,
        table_zh,
        expression,
        2,
        {
            "old": old,
            "new": new,
            "selected_indices": selected,
            "selected_divisions": tuple(labels_en[i] for i in selected),
        },
        f"{len(selected)}_row_aggregate_percent_change",
    )


def _aggregate_percent_change_with_loss(rng: random.Random, index: int) -> _Variant:
    old = [rng.randint(300, 1200) for _ in range(4)]
    new = [rng.randint(300, 1200) for _ in range(4)]
    loss_index = index % 4
    zero_index = (index + 2) % 4
    old[loss_index] = -rng.randint(40, 280)
    new[loss_index] = -rng.randint(40, 280)
    old[zero_index] = rng.randint(80, 400)
    new[zero_index] = 0
    old_total, new_total = sum(old), sum(new)
    questions = (
        (
            "Parentheses denote operating losses and the dash means zero. After aggregating "
            "all four divisions, what was the percentage change in total operating profit "
            "from 2022 to 2023? Round to two decimals.",
            "括号表示经营亏损，横线表示零。汇总四个部门后，总经营利润从 2022 年到 2023 年"
            "变化了百分之多少？保留两位小数。",
        ),
        (
            "Treat parenthesized figures as losses and the dash as zero. Considering all four "
            "divisions together, what was the signed percentage change in operating profit "
            "from 2022 to 2023? Round to two decimals.",
            "将括号内数字视为亏损、横线视为零。将四个部门作为一个整体，经营利润从 2022 "
            "年到 2023 年的带方向百分比变化是多少？保留两位小数。",
        ),
    )
    question_en, question_zh = questions[index % 2]
    labels_en = ("Consumer", "Industrial", "International", "Legacy")
    labels_zh = ("消费业务", "工业业务", "国际业务", "传统业务")
    table_en = (("Division", "2023 operating profit", "2022 operating profit"),) + tuple(
        (label, _signed_table_value(new_value), _signed_table_value(old_value))
        for label, new_value, old_value in zip(labels_en, new, old, strict=True)
    )
    table_zh = (("部门", "2023 年经营利润", "2022 年经营利润"),) + tuple(
        (label, _signed_table_value(new_value), _signed_table_value(old_value))
        for label, new_value, old_value in zip(labels_zh, new, old, strict=True)
    )
    expression = f"(({_sum_expression(new)})-({_sum_expression(old)}))/({_sum_expression(old)})*100"
    return _Variant(
        question_en, question_zh, table_en, table_zh, expression, 2,
        {
            "old": tuple(old),
            "new": tuple(new),
            "old_total": old_total,
            "new_total": new_total,
            "loss_index": loss_index,
            "zero_index": zero_index,
        },
        "all_rows_signed_aggregate_percent_change",
    )


def _average_growth_rate(rng: random.Random, index: int) -> _Variant:
    contexts = (
        ("research expense", "Research expense", "研发费用", (2017, 2018, 2019)),
        ("online sales", "Online sales", "线上销售额", (2020, 2021, 2022)),
        ("energy consumption", "Energy consumption", "能源消耗", (2021, 2022, 2023)),
    )
    metric_en, row_label_en, row_label_zh, years = contexts[index % len(contexts)]
    first, second, third = years
    value1 = rng.randint(1000, 9000)
    rate_pairs = ((-20, 15), (25, -10), (-15, -5), (10, 30), (35, -20), (-8, 22))
    rate1, rate2 = rate_pairs[index % len(rate_pairs)]
    value2 = round(value1 * (100 + rate1) / 100)
    value3 = round(value2 * (100 + rate2) / 100)
    values = (value1, value2, value3)
    questions = (
        (
            f"What is the arithmetic mean of the {first}-{second} and {second}-{third} "
            f"year-on-year percentage changes in {metric_en}? Round to two decimals.",
            f"{row_label_zh}在 {first}—{second} 年和 {second}—{third} 年的两个同比变化率，"
            "其算术平均值是多少？"
            "保留两位小数。",
        ),
        (
            "What was the arithmetic average of the two adjacent annual percentage changes "
            f"in {metric_en}? This is not CAGR. Round to two decimals.",
            f"{row_label_zh}两个相邻年度百分比变化率的算术平均值是多少？这里求的不是 CAGR。"
            "保留两位小数。",
        ),
    )
    question_en, question_zh = questions[index % 2]
    table_en = (
        ("Metric", str(third), str(second), str(first)),
        (row_label_en, _number(value3), _number(value2), _number(value1)),
    )
    table_zh = (
        ("指标", str(third), str(second), str(first)),
        (row_label_zh, _number(value3), _number(value2), _number(value1)),
    )
    expression = (
        f"((({value2}-{value1})/{value1})+"
        f"(({value3}-{value2})/{value2}))/2*100"
    )
    return _Variant(
        question_en, question_zh, table_en, table_zh, expression, 2,
        {
            "values": values,
            "planned_rates": (rate1, rate2),
            "metric": row_label_en,
            "years": years,
        },
        "arithmetic_mean_of_two_yoy_rates",
    )


def _derived_value_percent_change(rng: random.Random, index: int) -> _Variant:
    quantity1 = rng.randint(100_000, 900_000)
    quantity2 = round(quantity1 * rng.randint(60, 140) / 100)
    price1 = rng.randint(2000, 20_000) / 100
    price2 = round(price1 * rng.randint(70, 150) / 100, 2)
    questions = (
        (
            "Based on the number of unvested awards and fair value per award, what was the "
            "percentage change in their total value from 2022 to 2023? Round to two decimals.",
            "根据未归属奖励的数量和每项奖励的公允价值，其总价值从 2022 年到 2023 年"
            "变化了百分之多少？保留两位小数。",
        ),
        (
            "How much did the total fair value of unvested awards change in percentage terms "
            "from 2022 to 2023? Use the counts and per-award values shown, and round to two "
            "decimals.",
            "未归属奖励的总公允价值从 2022 年到 2023 年变化了百分之多少？请使用表中的"
            "奖励数量和每项奖励公允价值，并保留两位小数。",
        ),
    )
    question_en, question_zh = questions[index % 2]
    table_en = (
        ("Period", "Unvested awards", "Fair value per award"),
        ("End of 2022", _number(quantity1), f"${price1:.2f}"),
        ("End of 2023", _number(quantity2), f"${price2:.2f}"),
    )
    table_zh = (
        ("期间", "未归属奖励数量", "每项奖励公允价值"),
        ("2022 年末", _number(quantity1), f"${price1:.2f}"),
        ("2023 年末", _number(quantity2), f"${price2:.2f}"),
    )
    expression = f"(({quantity2}*{price2})-({quantity1}*{price1}))/({quantity1}*{price1})*100"
    return _Variant(
        question_en, question_zh, table_en, table_zh, expression, 2,
        {"quantities": (quantity1, quantity2), "prices": (price1, price2)},
        "percent_change_of_quantity_times_unit_value",
    )


def _difference_of_averages(rng: random.Random, index: int) -> _Variant:
    mode = index % 3
    if mode == 0:
        v17, v18, v19 = (rng.randint(1000, 20_000) for _ in range(3))
        question_en = (
            "Compute the 2018-2019 two-year average revenue minus the 2017-2018 "
            "two-year average revenue. Report an increase as positive and a decrease as negative."
        )
        question_zh = (
            "用 2018—2019 两年平均收入减去 2017—2018 两年平均收入。增加记为正，减少记为负。"
        )
        table_en = (("Metric", "2019", "2018", "2017"), ("Revenue", _number(v19), _number(v18), _number(v17)))
        table_zh = (("指标", "2019", "2018", "2017"), ("收入", _number(v19), _number(v18), _number(v17)))
        expression = f"({v18}+{v19})/2-({v17}+{v18})/2"
        parameters = {"values": (v17, v18, v19)}
        subtype = "later_period_average_minus_earlier_period_average"
    elif mode == 1:
        a22, a23, b22, b23 = (rng.randint(1000, 20_000) for _ in range(4))
        question_en = (
            "What is the 2022-2023 average processing revenue minus the 2022-2023 "
            "average cloud revenue? Report a signed result."
        )
        question_zh = "2022—2023 年处理业务的平均收入减去云业务的平均收入，结果是多少？保留正负号。"
        table_en = (
            ("Business", "2023 revenue", "2022 revenue"),
            ("Processing", _number(a23), _number(a22)),
            ("Cloud", _number(b23), _number(b22)),
        )
        table_zh = (
            ("业务", "2023 年收入", "2022 年收入"),
            ("处理业务", _number(a23), _number(a22)),
            ("云业务", _number(b23), _number(b22)),
        )
        expression = f"({a22}+{a23})/2-({b22}+{b23})/2"
        parameters = {"processing": (a22, a23), "cloud": (b22, b23)}
        subtype = "category_average_difference"
    else:
        v20, v21, v22, v23 = (rng.randint(1000, 20_000) for _ in range(4))
        question_en = (
            "What is the 2022-2023 average service revenue minus the 2020-2021 average "
            "service revenue? Report a signed result."
        )
        question_zh = (
            "2022—2023 年服务收入的平均值减去 2020—2021 年服务收入的平均值，结果是多少？"
            "保留正负号。"
        )
        table_en = (
            ("Metric", "2023", "2022", "2021", "2020"),
            ("Service revenue", _number(v23), _number(v22), _number(v21), _number(v20)),
        )
        table_zh = (
            ("指标", "2023", "2022", "2021", "2020"),
            ("服务收入", _number(v23), _number(v22), _number(v21), _number(v20)),
        )
        expression = f"({v22}+{v23})/2-({v20}+{v21})/2"
        parameters = {"earlier": (v20, v21), "later": (v22, v23)}
        subtype = "non_overlapping_period_average_difference"
    return _Variant(question_en, question_zh, table_en, table_zh, expression, 2, parameters, subtype)


def _midpoint_rate_application(rng: random.Random, index: int) -> _Variant:
    notional = rng.randrange(500, 5001, 10) / 10
    low_cents = rng.randint(250, 750)
    high_cents = low_cents + rng.randint(75, 400)
    low_text, high_text = f"{low_cents / 100:.2f}", f"{high_cents / 100:.2f}"
    low, high = float(low_text), float(high_text)
    instruments = (
        ("Swap portfolio", "掉期组合"),
        ("Revolving facility", "循环信贷额度"),
        ("Term loan", "定期贷款"),
    )
    instrument_en, instrument_zh = instruments[index % len(instruments)]
    questions = (
        (
            "Using the midpoint of the stated rate range, estimate the annual interest expense "
            "in millions of dollars. Round to one decimal place.",
            "使用所列利率区间的中点，估算年度利息费用（百万美元）。保留一位小数。",
        ),
        (
            "Using the rate-range midpoint, what annual interest cost does the notional amount "
            "imply? Report millions of dollars to one decimal place.",
            "使用利率区间的中点，该名义金额对应的年度利息成本是多少？以百万美元表示并"
            "保留一位小数。",
        ),
    )
    question_en, question_zh = questions[index % 2]
    table_en = (
        ("Instrument", "Notional amount ($m)", "Rate range"),
        (instrument_en, f"{notional:.1f}", f"{low:.2f}%–{high:.2f}%"),
    )
    table_zh = (
        ("工具", "名义金额（百万美元）", "利率区间"),
        (instrument_zh, f"{notional:.1f}", f"{low:.2f}%—{high:.2f}%"),
    )
    expression = f"{notional:.1f}*(({low_text}+{high_text})/2)/100"
    return _Variant(
        question_en, question_zh, table_en, table_zh, expression, 1,
        {
            "notional": notional,
            "low": low,
            "high": high,
            "instrument": instrument_en,
        },
        "midpoint_rate_times_notional",
    )


def _multi_period_interest(rng: random.Random, index: int) -> _Variant:
    payment = rng.randint(20, 400) / 10
    frequency = rng.choice((2, 4))
    years = rng.randint(4, 15)
    instruments = (("Notes", "票据"), ("Bond", "债券"), ("Term loan", "定期贷款"))
    instrument_en, instrument_zh = instruments[index % len(instruments)]
    questions = (
        (
            "Based on the payment schedule shown, what is the total interest paid over the "
            "full term, in millions of dollars?",
            "根据表中的付款安排，整个期限内累计支付多少百万美元利息？",
        ),
        (
            "Using the amount, annual payment count, and term in the table, how many millions "
            "of dollars of interest are paid in total?",
            "使用表中的每次付款额、每年付款次数和期限，累计支付的利息是多少百万美元？",
        ),
    )
    question_en, question_zh = questions[index % 2]
    table_en = (
        ("Payment schedule", "Payment amount ($m)", "Payments per year", "Full years"),
        (instrument_en, f"{payment:.1f}", str(frequency), str(years)),
    )
    table_zh = (
        ("付款安排", "每次付款（百万美元）", "每年付款次数", "完整年数"),
        (instrument_zh, f"{payment:.1f}", str(frequency), str(years)),
    )
    expression = f"{payment}*{frequency}*{years}"
    return _Variant(
        question_en, question_zh, table_en, table_zh, expression, 1,
        {
            "payment": payment,
            "frequency": frequency,
            "years": years,
            "instrument": instrument_en,
        },
        "installment_amount_times_payment_count",
    )


def _payout_ratio(rng: random.Random, index: int) -> _Variant:
    shares = rng.randint(20_000, 100_000)
    dividend = rng.randint(10, 150) / 100
    total_dividends = shares * dividend
    net_income = rng.randint(int(total_dividends * 1.3), int(total_dividends * 4.0))
    questions = (
        (
            "Based on the values shown, what was the common dividend payout ratio? Return a "
            "percentage rounded to two decimals.",
            "根据表中数值，普通股股利支付率是多少？以百分比表示并保留两位小数。",
        ),
        (
            "Based on shares outstanding, dividend per share, and income available for "
            "dividends, what percentage of available income was paid as common dividends? "
            "Round to two decimals.",
            "根据流通股数、每股股利和可供分红净利润，作为普通股股利支付的金额占可供分红"
            "净利润的百分比是多少？保留两位小数。",
        ),
    )
    question_en, question_zh = questions[index % 2]
    table_en = (
        ("Metric", "Value"),
        ("Common shares outstanding (thousands)", _number(shares)),
        ("Dividend per common share", f"${dividend:.2f}"),
        ("Net income available for dividends ($ thousands)", _number(net_income)),
    )
    table_zh = (
        ("指标", "数值"),
        ("流通普通股（千股）", _number(shares)),
        ("每股普通股股利", f"${dividend:.2f}"),
        ("可供分红净利润（千美元）", _number(net_income)),
    )
    expression = f"({shares}*{dividend})/{net_income}*100"
    return _Variant(
        question_en, question_zh, table_en, table_zh, expression, 2,
        {"shares": shares, "dividend": dividend, "net_income": net_income},
        "total_dividends_over_available_income",
    )


def _ratio_of_aggregates(rng: random.Random, index: int) -> _Variant:
    total1, total2 = rng.randint(1000, 8000), rng.randint(1000, 8000)
    numerator1, numerator2 = (
        rng.randint(200, total1 - 100),
        rng.randint(200, total2 - 100),
    )
    contexts = (
        ("long-term debt", "Long-term debt", "长期债务", "Total debt", "总债务", "Debt metric", "债务指标"),
        ("renewable output", "Renewable output", "可再生能源产量", "Total output", "总产量", "Output metric", "产量指标"),
        ("express shipments", "Express shipments", "加急货件", "Total shipments", "总货件", "Shipment metric", "货运指标"),
    )
    (
        numerator_phrase_en,
        numerator_label_en,
        numerator_label_zh,
        total_label_en,
        total_label_zh,
        header_en,
        header_zh,
    ) = contexts[index % len(contexts)]
    questions = (
        (
            f"On a combined 2022-and-2023 basis, what percentage of {total_label_en.lower()} "
            f"was {numerator_phrase_en}? Round to two decimals.",
            f"合并计算 2022 年和 2023 年，{numerator_label_zh}占{total_label_zh}的百分比是多少？"
            "保留两位小数。",
        ),
        (
            f"Across 2022 and 2023 together, what share of {total_label_en.lower()} consisted "
            f"of {numerator_phrase_en}? Express the result as a percentage rounded to two "
            "decimals.",
            f"将 2022 年和 2023 年合并考虑，{numerator_label_zh}占{total_label_zh}的百分比是多少？"
            "保留两位小数。",
        ),
    )
    question_en, question_zh = questions[index % 2]
    table_en = (
        (header_en, "2023", "2022"),
        (numerator_label_en, _number(numerator2), _number(numerator1)),
        (total_label_en, _number(total2), _number(total1)),
    )
    table_zh = (
        (header_zh, "2023", "2022"),
        (numerator_label_zh, _number(numerator2), _number(numerator1)),
        (total_label_zh, _number(total2), _number(total1)),
    )
    expression = f"({numerator1}+{numerator2})/({total1}+{total2})*100"
    return _Variant(
        question_en, question_zh, table_en, table_zh, expression, 2,
        {
            "numerator": (numerator1, numerator2),
            "denominator": (total1, total2),
            "metric": numerator_label_en,
        },
        "ratio_of_two_year_aggregates",
    )


def _ratio_of_derived_values(rng: random.Random, index: int) -> _Variant:
    granted, settled = rng.randint(300_000, 1_500_000), rng.randint(300_000, 1_500_000)
    grant_price, settle_price = rng.randint(300, 1500) / 100, rng.randint(300, 1500) / 100
    questions = (
        (
            "The settled count is shown in parentheses to indicate an outflow; use its absolute "
            "count. What is the ratio of the total value of units granted to the total value "
            "of units settled? Round the ratio to two decimals.",
            "结算数量用括号表示流出，计算时使用其数量的绝对值。授予单位的总价值与结算单位的"
            "总价值之比是多少？比值保留两位小数。",
        ),
        (
            "Treat the parenthesized settled count as an absolute quantity. Using the counts "
            "and fair values shown, what is the ratio of total value granted to total value "
            "settled? Round to two decimals.",
            "括号中的结算数量按绝对数量处理。根据表中的数量和公允价值，授予单位总价值与"
            "结算单位总价值之比是多少？比值保留两位小数。",
        ),
    )
    question_en, question_zh = questions[index % 2]
    table_en = (
        ("Activity", "Number of units", "Fair value per unit"),
        ("Granted", _number(granted), f"${grant_price:.2f}"),
        ("Settled", f"({_number(settled)})", f"${settle_price:.2f}"),
    )
    table_zh = (
        ("活动", "单位数量", "每单位公允价值"),
        ("授予", _number(granted), f"${grant_price:.2f}"),
        ("结算", f"({_number(settled)})", f"${settle_price:.2f}"),
    )
    expression = f"({granted}*{grant_price})/({settled}*{settle_price})"
    return _Variant(
        question_en, question_zh, table_en, table_zh, expression, 2,
        {"granted": granted, "settled": settled, "grant_price": grant_price, "settle_price": settle_price},
        "ratio_of_quantity_times_unit_value",
    )


def _signed_multi_value_average(rng: random.Random, index: int) -> _Variant:
    negative_count = index % 3 + 1
    values = [
        *(-rng.randint(10, 180) for _ in range(negative_count)),
        *(rng.randint(10, 200) for _ in range(3 - negative_count)),
        0,
    ]
    rng.shuffle(values)
    questions = (
        (
            "Parentheses denote negative amounts and the dash means zero. What is the arithmetic "
            "mean of the four amendment amounts? Round to two decimals.",
            "括号表示负数，横线表示零。四个修订金额的算术平均值是多少？保留两位小数。",
        ),
        (
            "Interpret parenthesized amendments as negative and the dash as zero, then average "
            "all four displayed amounts. Round the signed result to two decimals.",
            "将括号内修订金额按负数处理、横线按零处理，再对四个金额求平均。带符号结果保留"
            "两位小数。",
        ),
    )
    question_en, question_zh = questions[index % 2]
    headers = ("Pension 2023", "Pension 2022", "Other 2023", "Other 2022")
    headers_zh = ("养老金 2023", "养老金 2022", "其他福利 2023", "其他福利 2022")
    table_en = (("Metric",) + headers, ("Amendments",) + tuple(_signed_table_value(v) for v in values))
    table_zh = (("指标",) + headers_zh, ("修订金额",) + tuple(_signed_table_value(v) for v in values))
    expression = f"({_sum_expression(values)})/4"
    return _Variant(
        question_en, question_zh, table_en, table_zh, expression, 2,
        {"values": tuple(values), "negative_count": negative_count},
        "signed_four_value_average",
    )


def _signed_percent_change(rng: random.Random, index: int) -> _Variant:
    contexts = (
        ("interest expense", "Interest expense", "利息费用", "Interest income", "利息收入", (2022, 2023)),
        ("warranty expense", "Warranty expense", "保修费用", "Service revenue", "服务收入", (2021, 2022)),
        ("return-processing cost", "Return-processing cost", "退货处理成本", "Return fee income", "退货费收入", (2023, 2024)),
    )
    metric_en, row_en, row_zh, distractor_en, distractor_zh, years = contexts[
        index % len(contexts)
    ]
    old_year, new_year = years
    old = rng.randint(20, 500)
    new = round(old * rng.randint(40, 180) / 100)
    questions = (
        (
            f"Parentheses denote expense amounts. Using their absolute magnitudes, what was the "
            f"percentage change in {metric_en} from {old_year} to {new_year}? Report an increase as "
            "positive and a decrease as negative. Round to two decimals.",
            f"括号表示费用。使用费用的绝对金额，{row_zh}从 {old_year} 年到 {new_year} 年变化了"
            "百分之多少？"
            "增加记为正，减少记为负，保留两位小数。",
        ),
        (
            f"The {metric_en} row is shown in parentheses. Compare its absolute {new_year} "
            f"amount with the absolute {old_year} amount and report the signed percentage "
            "change to two decimals.",
            f"{row_zh}行以括号显示。比较 {new_year} 年和 {old_year} 年的绝对金额，计算带方向的"
            "百分比变化，"
            "保留两位小数。",
        ),
    )
    question_en, question_zh = questions[index % 2]
    distractor_new, distractor_old = rng.randint(10, 200), rng.randint(10, 200)
    table_en = (
        ("Metric", str(new_year), str(old_year)),
        (distractor_en, _number(distractor_new), _number(distractor_old)),
        (row_en, f"({_number(new)})", f"({_number(old)})"),
    )
    table_zh = (
        ("指标", str(new_year), str(old_year)),
        (distractor_zh, _number(distractor_new), _number(distractor_old)),
        (row_zh, f"({_number(new)})", f"({_number(old)})"),
    )
    expression = f"({new}-{old})/{old}*100"
    return _Variant(
        question_en, question_zh, table_en, table_zh, expression, 2,
        {
            "old": old,
            "new": new,
            "metric": row_en,
            "years": years,
        },
        "absolute_magnitude_signed_percent_change",
    )


_BUILDERS: dict[str, _Builder] = {
    "v3-public-weighted_average-v1": _weighted_average,
    "v3-public-aggregate_percent_change-v1": _aggregate_percent_change,
    "v3-public-aggregate_percent_change_with_loss-v1": _aggregate_percent_change_with_loss,
    "v3-public-average_growth_rate-v1": _average_growth_rate,
    "v3-public-derived_value_percent_change-v1": _derived_value_percent_change,
    "v3-public-difference_of_averages-v1": _difference_of_averages,
    "v3-public-midpoint_rate_application-v1": _midpoint_rate_application,
    "v3-public-multi_period_interest-v1": _multi_period_interest,
    "v3-public-payout_ratio-v1": _payout_ratio,
    "v3-public-ratio_of_aggregates-v1": _ratio_of_aggregates,
    "v3-public-ratio_of_derived_values-v1": _ratio_of_derived_values,
    "v3-public-signed_multi_value_average-v1": _signed_multi_value_average,
    "v3-public-signed_percent_change-v1": _signed_percent_change,
}


def _rounded_result(result: int | float, places: int) -> tuple[float, str, float]:
    quantum = Decimal(1).scaleb(-places)
    rounded = Decimal(str(result)).quantize(quantum, rounding=ROUND_HALF_UP)
    tolerance = float(quantum / 2)
    return float(rounded), f"{rounded:.{places}f}", tolerance


def build_public_seed_expansion_records(
    *, variants_per_family: int = 6, seed: int = 431
) -> tuple[PublicExpansionRecord, ...]:
    if variants_per_family <= 0:
        raise ValueError("variants_per_family must be positive")

    records: list[PublicExpansionRecord] = []
    seen_prompts: set[str] = set()
    for family_id, builder in _BUILDERS.items():
        for index in range(variants_per_family):
            variant = builder(_rng_for(seed, family_id, index), index)
            table_en = _render_table(variant.table_en)
            prompt = (
                "Use the calculator when arithmetic is needed. Return the final number.\n\n"
                f"{variant.question_en}\n\nSynthetic table:\n{table_en}"
            )
            if prompt in seen_prompts:
                raise ValueError(f"duplicate public expansion prompt: {family_id}-{index:03d}")
            seen_prompts.add(prompt)
            result = calculator(variant.expression)
            target, target_display, tolerance = _rounded_result(
                result, variant.decimal_places
            )
            slug = family_id.removeprefix("v3-public-").removesuffix("-v1")
            task = Task(
                task_id=f"v4-review-public-{slug}-{index:03d}",
                family_id=family_id,
                kind=TaskKind.CALCULATOR,
                split=Split.TRAIN,
                prompt=prompt,
                allowed_tools=("calculator",),
                ground_truth={"type": "number", "value": target, "tolerance": tolerance},
                metadata={
                    "synthetic": True,
                    "synthetic_table": True,
                    "source_table_reproduction": False,
                    "expansion_version": "v4_public_seed_relations_v0",
                    "expansion_seed": seed,
                    "generator_index": index,
                    "relation_subtype": variant.subtype,
                    "parameters": variant.parameters,
                    "reference_expression": variant.expression,
                    "reference_result": result,
                    "ground_truth_display": target_display,
                    "answer_decimal_places": variant.decimal_places,
                    "parent_family_id": family_id,
                    "parent_seed_task_ids": PUBLIC_SEED_PARENT_TASKS[family_id],
                    "parent_seed_artifact": "data/generated/v3_mixed_sft_custom_v1.jsonl",
                    "review_status": "pending",
                    "training_eligible": False,
                },
            )
            if not verify_numeric_answer(result, task.ground_truth).passed:
                raise ValueError(f"reference replay failed: {task.task_id}")
            records.append(PublicExpansionRecord(task, variant.question_zh, variant.table_zh))

    expected = len(_BUILDERS) * variants_per_family
    if len(records) != expected:
        raise ValueError(f"expected {expected} public expansion records, found {len(records)}")
    validate_task_dataset(record.task for record in records)
    return tuple(records)


def build_public_seed_expansion(
    *, variants_per_family: int = 6, seed: int = 431
) -> tuple[Task, ...]:
    return tuple(
        record.task
        for record in build_public_seed_expansion_records(
            variants_per_family=variants_per_family, seed=seed
        )
    )


def build_approved_public_seed_expansion(
    *,
    variants_per_family: int = 6,
    seed: int = 431,
    approved_on: str = "2026-10-06",
) -> tuple[Task, ...]:
    """Return the owner-approved task candidates, without creating trajectories.

    Approval makes the tasks eligible for search/trajectory collection. It does
    not make them SFT rows: a verified model trajectory or an explicitly
    labelled reference-program trajectory is still required before training.
    """

    if not approved_on.strip():
        raise ValueError("approved_on must be non-empty")
    approved = []
    for task in build_public_seed_expansion(
        variants_per_family=variants_per_family,
        seed=seed,
    ):
        metadata = dict(task.metadata)
        metadata.update(
            {
                "review_status": "approved",
                "training_eligible": True,
                "owner_approval_date": approved_on,
                "review_artifact": "docs/V4_PUBLIC_SEED_RELATIONS_AUDIT_ZH.md",
                "approval_scope": "all_78_public_relation_expansion_tasks",
            }
        )
        approved.append(replace(task, metadata=metadata))
    validate_task_dataset(approved)
    return tuple(approved)


def render_audit_table_zh(record: PublicExpansionRecord) -> str:
    return _render_table(record.table_zh)
