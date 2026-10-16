"""Tier A: draft one auditable test-only variant per frozen V3 test task.

The V3 test rows are never edited. Public-seed variants are new synthetic
questions, not additional GSM8K examples. Every proposed answer is checked
against both the safe calculator and an independently evaluated quantity model.
No model is run here; all outputs remain pending human review.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import re
from typing import Sequence

from .dataset import validate_task_dataset
from .schemas import Split, Task, TaskKind
from .tools.calculator import calculator
from .v3_evaluation import _SYNTHETIC_BUILDERS
from .verifier import verify_numeric_answer


@dataclass(frozen=True, slots=True)
class TestExtensionRecord:
    task: Task
    question_zh: str


def _d(value: int | float | str) -> Decimal:
    return Decimal(str(value))


def _cents(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _clean_generated_expression(expression: str) -> str:
    """Remove binary-float display tails in newly drafted reference programs."""

    return re.sub(
        r"(?<![\w.])\d+\.\d{7,}",
        lambda match: format(Decimal(match.group()).quantize(Decimal("0.01")), ".2f"),
        expression,
    )


def _synthetic_review(family: str, index: int) -> tuple[str, float]:
    """Chinese audit wording and independent arithmetic for V3 test builders."""

    cycle, odd = divmod(index, 2)
    if family.endswith("subscription-overage-v1"):
        if odd:
            base, included, used = 52 + 3 * cycle, 400 + 50 * cycle, 575 + 75 * cycle
            rate, tax, rental = _d("0.09") + _d("0.01") * cycle, 7 + cycle, 10 + cycle
        else:
            base, included, used = 45 + 3 * cycle, 300 + 50 * cycle, 460 + 75 * cycle
            rate, tax, rental = _d("0.12") + _d("0.01") * cycle, 6 + cycle, 8 + cycle
        zh = (f"月度流量套餐费{base}美元，包含{included}GB；超出部分每GB收费{rate:.2f}美元。"
              f"用户用了{used}GB。套餐费和超额费用加收{tax}%服务税，税后再加{rental}美元设备租赁费。"
              "最终账单是多少？保留两位小数。")
        expected = _cents((_d(base) + (used - included) * rate) * (1 + _d(tax) / 100) + rental)
        return zh, expected

    if family.endswith("route-cost-v1"):
        if odd:
            highway, hmpg, city, cmpg = 210 + 35 * cycle, 35, 96 + 24 * cycle, 24
            price, toll, voucher = _d("4.10") + _d("0.10") * cycle, 22 + 2 * cycle, 12 + cycle
        else:
            highway, hmpg, city, cmpg = 180 + 30 * cycle, 30, 120 + 24 * cycle, 24
            price, toll, voucher = _d("3.80") + _d("0.10") * cycle, 18 + 2 * cycle, 10 + cycle
        zh = (f"送货车在高速公路行驶{highway}英里，油耗为每加仑{hmpg}英里；"
              f"在城市道路行驶{city}英里，油耗为每加仑{cmpg}英里。油价每加仑{price:.2f}美元，"
              f"另有{toll}美元过路费，最后使用{voucher}美元出行抵用券。此次行程净成本是多少？")
        expected = float((_d(highway) / hmpg + _d(city) / cmpg) * price + toll - voucher)
        return zh, expected

    if family.endswith("partial-refund-v1"):
        if odd:
            qa, pa, qb, pb = 2 + cycle, 55 + 5 * cycle, 3 + cycle, 30 + 5 * cycle
            discount, delivery, refund = 20, 9 + cycle, 75
        else:
            qa, pa, qb, pb = 3 + cycle, 40 + 5 * cycle, 2 + cycle, 65 + 5 * cycle
            discount, delivery, refund = 15, 12 + cycle, 80
        zh = (f"顾客在全场优惠{discount}%期间购买{qa}件单价{pa}美元的商品和"
              f"{qb}件单价{pb}美元的商品，另付不可退的{delivery}美元配送费。"
              f"之后退回1件{pb}美元的商品，但因补货费只能退回该商品折后价的{refund}%。"
              "顾客最终净支付多少？保留两位小数。")
        sale_factor = 1 - _d(discount) / 100
        expected = _cents((qa * pa + qb * pb) * sale_factor + delivery
                          - _d(pb) * sale_factor * refund / 100)
        return zh, expected

    if family.endswith("bonus-deduction-v1"):
        if odd:
            regular, overtime, rate = 40, 5 + cycle, 27 + cycle
            bonus, tax, insurance = 8 + cycle, 20, 55 + 3 * cycle
        else:
            regular, overtime, rate = 38, 7 + cycle, 24 + cycle
            bonus, tax, insurance = 6 + cycle, 18, 42 + 3 * cycle
        zh = (f"员工正常工作{regular}小时、加班{overtime}小时，正常时薪{rate}美元，"
              f"加班时薪为正常时薪的1.5倍。绩效奖金等于正常工时工资的{bonus}%。"
              f"全部税前收入扣除{tax}%的税后，再扣{insurance}美元固定保险费。"
              "实发工资是多少？保留两位小数。")
        gross = regular * rate + _d(overtime) * rate * _d("1.5") + _d(regular) * rate * bonus / 100
        expected = _cents(gross * (1 - _d(tax) / 100) - insurance)
        return zh, expected

    raise ValueError(f"unexpected V3 test family: {family}")


def _public_variant(family: str) -> tuple[str, str, str, float, float]:
    """Hand-authored relation variants; never label them as public examples."""

    if family.endswith("loan-repayment-v1"):
        return (
            "Maya borrowed $480 and agreed to repay the original loan plus a one-time fee equal to 5% of the original amount. She pays $30 at the end of each of the first 14 months and clears the remaining balance in month 15. How much does she pay in month 15?",
            "玛雅借了480美元，同意偿还本金并一次性支付相当于原本金5%的费用。前14个月每月底各还30美元，第15个月付清余额。第15个月需付多少？",
            "480*(1+5/100)-30*14", float(_d(480) * (_d(1) + _d(5)/100) - _d(30)*14), 1e-6,
        )
    if family.endswith("bogo-purchase-v1"):
        return (
            "A bakery uses 2 pounds of butter for each batch and plans 4 batches. Butter costs $5 per pound. For every two pounds bought, the second pound is half price. How much will the bakery pay for all the butter it needs?",
            "面包店每批用2磅黄油，计划做4批。黄油每磅5美元；每买两磅，其中第二磅半价。所需黄油总共要付多少钱？",
            "(2*4/2)*(5+5/2)", float(_d(4) * (_d(5) + _d(5)/2)), 1e-6,
        )
    if family.endswith("delivery-fee-v1"):
        subtotal = _d(3)*_d("8.25") + _d(2)*_d("2.50") + _d(4)*_d("1.25")
        return (
            "An order contains 3 wraps at $8.25 each, 2 drinks at $2.50 each, and 4 cookies at $1.25 each. A 15% delivery fee is charged on the food and drink subtotal, then a $4 tip is added. What is the total cost? Round to two decimals.",
            "订单有3份单价8.25美元的卷饼、2杯单价2.50美元的饮料和4块单价1.25美元的饼干。食物与饮料小计加收15%配送费，之后再加4美元小费。总费用是多少？保留两位小数。",
            "(3*8.25+2*2.5+4*1.25)*(1+15/100)+4",
            _cents(subtotal * (_d(1) + _d(15)/100) + _d(4)), 0.005,
        )
    if family.endswith("weighted-test-score-v1"):
        return (
            "A quiz has 15 multiple-choice questions worth 1 point each, 10 true/false questions worth 1 point each, and 8 long-answer questions worth 4 points each. A student answers 80%, 70%, and 75% of those three groups correctly, respectively. How many points does the student earn?",
            "一场测验有15道每题1分的选择题、10道每题1分的判断题和8道每题4分的长答题。学生在这三组中分别答对80%、70%和75%。共得多少分？",
            "15*80/100+10*70/100+8*75/100*4",
            float(_d(15)*_d("0.8") + _d(10)*_d("0.7") + _d(8)*_d("0.75")*_d(4)), 1e-6,
        )
    raise ValueError(f"unexpected V3 public test family: {family}")


def build_v4_test_extension_records(frozen_test: Sequence[Task]) -> tuple[TestExtensionRecord, ...]:
    """Build exactly one new pending task for each of the 36 original tasks."""

    if len(frozen_test) != 36 or len({task.task_id for task in frozen_test}) != 36:
        raise ValueError("expected 36 distinct frozen V3 test tasks")
    builders = {family: builder for family, split, builder in _SYNTHETIC_BUILDERS if split is Split.TEST}
    records: list[TestExtensionRecord] = []
    for parent in frozen_test:
        if parent.split is not Split.TEST or parent.kind is not TaskKind.CALCULATOR:
            raise ValueError(f"invalid frozen test parent: {parent.task_id}")
        if parent.family_id in builders:
            old_index = parent.metadata.get("generator_index")
            if not isinstance(old_index, int) or not 0 <= old_index < 8:
                raise ValueError(f"invalid V3 generator index: {parent.task_id}")
            index = old_index + 8
            question_en, expression, round_two = builders[parent.family_id](index)
            expression = _clean_generated_expression(expression)
            if parent.family_id.endswith("subscription-overage-v1"):
                tax = (7 if index % 2 else 6) + index // 2
                question_en = question_en.replace(
                    f"A {tax}% service tax applies", f"A service tax of {tax}% applies"
                )
            elif parent.family_id.endswith("route-cost-v1"):
                voucher = (12 if index % 2 else 10) + index // 2
                question_en = question_en.replace(
                    f"a ${voucher} travel voucher is applied",
                    f"a travel voucher of ${voucher} is applied",
                )
            question_zh, independently_expected = _synthetic_review(parent.family_id, index)
            tolerance = 0.005 if round_two else 1e-6
            source_group = "self_written_extension"
        else:
            if parent.metadata.get("source_dataset") != "openai/grade-school-math":
                raise ValueError(f"unknown public test parent: {parent.task_id}")
            question_en, question_zh, expression, independently_expected, tolerance = _public_variant(parent.family_id)
            source_group = "public_seed_derived_synthetic"
        replayed = calculator(expression)
        truth = {"type": "number", "value": independently_expected, "tolerance": tolerance}
        if not verify_numeric_answer(replayed, truth).passed:
            raise ValueError(f"independent oracle mismatch: {parent.task_id}")
        prefix = ("Solve this problem. The calculator tool is available for arithmetic. "
                  if source_group == "public_seed_derived_synthetic"
                  else "Use the calculator to solve this quantitative reasoning problem. ")
        prompt = prefix + f"Return the final number.\n\n{question_en}"
        task = Task(
            task_id=f"v4-review-test-derived-{parent.task_id.removeprefix('v3-eval-test-')}",
            family_id=parent.family_id,
            kind=TaskKind.CALCULATOR,
            split=Split.TEST,
            prompt=prompt,
            allowed_tools=("calculator",),
            ground_truth=truth,
            metadata={
                "dataset_version": "v4_test_extension_audit_v0",
                "synthetic": True,
                "source_group": source_group,
                "parent_test_task_id": parent.task_id,
                "parent_source_dataset": parent.metadata.get("source_dataset"),
                "parent_source_index": parent.metadata.get("source_index"),
                "evaluation_only": True,
                "training_eligible": False,
                "review_status": "pending",
                "reference_expression": expression,
                "review_artifact": "docs/V4_TEST_EXTENSION_AUDIT_ZH.md",
            },
        )
        records.append(TestExtensionRecord(task, question_zh))
    if len(records) != 36 or len({r.task.prompt for r in records}) != 36:
        raise ValueError("test extension must contain 36 unique new prompts")
    validate_task_dataset((*frozen_test, *(record.task for record in records)))
    return tuple(records)
