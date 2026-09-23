import unittest

from verifiable_posttraining.schemas import ToolCall
from verifiable_posttraining.tools.calculator import (
    CalculatorError,
    evaluate_expression,
    execute_calculator,
)


class CalculatorExpressionTests(unittest.TestCase):
    def test_operator_precedence_parentheses_and_unary_signs(self) -> None:
        self.assertEqual(evaluate_expression("-(2 + 3) * 4 / 2"), -10)

    def test_fractional_result_is_returned_as_float(self) -> None:
        self.assertAlmostEqual(evaluate_expression("1 / 8"), 0.125)

    def test_function_calls_are_rejected(self) -> None:
        with self.assertRaisesRegex(CalculatorError, "unsupported syntax"):
            evaluate_expression("__import__('os').system('whoami')")

    def test_names_are_rejected(self) -> None:
        with self.assertRaisesRegex(CalculatorError, "unsupported syntax"):
            evaluate_expression("secret + 1")

    def test_division_by_zero_has_stable_code(self) -> None:
        with self.assertRaises(CalculatorError) as raised:
            evaluate_expression("1 / 0")
        self.assertEqual(raised.exception.code, "division_by_zero")

    def test_excessive_values_are_rejected(self) -> None:
        with self.assertRaises(CalculatorError) as raised:
            evaluate_expression("1000000000000 * 2")
        self.assertEqual(raised.exception.code, "numeric_limit_exceeded")


class CalculatorToolTests(unittest.TestCase):
    def test_successful_call_returns_aligned_observation(self) -> None:
        call = ToolCall(
            call_id="call-1",
            name="calculator",
            arguments={"expression": "40 / 10"},
        )
        observation = execute_calculator(call)
        self.assertTrue(observation.ok)
        self.assertEqual(observation.call_id, call.call_id)
        self.assertEqual(observation.content, {"value": 4})

    def test_extra_arguments_are_rejected(self) -> None:
        call = ToolCall(
            call_id="call-1",
            name="calculator",
            arguments={"expression": "1 + 1", "precision": 2},
        )
        observation = execute_calculator(call)
        self.assertFalse(observation.ok)
        self.assertEqual(observation.error_code, "invalid_arguments")

    def test_expected_failures_become_observations(self) -> None:
        call = ToolCall(
            call_id="call-1",
            name="calculator",
            arguments={"expression": "1 / 0"},
        )
        observation = execute_calculator(call)
        self.assertFalse(observation.ok)
        self.assertEqual(observation.error_code, "division_by_zero")


if __name__ == "__main__":
    unittest.main()
