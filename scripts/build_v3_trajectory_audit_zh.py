"""Render the V3 training-eligible successful trajectories for Chinese review."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence


QUESTION_ZH: Mapping[str, tuple[str, str]] = {
    "v3-public-cb26a8ffa95b-arithmetic": (
        "3月至4月的加权平均回购价",
        "3月回购58.0百万股（5800万股）、平均每股52.93美元；4月回购29.1百万股（2910万股）、平均每股54.41美元。按回购股数加权，求两个月合计的平均每股回购价格。",
    ),
    "v3-public-f2f32edba913-arithmetic": (
        "两个业务合计净销售额的增长率",
        "International业务净销售额由2017年的816.0增至2018年的843.5；Refrigerated & Frozen由2652.7增至2753.0。求两个业务合计净销售额从2017到2018年的百分比变化。",
    ),
    "v3-public-e511f3abfa5e-arithmetic": (
        "流动与非流动合同资产合计变化率",
        "流动合同资产由169增至2350，非流动合同资产由507增至581。求合同资产合计余额从2018到2019年的百分比变化。",
    ),
    "v3-public-9d6f397353af-arithmetic": (
        "未拨备债务绝对金额的变化率",
        "括号表示负债。按负债绝对金额计算：未拨备债务由2018年的28变为2019年的30。金额增加记正、减少记负，求百分比变化。",
    ),
    "v3-public-2adfb9bf033b-arithmetic": (
        "利息费用绝对金额的变化率",
        "括号表示费用。按费用绝对金额计算：利息费用由2017年的14762增至2018年的28176。增加记正、减少记负，求百分比变化。",
    ),
    "v3-public-aa20ff7068b0-arithmetic": (
        "保修成本绝对金额的变化率",
        "括号表示成本。按成本绝对金额计算：已发生保修成本由2018年的26降至2019年的22。增加记正、减少记负，求百分比变化。",
    ),
    "v3-public-42e42100b593-arithmetic": (
        "四个福利修订额的算术平均",
        "2018和2019财年中，养老金福利修订额为-1.4、-0.6，其他福利修订额为0.8、17.2。求这四个数的算术平均值。",
    ),
    "v3-public-7aca02f2885b-arithmetic": (
        "两年合并口径的长期债务占比",
        "2014与2013年的长期债务分别为1623.5和1129.8，总债务分别为1732.8和1662.5。按两年合并口径，求长期债务占总债务的百分比。",
    ),
    "v3-screen-curriculum-v2-sales-returns-000": (
        "销售、退货与服务费（一）",
        "售出18件普通商品，每件9美元；7件高级商品，每件15美元。退回2件普通商品，另收入11美元服务费。求净收入。",
    ),
    "v3-screen-curriculum-v2-sales-returns-001": (
        "销售、退货与服务费（二）",
        "售出19件普通商品，每件10美元；8件高级商品，每件16美元。退回3件普通商品，另收入12美元服务费。求净收入。",
    ),
    "v3-screen-curriculum-v2-markup-discount-000": (
        "先加价再打折（一）",
        "商品成本80美元，先加价25%，再对标价打九折。求最终价格，保留两位小数。",
    ),
    "v3-screen-curriculum-v2-markup-discount-001": (
        "先加价再打折（二）",
        "商品成本100美元，先加价30%，再对标价打八五折。求最终价格，保留两位小数。",
    ),
    "v3-screen-curriculum-v2-required-score-000": (
        "反推第五次考试成绩（一）",
        "前四次成绩为62、68、74、80。若五次平均分需要达到75，第五次应得多少分？",
    ),
    "v3-screen-curriculum-v2-required-score-001": (
        "反推第五次考试成绩（二）",
        "前四次成绩为63、69、75、81。若五次平均分需要达到76，第五次应得多少分？",
    ),
    "v3-screen-curriculum-v2-cartons-damage-000": (
        "多层包装扣除损坏品（一）",
        "3箱货物，每箱4包，每包6件。去掉5件损坏品和2件样品后，还剩多少件可销售商品？",
    ),
    "v3-screen-curriculum-v2-cartons-damage-001": (
        "多层包装扣除损坏品（二）",
        "4箱货物，每箱5包，每包7件。去掉6件损坏品和3件样品后，还剩多少件可销售商品？",
    ),
    "v3-screen-curriculum-v2-shared-bill-000": (
        "含免单者的均摊账单（一）",
        "6人的餐费为每人14美元，另有20美元房间费。其中1人不付款，其余人平摊全部账单。每位付款者应付多少？",
    ),
    "v3-screen-curriculum-v2-shared-bill-001": (
        "含免单者的均摊账单（二）",
        "7人的餐费为每人15美元，另有22美元房间费。其中2人不付款，其余人平摊全部账单。每位付款者应付多少？",
    ),
    "v3-screen-curriculum-v2-growth-fee-000": (
        "连续增长两年后扣费（一）",
        "账户初始200美元，连续两年每年增长5%，然后一次性扣除8美元费用。求最终余额。",
    ),
    "v3-screen-curriculum-v2-growth-fee-001": (
        "连续增长两年后扣费（二）",
        "账户初始225美元，连续两年每年增长6%，然后一次性扣除9美元费用。求最终余额。",
    ),
    "v3-gsm8k-train-6486-calculator": (
        "同日往返两个相反方向的地点",
        "Janet从家向东30英里看皮肤科，又要从家向西50英里看妇科。同一天完成两次看诊并分别返回家中，汽车每加仑行驶20英里。共用多少加仑汽油？",
    ),
    "v3-gsm8k-train-5525-calculator": (
        "薯片袋数的增减",
        "Abie原有20袋薯片，送给朋友4袋，又在商店买了6袋。最后有多少袋？",
    ),
    "v3-gsm8k-train-3229-calculator": (
        "两人每小时销量差",
        "Stanley每小时卖4杯柠檬水，Carl每小时卖7杯。3小时内Carl比Stanley多卖多少杯？",
    ),
    "v3-gsm8k-train-0535-calculator": (
        "按打购买鸡蛋",
        "Tim买了3打鸡蛋，每个鸡蛋0.50美元。一共支付多少美元？",
    ),
    "v3-gsm8k-train-6511-calculator": (
        "两类外星学生的脚趾总数",
        "每个Hoopit有4只手，每只手3个脚趾；每个Neglart有5只手，每只手2个脚趾。校车载7个Hoopit和8个Neglart，共有多少个脚趾？",
    ),
    "v3-gsm8k-train-0544-calculator": (
        "反推原有狗粮重量",
        "Elise买了一袋15千克和一袋10千克狗粮，此时共有40千克。购买前原有多少千克？",
    ),
    "v3-gsm8k-train-5655-calculator": (
        "工作日与周末牛奶消费",
        "Lolita每个工作日喝3盒牛奶；周六喝工作日每天的2倍，周日喝工作日每天的3倍。一周共喝多少盒？",
    ),
    "v3-gsm8k-train-3946-calculator": (
        "两天制作与吃掉的布朗尼",
        "第一天做2打布朗尼，父亲吃8块、女儿吃4块。第二天又做2打并加入剩余部分。台面上共有多少块？",
    ),
    "v3-gsm8k-train-2502-calculator": (
        "游戏中有趣内容时长",
        "游戏承诺100小时内容，其中80%是枯燥刷取；扩展包再增加30小时有趣内容。总共有多少小时有趣内容？",
    ),
}


GROUP_ZH = {
    "reviewed_public": "公开审核题",
    "self_written_v2": "自建V2题",
    "fresh_gsm8k_train": "新GSM8K-train题",
}


REJECTED_TASK_IDS = {
    # Rejected after human review: the source says "3 boxes during weekdays"
    # but the label assumes 3 boxes on each of five weekdays.
    "v3-gsm8k-train-5655-calculator",
}


GT_DISPLAY = {
    # JSON numbers do not preserve insignificant trailing zeros.  The review
    # view keeps the precision explicitly requested by these prompts.
    "v3-screen-curriculum-v2-markup-discount-000": "90.00",
    "v3-screen-curriculum-v2-markup-discount-001": "110.50",
}


def read_jsonl(path: Path) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def difficulty_label(successes: int) -> str:
    if successes <= 2:
        return "🟠 稀有成功（适合搜索，但需重点核验）"
    if successes <= 6:
        return "🟢 中间难度（优先审核）"
    if successes == 7:
        return "🟡 接近过易"
    return "⚪ 8/8全对（可能过易）"


def original_question(prompt: str) -> str:
    parts = prompt.split("\n\n")
    return parts[1].strip() if len(parts) > 1 else prompt.strip()


def render(
    candidates: Sequence[Mapping[str, Any]],
    verified: Sequence[Mapping[str, Any]],
) -> str:
    eligible = [
        row
        for row in verified
        if row["task"]["metadata"]["training_eligible"]
        and row["task"]["task_id"] not in REJECTED_TASK_IDS
    ]
    if len(eligible) != 28:
        raise ValueError(f"expected 28 eligible verified tasks, found {len(eligible)}")
    task_ids = {row["task"]["task_id"] for row in eligible}
    missing_translations = task_ids - set(QUESTION_ZH)
    if missing_translations:
        raise ValueError(f"missing Chinese translations: {sorted(missing_translations)}")

    success_counts = Counter(
        row["task"]["task_id"]
        for row in candidates
        if row["rollout"]["task_success"]
    )
    group_counts = Counter(row["task"]["metadata"]["seed_screen_group"] for row in eligible)
    no_tool_path_count = sum(not row["trajectory"]["steps"] for row in eligible)
    lines = [
        "# V3 可训练成功轨迹中文审核页",
        "",
        "> 状态：人工审核中。这28条只是候选，尚未批准进入SFT。",
        "",
        "## 怎么审核",
        "",
        "每题展示的是Best-of-8中被搜索器选中的第一条严格成功轨迹。请重点判断：",
        "",
        "1. 中文题意是否与原英文任务一致；",
        "2. 模型公式是否表达了正确的数量关系；",
        "3. 工具返回值、final与GT是否一致；",
        "4. 即使答案正确，轨迹是否适合教给模型；",
        "5. 没有调用工具的轨迹只能作为数量推理数据，不能冒充工具调用数据。",
        "",
        "## 总览",
        "",
        f"- 候选任务：{len(eligible)}",
        f"- 公开审核题：{group_counts['reviewed_public']}",
        f"- 自建V2题：{group_counts['self_written_v2']}",
        f"- 新GSM8K-train题：{group_counts['fresh_gsm8k_train']}",
        f"- 选中轨迹未调用工具：{no_tool_path_count}",
        "- 已拒绝并移出本页：原第27题 `v3-gsm8k-train-5655-calculator`（英文题意有歧义）。",
        "- 审核结论未填写前，不生成SFT数据。",
        "",
    ]

    ordered = sorted(
        eligible,
        key=lambda row: (
            ("reviewed_public", "self_written_v2", "fresh_gsm8k_train").index(
                row["task"]["metadata"]["seed_screen_group"]
            ),
            row["task"]["task_id"],
        ),
    )
    for index, row in enumerate(ordered, start=1):
        task = row["task"]
        task_id = task["task_id"]
        metadata = task["metadata"]
        title, question_zh = QUESTION_ZH[task_id]
        group = metadata["seed_screen_group"]
        successes = success_counts[task_id]
        steps = row["trajectory"]["steps"]
        selected_index = int(row["search"]["selected_sample_index"])
        lines.extend(
            [
                f"## {index}. {title}",
                "",
                f"- **分组：** {GROUP_ZH[group]}",
                f"- **Task ID：** `{task_id}`",
                f"- **Family：** `{task['family_id']}`",
                f"- **成功次数：** {successes}/8（选中第{selected_index + 1}次采样）",
                f"- **难度标记：** {difficulty_label(successes)}",
                f"- **是否调用工具：** {'是' if steps else '否 ⚠️'}",
            ]
        )
        source_id = metadata.get("source_id")
        source_index = metadata.get("source_index")
        if source_id:
            lines.append(f"- **来源ID：** `{source_id}`")
        if source_index is not None:
            lines.append(f"- **GSM8K source_index：** `{source_index}`")
        lines.extend(["", f"**中文题意：** {question_zh}", ""])

        if steps:
            for step in steps:
                call = step["tool_call"]
                observation = step["observation"]
                arguments = call.get("arguments", {})
                expression = arguments.get("expression", json.dumps(arguments, ensure_ascii=False))
                content = observation.get("content")
                if isinstance(content, Mapping) and "value" in content:
                    content = content["value"]
                lines.extend(
                    [
                        f"- **模型公式：** `{expression}`",
                        f"- **工具返回：** `{content}`",
                    ]
                )
        else:
            lines.append("- **模型路径：** 未调用计算器，直接给出final。")
        lines.extend(
            [
                f"- **模型final：** `{row['trajectory']['final_answer']}`",
                f"- **GT：** `{GT_DISPLAY.get(task_id, task['ground_truth']['value'])}`",
                f"- **允许误差：** `{task['ground_truth'].get('tolerance', 0)}`",
                "",
                "<details>",
                "<summary>查看原英文问题</summary>",
                "",
                original_question(task["prompt"]),
                "",
                "</details>",
                "",
                "### 人工审核",
                "",
                "- [ ] 中文题意与英文来源一致",
                "- [ ] 题目无歧义且没有泄露解法",
                "- [ ] 模型公式/直接推理在语义上正确",
                "- [ ] 工具结果、final和GT一致",
                "- [ ] 轨迹不是偶然命中或verifier漏洞",
                "- [ ] 批准进入SFT候选",
                "- **审核备注：**",
                "",
                "---",
                "",
            ]
        )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--verified", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)

    text = render(read_jsonl(args.candidates), read_jsonl(args.verified))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text + "\n", encoding="utf-8")
    print(json.dumps({"review_tasks": 28, "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
