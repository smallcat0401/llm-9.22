"""Tier A: a deliberately small and auditable arithmetic tool.

Model-generated tool arguments are untrusted input.  The calculator therefore
parses an expression into an AST and evaluates only numeric literals and the
four basic arithmetic operators.  It never delegates to ``eval`` or ``exec``.

Safety invariants:

* names, calls, attributes, containers, and comprehensions are rejected;
* input length and AST size are bounded;
* intermediate and final values must be finite and within a fixed magnitude;
* malformed arguments become failed observations instead of exceptions that
  can crash an evaluation run.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from decimal import Decimal, DivisionByZero, InvalidOperation
from typing import Mapping

from ..schemas import Observation, ToolCall

MAX_EXPRESSION_LENGTH = 200
MAX_AST_NODES = 64
MAX_ABSOLUTE_VALUE = Decimal("1e12")


@dataclass(frozen=True, slots=True)
class CalculatorError(ValueError):
    """A stable, machine-readable calculator failure."""

    code: str
    message: str

    def __str__(self) -> str:
        return self.message


_BINARY_OPERATORS = {
    ast.Add: lambda left, right: left + right,
    ast.Sub: lambda left, right: left - right,
    ast.Mult: lambda left, right: left * right,
    ast.Div: lambda left, right: left / right,
}

_UNARY_OPERATORS = {
    ast.UAdd: lambda value: value,
    ast.USub: lambda value: -value,
}


def _checked(value: Decimal) -> Decimal:
    if not value.is_finite() or abs(value) > MAX_ABSOLUTE_VALUE:
        raise CalculatorError(
            "numeric_limit_exceeded",
            f"absolute values must not exceed {MAX_ABSOLUTE_VALUE}",
        )
    return value


def _evaluate_node(node: ast.AST) -> Decimal:
    if isinstance(node, ast.Constant):
        # bool is a subclass of int, so it must be rejected explicitly.
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise CalculatorError("unsupported_expression", "only numeric literals are allowed")
        try:
            return _checked(Decimal(str(node.value)))
        except InvalidOperation as exc:
            raise CalculatorError("invalid_number", "invalid numeric literal") from exc

    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _evaluate_node(node.left)
        right = _evaluate_node(node.right)
        try:
            return _checked(_BINARY_OPERATORS[type(node.op)](left, right))
        except (DivisionByZero, ZeroDivisionError) as exc:
            raise CalculatorError("division_by_zero", "division by zero is not allowed") from exc
        except InvalidOperation as exc:
            raise CalculatorError("invalid_operation", "invalid arithmetic operation") from exc

    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _checked(_UNARY_OPERATORS[type(node.op)](_evaluate_node(node.operand)))

    raise CalculatorError(
        "unsupported_expression",
        f"unsupported syntax: {type(node).__name__}",
    )


def evaluate_expression(expression: str) -> int | float:
    """Safely evaluate a bounded expression containing ``+``, ``-``, ``*``, ``/``.

    Parentheses and unary signs work because they are represented by the
    allowed AST nodes.  Every other Python construct is rejected.
    """

    if not isinstance(expression, str):
        raise CalculatorError("invalid_arguments", "expression must be a string")
    if not expression.strip():
        raise CalculatorError("invalid_arguments", "expression must not be empty")
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise CalculatorError("expression_too_long", "expression is too long")

    try:
        parsed = ast.parse(expression, mode="eval")
    except (SyntaxError, ValueError) as exc:
        raise CalculatorError("invalid_syntax", "expression is not valid arithmetic") from exc

    if sum(1 for _ in ast.walk(parsed)) > MAX_AST_NODES:
        raise CalculatorError("expression_too_complex", "expression has too many AST nodes")

    value = _evaluate_node(parsed.body)
    if value == value.to_integral_value():
        return int(value)
    return float(value)


def execute_calculator(call: ToolCall) -> Observation:
    """Execute one calculator call and convert every expected failure to an observation."""

    if call.name != "calculator":
        return Observation(
            call_id=call.call_id,
            ok=False,
            content={"message": "tool call name must be 'calculator'"},
            error_code="wrong_tool",
        )

    arguments: Mapping[str, object] = call.arguments
    if set(arguments) != {"expression"}:
        return Observation(
            call_id=call.call_id,
            ok=False,
            content={"message": "calculator requires exactly one 'expression' argument"},
            error_code="invalid_arguments",
        )

    try:
        value = evaluate_expression(arguments["expression"])
    except CalculatorError as exc:
        return Observation(
            call_id=call.call_id,
            ok=False,
            content={"message": exc.message},
            error_code=exc.code,
        )

    return Observation(call_id=call.call_id, ok=True, content={"value": value})
