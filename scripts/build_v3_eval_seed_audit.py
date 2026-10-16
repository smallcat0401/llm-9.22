"""Build the Chinese-reviewable V3 evaluation seed audit pack."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Sequence

from verifiable_posttraining.v3_eval_seed import build_v3_eval_seed_candidates


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _render_markdown(rows: list[dict[str, object]]) -> str:
    lines = [
        "# V3 validation/test 种子题审核（待审核）",
        "",
        "> 这不是冻结评估集，也没有运行模型。所有题目目前都是 `pending`。",
        "> 审核通过后才会扩展自写模板，并分别冻结 validation 与 test。",
        "",
        "## 当前设计",
        "",
        "- 共 24 道：validation 12 道、test 12 道。",
        "- 每个 split 含 8 道自写题（4 个模板，每模板 2 道）和 4 道未使用的 GSM8K 公开题。",
        "- validation/test 的自写模板互不重复。",
        "- 英文题将来给模型；中文仅用于审核，不修改公开数据原文。",
        "- 参考公式只用于离线重算 GT，绝不会放进模型 prompt。",
        "",
        "## 自审核结论",
        "",
        "- 已逐题核对题意、公式、GT、舍入和区分度。",
        "- 补助题英文已改为‘人工与材料合计的百分比’，消除语法歧义。",
        "- 原 validation 候选 GSM8K train #4379 因休息和加油次数存在边界争议，已替换为 #6154。",
        "- 原 test 候选 GSM8K test #576 因安装费数值异常，已替换为 #1070。",
        "- 第 23 题是较简单的低难度锚点，只观察基础稳定性，不扩展同类模板。",
        "- 修正后的 24 道题均通过公式重放；仍等待项目所有者最终审核。",
        "",
    ]
    number = 0
    for split, title in (("validation", "Validation 候选"), ("test", "Test 候选")):
        lines.extend((f"## {title}", ""))
        for row in [item for item in rows if item["proposed_split"] == split]:
            number += 1
            source = "自写" if row["source_type"] == "self_written" else (
                f"GSM8K {row['source_split']} #{row['source_index']}"
            )
            lines.extend((
                f"### {number}. `{row['candidate_id']}`",
                "",
                f"- 来源：{source}",
                f"- 题族：`{row['family_id']}`",
                f"- 状态：`{row['review_status']}`",
                f"- 中文审核题：{row['prompt_zh']}",
                f"- 英文原题/拟用题：{row['prompt_en']}",
                f"- 参考公式：`{row['reference_expression']}`",
                f"- GT：`{row['ground_truth']}`（容差 `{row['tolerance']}`）",
                "",
            ))
    lines.extend((
        "## 审核通过后",
        "",
        "1. 删除或改写有歧义、过于简单、暗示解法的题。",
        "2. 只扩展通过审核的自写模板；公开题不替换数字。",
        "3. 生成正式 Task JSONL，重新检查 family/source 泄漏并记录 SHA-256。",
        "4. 先测 starting policy；validation 选择 checkpoint，test 保持封存。",
        "",
    ))
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gsm8k-train", type=Path, required=True)
    parser.add_argument("--gsm8k-test", type=Path, required=True)
    parser.add_argument("--exclude-artifact", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args(argv)

    candidates = build_v3_eval_seed_candidates(
        gsm8k_train_path=args.gsm8k_train,
        gsm8k_test_path=args.gsm8k_test,
        exclusion_artifacts=args.exclude_artifact,
    )
    rows = [candidate.to_dict() for candidate in candidates]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text(_render_markdown(rows), encoding="utf-8")
    manifest = {
        "dataset": "v3_eval_seed_audit_v0",
        "status": "pending_human_review",
        "not_frozen_evaluation_data": True,
        "candidate_count": len(rows),
        "split_counts": {
            split: sum(row["proposed_split"] == split for row in rows)
            for split in ("validation", "test")
        },
        "source_counts": {
            source: sum(row["source_type"] == source for row in rows)
            for source in ("self_written", "public")
        },
        "source_files": {
            "gsm8k_train": str(args.gsm8k_train),
            "gsm8k_train_sha256": _sha256(args.gsm8k_train),
            "gsm8k_test": str(args.gsm8k_test),
            "gsm8k_test_sha256": _sha256(args.gsm8k_test),
            "exclusion_artifacts": [str(path) for path in args.exclude_artifact],
        },
        "outputs": {
            "jsonl": str(args.output),
            "jsonl_sha256": _sha256(args.output),
            "markdown": str(args.markdown),
            "markdown_sha256": _sha256(args.markdown),
        },
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
