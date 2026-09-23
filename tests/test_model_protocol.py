import unittest

from verifiable_posttraining.model_protocol import (
    MAX_MODEL_OUTPUT_LENGTH,
    FinalAnswer,
    parse_model_action,
)
from verifiable_posttraining.schemas import ToolCall


class ModelProtocolTests(unittest.TestCase):
    def test_valid_tool_call_is_parsed(self) -> None:
        result = parse_model_action(
            '{"type":"tool_call","call_id":"call-1","name":"calculator",'
            '"arguments":{"expression":"1 + 1"}}'
        )
        self.assertTrue(result.ok)
        self.assertEqual(
            result.action,
            ToolCall(
                call_id="call-1",
                name="calculator",
                arguments={"expression": "1 + 1"},
            ),
        )

    def test_valid_final_answer_is_parsed(self) -> None:
        result = parse_model_action('{"type":"final","answer":"25%"}')
        self.assertEqual(result.action, FinalAnswer(answer="25%"))

    def test_runner_can_supply_a_deterministic_call_id(self) -> None:
        result = parse_model_action(
            '{"type":"tool_call","name":"calculator",'
            '"arguments":{"expression":"1 + 1"}}',
            default_call_id="call-3",
        )
        self.assertEqual(
            result.action,
            ToolCall(
                call_id="call-3",
                name="calculator",
                arguments={"expression": "1 + 1"},
            ),
        )

    def test_missing_call_id_without_default_is_rejected(self) -> None:
        result = parse_model_action(
            '{"type":"tool_call","name":"calculator",'
            '"arguments":{"expression":"1 + 1"}}'
        )
        self.assertEqual(result.error_code, "invalid_tool_call")

    def test_complete_json_code_fence_is_allowed(self) -> None:
        result = parse_model_action('```json\n{"type":"final","answer":25}\n```')
        self.assertEqual(result.action, FinalAnswer(answer=25))

    def test_prose_around_json_is_rejected(self) -> None:
        result = parse_model_action('Here is my answer: {"type":"final","answer":25}')
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "malformed_json")

    def test_partial_code_fence_is_rejected(self) -> None:
        result = parse_model_action('```json\n{"type":"final","answer":25}')
        self.assertEqual(result.error_code, "malformed_json_fence")

    def test_duplicate_json_keys_are_rejected(self) -> None:
        result = parse_model_action('{"type":"final","answer":25,"answer":30}')
        self.assertEqual(result.error_code, "malformed_json")
        self.assertIn("duplicate", result.message or "")

    def test_non_standard_nan_is_rejected(self) -> None:
        result = parse_model_action('{"type":"final","answer":NaN}')
        self.assertEqual(result.error_code, "malformed_json")

    def test_tool_arguments_must_be_an_object(self) -> None:
        result = parse_model_action(
            '{"type":"tool_call","call_id":"call-1","name":"calculator",'
            '"arguments":"1 + 1"}'
        )
        self.assertEqual(result.error_code, "invalid_tool_call")

    def test_non_string_call_id_is_a_parse_failure(self) -> None:
        result = parse_model_action(
            '{"type":"tool_call","call_id":1,"name":"calculator",'
            '"arguments":{"expression":"1 + 1"}}'
        )
        self.assertEqual(result.error_code, "invalid_tool_call")
        self.assertIn("call_id must be a string", result.message or "")

    def test_unexpected_fields_are_rejected(self) -> None:
        result = parse_model_action('{"type":"final","answer":25,"confidence":1}')
        self.assertEqual(result.error_code, "invalid_final_answer")

    def test_unknown_action_type_is_rejected(self) -> None:
        result = parse_model_action('{"type":"browse","query":"secret"}')
        self.assertEqual(result.error_code, "unknown_action_type")

    def test_non_scalar_final_answer_is_rejected(self) -> None:
        result = parse_model_action('{"type":"final","answer":[25]}')
        self.assertEqual(result.error_code, "invalid_final_answer")

    def test_empty_and_oversized_outputs_are_rejected(self) -> None:
        self.assertEqual(parse_model_action("  ").error_code, "empty_output")
        oversized = "x" * (MAX_MODEL_OUTPUT_LENGTH + 1)
        self.assertEqual(parse_model_action(oversized).error_code, "output_too_long")
        oversized_whitespace = " " * (MAX_MODEL_OUTPUT_LENGTH + 1)
        self.assertEqual(
            parse_model_action(oversized_whitespace).error_code,
            "output_too_long",
        )


if __name__ == "__main__":
    unittest.main()
