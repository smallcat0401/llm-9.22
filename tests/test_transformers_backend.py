import unittest
from unittest.mock import MagicMock, patch

import torch

from verifiable_posttraining.prompting import ChatMessage
from verifiable_posttraining.transformers_backend import (
    GenerationSettings,
    TransformersPolicy,
)


class FakeProcessor:
    def __init__(self) -> None:
        self.messages = None
        self.decoded_tokens = None

    def apply_chat_template(self, messages, **kwargs):
        self.messages = messages
        self.template_kwargs = kwargs
        return {"input_ids": torch.tensor([[10, 11]])}

    def decode(self, tokens, *, skip_special_tokens):
        self.decoded_tokens = tokens.tolist()
        self.skip_special_tokens = skip_special_tokens
        return '  {"type":"final","answer":"2"}  '


class FakeModel:
    device = torch.device("cpu")

    def __init__(self) -> None:
        self.generate_kwargs = None

    def generate(self, **kwargs):
        self.generate_kwargs = kwargs
        return torch.tensor([[10, 11, 12, 13]])


class TransformersBackendTests(unittest.TestCase):
    def test_generation_decodes_only_new_tokens(self) -> None:
        processor = FakeProcessor()
        model = FakeModel()
        policy = TransformersPolicy(processor, model)
        output = policy.generate(
            [ChatMessage(role="user", content="Compute one plus one")],
            seed=7,
        )
        self.assertEqual(output, '{"type":"final","answer":"2"}')
        self.assertEqual(processor.decoded_tokens, [12, 13])
        self.assertFalse(model.generate_kwargs["do_sample"])
        self.assertNotIn("temperature", model.generate_kwargs)

    def test_sampling_settings_are_forwarded(self) -> None:
        model = FakeModel()
        policy = TransformersPolicy(
            FakeProcessor(),
            model,
            settings=GenerationSettings(
                do_sample=True,
                temperature=0.8,
                top_p=0.9,
                top_k=10,
            ),
        )
        policy.generate([ChatMessage(role="user", content="Answer")], seed=7)
        self.assertEqual(model.generate_kwargs["temperature"], 0.8)
        self.assertEqual(model.generate_kwargs["top_p"], 0.9)
        self.assertEqual(model.generate_kwargs["top_k"], 10)

    def test_invalid_settings_fail_fast(self) -> None:
        with self.assertRaisesRegex(ValueError, "max_new_tokens"):
            GenerationSettings(max_new_tokens=0)

    def test_four_bit_loading_uses_nf4_double_quantization(self) -> None:
        fake_model = MagicMock()
        with (
            patch("transformers.AutoProcessor.from_pretrained") as processor_loader,
            patch("transformers.AutoModelForMultimodalLM.from_pretrained") as model_loader,
            patch("transformers.BitsAndBytesConfig") as quantization_config,
        ):
            processor_loader.return_value = MagicMock()
            model_loader.return_value = fake_model
            policy = TransformersPolicy.from_pretrained(
                "Qwen/Qwen3.5-4B",
                cache_dir="cache",
                load_in_4bit=True,
            )

        self.assertIs(policy.model, fake_model)
        quantization_config.assert_called_once()
        config_kwargs = quantization_config.call_args.kwargs
        self.assertTrue(config_kwargs["load_in_4bit"])
        self.assertEqual(config_kwargs["bnb_4bit_quant_type"], "nf4")
        self.assertTrue(config_kwargs["bnb_4bit_use_double_quant"])
        self.assertIs(
            model_loader.call_args.kwargs["quantization_config"],
            quantization_config.return_value,
        )


if __name__ == "__main__":
    unittest.main()
