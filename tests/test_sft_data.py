import unittest
from collections.abc import Sequence
from copy import deepcopy

from verifiable_posttraining.evaluation import rollout_record
from verifiable_posttraining.prompting import ChatMessage
from verifiable_posttraining.rollout import run_episode
from verifiable_posttraining.schemas import Split, Task, TaskKind
from verifiable_posttraining.sft_data import (
    SFTDataError,
    build_sft_dataset,
    build_sft_example,
    is_path_aligned_sft_record,
    merge_sft_examples,
    select_path_aligned_sft_records,
)
from verifiable_posttraining.tools import execute_calculator


class ScriptedPolicy:
    def __init__(self, outputs: list[str]) -> None:
        self._outputs = iter(outputs)

    def generate(self, messages: Sequence[ChatMessage], *, seed: int) -> str:
        del messages, seed
        return next(self._outputs)


def _verified_record(*, split: Split = Split.TRAIN):
    task = Task(
        task_id="calculator-001",
        family_id="calculator-family",
        kind=TaskKind.CALCULATOR,
        split=split,
        prompt="Use the calculator to compute 1 + 1.",
        allowed_tools=("calculator",),
        ground_truth={"type": "number", "value": 2, "tolerance": 0},
    )
    rollout = run_episode(
        task,
        ScriptedPolicy(
            [
                '{"type":"tool_call","name":"calculator",'
                '"arguments":{"expression":"1 + 1"}}',
                '{"type":"final","answer":2}',
            ]
        ),
        {"calculator": execute_calculator},
        trajectory_id="trajectory-001",
        model_id="scripted",
        seed=7,
    )
    return rollout_record(rollout, latency_seconds=0.1)


def _verified_direct_calculator_record():
    task = Task(
        task_id="calculator-001",
        family_id="calculator-family",
        kind=TaskKind.CALCULATOR,
        split=Split.TRAIN,
        prompt="Use the calculator to compute 1 + 1.",
        allowed_tools=("calculator",),
        ground_truth={"type": "number", "value": 2, "tolerance": 0},
    )
    rollout = run_episode(
        task,
        ScriptedPolicy(['{"type":"final","answer":2}']),
        {"calculator": execute_calculator},
        trajectory_id="trajectory-direct",
        model_id="scripted",
        seed=7,
    )
    return rollout_record(rollout, latency_seconds=0.1)


class SFTDataTests(unittest.TestCase):
    def test_merge_sft_examples_preserves_source_and_rejects_duplicates(self) -> None:
        first = {
            "example_id": "first",
            "messages": [],
            "metadata": {"kind": "calculator", "family_id": "family-a"},
        }
        second = {
            "example_id": "second",
            "messages": [],
            "metadata": {"kind": "calculator", "family_id": "family-b"},
        }
        merged = merge_sft_examples((("native37", (first,)), ("curriculum", (second,))))
        self.assertEqual([row["metadata"]["mixture_source"] for row in merged], ["native37", "curriculum"])
        with self.assertRaisesRegex(SFTDataError, "duplicate SFT example_id"):
            merge_sft_examples((("a", (first,)), ("b", (first,))))

    def test_verified_tool_trajectory_becomes_multiturn_messages(self) -> None:
        example = build_sft_example(_verified_record())

        self.assertEqual(
            [message["role"] for message in example["messages"]],
            ["system", "user", "assistant", "tool", "assistant"],
        )
        self.assertEqual(example["metadata"]["split"], "train")
        self.assertEqual(example["metadata"]["source_trajectory_id"], "trajectory-001")

    def test_non_train_or_unsuccessful_sources_are_rejected(self) -> None:
        with self.assertRaisesRegex(SFTDataError, "train split"):
            build_sft_example(_verified_record(split=Split.VALIDATION))

        failed = deepcopy(_verified_record())
        failed["rollout"]["task_success"] = False
        with self.assertRaisesRegex(SFTDataError, "strict verified success"):
            build_sft_example(failed)

    def test_tampered_raw_tool_call_is_rejected(self) -> None:
        tampered = deepcopy(_verified_record())
        tampered["raw_outputs"][0] = (
            '{"type":"tool_call","name":"calculator",'
            '"arguments":{"expression":"2 + 2"}}'
        )
        with self.assertRaisesRegex(SFTDataError, "does not match"):
            build_sft_example(tampered)

    def test_duplicate_tasks_are_rejected(self) -> None:
        record = _verified_record()
        with self.assertRaisesRegex(SFTDataError, "duplicate SFT example_id"):
            build_sft_dataset([record, record])

    def test_curation_prefers_aligned_tool_success_over_direct_success(self) -> None:
        direct = _verified_direct_calculator_record()
        tool_aligned = _verified_record()

        self.assertFalse(is_path_aligned_sft_record(direct))
        self.assertTrue(is_path_aligned_sft_record(tool_aligned))
        selected = select_path_aligned_sft_records([direct, tool_aligned])
        self.assertEqual(len(selected), 1)
        self.assertEqual(
            selected[0]["trajectory"]["trajectory_id"],
            "trajectory-001",
        )


if __name__ == "__main__":
    unittest.main()
