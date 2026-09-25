import unittest

from verifiable_posttraining.reward import (
    calculator_result_rewards,
    calculator_trace_rewards,
    numeric_closeness_rewards,
    numeric_outcome_rewards,
    tool_numeric_closeness_rewards,
    tool_numeric_outcome_rewards,
    tool_typed_final_rewards,
    typed_final_rewards,
)


class RewardTests(unittest.TestCase):
    def test_format_and_outcome_rewards_are_separate(self) -> None:
        completions = [
            [{"role": "assistant", "content": '{"type":"final","answer":"2"}'}],
            [{"role": "assistant", "content": '{"type":"final","answer":"3"}'}],
            [{"role": "assistant", "content": '{"answer":"2"}'}],
        ]
        truths = [
            {"type": "number", "value": 2, "tolerance": 0},
            {"type": "number", "value": 2, "tolerance": 0},
            {"type": "number", "value": 2, "tolerance": 0},
        ]

        self.assertEqual(typed_final_rewards(completions), [1.0, 1.0, 0.0])
        self.assertEqual(numeric_outcome_rewards(completions, truths), [1.0, 0.0, 0.0])

    def test_tool_call_and_malformed_json_receive_zero(self) -> None:
        completions = [
            [{"role": "assistant", "content": '{"type":"tool_call"}'}],
            [{"role": "assistant", "content": "not json"}],
        ]
        truths = [
            {"type": "number", "value": 2, "tolerance": 0},
            {"type": "number", "value": 2, "tolerance": 0},
        ]

        self.assertEqual(typed_final_rewards(completions), [0.0, 0.0])
        self.assertEqual(numeric_outcome_rewards(completions, truths), [0.0, 0.0])
        self.assertEqual(numeric_closeness_rewards(completions, truths), [0.0, 0.0])

    def test_closeness_is_bounded_and_prefers_smaller_normalized_error(self) -> None:
        completions = [
            '{"type":"final","answer":100}',
            '{"type":"final","answer":90}',
            '{"type":"final","answer":50}',
            '{"type":"final","answer":"not numeric"}',
        ]
        truths = [
            {"type": "number", "value": 100, "tolerance": 0}
            for _ in completions
        ]

        rewards = numeric_closeness_rewards(completions, truths)

        self.assertEqual(rewards[0], 1.0)
        self.assertGreater(rewards[1], rewards[2])
        self.assertGreater(rewards[2], 0.0)
        self.assertEqual(rewards[3], 0.0)
        self.assertTrue(all(0.0 <= reward <= 1.0 for reward in rewards))

    def test_multiturn_calculator_trace_and_final_are_scored_separately(self) -> None:
        successful = [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "type": "function",
                        "function": {
                            "name": "calculator",
                            "arguments": {"expression": "2 + 3"},
                        },
                    }
                ],
            },
            {"role": "tool", "name": "calculator", "content": "5"},
            {"role": "assistant", "content": '{"type":"final","answer":5}'},
        ]
        missing_tool = [
            {"role": "assistant", "content": '{"type":"final","answer":5}'}
        ]
        truth = {"type": "number", "value": 5, "tolerance": 0}

        self.assertEqual(calculator_trace_rewards([successful, missing_tool]), [1.0, 0.0])
        self.assertEqual(
            calculator_result_rewards([successful, missing_tool], [truth, truth]),
            [1.0, 0.0],
        )
        self.assertEqual(tool_typed_final_rewards([successful, missing_tool]), [1.0, 1.0])
        self.assertEqual(
            tool_numeric_outcome_rewards([successful, missing_tool], [truth, truth]),
            [1.0, 1.0],
        )
        self.assertEqual(tool_numeric_closeness_rewards([successful], [truth]), [1.0])

        native_plain_final = [
            successful[0],
            successful[1],
            {"role": "assistant", "content": "5"},
        ]
        self.assertEqual(tool_typed_final_rewards([native_plain_final]), [0.0])
        self.assertEqual(tool_numeric_outcome_rewards([native_plain_final], [truth]), [1.0])

        wrong_expression = [
            successful[0],
            {"role": "tool", "name": "calculator", "content": "4"},
            {"role": "assistant", "content": "5"},
        ]
        self.assertEqual(calculator_trace_rewards([wrong_expression]), [1.0])
        self.assertEqual(tool_numeric_outcome_rewards([wrong_expression], [truth]), [1.0])
        self.assertEqual(calculator_result_rewards([wrong_expression], [truth]), [0.0])


if __name__ == "__main__":
    unittest.main()
