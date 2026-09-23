import unittest

from verifiable_posttraining.verifier import normalize_numeric_answer, verify_numeric_answer


class NumericNormalizationTests(unittest.TestCase):
    def test_percent_is_normalized_to_percentage_points(self) -> None:
        self.assertEqual(normalize_numeric_answer("The answer is 25%."), 25)

    def test_thousands_separator_is_supported(self) -> None:
        self.assertEqual(normalize_numeric_answer("1,234.5"), 1234.5)

    def test_multiple_numbers_are_rejected_as_ambiguous(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly one"):
            normalize_numeric_answer("The result is between 20 and 30")

    def test_non_finite_answer_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite"):
            normalize_numeric_answer(float("nan"))


class NumericVerifierTests(unittest.TestCase):
    def test_exact_answer_passes(self) -> None:
        result = verify_numeric_answer(
            "25%",
            {"type": "number", "value": 25.0, "tolerance": 1e-6},
        )
        self.assertTrue(result.passed)
        self.assertEqual(result.absolute_error, 0.0)

    def test_absolute_tolerance_is_applied(self) -> None:
        result = verify_numeric_answer(
            "10.04",
            {"type": "number", "value": 10, "tolerance": 0.05},
        )
        self.assertTrue(result.passed)

    def test_relative_tolerance_is_applied(self) -> None:
        result = verify_numeric_answer(
            101,
            {"type": "number", "value": 100, "relative_tolerance": 0.02},
        )
        self.assertTrue(result.passed)
        self.assertEqual(result.allowed_error, 2.0)

    def test_wrong_answer_has_diagnostic_code(self) -> None:
        result = verify_numeric_answer(
            "12",
            {"type": "number", "value": 10, "tolerance": 0.1},
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.error_code, "wrong_answer")

    def test_malformed_answer_is_a_scored_failure(self) -> None:
        result = verify_numeric_answer(
            "I do not know",
            {"type": "number", "value": 10},
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.error_code, "invalid_answer")

    def test_invalid_ground_truth_fails_fast(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-negative"):
            verify_numeric_answer(
                "10",
                {"type": "number", "value": 10, "tolerance": -1},
            )


if __name__ == "__main__":
    unittest.main()
