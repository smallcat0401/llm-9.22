"""Tier A: reviewed seed candidates for the V3 validation/test protocol.

This module deliberately builds an *audit pack*, not a frozen benchmark.  A
candidate cannot become evaluation data until its wording, reference program,
ground truth, split, and source provenance have been reviewed.

Invariants:

* validation and test synthetic templates are disjoint;
* public source questions are disjoint from every supplied prior artifact;
* every reference expression is replayed with the bounded calculator;
* replayed values must agree with the public label when one exists;
* every emitted row remains ``review_status=pending``.

Failure is explicit: a stale public source index, reused source question,
incorrect reference program, or accidental split overlap aborts the build.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .public_eval import extract_gsm8k_final_answer, load_gsm8k_jsonl
from .tools.calculator import calculator
from .verifier import verify_numeric_answer


@dataclass(frozen=True, slots=True)
class EvalSeedCandidate:
    candidate_id: str
    proposed_split: str
    source_type: str
    family_id: str
    prompt_en: str
    prompt_zh: str
    reference_expression: str
    ground_truth: float | int
    tolerance: float
    source_dataset: str | None = None
    source_split: str | None = None
    source_index: int | None = None
    review_status: str = "pending"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Each synthetic family occurs in exactly one proposed split.  Two seeds expose
# the template for human review before parameterized expansion is considered.
_SYNTHETIC: tuple[EvalSeedCandidate, ...] = (
    EvalSeedCandidate(
        "v3-eval-val-tiered-commission-01", "validation", "self_written",
        "v3-eval-val-tiered-commission-v1",
        "A sales representative receives a $420 base payment. The first $4,000 of sales earns 3% commission and sales above $4,000 earn 5%. After a fixed $35 platform charge, what is the representative's pay when total sales are $6,800?",
        "一名销售代表获得420美元底薪。销售额前4000美元按3%提成，超过4000美元的部分按5%提成，最后扣除35美元固定平台费。总销售额为6800美元时，最终收入是多少？",
        "420+4000*0.03+(6800-4000)*0.05-35", 645, 1e-6,
    ),
    EvalSeedCandidate(
        "v3-eval-val-tiered-commission-02", "validation", "self_written",
        "v3-eval-val-tiered-commission-v1",
        "A sales representative receives a $500 base payment. The first $6,000 of sales earns 2.5% commission and sales above $6,000 earn 4%. After a fixed $48 platform charge, what is the representative's pay when total sales are $9,200?",
        "一名销售代表获得500美元底薪。销售额前6000美元按2.5%提成，超过6000美元的部分按4%提成，最后扣除48美元固定平台费。总销售额为9200美元时，最终收入是多少？",
        "500+6000*0.025+(9200-6000)*0.04-48", 730, 1e-6,
    ),
    EvalSeedCandidate(
        "v3-eval-val-restricted-grant-01", "validation", "self_written",
        "v3-eval-val-restricted-grant-v1",
        "An event uses 18 staff for 6 hours at $22 per hour, $1,450 of materials, and a $620 venue. A grant covers 18% of the combined labor and material costs; it does not cover the venue. A separate donor contributes $120. How much must the organizers still pay?",
        "一场活动雇用18名员工，每人工作6小时，时薪22美元；材料费1450美元，场地费620美元。一笔补助承担人工费与材料费合计的18%，但不承担场地费；另有捐赠者提供120美元。主办方还需支付多少？",
        "18*6*22+1450+620-(18*6*22+1450)*0.18-120", 3637.32, 0.005,
    ),
    EvalSeedCandidate(
        "v3-eval-val-restricted-grant-02", "validation", "self_written",
        "v3-eval-val-restricted-grant-v1",
        "A workshop uses 14 instructors for 5 hours at $28 per hour, $980 of materials, and a $540 venue. A grant covers 22% of the combined instructor-pay and material costs; it does not cover the venue. A donor then contributes $150. How much must the organizers still pay?",
        "一场研讨会雇用14名讲师，每人工作5小时，时薪28美元；材料费980美元，场地费540美元。一笔补助承担讲师报酬与材料费合计的22%，但不承担场地费；之后另获150美元捐赠。主办方还需支付多少？",
        "14*5*28+980+540-(14*5*28+980)*0.22-150", 2683.2, 0.005,
    ),
    EvalSeedCandidate(
        "v3-eval-val-basket-change-01", "validation", "self_written",
        "v3-eval-val-fixed-basket-change-v1",
        "A fixed basket contains 12 units of product A and 7 units of product B. A cost $8.00 and B cost $15.00 last year; this year they cost $9.20 and $14.50. A $20 delivery charge applies in both years. What is the percentage change in the basket's total cost? Round to two decimals.",
        "一个固定商品篮含12件A商品和7件B商品。去年A单价8.00美元、B单价15.00美元；今年分别为9.20美元和14.50美元。两年都另收20美元配送费。商品篮总成本的百分比变化是多少？保留两位小数。",
        "((12*9.2+7*14.5+20)-(12*8+7*15+20))/(12*8+7*15+20)*100", 4.93, 0.005,
    ),
    EvalSeedCandidate(
        "v3-eval-val-basket-change-02", "validation", "self_written",
        "v3-eval-val-fixed-basket-change-v1",
        "A fixed basket contains 9 units of product A and 11 units of product B. A cost $12.00 and B cost $7.50 last year; this year they cost $11.40 and $8.10. A $16 delivery charge applies in both years. What is the percentage change in the basket's total cost? Round to two decimals.",
        "一个固定商品篮含9件A商品和11件B商品。去年A单价12.00美元、B单价7.50美元；今年分别为11.40美元和8.10美元。两年都另收16美元配送费。商品篮总成本的百分比变化是多少？保留两位小数。",
        "((9*11.4+11*8.1+16)-(9*12+11*7.5+16))/(9*12+11*7.5+16)*100", 0.58, 0.005,
    ),
    EvalSeedCandidate(
        "v3-eval-val-rework-yield-01", "validation", "self_written",
        "v3-eval-val-rework-yield-v1",
        "Five production lines each make 240 units. Initial inspection rejects 8% of all units, but rework recovers three quarters of the rejected units. How many sellable units remain?",
        "5条生产线各生产240件产品。初检淘汰全部产品的8%，但返工可以挽回被淘汰产品的四分之三。最终有多少件可销售产品？",
        "5*240*(1-0.08)+5*240*0.08*0.75", 1176, 1e-6,
    ),
    EvalSeedCandidate(
        "v3-eval-val-rework-yield-02", "validation", "self_written",
        "v3-eval-val-rework-yield-v1",
        "Four production lines each make 350 units. Initial inspection rejects 6% of all units, but rework recovers two thirds of the rejected units. How many sellable units remain?",
        "4条生产线各生产350件产品。初检淘汰全部产品的6%，但返工可以挽回被淘汰产品的三分之二。最终有多少件可销售产品？",
        "4*350*(1-0.06)+4*350*0.06*(2/3)", 1372, 1e-6,
    ),
    EvalSeedCandidate(
        "v3-eval-test-subscription-overage-01", "test", "self_written",
        "v3-eval-test-subscription-overage-v1",
        "A monthly data plan costs $45 and includes 300 GB. Extra usage costs $0.12 per GB. A customer uses 460 GB. A 6% service tax applies to the plan and overage charges, while an $8 equipment rental is added after tax. What is the final bill? Round to two decimals.",
        "某月度流量套餐收费45美元，包含300GB；超出部分每GB收费0.12美元。用户当月使用460GB。套餐费和超额流量费需加收6%服务税，税后再加8美元设备租赁费。最终账单是多少？保留两位小数。",
        "(45+(460-300)*0.12)*1.06+8", 76.05, 0.005,
    ),
    EvalSeedCandidate(
        "v3-eval-test-subscription-overage-02", "test", "self_written",
        "v3-eval-test-subscription-overage-v1",
        "A monthly data plan costs $52 and includes 400 GB. Extra usage costs $0.09 per GB. A customer uses 575 GB. A 7% service tax applies to the plan and overage charges, while a $10 equipment rental is added after tax. What is the final bill? Round to two decimals.",
        "某月度流量套餐收费52美元，包含400GB；超出部分每GB收费0.09美元。用户当月使用575GB。套餐费和超额流量费需加收7%服务税，税后再加10美元设备租赁费。最终账单是多少？保留两位小数。",
        "(52+(575-400)*0.09)*1.07+10", 82.49, 0.005,
    ),
    EvalSeedCandidate(
        "v3-eval-test-route-cost-01", "test", "self_written",
        "v3-eval-test-route-cost-v1",
        "A delivery van travels 180 miles on highways at 30 miles per gallon and 120 miles in cities at 24 miles per gallon. Fuel costs $3.80 per gallon. The route also has an $18 toll, and a $10 travel voucher is applied to the total. What is the trip's net cost?",
        "一辆送货车在高速公路行驶180英里，油耗为每加仑30英里；在城市道路行驶120英里，油耗为每加仑24英里。油价为每加仑3.80美元，另有18美元过路费，最后使用10美元出行抵用券。此次行程的净成本是多少？",
        "(180/30+120/24)*3.8+18-10", 49.8, 1e-6,
    ),
    EvalSeedCandidate(
        "v3-eval-test-route-cost-02", "test", "self_written",
        "v3-eval-test-route-cost-v1",
        "A delivery van travels 210 miles on highways at 35 miles per gallon and 96 miles in cities at 24 miles per gallon. Fuel costs $4.10 per gallon. The route also has a $22 toll, and a $12 travel voucher is applied to the total. What is the trip's net cost?",
        "一辆送货车在高速公路行驶210英里，油耗为每加仑35英里；在城市道路行驶96英里，油耗为每加仑24英里。油价为每加仑4.10美元，另有22美元过路费，最后使用12美元出行抵用券。此次行程的净成本是多少？",
        "(210/35+96/24)*4.1+22-12", 51, 1e-6,
    ),
    EvalSeedCandidate(
        "v3-eval-test-partial-refund-01", "test", "self_written",
        "v3-eval-test-partial-refund-v1",
        "A customer buys three $40 items and two $65 items during a 15%-off sale, plus a nonrefundable $12 delivery charge. The customer returns one $65 item but receives only 80% of that item's discounted price because of a restocking fee. What is the customer's final net payment?",
        "顾客在全场八五折促销期间购买3件单价40美元的商品和2件单价65美元的商品，另付不可退的12美元配送费。之后退回1件65美元商品，但因补货费只能退回该商品折后价的80%。顾客最终净支付多少？",
        "(3*40+2*65)*0.85+12-65*0.85*0.8", 180.3, 0.005,
    ),
    EvalSeedCandidate(
        "v3-eval-test-partial-refund-02", "test", "self_written",
        "v3-eval-test-partial-refund-v1",
        "A customer buys two $55 items and three $30 items during a 20%-off sale, plus a nonrefundable $9 delivery charge. The customer returns one $55 item but receives only 75% of that item's discounted price because of a restocking fee. What is the customer's final net payment?",
        "顾客在全场八折促销期间购买2件单价55美元的商品和3件单价30美元的商品，另付不可退的9美元配送费。之后退回1件55美元商品，但因补货费只能退回该商品折后价的75%。顾客最终净支付多少？",
        "(2*55+3*30)*0.8+9-55*0.8*0.75", 136, 0.005,
    ),
    EvalSeedCandidate(
        "v3-eval-test-bonus-deduction-01", "test", "self_written",
        "v3-eval-test-bonus-deduction-v1",
        "An employee works 38 regular hours and 7 overtime hours at $24 per hour. Overtime pays 1.5 times the regular rate. A performance bonus equals 6% of regular-hour wages. After 18% tax on all gross pay, a fixed $42 insurance deduction is taken. What is take-home pay? Round to two decimals.",
        "一名员工正常工作38小时、加班7小时，正常时薪24美元，加班时薪为正常时薪的1.5倍。绩效奖金等于正常工时工资的6%。全部税前收入扣除18%的税后，再扣42美元固定保险费。实发工资是多少？保留两位小数。",
        "(38*24+7*24*1.5+38*24*0.06)*(1-0.18)-42", 957.35, 0.005,
    ),
    EvalSeedCandidate(
        "v3-eval-test-bonus-deduction-02", "test", "self_written",
        "v3-eval-test-bonus-deduction-v1",
        "An employee works 40 regular hours and 5 overtime hours at $27 per hour. Overtime pays 1.5 times the regular rate. A performance bonus equals 8% of regular-hour wages. After 20% tax on all gross pay, a fixed $55 insurance deduction is taken. What is take-home pay? Round to two decimals.",
        "一名员工正常工作40小时、加班5小时，正常时薪27美元，加班时薪为正常时薪的1.5倍。绩效奖金等于正常工时工资的8%。全部税前收入扣除20%的税后，再扣55美元固定保险费。实发工资是多少？保留两位小数。",
        "(40*27+5*27*1.5+40*27*0.08)*(1-0.20)-55", 1040.12, 0.005,
    ),
)


_PUBLIC: tuple[Mapping[str, Any], ...] = (
    {
        "candidate_id": "v3-eval-val-gsm8k-6154", "proposed_split": "validation",
        "source_split": "train", "source_index": 6154,
        "family_id": "v3-eval-val-public-ratio-allocation-v1",
        "prompt_zh": "玛丽写故事，需要按姓名首字母分配60个角色。其中一半角色的首字母为A，首字母为C的角色数又是A类角色数的一半。其余角色分配给D和E，并且D类角色数是E类的两倍。D类角色有多少个？",
        "reference_expression": "(60-60/2-60/4)*2/3",
    },
    {
        "candidate_id": "v3-eval-val-gsm8k-0839", "proposed_split": "validation",
        "source_split": "train", "source_index": 839,
        "family_id": "v3-eval-val-public-weighted-demand-v1",
        "prompt_zh": "扶轮社早餐募款活动售出53张幼儿票、35张大龄儿童票、75张成人票和37张老年票。预计幼儿吃半份煎蛋、大龄儿童1份、成人2份、老年人1.5份，并额外准备25份。每份使用2个鸡蛋，需要购买多少个鸡蛋？",
        "reference_expression": "(53*0.5+35+75*2+37*1.5+25)*2",
    },
    {
        "candidate_id": "v3-eval-val-gsm8k-4495", "proposed_split": "validation",
        "source_split": "train", "source_index": 4495,
        "family_id": "v3-eval-val-public-population-flow-v1",
        "prompt_zh": "某地区初始人口为100000。十年间因出生人口增长60%；同期每年有2000人迁出、2500人迁入。十年后人口是多少？",
        "reference_expression": "100000*1.6-2000*10+2500*10",
    },
    {
        "candidate_id": "v3-eval-val-gsm8k-4967", "proposed_split": "validation",
        "source_split": "train", "source_index": 4967,
        "family_id": "v3-eval-val-public-tank-loss-recovery-v1",
        "prompt_zh": "一个容量350000加仑且已装满的水箱先以每小时32000加仑漏水5小时；第一次维修后仍以每小时10000加仑漏水10小时；第二次修好后以每小时40000加仑注水3小时。距离重新装满还差多少加仑？",
        "reference_expression": "350000-(350000-32000*5-10000*10+40000*3)",
    },
    {
        "candidate_id": "v3-eval-test-gsm8k-1213", "proposed_split": "test",
        "source_split": "test", "source_index": 1213,
        "family_id": "v3-eval-test-public-loan-repayment-v1",
        "prompt_zh": "斯蒂芬向姐姐借300美元，并承诺额外支付欠款的2%。前11个月每月还25美元，剩余本金和利息在第12个月付清。第12个月要支付多少？",
        "reference_expression": "300*1.02-25*11",
    },
    {
        "candidate_id": "v3-eval-test-gsm8k-1070", "proposed_split": "test",
        "source_split": "test", "source_index": 1070,
        "family_id": "v3-eval-test-public-bogo-purchase-v1",
        "prompt_zh": "丹尼斯每做一打羊角面包需要1磅黄油，他要做6打。商店正在进行“买1磅、另1磅半价”的促销，黄油原价每磅4美元。购买6磅黄油需要多少钱？",
        "reference_expression": "3*4+3*4*0.5",
    },
    {
        "candidate_id": "v3-eval-test-gsm8k-0137", "proposed_split": "test",
        "source_split": "test", "source_index": 137,
        "family_id": "v3-eval-test-public-delivery-fee-v1",
        "prompt_zh": "罗里点了2份每份7.50美元的三明治、2袋每袋1.50美元的薯片和2块每块1美元的饼干。结账时加收20%配送费，她还给5美元小费。订单总价是多少？",
        "reference_expression": "(2*7.5+2*1.5+2*1)*1.2+5",
    },
    {
        "candidate_id": "v3-eval-test-gsm8k-0876", "proposed_split": "test",
        "source_split": "test", "source_index": 876,
        "family_id": "v3-eval-test-public-weighted-test-score-v1",
        "prompt_zh": "艾米参加历史考试：10道选择题答对80%，20道判断题答对90%，5道简答题答对60%。选择题和判断题每题1分，简答题每题5分。她得到多少分？",
        "reference_expression": "10*0.8+20*0.9+5*0.6*5",
    },
)


def _artifact_source_indices(paths: Iterable[str | Path]) -> dict[str, set[int]]:
    used = {"train": set(), "test": set()}
    for path_value in paths:
        path = Path(path_value)
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            task = row.get("task", row) if isinstance(row, Mapping) else {}
            metadata = task.get("metadata", {}) if isinstance(task, Mapping) else {}
            split = metadata.get("source_split") if isinstance(metadata, Mapping) else None
            index = metadata.get("source_index") if isinstance(metadata, Mapping) else None
            if split in used and index is not None:
                used[str(split)].add(int(index))
    return used


def _validate_reference(candidate: EvalSeedCandidate) -> None:
    replayed = calculator(candidate.reference_expression)
    result = verify_numeric_answer(
        replayed,
        {"type": "number", "value": candidate.ground_truth, "tolerance": candidate.tolerance},
    )
    if not result.passed:
        raise ValueError(f"reference replay failed: {candidate.candidate_id}")


def build_v3_eval_seed_candidates(
    *,
    gsm8k_train_path: str | Path,
    gsm8k_test_path: str | Path,
    exclusion_artifacts: Sequence[str | Path] = (),
) -> tuple[EvalSeedCandidate, ...]:
    """Build pending candidates; this function does not freeze evaluation data."""

    records = {
        "train": {int(row["source_index"]): row for row in load_gsm8k_jsonl(gsm8k_train_path)},
        "test": {int(row["source_index"]): row for row in load_gsm8k_jsonl(gsm8k_test_path)},
    }
    used = _artifact_source_indices(exclusion_artifacts)
    public_candidates = []
    for spec in _PUBLIC:
        split = str(spec["source_split"])
        index = int(spec["source_index"])
        if index in used[split]:
            raise ValueError(f"public source already appears in prior artifact: {split}:{index}")
        try:
            record = records[split][index]
        except KeyError as exc:
            raise ValueError(f"public source index is unavailable: {split}:{index}") from exc
        official = extract_gsm8k_final_answer(str(record["answer"]))
        replayed = calculator(str(spec["reference_expression"]))
        if not verify_numeric_answer(
            replayed, {"type": "number", "value": official, "tolerance": 1e-6}
        ).passed:
            raise ValueError(f"public reference disagrees with official label: {split}:{index}")
        public_candidates.append(EvalSeedCandidate(
            candidate_id=str(spec["candidate_id"]),
            proposed_split=str(spec["proposed_split"]),
            source_type="public",
            family_id=str(spec["family_id"]),
            prompt_en=str(record["question"]).strip(),
            prompt_zh=str(spec["prompt_zh"]),
            reference_expression=str(spec["reference_expression"]),
            ground_truth=official,
            tolerance=1e-6,
            source_dataset="openai/grade-school-math",
            source_split=split,
            source_index=index,
        ))

    candidates = (*_SYNTHETIC, *public_candidates)
    ids = [candidate.candidate_id for candidate in candidates]
    if len(candidates) != 24 or len(set(ids)) != len(ids):
        raise ValueError("V3 evaluation audit pack must contain 24 unique candidates")
    if any(candidate.review_status != "pending" for candidate in candidates):
        raise ValueError("audit candidates must remain pending until human review")
    for candidate in candidates:
        _validate_reference(candidate)

    synthetic_families = {
        split: {
            candidate.family_id
            for candidate in candidates
            if candidate.source_type == "self_written" and candidate.proposed_split == split
        }
        for split in ("validation", "test")
    }
    if synthetic_families["validation"] & synthetic_families["test"]:
        raise ValueError("validation/test synthetic families must be disjoint")
    counts = {
        split: sum(candidate.proposed_split == split for candidate in candidates)
        for split in ("validation", "test")
    }
    if counts != {"validation": 12, "test": 12}:
        raise ValueError(f"unexpected proposed split counts: {counts}")
    return tuple(candidates)
