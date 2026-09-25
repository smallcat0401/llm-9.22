import unittest

from verifiable_posttraining.calculator_analysis import (
    CalculatorFailureCategory,
    analyze_native_record,
    analyze_trajectory_record,
    summarize_analyses,
)
from verifiable_posttraining.dataset import generate_pilot_tasks
from verifiable_posttraining.schemas import Split, Task, TaskKind


class CalculatorAnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.task = Task(
            task_id="calculator-1",
            family_id="calculator-family",
            kind=TaskKind.CALCULATOR,
            split=Split.TEST,
            prompt="Compute a percentage.",
            allowed_tools=("calculator",),
            ground_truth={"type": "number", "value": 27.906976744186, "tolerance": 0.005},
        )

    def test_percent_change_dataset_accepts_two_decimal_rounding(self) -> None:
        task = next(
            task for task in generate_pilot_tasks(seed=7)
            if task.family_id == "calculator-percent-change-v1"
        )
        self.assertEqual(task.ground_truth["tolerance"], 0.005)
        self.assertIn("two decimal places", task.prompt)

    def test_native_correct_tool_result_and_rounded_final_is_success(self) -> None:
        record = {
            "tool_called": True,
            "tool_succeeded": True,
            "messages": [
                {"role": "assistant", "tool_calls": [{"function": {
                    "name": "calculator", "arguments": {"expression": "(55-43)/43*100"}
                }}]},
                {"role": "tool", "content": "27.906976744186"},
            ],
            "verification": {"predicted_value": 27.91},
        }
        analysis = analyze_native_record(record, self.task)
        self.assertEqual(analysis.category, CalculatorFailureCategory.SUCCESS)

    def test_native_wrong_expression_is_not_hidden_by_valid_tool_call(self) -> None:
        record = {
            "tool_called": True,
            "tool_succeeded": True,
            "messages": [
                {"role": "assistant", "tool_calls": [{"function": {
                    "name": "calculator", "arguments": {"expression": "55-43/43*100"}
                }}]},
                {"role": "tool", "content": "-45"},
            ],
            "verification": {"predicted_value": -45},
        }
        analysis = analyze_native_record(record, self.task)
        self.assertEqual(analysis.category, CalculatorFailureCategory.WRONG_TOOL_RESULT)

    def test_trajectory_protocol_error_is_separate(self) -> None:
        record = {
            "task": self.task.to_dict(),
            "trajectory": {"steps": [], "final_answer": None},
            "rollout": {"protocol_error": "invalid JSON"},
            "verification": {"predicted_value": None},
        }
        analysis = analyze_trajectory_record(record)
        self.assertEqual(analysis.category, CalculatorFailureCategory.PROTOCOL_ERROR)

    def test_summary_keeps_zero_count_categories(self) -> None:
        analysis = analyze_native_record(
            {
                "tool_called": False,
                "tool_succeeded": False,
                "messages": [],
                "verification": {"predicted_value": None},
            },
            self.task,
        )
        summary = summarize_analyses((analysis,))
        self.assertEqual(summary["category_counts"]["no_tool_call"], 1)
        self.assertEqual(summary["category_counts"]["success"], 0)
        self.assertEqual(summary["by_family"]["calculator-family"]["record_count"], 1)
        self.assertEqual(
            summary["by_family"]["calculator-family"]["category_counts"][
                "no_tool_call"
            ],
            1,
        )


if __name__ == "__main__":
    unittest.main()
