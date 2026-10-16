"""Produce a pending, Chinese-readable V4 test extension audit pack."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Sequence

from verifiable_posttraining.dataset import load_tasks_jsonl, validate_task_dataset, write_tasks_jsonl
from verifiable_posttraining.v4_test_extension import TestExtensionRecord, build_v4_test_extension_records


EXPECTED_V3_TEST_SHA256 = "9e6613d6f11f3cdc38e90a5b0b6aeddf94b4378b96c5be04116af45e2cf82eae"

FAMILY_TITLES = {
    "v3-eval-test-subscription-overage-v1": "流量套餐、超额费与税后租赁费",
    "v3-eval-test-route-cost-v1": "分路段油耗、过路费与抵用券",
    "v3-eval-test-partial-refund-v1": "折扣购买与部分退款",
    "v3-eval-test-bonus-deduction-v1": "加班、奖金、税与保险费",
    "v3-eval-test-public-loan-repayment-v1": "一次性借款费用与分期还款",
    "v3-eval-test-public-bogo-purchase-v1": "买一件、第二件半价",
    "v3-eval-test-public-delivery-fee-v1": "订单小计、配送费与小费",
    "v3-eval-test-public-weighted-test-score-v1": "分组正确率与加权得分",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _markdown(records: Sequence[TestExtensionRecord], originals: Sequence) -> str:
    by_family: dict[str, list[TestExtensionRecord]] = defaultdict(list)
    old_counts = Counter(task.family_id for task in originals)
    for record in records:
        by_family[record.task.family_id].append(record)
    lines = [
        "# V4 test 母题扩充：中文审核稿",
        "",
        "> 待审核候选，尚未冻结，尚未运行任何模型。英文题面将来给模型；中文、参考公式和 GT 只用于人工审核。",
        "",
        "## 总体分组",
        "",
        "- 原 V3 test：36 题，文件和哈希保持不变。",
        "- 本轮：36 道原题各衍生 1 道，新增 36 道待审核候选。若全部通过，组合共 72 题。",
        "- 自写母题衍生：32 道；4 道 GSM8K-test 母题衍生：4 道新写合成题。后者**不是**新 GSM8K 公开题，不能算作独立公开样本。",
        "- 8 个 test-only family；与 train、validation 的 family 隔离。本轮只生成题目和 GT，不执行模型搜索或评估。",
        "- 同一 family 的题互相关联；最终须报告每族成功数，也应分开报告原题与扩充题、原公开题与公开母题衍生题。",
        "",
        "| 题族 | 原题 | 新题 | 合计 | 新题来源 |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for family, title in FAMILY_TITLES.items():
        new_count = len(by_family[family])
        group = "公开母题衍生的合成题" if "-public-" in family else "自写母题衍生"
        lines.append(f"| {title} | {old_counts[family]} | {new_count} | {old_counts[family] + new_count} | {group} |")
    lines.extend(("| **总计** | **36** | **36** | **72** | — |", "", "## 审核边界", "",
                  "- 每道新题的参考公式已经用安全计算器重放，并与独立数量公式的计算结果核对。",
                  "- 计算自检不等于题意审核：仍需逐题确认英文/中文、单位、税费顺序、舍入与 GT。",
                  "- 全部新题为 `review_status=pending`、`evaluation_only=true`、`training_eligible=false`。未获审核通过不得合并冻结。",
                  "- test 仅用于最终评价；看过模型在 test 上的错题后，不得据此调训练再用同一 test 宣称独立提升。",
                  ""))
    for family, title in FAMILY_TITLES.items():
        lines.extend((f"## {title}", "", f"- Family：`{family}`", ""))
        for number, record in enumerate(by_family[family], 1):
            task = record.task
            en = task.prompt.split("\n\n", 1)[1]
            lines.extend((f"### {number}. `{task.task_id}`", "",
                          f"- 母题：`{task.metadata['parent_test_task_id']}`",
                          f"- 来源类别：`{task.metadata['source_group']}`",
                          f"- 中文题意：{record.question_zh}",
                          f"- 英文题意：{en}",
                          f"- 参考公式：`{task.metadata['reference_expression']}`",
                          f"- GT：`{task.ground_truth['value']}`；容差：`{task.ground_truth['tolerance']}`",
                          "- 审核结论：□保留　□修改　□删除", ""))
    return "\n".join(lines).rstrip() + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen-test", type=Path, default=Path("data/generated/v3_test_v1.jsonl"))
    parser.add_argument("--train", type=Path, default=Path("data/generated/v4_train_tasks_curated_v2.jsonl"))
    parser.add_argument("--validation", type=Path, default=Path("data/generated/v4_validation_v1.jsonl"))
    parser.add_argument("--jsonl", type=Path, default=Path("data/review/v4_test_extension_audit_v0.jsonl"))
    parser.add_argument("--markdown", type=Path, default=Path("docs/V4_TEST_EXTENSION_AUDIT_ZH.md"))
    parser.add_argument("--manifest", type=Path, default=Path("artifacts/dataset_manifests/v4_test_extension_audit_v0.json"))
    args = parser.parse_args(argv)

    if _sha256(args.frozen_test) != EXPECTED_V3_TEST_SHA256:
        raise ValueError("frozen V3 test hash differs from the approved manifest")
    originals = load_tasks_jsonl(args.frozen_test)
    records = build_v4_test_extension_records(originals)
    train = load_tasks_jsonl(args.train)
    validation = load_tasks_jsonl(args.validation)
    validate_task_dataset((*train, *validation, *originals, *(record.task for record in records)))
    write_tasks_jsonl((record.task for record in records), args.jsonl)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text(_markdown(records, originals), encoding="utf-8")

    family_counts = Counter(task.family_id for task in originals)
    family_counts.update(record.task.family_id for record in records)
    manifest = {
        "dataset": "v4_test_extension_audit_v0",
        "status": "pending_owner_review",
        "evaluation_only": True,
        "training_eligible": False,
        "original_frozen_count": len(originals),
        "new_candidate_count": len(records),
        "planned_total_if_approved": len(originals) + len(records),
        "new_by_source_group": dict(Counter(record.task.metadata["source_group"] for record in records)),
        "planned_family_counts": dict(sorted(family_counts.items())),
        "input_frozen_test": str(args.frozen_test),
        "input_frozen_test_sha256": _sha256(args.frozen_test),
        "input_train": str(args.train),
        "input_train_sha256": _sha256(args.train),
        "input_validation": str(args.validation),
        "input_validation_sha256": _sha256(args.validation),
        "output": str(args.jsonl),
        "output_sha256": _sha256(args.jsonl),
        "review_artifact": str(args.markdown),
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if not k.endswith("sha256")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
