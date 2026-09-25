import unittest

from verifiable_posttraining.prompting import (
    PROMPT_PROTOCOL_VERSION,
    append_tool_exchange,
    build_initial_messages,
    build_native_calculator_grpo_messages,
)
from verifiable_posttraining.schemas import Observation, Split, Task, TaskKind


class PromptingTests(unittest.TestCase):
    def test_initial_messages_do_not_leak_ground_truth_or_metadata(self) -> None:
        task = Task(
            task_id="hidden-001",
            family_id="hidden-family",
            kind=TaskKind.CALCULATOR,
            split=Split.TEST,
            prompt="Compute the requested quantity.",
            allowed_tools=("calculator",),
            ground_truth={"type": "number", "value": 987654321},
            metadata={"private_marker": "DO_NOT_LEAK"},
        )
        rendered = "\n".join(message.content for message in build_initial_messages(task))
        self.assertNotIn("987654321", rendered)
        self.assertNotIn("DO_NOT_LEAK", rendered)
        self.assertIn("calculator", rendered)
        self.assertIn('"expression":"1 + 1"', rendered)

    def test_sql_prompt_contains_exact_query_argument_shape(self) -> None:
        task = Task(
            task_id="sql-001",
            family_id="sql-family",
            kind=TaskKind.SQL,
            split=Split.TEST,
            prompt="Query the documented table.",
            allowed_tools=("sql",),
            ground_truth={"type": "number", "value": 1},
        )
        rendered = "\n".join(message.content for message in build_initial_messages(task))
        self.assertIn('"name":"sql"', rendered)
        self.assertIn('"arguments":{"query":"SELECT ..."}', rendered)
        self.assertIn("a tool_call OR a final answer, never both", rendered)
        self.assertIn("Never put type, name, or answer inside arguments", rendered)
        self.assertIn("final answer must be one scalar", rendered)
        self.assertIn("aggregate them in SQL", rendered)
        self.assertEqual(PROMPT_PROTOCOL_VERSION, "v3-sql-scalar-aggregate")

    def test_tool_observation_is_serialized_as_a_tool_message(self) -> None:
        task = Task(
            task_id="calculator-001",
            family_id="calculator-family",
            kind=TaskKind.CALCULATOR,
            split=Split.TEST,
            prompt="Compute one plus one.",
            allowed_tools=("calculator",),
            ground_truth={"type": "number", "value": 2},
        )
        messages = append_tool_exchange(
            build_initial_messages(task),
            raw_model_output='{"type":"tool_call"}',
            observation=Observation(call_id="call-1", ok=True, content={"value": 2}),
        )
        self.assertEqual(messages[-2].role, "assistant")
        self.assertEqual(messages[-1].role, "tool")
        self.assertIn('"call_id": "call-1"', messages[-1].content)
        self.assertIn('"value": 2', messages[-1].content)

    def test_native_calculator_grpo_prompt_requires_tool_then_typed_final(self) -> None:
        task = Task(
            task_id="calc-1",
            family_id="calc-family",
            kind=TaskKind.CALCULATOR,
            split=Split.TRAIN,
            prompt="Use the calculator to compute 2 + 3.",
            allowed_tools=("calculator",),
            ground_truth={"type": "number", "value": 5, "tolerance": 0},
        )

        messages = build_native_calculator_grpo_messages(task)

        self.assertIn("calculator exactly once", messages[0].content)
        self.assertIn('{"type":"final"', messages[0].content)
        self.assertNotIn('"value": 5', messages[0].content)


if __name__ == "__main__":
    unittest.main()
