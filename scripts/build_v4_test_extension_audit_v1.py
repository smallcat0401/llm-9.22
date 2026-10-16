"""Build the revised, pending V4 test extension and Chinese review artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Sequence

from verifiable_posttraining.dataset import load_tasks_jsonl, validate_task_dataset, write_tasks_jsonl
from verifiable_posttraining.v4_test_extension import TestExtensionRecord
from verifiable_posttraining.v4_test_extension_v1 import build_v4_test_extension_v1_records

from scripts.build_v4_test_extension_audit import EXPECTED_V3_TEST_SHA256, FAMILY_TITLES


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _wording_pattern(prompt: str) -> str:
    return re.sub(r"\d+(?:\.\d+)?", "<n>", prompt)


def _audit_markdown(records: Sequence[TestExtensionRecord], originals: Sequence) -> str:
    by_family: dict[str, list[TestExtensionRecord]] = defaultdict(list)
    old_counts = Counter(task.family_id for task in originals)
    for record in records:
        by_family[record.task.family_id].append(record)
    lines = [
        "# V4 test 母题扩充 v1：中文审核稿",
        "",
        "> **待审核，未冻结，未运行模型。** 英文题给模型；中文、公式和 GT 只供审核。",
        "> v0 审核稿保留不动。v1 主要修正自写题只有一套句式、数字单调变大的问题。",
        "",
        "## 数量和分组",
        "",
        "- 原冻结 V3 test：36 道，不改题面或 GT。v1 对每道母题各新增一道待审核题。",
        "- 新增 36 道：32 道自写题族扩充，4 道为 GSM8K-test 母题衍生的**新写合成题**。",
        "- 若 36 道全部审核通过，拟组合 72 道；现在**尚未**把它们并入正式 test。",
        "- 四个自写题族各用四种英文数量关系表述，每种两道；参数不按索引持续加大。",
        "- 这些题仍沿用既有八个 test-only family，没有增加八种全新推理类型；同族题相关。",
        "",
        "| 题族 | 原题 | 新题 | 拟合计 | 新题类别 |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for family, title in FAMILY_TITLES.items():
        group = "公开母题衍生合成题" if "-public-" in family else "自写扩充"
        new_count = len(by_family[family])
        lines.append(f"| {title} | {old_counts[family]} | {new_count} | "
                     f"{old_counts[family] + new_count} | {group} |")
    lines.extend(("| **总计** | **36** | **36** | **72** | — |", "", "## 自检与评估边界", "",
                  "- 每题的参考表达式已由安全计算器执行，GT 又由独立的 Decimal 数量公式计算；两者通过数值 verifier 比对。",
                  "- 新旧题 ID/题面不重复，36 道新题各有一条母题记录；与 V4 train、validation 的 family 不交叉。",
                  "- 要求保留两位小数的 GT 在本审核稿按两位显示；JSONL 仍按 numeric GT 存值，不检查最终答案的字面尾零。",
                  "- 原公开题仍是 4 道；衍生合成题不可报告为新 GSM8K 公开题或独立外部评估。",
                  "- 四个自写家族拟占 64/72，整体分数会偏向它们。最终请分别报告每族、原题/扩充题及公开原题/合成衍生题结果。",
                  "- 数值核对不能替代语义审核；请逐题检查中英题意、题面信息是否充分、税费顺序、单位和舍入。",
                  "- 审核前 `review_status=pending`，全部为 test-only 且 `training_eligible=false`；不得用于搜索、SFT、GRPO 或 checkpoint 选择。",
                  ""))
    for family, title in FAMILY_TITLES.items():
        lines.extend((f"## {title}", "", f"- Family：`{family}`", ""))
        for number, record in enumerate(by_family[family], 1):
            task = record.task
            en = task.prompt.split("\n\n", 1)[1]
            value = task.ground_truth["value"]
            gt_display = f"{value:.2f}" if "to two decimals" in en else str(value)
            lines.extend((f"### {number}. `{task.task_id}`", "",
                          f"- 母题：`{task.metadata['parent_test_task_id']}`",
                          f"- 类别：`{task.metadata['source_group']}`；措辞变体：`{task.metadata['wording_variant']}`",
                          f"- 中文题意：{record.question_zh}",
                          f"- 英文题意：{en}",
                          f"- 参考公式：`{task.metadata['reference_expression']}`",
                          f"- GT：`{gt_display}`；容差：`{task.ground_truth['tolerance']}`",
                          "- 审核结论：□保留　□修改　□删除", ""))
    return "\n".join(lines).rstrip() + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen-test", type=Path, default=Path("data/generated/v3_test_v1.jsonl"))
    parser.add_argument("--v0-audit", type=Path, default=Path("data/review/v4_test_extension_audit_v0.jsonl"))
    parser.add_argument("--train", type=Path, default=Path("data/generated/v4_train_tasks_curated_v2.jsonl"))
    parser.add_argument("--validation", type=Path, default=Path("data/generated/v4_validation_v1.jsonl"))
    parser.add_argument("--jsonl", type=Path, default=Path("data/review/v4_test_extension_audit_v1.jsonl"))
    parser.add_argument("--markdown", type=Path, default=Path("docs/V4_TEST_EXTENSION_AUDIT_V1_ZH.md"))
    parser.add_argument("--manifest", type=Path, default=Path("artifacts/dataset_manifests/v4_test_extension_audit_v1.json"))
    args = parser.parse_args(argv)

    if _sha256(args.frozen_test) != EXPECTED_V3_TEST_SHA256:
        raise ValueError("frozen V3 test hash changed")
    originals = load_tasks_jsonl(args.frozen_test)
    records = build_v4_test_extension_v1_records(originals)
    train = load_tasks_jsonl(args.train)
    validation = load_tasks_jsonl(args.validation)
    validate_task_dataset((*train, *validation, *originals, *(row.task for row in records)))
    write_tasks_jsonl((row.task for row in records), args.jsonl)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text(_audit_markdown(records, originals), encoding="utf-8")

    family_counts = Counter(task.family_id for task in originals)
    family_counts.update(row.task.family_id for row in records)
    pattern_counts = {
        family: len({_wording_pattern(row.task.prompt) for row in records
                     if row.task.family_id == family})
        for family in FAMILY_TITLES
    }
    manifest = {
        "dataset": "v4_test_extension_audit_v1",
        "status": "pending_owner_review",
        "evaluation_only": True,
        "training_eligible": False,
        "original_frozen_count": 36,
        "new_candidate_count": len(records),
        "planned_total_if_approved": 36 + len(records),
        "new_by_source_group": dict(Counter(row.task.metadata["source_group"] for row in records)),
        "planned_family_counts": dict(sorted(family_counts.items())),
        "new_wording_patterns_by_family": pattern_counts,
        "input_frozen_test": str(args.frozen_test),
        "input_frozen_test_sha256": _sha256(args.frozen_test),
        "previous_pending_audit": str(args.v0_audit),
        "previous_pending_audit_sha256": _sha256(args.v0_audit),
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
    print(json.dumps({key: value for key, value in manifest.items() if not key.endswith("sha256")},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
