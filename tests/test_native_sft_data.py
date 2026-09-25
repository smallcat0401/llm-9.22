import copy
import json
import unittest

from verifiable_posttraining.native_sft_data import (
    NativeSFTDataError,
    build_native_calculator_sft_dataset,
    build_native_calculator_sft_example,
)
from verifiable_posttraining.schemas import Split, Task, TaskKind


def _task(split=Split.TRAIN):
    return Task(
        task_id="calculator-average-v1-001",
        family_id="calculator-average-v1",
        kind=TaskKind.CALCULATOR,
        split=split,
        prompt="Use the calculator: find the mean of 12, 24, and 36.",
        allowed_tools=("calculator",),
        ground_truth={"type": "number", "value": 24, "tolerance": 0},
    )


def _source():
    return {
        "example_id": "sft-calculator-average-v1-001",
        "messages": [
            {"role": "system", "content": "custom protocol"},
            {"role": "user", "content": "question"},
            {
                "role": "assistant",
                "content": '{"type":"tool_call","name":"calculator","arguments":{"expression":"(12+24+36)/3"}}',
            },
            {
                "role": "tool",
                "content": json.dumps({
                    "call_id": "call-1", "ok": True,
                    "content": {"value": 24}, "error_code": None,
                }),
            },
            {"role": "assistant", "content": '{"type":"final","answer":"24"}'},
        ],
        "metadata": {
            "task_id": "calculator-average-v1-001",
            "family_id": "calculator-average-v1",
            "kind": "calculator",
            "split": "train",
        },
    }


class NativeSFTDataTests(unittest.TestCase):
    def test_verified_source_becomes_native_tool_exchange(self):
        row = build_native_calculator_sft_example(_source(), _task())

        self.assertEqual(row["metadata"]["format"], "transformers-native-calculator-v1")
        self.assertEqual(row["messages"][2]["tool_calls"][0]["function"]["name"], "calculator")
        self.assertEqual(row["messages"][3]["content"], "24")
        self.assertEqual(row["messages"][4]["content"], '{"type":"final","answer":"24"}')
        self.assertEqual(row["tools"][0]["function"]["name"], "calculator")

    def test_replay_rejects_tampered_observation(self):
        source = copy.deepcopy(_source())
        source["messages"][3]["content"] = json.dumps({
            "call_id": "call-1", "ok": True,
            "content": {"value": 25}, "error_code": None,
        })
        with self.assertRaisesRegex(NativeSFTDataError, "does not match"):
            build_native_calculator_sft_example(source, _task())

    def test_replay_rejects_unsafe_expression(self):
        source = copy.deepcopy(_source())
        source["messages"][2]["content"] = (
            '{"type":"tool_call","name":"calculator",'
            '"arguments":{"expression":"__import__(\\"os\\")"}}'
        )
        with self.assertRaisesRegex(NativeSFTDataError, "replay failed"):
            build_native_calculator_sft_example(source, _task())

    def test_test_split_cannot_enter_training_data(self):
        with self.assertRaisesRegex(NativeSFTDataError, "train calculator"):
            build_native_calculator_sft_example(_source(), _task(Split.TEST))

    def test_dataset_filters_non_calculator_sources(self):
        other = copy.deepcopy(_source())
        other["metadata"]["kind"] = "sql"
        rows = build_native_calculator_sft_dataset((_source(), other), (_task(),))
        self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
