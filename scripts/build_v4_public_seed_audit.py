"""Build review JSONL and a Chinese audit view for public-relation expansion."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Sequence

from verifiable_posttraining.dataset import write_tasks_jsonl
from verifiable_posttraining.public_seed_expansion import (
    PUBLIC_SEED_PARENT_TASKS,
    PublicExpansionRecord,
    build_public_seed_expansion_records,
    render_audit_table_zh,
)


_FAMILY_INFO = {
    "v3-public-weighted_average-v1": ("加权平均", "数量×单价求和，再除以总数量。"),
    "v3-public-aggregate_percent_change-v1": (
        "汇总后百分比变化",
        "先分别汇总指定行的新旧数值，再计算汇总值的百分比变化。",
    ),
    "v3-public-aggregate_percent_change_with_loss-v1": (
        "包含亏损和零值的汇总变化",
        "括号按负数、横线按零处理，汇总全部行后计算百分比变化。",
    ),
    "v3-public-average_growth_rate-v1": (
        "两个同比变化率的算术平均",
        "分别计算相邻年度同比变化率，再求两个变化率的算术平均；不是 CAGR。",
    ),
    "v3-public-derived_value_percent_change-v1": (
        "派生总价值的百分比变化",
        "每期先用数量×单位价值求总价值，再比较两个总价值。",
    ),
    "v3-public-difference_of_averages-v1": (
        "两个平均值之差",
        "先计算两个指定平均值，再以前者减去后者并保留正负号。",
    ),
    "v3-public-midpoint_rate_application-v1": (
        "利率区间中点应用",
        "先求利率上下限的中点，再乘名义金额。",
    ),
    "v3-public-multi_period_interest-v1": (
        "多期利息累计",
        "每次付款金额×每年付款次数×完整年数。",
    ),
    "v3-public-payout_ratio-v1": (
        "股利支付率",
        "流通股数×每股股利得到股利总额，再除以可供分红净利润。",
    ),
    "v3-public-ratio_of_aggregates-v1": (
        "汇总值之比",
        "先跨年度汇总分子和分母，再计算百分比。",
    ),
    "v3-public-ratio_of_derived_values-v1": (
        "两个派生价值之比",
        "分子、分母分别由数量×单位价值形成，再求比值。",
    ),
    "v3-public-signed_multi_value_average-v1": (
        "带符号多值平均",
        "括号视为负数、横线视为零，再求多个值的算术平均。",
    ),
    "v3-public-signed_percent_change-v1": (
        "负数展示下的绝对金额变化",
        "括号仅表示费用或负债；先取绝对金额，再计算有方向的百分比变化。",
    ),
}


def _english_question(record: PublicExpansionRecord) -> str:
    body = record.task.prompt.split("\n\n", 1)[1]
    return body.split("\n\nSynthetic table:", 1)[0]


def _markdown(records: Sequence[PublicExpansionRecord]) -> str:
    by_family: dict[str, list[PublicExpansionRecord]] = defaultdict(list)
    for record in records:
        by_family[record.task.family_id].append(record)
    lines = [
        "# V4 公开表格种子关系扩充：中文审核稿",
        "",
        "> 模型输入仍是英文。中文题意和中文表格只用于人工审核。",
        "",
        "## 本批边界",
        "",
        f"- 原公开种子关系 family：{len(PUBLIC_SEED_PARENT_TASKS)} 个。",
        "- 每个 family 新生成 6 道合成表格题，共 78 道。",
        "- 保留的是数量关系，不复制、改写原公开数据表中的公司数值。",
        "- 本审核快照中的任务保持 `review_status=pending`、`training_eligible=false`，",
        "  用于保留批准前状态。",
        "- 本批只属于 train family，没有使用 V3 validation/test 题生成变体。",
        "",
        "## 审核记录",
        "",
        "- 所有 78 道题已由项目所有者于 2026-10-06 审核通过。",
        "- 批准后的任务另存为 `data/generated/v4_public_seed_relations_approved_v1.jsonl`。",
        "- 批准只允许进入轨迹收集；本文件不是 SFT 数据。",
        "",
        "## 审核重点",
        "",
        "1. 表头、题意和公式引用的行列是否一致。",
        "2. 括号、横线、百分比和正负方向是否明确。",
        "3. 问题是否要求推导，但没有把计算步骤直接泄露在题面中。",
        "4. 参考公式仅供离线校验，不会放入模型看到的用户问题。",
        "",
    ]
    for family_id, (title, relation) in _FAMILY_INFO.items():
        lines.extend((
            f"## {title}",
            "",
            f"- Family：`{family_id}`",
            f"- 母题：`{'`、`'.join(PUBLIC_SEED_PARENT_TASKS[family_id])}`",
            f"- 保留关系：{relation}",
            "",
        ))
        for number, record in enumerate(by_family[family_id], start=1):
            task = record.task
            lines.extend((
                f"### {number}. `{task.task_id}`",
                "",
                f"- 中文题意：{record.question_zh}",
                f"- 英文题意：{_english_question(record)}",
                "- 中文审核表：",
                "",
                render_audit_table_zh(record),
                "",
                f"- 参考公式：`{task.metadata['reference_expression']}`",
                f"- GT：`{task.metadata['ground_truth_display']}`；容差：`{task.ground_truth['tolerance']}`",
                "- 审核结论：□保留　□修改　□删除",
                "",
            ))
    return "\n".join(lines).rstrip() + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--jsonl",
        type=Path,
        default=Path("data/review/v4_public_seed_relations_audit_v0.jsonl"),
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        default=Path("docs/V4_PUBLIC_SEED_RELATIONS_AUDIT_ZH.md"),
    )
    parser.add_argument("--variants-per-family", type=int, default=6)
    args = parser.parse_args(argv)

    records = build_public_seed_expansion_records(
        variants_per_family=args.variants_per_family
    )
    write_tasks_jsonl((record.task for record in records), args.jsonl)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text(_markdown(records), encoding="utf-8")
    print(json.dumps({
        "candidate_count": len(records),
        "family_count": len({record.task.family_id for record in records}),
        "jsonl": str(args.jsonl),
        "markdown": str(args.markdown),
        "training_eligible": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
