"""Build the pending Chinese audit pack for the V4 validation extension."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Sequence

from verifiable_posttraining.dataset import write_tasks_jsonl
from verifiable_posttraining.v4_validation_extension import (
    V4_VALIDATION_PUBLIC_FAMILIES,
    ValidationExtensionRecord,
    build_v4_validation_extension_records,
)


_FAMILY_INFO = {
    "v3-eval-val-public-ratio-allocation-v1": (
        "嵌套比例分配",
        "先确定两个已知类别，再把剩余数量按给定比例分配。",
    ),
    "v3-eval-val-public-weighted-demand-v1": (
        "多组加权需求",
        "各组人数乘以人均份数，加入备用量后再换算为原料单位。",
    ),
    "v3-eval-val-public-population-flow-v1": (
        "期间增长与逐年流动",
        "期间自然增长按初始人口计算，迁入迁出按每年重复发生。",
    ),
    "v3-eval-val-public-tank-loss-recovery-v1": (
        "多阶段损失与部分恢复",
        "从满容量开始经历两段损失和一段补充，求距离重新装满的缺口。",
    ),
}


def _english_question(record: ValidationExtensionRecord) -> str:
    return record.task.prompt.split("\n\n", maxsplit=1)[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _markdown(records: Sequence[ValidationExtensionRecord]) -> str:
    by_family: dict[str, list[ValidationExtensionRecord]] = defaultdict(list)
    for record in records:
        by_family[record.task.family_id].append(record)

    lines = [
        "# V4 validation公开family扩充：中文审核稿",
        "",
        "> 模型输入为英文；中文题意、参考公式和GT只用于人工审核。",
        "> 后续状态：用户于2026-10-06完成审核且未提出修改；28题已纳入 `data/generated/v4_validation_v1.jsonl`。下方空白勾选框保留初版审核格式。",
        "",
        "## 为什么是28题",
        "",
        "- 现有冻结validation共有36题。",
        "- 4个自写family已经各有8题，共32题，不做修改。",
        "- 另有4个公开family各只有1道原题。这里为每个family新增7道合成题，共28题。",
        "- 若全部审核通过，后续V4 validation将是64题，即8个family各8题。",
        "- 原36题不会被覆盖；冻结test也不会读取或修改。",
        "",
        "## 提交人工审核时的状态（历史）",
        "",
        "- 这28题全部为 `review_status=pending`。",
        "- 全部为 `evaluation_only=true`、`training_eligible=false`。",
        "- 它们不能进入SFT、GRPO或训练轨迹收集。",
        "- 参考表达式通过安全计算器回放，并由独立关系公式复算。",
        "",
        "## 本轮自检结论",
        "",
        "- 逐题核对28道英文题、中文题、参考公式和GT：未发现题意与数值冲突。",
        "- 比例分配7题：A、C、D、E数量均为正整数；加权需求7题：需求份数总量均为整数。",
        "- 人口流动7题：自然增长明确为整个期间相对初始人口的增量，期末人口均为正数。",
        "- 储罐7题：累计漏失小于容量，补充量小于漏失量，因此未出现空罐或补水溢出。",
        "- 28道题的ID、英文题面均不重复；每个family的7道新增题GT各不相同；与V4 train及冻结test无family交叉。",
        "- 注意：比例分配和储罐题使用固定参数组合；`seed=509`只会改变加权需求与人口流动的随机参数。",
        "- 注意：同一family的7道题仍是同一种数量关系，主要检验该关系下的稳定性；V3验证题曾用于选择模型，合并后的64题不能称为全新独立holdout。",
        "- 以上是冻结前的自检记录；审核完成后已生成独立的V4验证集，尚未用于V4模型评估。",
        "",
    ]
    for family_id, (title, relation) in _FAMILY_INFO.items():
        lines.extend((
            f"## {title}",
            "",
            f"- Family：`{family_id}`",
            f"- 原公开题：`{V4_VALIDATION_PUBLIC_FAMILIES[family_id]}`",
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
                f"- 参考公式：`{task.metadata['reference_expression']}`",
                f"- GT：`{task.ground_truth['value']}`；容差：`{task.ground_truth['tolerance']}`",
                "- 审核结论：□保留　□修改　□删除",
                "",
            ))
    return "\n".join(lines).rstrip() + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--jsonl",
        type=Path,
        default=Path("data/review/v4_validation_public_extension_audit_v0.jsonl"),
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        default=Path("docs/V4_VALIDATION_EXTENSION_AUDIT_ZH.md"),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(
            "artifacts/dataset_manifests/"
            "v4_validation_public_extension_audit_v0.json"
        ),
    )
    parser.add_argument(
        "--frozen-validation",
        type=Path,
        default=Path("data/generated/v3_validation_v1.jsonl"),
    )
    args = parser.parse_args(argv)

    records = build_v4_validation_extension_records()
    write_tasks_jsonl((record.task for record in records), args.jsonl)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text(_markdown(records), encoding="utf-8")
    manifest = {
        "dataset": "v4_validation_public_extension_audit_v0",
        "status": "pending_owner_review",
        "evaluation_only": True,
        "training_eligible": False,
        "candidate_count": len(records),
        "family_count": len({record.task.family_id for record in records}),
        "family_counts": dict(Counter(record.task.family_id for record in records)),
        "planned_combined_validation_count": 64,
        "input_frozen_validation": str(args.frozen_validation),
        "input_frozen_validation_sha256": _sha256(args.frozen_validation),
        "output": str(args.jsonl),
        "output_sha256": _sha256(args.jsonl),
        "review_artifact": str(args.markdown),
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
