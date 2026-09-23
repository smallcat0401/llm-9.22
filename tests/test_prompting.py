import unittest

from verifiable_posttraining.prompting import append_tool_exchange, build_initial_messages
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


if __name__ == "__main__":
    unittest.main()
