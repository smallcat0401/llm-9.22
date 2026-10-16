import unittest

from verifiable_posttraining.native_tool_evaluation import (
    _build_parser,
    evaluate_native_calculator,
    parse_native_response,
    run_native_calculator_episode,
)
from verifiable_posttraining.schemas import Split, Task, TaskKind


class ScriptedNativePolicy:
    def __init__(self, messages):
        self.messages = iter(messages)

    def generate_message(self, messages, *, seed):
        del messages, seed
        return next(self.messages)


class NativeToolEvaluationTests(unittest.TestCase):
    def test_cli_adapter_is_optional_for_starting_policy_evaluation(self) -> None:
        args = _build_parser().parse_args(
            ["--output-dir", "out", "--run-id", "starting-policy"]
        )

        self.assertIsNone(args.adapter_path)

    def test_malformed_parser_output_is_a_failure_not_an_exception(self):
        class Tokenizer:
            eos_token_id = 2

            def parse_response(self, ids, *, prefix, tools):
                raise ValueError("malformed tool XML")

        self.assertTrue(parse_native_response(Tokenizer(), [1, 2], "")["parse_error"])

    def test_malformed_tool_call_does_not_crash_or_receive_credit(self):
        task = Task(
            task_id="calculator-1", family_id="calculator-family",
            kind=TaskKind.CALCULATOR, split=Split.TEST,
            prompt="Use the calculator to compute 2 + 3.",
            allowed_tools=("calculator",),
            ground_truth={"type": "number", "value": 5, "tolerance": 0},
        )
        for calls in [[None], [{"function": None}], [{"function": {"name": "wrong"}}]]:
            with self.subTest(calls=calls):
                result = run_native_calculator_episode(task, ScriptedNativePolicy([
                    {"role": "assistant", "content": "5", "tool_calls": calls}
                ]), seed=7)
                self.assertFalse(result.tool_succeeded)
                self.assertFalse(result.verification.passed)

    def test_parser_truncates_at_chat_eos_before_trailing_document_eos(self):
        from transformers.utils.chat_parsing import parse_response
        from trl.chat_template_utils import qwen3_5_template

        class Tokenizer:
            eos_token_id = 2

            def parse_response(self, ids, *, prefix, tools):
                raw = "".join({1: "25", 2: "<|im_end|>", 3: "<|endoftext|>"}[i] for i in ids)
                return parse_response(raw, qwen3_5_template, prefix=prefix)

        parsed = parse_native_response(Tokenizer(), [1, 2, 3], "<|im_start|>assistant\n")
        self.assertEqual(parsed["content"], "25")

    def test_success_requires_executed_tool_and_correct_final(self) -> None:
        task = Task(
            task_id="calculator-1",
            family_id="calculator-family",
            kind=TaskKind.CALCULATOR,
            split=Split.TEST,
            prompt="Use the calculator to compute 2 + 3.",
            allowed_tools=("calculator",),
            ground_truth={"type": "number", "value": 5, "tolerance": 0},
        )
        policy = ScriptedNativePolicy(
            [
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
                {"role": "assistant", "content": "5"},
            ]
        )

        result = run_native_calculator_episode(task, policy, seed=7)

        self.assertTrue(result.tool_succeeded)
        self.assertTrue(result.task_success)
        self.assertFalse(result.typed_final)
        self.assertEqual(result.messages[-2]["content"], "5")

    def test_direct_answer_does_not_count_as_native_tool_success(self) -> None:
        task = Task(
            task_id="calculator-1",
            family_id="calculator-family",
            kind=TaskKind.CALCULATOR,
            split=Split.TEST,
            prompt="Use the calculator to compute 2 + 3.",
            allowed_tools=("calculator",),
            ground_truth={"type": "number", "value": 5, "tolerance": 0},
        )
        result = run_native_calculator_episode(
            task,
            ScriptedNativePolicy([{"role": "assistant", "content": "5"}]),
            seed=7,
        )

        self.assertFalse(result.tool_called)
        self.assertFalse(result.task_success)
        self.assertTrue(result.verification.passed)

    def test_correct_final_after_wrong_expression_is_not_effective_tool_success(self) -> None:
        task = Task(
            task_id="calculator-1", family_id="calculator-family",
            kind=TaskKind.CALCULATOR, split=Split.TEST,
            prompt="Use the calculator to compute 2 + 3.",
            allowed_tools=("calculator",),
            ground_truth={"type": "number", "value": 5, "tolerance": 0},
        )
        policy = ScriptedNativePolicy([
            {"role": "assistant", "tool_calls": [{"function": {
                "name": "calculator", "arguments": {"expression": "2 + 2"}
            }}]},
            {"role": "assistant", "content": "5"},
        ])
        result = run_native_calculator_episode(task, policy, seed=7)
        self.assertTrue(result.tool_succeeded)
        self.assertFalse(result.tool_result_verification.passed)
        self.assertTrue(result.verification.passed)
        self.assertFalse(result.task_success)

    def test_sampled_evaluation_runs_requested_trials(self) -> None:
        task = Task(
            task_id="calculator-1",
            family_id="calculator-family",
            kind=TaskKind.CALCULATOR,
            split=Split.TEST,
            prompt="Use the calculator to compute 2 + 3.",
            allowed_tools=("calculator",),
            ground_truth={"type": "number", "value": 5, "tolerance": 0},
        )
        call = {
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
        }
        policy = ScriptedNativePolicy([call, {"role": "assistant", "content": "5"}] * 2)

        results = evaluate_native_calculator((task,), policy, seed=7, num_samples=2)

        self.assertEqual(len(results), 2)
        self.assertTrue(all(result.task_success for result in results))


if __name__ == "__main__":
    unittest.main()
