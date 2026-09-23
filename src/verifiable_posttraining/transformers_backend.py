"""Transformers generation backend for the Qwen starting policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from .prompting import ChatMessage


@dataclass(frozen=True, slots=True)
class GenerationSettings:
    max_new_tokens: int = 256
    do_sample: bool = False
    temperature: float = 1.0
    top_p: float = 1.0
    top_k: int = 20

    def __post_init__(self) -> None:
        if self.max_new_tokens <= 0:
            raise ValueError("max_new_tokens must be positive")
        if self.temperature <= 0:
            raise ValueError("temperature must be positive")
        if not 0 < self.top_p <= 1:
            raise ValueError("top_p must be in (0, 1]")
        if self.top_k < 0:
            raise ValueError("top_k must be non-negative")


class TransformersPolicy:
    """Generate one action from a local Transformers model.

    Model loading is explicit and separate from construction so unit tests do
    not need model weights.  ``local_files_only=True`` is used by the smoke CLI
    to ensure running a test never starts an unannounced download.
    """

    def __init__(
        self,
        processor: Any,
        model: Any,
        *,
        settings: GenerationSettings | None = None,
    ) -> None:
        self.processor = processor
        self.model = model
        self.settings = settings or GenerationSettings()

    @classmethod
    def from_pretrained(
        cls,
        model_id: str,
        *,
        cache_dir: str | None = None,
        local_files_only: bool = True,
        settings: GenerationSettings | None = None,
    ) -> "TransformersPolicy":
        from transformers import AutoModelForMultimodalLM, AutoProcessor

        processor = AutoProcessor.from_pretrained(
            model_id,
            cache_dir=cache_dir,
            local_files_only=local_files_only,
        )
        model = AutoModelForMultimodalLM.from_pretrained(
            model_id,
            cache_dir=cache_dir,
            local_files_only=local_files_only,
            device_map="auto",
            dtype="auto",
            low_cpu_mem_usage=True,
        )
        model.eval()
        return cls(processor, model, settings=settings)

    def generate(self, messages: Sequence[ChatMessage], *, seed: int) -> str:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

        chat_messages = [message.to_dict() for message in messages]
        inputs = self.processor.apply_chat_template(
            chat_messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
            enable_thinking=False,
        )
        model_device = self._model_device()
        inputs = {
            name: value.to(model_device) if hasattr(value, "to") else value
            for name, value in inputs.items()
        }
        input_length = inputs["input_ids"].shape[-1]

        generation_kwargs: dict[str, Any] = {
            "max_new_tokens": self.settings.max_new_tokens,
            "do_sample": self.settings.do_sample,
        }
        if self.settings.do_sample:
            generation_kwargs.update(
                temperature=self.settings.temperature,
                top_p=self.settings.top_p,
                top_k=self.settings.top_k,
            )

        with torch.inference_mode():
            generated = self.model.generate(**inputs, **generation_kwargs)
        new_tokens = generated[0, input_length:]
        return self.processor.decode(new_tokens, skip_special_tokens=True).strip()

    def _model_device(self) -> Any:
        if hasattr(self.model, "device"):
            return self.model.device
        return next(self.model.parameters()).device
