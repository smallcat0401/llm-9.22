import unittest

from verifiable_posttraining.sft_training import (
    IGNORE_INDEX,
    AssistantOnlyCollator,
    SFTTrainingConfig,
    SFTTrainingError,
    encode_assistant_only_example,
    select_balanced_examples,
)


class FakeTokenizer:
    role_tokens = {"system": 10, "user": 20, "assistant": 30, "tool": 40}

    def apply_chat_template(
        self,
        messages,
        *,
        tokenize,
        add_generation_prompt,
        enable_thinking,
        tools=None,
    ):
        assert tokenize is True
        assert enable_thinking is False
        ids = []
        for message in messages:
            ids.extend(
                [self.role_tokens[message["role"]], *map(ord, message["content"]), 99]
            )
        if add_generation_prompt:
            ids.append(self.role_tokens["assistant"])
        return {"input_ids": ids, "attention_mask": [1] * len(ids)}


def _example(kind="calculator", example_id="example-1"):
    return {
        "example_id": example_id,
        "messages": [
            {"role": "system", "content": "S"},
            {"role": "user", "content": "U"},
            {"role": "assistant", "content": "CALL"},
            {"role": "tool", "content": "OBS"},
            {"role": "assistant", "content": "FINAL"},
        ],
        "metadata": {"kind": kind},
    }


class SFTTrainingTests(unittest.TestCase):
    def test_checkpoint_steps_must_align_with_optimizer_updates(self) -> None:
        common = {
            "run_id": "test", "model_id": "model", "dataset_path": "data.jsonl",
            "output_dir": "output", "metrics_path": "metrics.json",
            "max_steps": 8, "gradient_accumulation_steps": 4,
        }
        config = SFTTrainingConfig(**common, checkpoint_steps=(4,))
        self.assertEqual(config.checkpoint_steps, (4,))
        with self.assertRaisesRegex(SFTTrainingError, "align"):
            SFTTrainingConfig(**common, checkpoint_steps=(3,))

    def test_only_assistant_content_and_end_markers_are_supervised(self) -> None:
        row = encode_assistant_only_example(FakeTokenizer(), _example(), max_length=100)
        supervised = [
            token for token, label in zip(row["input_ids"], row["labels"]) if label != IGNORE_INDEX
        ]

        self.assertEqual(supervised, [*map(ord, "CALL"), 99, *map(ord, "FINAL"), 99])
        for token, label in zip(row["input_ids"], row["labels"]):
            if token in {10, 20, 30, 40}:
                self.assertEqual(label, IGNORE_INDEX)

    def test_long_example_is_rejected_instead_of_silent_truncation(self) -> None:
        with self.assertRaisesRegex(SFTTrainingError, "exceeding max_length"):
            encode_assistant_only_example(FakeTokenizer(), _example(), max_length=5)

    def test_native_tool_schema_is_accepted(self) -> None:
        example = _example()
        example["tools"] = [{"type": "function", "function": {"name": "calculator"}}]
        example["messages"][2] = {
            "role": "assistant",
            "content": "",
            "tool_calls": [{"type": "function", "function": {"name": "calculator"}}],
        }

        row = encode_assistant_only_example(FakeTokenizer(), example, max_length=100)

        self.assertTrue(any(label != IGNORE_INDEX for label in row["labels"]))

    def test_balanced_selection_interleaves_kinds_deterministically(self) -> None:
        examples = [
            _example(kind=kind, example_id=f"{kind}-{index}")
            for kind in ("no_tool", "calculator", "sql")
            for index in range(4)
        ]
        first = select_balanced_examples(examples, limit=6, seed=7)
        second = select_balanced_examples(examples, limit=6, seed=7)

        self.assertEqual(
            [item["example_id"] for item in first],
            [item["example_id"] for item in second],
        )
        self.assertEqual(
            {kind: sum(item["metadata"]["kind"] == kind for item in first) for kind in ("no_tool", "calculator", "sql")},
            {"no_tool": 2, "calculator": 2, "sql": 2},
        )

    def test_balanced_selection_can_select_the_entire_dataset(self) -> None:
        examples = [
            _example(kind=kind, example_id=f"{kind}-{index}")
            for kind in ("no_tool", "calculator", "sql")
            for index in range(4)
        ]

        selected = select_balanced_examples(examples, limit=12, seed=7)

        self.assertEqual(len(selected), 12)
        self.assertEqual({item["example_id"] for item in selected}, {
            item["example_id"] for item in examples
        })

    def test_collator_uses_ignore_index_for_label_padding(self) -> None:
        collator = AssistantOnlyCollator(pad_token_id=0)
        batch = collator(
            [
                {"input_ids": [1, 2], "attention_mask": [1, 1], "labels": [-100, 2]},
                {"input_ids": [3], "attention_mask": [1], "labels": [3]},
            ]
        )

        self.assertEqual(batch["input_ids"].tolist(), [[1, 2], [3, 0]])
        self.assertEqual(batch["attention_mask"].tolist(), [[1, 1], [1, 0]])
        self.assertEqual(batch["labels"].tolist(), [[-100, 2], [3, -100]])


if __name__ == "__main__":
    unittest.main()
