"""Tier A: outcome verifiers for final model answers.

The verifier scores the task outcome.  Whether the model followed one expected
tool path is intentionally not part of numeric correctness; tool-use behavior
is measured separately as a diagnostic signal.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

_NUMBER_PATTERN = re.compile(
    r"(?<![\w.])[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:[eE][-+]?\d+)?%?(?![\w.])"
)


@dataclass(frozen=True, slots=True)
class VerificationResult:
    passed: bool
    predicted_value: float | None
    target_value: float
    absolute_error: float | None
    allowed_error: float
    error_code: str | None = None


def _finite_decimal(value: Any, *, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be numeric, not bool")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc
    if not number.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return number


def normalize_numeric_answer(answer: Any) -> Decimal:
    """Extract exactly one finite number from a final answer.

    A percent sign is treated as a display unit: ``25%`` normalizes to ``25``.
    Ground-truth values for percentage-point tasks must therefore also use 25,
    not 0.25.  Answers containing zero or multiple numeric candidates are
    rejected rather than guessed.
    """

    if isinstance(answer, bool):
        raise ValueError("boolean answers are not numeric answers")
    if isinstance(answer, (int, float, Decimal)):
        return _finite_decimal(answer, field_name="answer")
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("answer must be a non-empty string or number")

    matches = _NUMBER_PATTERN.findall(answer)
    if len(matches) != 1:
        raise ValueError("answer must contain exactly one numeric value")
    token = matches[0].rstrip("%").replace(",", "")
    return _finite_decimal(token, field_name="answer")


def verify_numeric_answer(
    answer: Any,
    ground_truth: Mapping[str, Any],
) -> VerificationResult:
    """Compare one answer with a validated numeric ground-truth specification."""

    if ground_truth.get("type") != "number":
        raise ValueError("numeric verifier requires ground_truth type 'number'")
    if "value" not in ground_truth:
        raise ValueError("numeric ground_truth requires a value")

    target = _finite_decimal(ground_truth["value"], field_name="ground_truth.value")
    absolute_tolerance = _finite_decimal(
        ground_truth.get("tolerance", 0), field_name="ground_truth.tolerance"
    )
    relative_tolerance = _finite_decimal(
        ground_truth.get("relative_tolerance", 0),
        field_name="ground_truth.relative_tolerance",
    )
    if absolute_tolerance < 0 or relative_tolerance < 0:
        raise ValueError("tolerances must be non-negative")

    allowed_error = max(absolute_tolerance, relative_tolerance * abs(target))
    result_kwargs = {
        "target_value": float(target),
        "allowed_error": float(allowed_error),
    }
    try:
        predicted = normalize_numeric_answer(answer)
    except ValueError:
        return VerificationResult(
            passed=False,
            predicted_value=None,
            absolute_error=None,
            error_code="invalid_answer",
            **result_kwargs,
        )

    error = abs(predicted - target)
    return VerificationResult(
        passed=error <= allowed_error,
        predicted_value=float(predicted),
        absolute_error=float(error),
        error_code=None if error <= allowed_error else "wrong_answer",
        **result_kwargs,
    )
