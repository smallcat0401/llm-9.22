"""Build the Chinese audit view for direct expansion of audited V3 seeds."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Sequence

from verifiable_posttraining.calculator_curriculum import generate_calculator_curriculum_v2
from verifiable_posttraining.schemas import Task
from verifiable_posttraining.seed_expansion import (
    AUDITED_SELF_WRITTEN_SEED_FAMILIES,
    build_self_written_seed_expansion,
)


_FAMILY_TITLES = {
    "curriculum-v2-sales-returns": "销售、退货与固定服务费",
    "curriculum-v2-markup-discount": "先加价、再打折",
    "curriculum-v2-required-score": "达到目标平均分所需成绩",
    "curriculum-v2-cartons-damage": "多层包装扣除损坏品与样品",
    "curriculum-v2-shared-bill": "部分人免单后的账单平摊",
    "curriculum-v2-growth-fee": "连续两年增长后扣固定费用",
}


def _problem_zh(task: Task) -> str:
    parameters = task.metadata.get("parameters")
    if isinstance(parameters, dict):
        p = parameters
        surface = int(task.metadata["surface_variant"])
        if task.family_id == "curriculum-v2-sales-returns":
            variants = (
                f"一家商店以每件 {p['regular_price']} 美元售出 {p['regular']} 件普通商品，"
                f"并以每件 {p['premium_price']} 美元售出 {p['premium']} 件高档商品。顾客"
                f"全额退回 {p['returned']} 件普通商品，商店另获得固定 {p['fee']} 美元"
                "服务费。净收入是多少？",
                f"一家网店售出并发出 {p['regular']} 件单价 {p['regular_price']} 美元的标准商品和 "
                f"{p['premium']} 件单价 {p['premium_price']} 美元的豪华商品。网店对 "
                f"{p['returned']} 件标准商品作全额退款，并另外收取固定 {p['fee']} 美元"
                "手续费。求网店净收入。",
                f"一个市场摊位售出 {p['regular']} 件单价 {p['regular_price']} 美元的基础商品"
                f"和 {p['premium']} 件单价 {p['premium_price']} 美元的升级商品。随后有 "
                f"{p['returned']} 件基础商品全额退回；另有 {p['fee']} 美元服务收入。最终"
                "保留的收入是多少？",
            )
            return variants[surface]
        if task.family_id == "curriculum-v2-markup-discount":
            variants = (
                f"一件商品成本为 {p['cost']} 美元。价格先提高 {p['markup']}%，再对标价优惠 "
                f"{p['discount']}%。最终价格是多少？结果保留两位小数。",
                f"零售商在一件成本为 {p['cost']} 美元的商品上加价 {p['markup']}% 得到标价。"
                f"促销时再从标价中减去 {p['discount']}%。求促销价，保留两位小数。",
                f"一台设备起始价格为 {p['cost']} 美元，先加价 {p['markup']}%，然后按加价后的"
                f"价格打 {p['discount']}% 的折扣。最终支付多少？保留两位小数。",
            )
            return variants[surface]
        if task.family_id == "curriculum-v2-required-score":
            scores = "、".join(str(value) for value in p["scores"])
            variants = (
                f"前四次考试成绩分别为 {scores}。要使五次考试的平均分达到 {p['target']}，"
                "第五次需要多少分？",
                f"一名学生前四次小测成绩为 {scores}。若五次小测的最终平均分需要达到 "
                f"{p['target']}，最后一次小测必须取得多少分？",
                f"四项等权考核的成绩为 {scores}。第五项考核需要多少分，才能使总平均分达到 "
                f"{p['target']}？",
            )
            return variants[surface]
        if task.family_id == "curriculum-v2-cartons-damage":
            variants = (
                f"一批货有 {p['cartons']} 个纸箱，每箱 {p['packs']} 包，每包 {p['items']} 件"
                f"商品。去掉 {p['damaged']} 件损坏品和 {p['samples']} 件样品后，还剩多少件"
                "可售商品？",
                f"仓库收到 {p['cartons']} 个货箱，每箱有 {p['packs']} 个小盒，每盒装 "
                f"{p['items']} 个零件。质检丢弃 {p['damaged']} 个损坏零件，并另留 "
                f"{p['samples']} 个作为样品。可销售多少个零件？",
                f"一份订单包含 {p['cartons']} 个外箱，每个外箱装 {p['packs']} 个内包，每包 "
                f"{p['items']} 件。售前移除 {p['damaged']} 件次品和 {p['samples']} 件展示品。"
                "还剩多少件可售？",
            )
            return variants[surface]
        if task.family_id == "curriculum-v2-shared-bill":
            variants = (
                f"一行 {p['diners']} 人用餐，每人的餐费为 {p['meal']} 美元，另有 "
                f"{p['room']} 美元包间费。其中 {p['nonpaying']} 人不用付款，其余人平均承担"
                "全部账单。每位付款者应付多少？保留两位小数。",
                f"共有 {p['diners']} 人参加团队晚餐，每人餐费 {p['meal']} 美元，包间另收 "
                f"{p['room']} 美元。团队替 {p['nonpaying']} 位受邀者承担费用，其余人均摊"
                "全部账单。每位付款者应付多少？保留两位小数。",
                f"一场宴会有 {p['diners']} 人参加，每人费用 {p['meal']} 美元，另加固定场地费 "
                f"{p['room']} 美元。因其中 {p['nonpaying']} 人免单，其余人平均承担全部费用。"
                "每人应付多少？保留两位小数。",
            )
            return variants[surface]
        if task.family_id == "curriculum-v2-growth-fee":
            variants = (
                f"一个账户初始有 {p['initial']} 美元，第一年增长 {p['rate1']}%，第二年增长 "
                f"{p['rate2']}%，之后一次性扣除 {p['fee']} 美元费用。余额是多少？保留两位小数。",
                f"一个基金初始有 {p['initial']} 美元，第一年增长 {p['rate1']}%，第二年再增长 "
                f"{p['rate2']}%。两次增长后扣除 {p['fee']} 美元管理费。求最终余额，保留两位小数。",
                f"一笔 {p['initial']} 美元的投资第一年收益率为 {p['rate1']}%，第二年在新余额"
                f"基础上收益 {p['rate2']}%，之后支付固定费用 {p['fee']} 美元。还剩多少钱？"
                "保留两位小数。",
            )
            return variants[surface]

    # Historical parent rows use the original V2 deterministic parameters.
    i = int(task.metadata["generator_index"])
    if task.family_id == "curriculum-v2-sales-returns":
        regular, regular_price = 18 + i, 9 + i % 4
        premium, premium_price = 7 + i % 5, 15 + i % 3
        returned, fee = 2 + i % 3, 11 + i
        return (
            f"一家商店以每件 {regular_price} 美元售出 {regular} 件普通商品，并以每件 "
            f"{premium_price} 美元售出 {premium} 件高档商品。顾客退回 {returned} 件普通商品，"
            f"商店另获得固定 {fee} 美元服务费。净收入是多少？"
        )
    if task.family_id == "curriculum-v2-markup-discount":
        cost, markup, discount = 80 + 20 * i, 25 + 5 * (i % 3), 10 + 5 * (i % 2)
        return (
            f"一件商品成本为 {cost} 美元。价格先提高 {markup}%，再对标价打 {discount}% "
            "的折扣。最终价格是多少？结果保留两位小数。"
        )
    if task.family_id == "curriculum-v2-required-score":
        scores = (62 + i, 68 + i, 74 + i, 80 + i)
        target = 75 + i
        return (
            f"前四次考试成绩分别是 {scores[0]}、{scores[1]}、{scores[2]}、{scores[3]}。"
            f"要使五次考试的平均分达到 {target}，第五次需要多少分？"
        )
    if task.family_id == "curriculum-v2-cartons-damage":
        cartons, packs, items = 3 + i % 4, 4 + i % 3, 6 + i
        damaged, samples = 5 + i, 2 + i % 4
        return (
            f"一批货有 {cartons} 个纸箱，每箱 {packs} 包，每包 {items} 件商品。去掉 "
            f"{damaged} 件损坏品和 {samples} 件样品后，还剩多少件可售商品？"
        )
    if task.family_id == "curriculum-v2-shared-bill":
        diners, meal, room, nonpaying = 6 + i % 4, 14 + i, 20 + 2 * i, 1 + i % 2
        return (
            f"一行 {diners} 人用餐，每人的餐费为 {meal} 美元，另有 {room} 美元包间费。"
            f"其中 {nonpaying} 人不用付款，其余人平均承担全部账单。每位付款者应付多少？"
            "结果保留两位小数。"
        )
    if task.family_id == "curriculum-v2-growth-fee":
        initial, rate, fee = 200 + 25 * i, 5 + i % 4, 8 + i
        return (
            f"一个账户初始有 {initial} 美元，连续两年每年增长 {rate}%，之后一次性扣除 "
            f"{fee} 美元费用。余额是多少？结果保留两位小数。"
        )
    raise ValueError(f"unsupported audit family: {task.family_id}")


def _write_jsonl(path: Path, tasks: Sequence[Task]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(task.to_dict(), ensure_ascii=False) + "\n" for task in tasks),
        encoding="utf-8",
    )


def _audit_markdown(tasks: Sequence[Task]) -> str:
    parents = generate_calculator_curriculum_v2(examples_per_family=2)
    parents_by_family: dict[str, list[Task]] = defaultdict(list)
    variants_by_family: dict[str, list[Task]] = defaultdict(list)
    for task in parents:
        if task.family_id in AUDITED_SELF_WRITTEN_SEED_FAMILIES:
            parents_by_family[task.family_id].append(task)
    for task in tasks:
        variants_by_family[task.family_id].append(task)

    lines = [
        "# V4 从原种子题直接扩充：中文审核稿",
        "",
        "> 数据文件仍保留英文原题；本页中文仅供人工审核，不会作为模型训练输入。",
        "",
        "## 后续审核记录",
        "",
        "- 2026-10-05：项目所有者确认本页 84 道新增题全部审核通过。",
        "- 已批准副本：`data/generated/v4_seed_derived_self_written_approved_v1.jsonl`。",
        "- 下方 `pending` 描述和空复选框保留的是审核发生前的候选状态。",
        "- 已批准文件仍只是任务集；生成并审核轨迹后才能形成 SFT 数据。",
        "",
        "## 本批边界",
        "",
        f"- 母题 family：{len(AUDITED_SELF_WRITTEN_SEED_FAMILIES)} 个。",
        "- 每个 family 的母题：V3 已审核的 `000`、`001` 两题。",
        "- 每个 family 的新增变体：14 题，使用生成器索引 `002`—`015`。",
        f"- 新增候选总数：{len(tasks)} 题。",
        "- 当前状态：`review_status=pending`、`training_eligible=false`，尚未并入 SFT。",
        "- 只扩充历史 train family；旧 validation/test family 没有被挪入训练。",
        "",
        "## 审核重点",
        "",
        "1. 题意是否明确，但没有把解题公式直接写进题目。",
        "2. 数值是否自然，答案是否处于合理范围。",
        "3. 中文翻译是否准确表达英文原题；真正训练仍使用英文。",
        "4. 参考公式只用于离线校验，不会放进用户问题。",
        "",
    ]
    for family_id in AUDITED_SELF_WRITTEN_SEED_FAMILIES:
        lines.extend((
            f"## {_FAMILY_TITLES[family_id]}",
            "",
            f"- Family：`{family_id}`",
            "- 扩充方式：保持母题数量关系，独立生成数值，并轮换三种措辞或场景。",
            "",
            "### 已审核母题",
            "",
        ))
        for parent in parents_by_family[family_id]:
            lines.extend((
                f"- `{parent.task_id}`：{_problem_zh(parent)}",
                f"  - 参考公式：`{parent.metadata['reference_expression']}`",
                f"  - GT：`{parent.ground_truth['value']}`",
            ))
        lines.extend(("", "### 新增待审核变体", ""))
        for number, task in enumerate(variants_by_family[family_id], start=1):
            lines.extend((
                f"#### {number}. `{task.task_id}`",
                "",
                f"- 中文题意：{_problem_zh(task)}",
                f"- 英文原题：{task.prompt.split(chr(10) * 2, 1)[-1]}",
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
        default="data/review/v4_seed_derived_self_written_audit_v1.jsonl",
    )
    parser.add_argument(
        "--markdown",
        default="docs/V4_SEED_DERIVED_AUDIT_ZH.md",
    )
    parser.add_argument("--variants-per-family", type=int, default=14)
    args = parser.parse_args(argv)

    tasks = build_self_written_seed_expansion(
        variants_per_family=args.variants_per_family
    )
    jsonl_path = Path(args.jsonl)
    markdown_path = Path(args.markdown)
    _write_jsonl(jsonl_path, tasks)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(_audit_markdown(tasks), encoding="utf-8")
    print(
        json.dumps(
            {
                "candidate_count": len(tasks),
                "family_count": len({task.family_id for task in tasks}),
                "jsonl": str(jsonl_path),
                "markdown": str(markdown_path),
                "training_eligible": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
