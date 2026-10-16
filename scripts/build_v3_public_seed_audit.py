"""Build a human-review pack of public numerical-reasoning seed questions.

This script does not create training data. It extracts a frozen set of
candidate questions from the official *training* splits of TAT-QA and FinQA,
independently replays their arithmetic labels, and marks every row as pending
human review.
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import operator
import re
from pathlib import Path
from typing import Any, Mapping, Sequence


TATQA_SOURCE = "https://github.com/NExTplusplus/TAT-QA"
FINQA_SOURCE = "https://github.com/czyssrs/FinQA"


TATQA_SELECTION = {
    "8bb54bf1-f6da-41ca-895d-602dbb88cfa3": "weighted_average",
    "347e3b8b-1982-4c53-a585-ab3001baed32": "weighted_average",
    "28b7f2b6-f15a-4390-b42c-310d7e727e14": "average_growth_rate",
    "8ade1eac-5a92-41bd-8b03-a74ae2769a6f": "average_growth_rate",
    "072b176c-a53e-4e12-97e6-b129ceb92da9": "average_growth_rate",
    "8fb16496-4bed-4e19-b230-a83de9ee6a59": "average_growth_rate",
    "af742fab-b68a-43ac-bb2b-77ef9f2fdbdf": "difference_of_averages",
    "2671e667-7692-483f-9710-2390e33cbcd2": "difference_of_averages",
    "ed480f2f-da8f-41b2-a68e-b837920a8a6f": "difference_of_averages",
    "21da1beb-b4d6-4439-8a3d-d91a8270b27d": "difference_of_averages",
    "d161e8c3-56f2-44bb-8c38-635fca79b1aa": "aggregate_percent_change",
    "7dd9e6c9-76f7-4600-8dd5-1d1820a42462": "aggregate_percent_change",
    "2b937b8e-a4b1-425c-a381-d6eab14bcc09": "aggregate_percent_change",
    "74bc19b4-b4f2-474d-8800-7d645ea59a8f": "aggregate_percent_change",
    "c1a00c0a-57ac-4370-a0dd-448fb21daf29": "derived_value_percent_change",
    "27c35832-3665-49c5-98df-e669b51effaf": "signed_percent_change",
    "858940e9-21f1-45db-acf2-21f298e367e5": "signed_percent_change",
    "bc009826-d4f1-4c53-9e3c-0e6349e8b527": "signed_percent_change",
    "dc0cf4b4-cb13-42b3-8280-06dedbf02128": "signed_multi_value_average",
    "a018d9b5-a8ed-4b3d-b4cb-7fdf8692b17c": "signed_multi_value_average",
    "b11bd2c7-36da-437a-af89-face31263fee": "signed_multi_value_average",
    "b160a76e-1ecf-4b21-9741-846d837e37f8": "ratio_of_derived_values",
    "529497d1-cff1-4784-bc46-2c6a6839ca20": "ratio_of_derived_values",
    "7b071ea4-9b6f-42cd-b50b-71f0845d4ce8": "payout_ratio",
    "0ccce335-dd41-498d-938a-cf526b7f6357": "aggregate_percent_change_with_loss",
}


FINQA_SELECTION = {
    "RCL/2009/page_90.pdf-1": "sum_of_products",
    "MRO/2009/page_137.pdf-3": "derived_value_percent_change",
    "BLK/2015/page_123.pdf-2": "multi_period_interest",
    "AMT/2014/page_88.pdf-1": "midpoint_rate_application",
    "IPG/2014/page_37.pdf-1": "ratio_of_aggregates",
}


_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
_UNARY_OPERATORS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _number(value: Any) -> float:
    text = str(value).replace("$", "").replace(",", "").replace("%", "").strip()
    return float(text)


def _evaluate_ast(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _evaluate_ast(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        return _BINARY_OPERATORS[type(node.op)](
            _evaluate_ast(node.left), _evaluate_ast(node.right)
        )
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _UNARY_OPERATORS[type(node.op)](_evaluate_ast(node.operand))
    raise ValueError(f"unsupported arithmetic node: {type(node).__name__}")


def evaluate_tatqa_derivation(derivation: str) -> float:
    expression = derivation.replace("$", "").replace(",", "")
    expression = expression.replace("[", "(").replace("]", ")").strip()
    expression = re.sub(r"(\d+(?:\.\d+)?)%", r"(\1/100)", expression)
    return _evaluate_ast(ast.parse(expression, mode="eval"))


def _finqa_argument(token: str, results: Sequence[float]) -> float:
    token = token.strip()
    if token.startswith("#"):
        return results[int(token[1:])]
    if token.startswith("const_"):
        token = token.removeprefix("const_")
    if token.endswith("%"):
        return float(token[:-1]) / 100
    return float(token)


def evaluate_finqa_program(program: str) -> float:
    results: list[float] = []
    calls = re.findall(r"([a-z_]+)\(([^,]+),\s*([^)]+)\)", program)
    if not calls:
        raise ValueError("FinQA program contains no calls")
    operations = {
        "add": operator.add,
        "subtract": operator.sub,
        "multiply": operator.mul,
        "divide": operator.truediv,
    }
    for name, left_token, right_token in calls:
        if name not in operations:
            raise ValueError(f"unsupported FinQA operation: {name}")
        left = _finqa_argument(left_token, results)
        right = _finqa_argument(right_token, results)
        results.append(float(operations[name](left, right)))
    return results[-1]


def _close(actual: float, expected: float) -> bool:
    # Public labels are sometimes rounded to one decimal place. Keep the raw
    # replay value in the audit row, but allow at most half of one tenth here.
    return math.isclose(actual, expected, rel_tol=1e-4, abs_tol=0.05)


def _audit_fields() -> dict[str, Any]:
    return {
        "status": "pending_review",
        "question_unambiguous": None,
        "ground_truth_correct": None,
        "solution_not_leaked": None,
        "keep_for_search_screen": None,
        "review_notes": "",
    }


def extract_tatqa(path: Path) -> list[dict[str, Any]]:
    documents = json.loads(path.read_text(encoding="utf-8"))
    found: dict[str, dict[str, Any]] = {}
    for document in documents:
        for question in document.get("questions", []):
            uid = question.get("uid")
            if uid not in TATQA_SELECTION:
                continue
            raw_value = evaluate_tatqa_derivation(question["derivation"])
            normalized_value = raw_value * 100 if question.get("scale") == "percent" else raw_value
            expected = _number(question["answer"])
            if not _close(normalized_value, expected):
                raise ValueError(
                    f"TAT-QA replay mismatch for {uid}: {normalized_value} != {expected}"
                )
            found[uid] = {
                "candidate_id": f"tatqa:{uid}",
                "source_dataset": "TAT-QA",
                "source_url": TATQA_SOURCE,
                "source_split": "train",
                "source_id": uid,
                "relation_family": TATQA_SELECTION[uid],
                "question": question["question"],
                "context": {"table": document["table"]},
                "reference_derivation": question["derivation"],
                "ground_truth": {
                    "type": "number",
                    "value": expected,
                    "scale": question.get("scale", ""),
                },
                "replay": {
                    "value": normalized_value,
                    "matches_source_answer": True,
                },
                "audit": _audit_fields(),
            }
    missing = set(TATQA_SELECTION) - set(found)
    if missing:
        raise ValueError(f"missing TAT-QA ids: {sorted(missing)}")
    return [found[uid] for uid in TATQA_SELECTION]


def extract_finqa(path: Path) -> list[dict[str, Any]]:
    documents = json.loads(path.read_text(encoding="utf-8"))
    found: dict[str, dict[str, Any]] = {}
    for document in documents:
        source_id = document.get("id")
        if source_id not in FINQA_SELECTION:
            continue
        qa = document["qa"]
        replay_value = evaluate_finqa_program(qa["program"])
        expected = _number(qa["answer"])
        normalized_value = replay_value * 100 if "%" in str(qa["answer"]) else replay_value
        if not _close(normalized_value, expected):
            raise ValueError(
                f"FinQA replay mismatch for {source_id}: {normalized_value} != {expected}"
            )
        found[source_id] = {
            "candidate_id": f"finqa:{source_id}",
            "source_dataset": "FinQA",
            "source_url": FINQA_SOURCE,
            "source_split": "train",
            "source_id": source_id,
            "relation_family": FINQA_SELECTION[source_id],
            "question": qa["question"],
            "context": {
                "table": document.get("table", []),
                "gold_evidence": qa.get("gold_inds", {}),
            },
            "reference_derivation": qa["program"],
            "ground_truth": {
                "type": "number",
                "value": expected,
                "scale": "percent" if "%" in str(qa["answer"]) else "",
            },
            "replay": {
                "value": normalized_value,
                "matches_source_answer": True,
                "matches_source_exe_ans": _close(replay_value, float(qa["exe_ans"])),
            },
            "audit": _audit_fields(),
        }
    missing = set(FINQA_SELECTION) - set(found)
    if missing:
        raise ValueError(f"missing FinQA ids: {sorted(missing)}")
    return [found[source_id] for source_id in FINQA_SELECTION]


def write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n"
    path.write_text(text, encoding="utf-8")


def write_markdown(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    counts: dict[str, int] = {}
    for row in rows:
        family = str(row["relation_family"])
        counts[family] = counts.get(family, 0) + 1
    lines = [
        "# V3 public seed-question audit pack v0",
        "",
        "> Status: review-only. These rows are not approved SFT, RL, validation, or test data.",
        "",
        "## Purpose",
        "",
        "This pack freezes 30 public **train-split** candidates for human review before any",
        "4B search screen. Arithmetic labels were independently replayed during extraction,",
        "but replay agreement does not prove that a question is unambiguous or useful.",
        "",
        "## Composition",
        "",
        f"- TAT-QA: {sum(row['source_dataset'] == 'TAT-QA' for row in rows)}",
        f"- FinQA: {sum(row['source_dataset'] == 'FinQA' for row in rows)}",
        "- TabMWP: 0 (withheld because inspected candidates were heavily templated)",
        "",
        "Relation-family counts:",
        "",
    ]
    lines.extend(f"- `{family}`: {count}" for family, count in sorted(counts.items()))
    lines.extend(
        [
            "",
            "## Review checklist",
            "",
            "For every row in `data/review/v3_public_seed_audit_v0.jsonl`, decide:",
            "",
            "1. Is the question unambiguous without revealing the solution procedure?",
            "2. Are the referenced table/text values sufficient?",
            "3. Is the derivation mathematically and semantically correct?",
            "4. Are units and percentage conventions explicit enough?",
            "5. Is the relation meaningfully different from already accepted rows?",
            "6. Should the row enter the 4B pass@1/pass@N search screen?",
            "",
            "## Candidate index",
            "",
            "| # | Source | Family | Source ID | Ground truth | Question |",
            "|---:|---|---|---|---:|---|",
        ]
    )
    for index, row in enumerate(rows, 1):
        question = str(row["question"]).replace("|", "\\|")
        truth = row["ground_truth"]
        value = f"{truth['value']} {truth.get('scale', '')}".strip()
        lines.append(
            f"| {index} | {row['source_dataset']} | `{row['relation_family']}` | "
            f"`{row['source_id']}` | {value} | {question} |"
        )
    lines.extend(
        [
            "",
            "## Non-goals",
            "",
            "- Passing arithmetic replay is not automatic approval.",
            "- Source programs are references, not the only acceptable model trajectory.",
            "- No validation/test examples are included.",
            "- The 30 rows must not be used for SFT until human review and split-family design are complete.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tatqa-train", required=True, type=Path)
    parser.add_argument("--finqa-train", required=True, type=Path)
    parser.add_argument("--output-jsonl", required=True, type=Path)
    parser.add_argument("--output-markdown", required=True, type=Path)
    args = parser.parse_args(argv)

    rows = extract_tatqa(args.tatqa_train) + extract_finqa(args.finqa_train)
    if len(rows) != 30:
        raise ValueError(f"expected 30 candidates, found {len(rows)}")
    write_jsonl(args.output_jsonl, rows)
    write_markdown(args.output_markdown, rows)
    print(json.dumps({"candidate_count": len(rows), "status": "pending_review"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
