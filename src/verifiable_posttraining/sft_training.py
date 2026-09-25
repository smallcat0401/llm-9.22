"""Small, auditable QLoRA SFT runner for verified chat trajectories.

This module is Tier B: the important behavior is deliberately visible.  In
particular, labels are built from chat-template boundaries instead of trusting
``assistant_masks`` because the current Qwen3.5 template does not expose Jinja
``generation`` regions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import random
import time
import tomllib
from typing import Any, Iterable, Mapping, Sequence


IGNORE_INDEX = -100


class SFTTrainingError(ValueError):
    """Raised when training data or configuration violates an invariant."""


@dataclass(frozen=True, slots=True)
class SFTTrainingConfig:
    run_id: str
    model_id: str
    dataset_path: str
    output_dir: str
    metrics_path: str
    adapter_path: str | None = None
    seed: int = 7
    sample_count: int = 18
    max_length: int = 1024
    max_steps: int = 60
    learning_rate: float = 5e-4
    batch_size: int = 1
    gradient_accumulation_steps: int = 1
    max_grad_norm: float = 1.0
    lora_rank: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.0
    target_modules: tuple[str, ...] = (
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "in_proj_qkv",
        "in_proj_z",
        "in_proj_b",
        "in_proj_a",
        "out_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    )
    checkpoint_steps: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        positive_ints = {
            "sample_count": self.sample_count,
            "max_length": self.max_length,
            "max_steps": self.max_steps,
            "batch_size": self.batch_size,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "lora_rank": self.lora_rank,
            "lora_alpha": self.lora_alpha,
        }
        for name, value in positive_ints.items():
            if value <= 0:
                raise SFTTrainingError(f"{name} must be positive")
        if self.learning_rate <= 0:
            raise SFTTrainingError("learning_rate must be positive")
        if self.max_grad_norm <= 0:
            raise SFTTrainingError("max_grad_norm must be positive")
        if not 0 <= self.lora_dropout < 1:
            raise SFTTrainingError("lora_dropout must be in [0, 1)")
        if not self.target_modules:
            raise SFTTrainingError("target_modules must not be empty")
        if len(set(self.checkpoint_steps)) != len(self.checkpoint_steps):
            raise SFTTrainingError("checkpoint_steps must be unique")
        for step in self.checkpoint_steps:
            if step <= 0 or step >= self.max_steps:
                raise SFTTrainingError(
                    "checkpoint_steps must be positive and smaller than max_steps"
                )
            if step % self.gradient_accumulation_steps:
                raise SFTTrainingError(
                    "checkpoint_steps must align with gradient_accumulation_steps"
                )


def load_sft_training_config(path: str | Path) -> SFTTrainingConfig:
    payload = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    section = payload.get("sft")
    if not isinstance(section, Mapping):
        raise SFTTrainingError("config must contain an [sft] table")
    values = dict(section)
    if "target_modules" in values:
        values["target_modules"] = tuple(values["target_modules"])
    if "checkpoint_steps" in values:
        values["checkpoint_steps"] = tuple(values["checkpoint_steps"])
    try:
        return SFTTrainingConfig(**values)
    except TypeError as exc:
        raise SFTTrainingError(f"invalid SFT config: {exc}") from exc


def load_sft_examples(path: str | Path) -> tuple[dict[str, Any], ...]:
    examples: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        Path(path).read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SFTTrainingError(f"invalid JSON at line {line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise SFTTrainingError(f"example at line {line_number} must be an object")
        examples.append(value)
    if not examples:
        raise SFTTrainingError("SFT dataset must not be empty")
    return tuple(examples)


def select_balanced_examples(
    examples: Iterable[Mapping[str, Any]], *, limit: int, seed: int
) -> tuple[Mapping[str, Any], ...]:
    """Deterministically interleave task kinds so a smoke test is representative."""

    if limit <= 0:
        raise SFTTrainingError("limit must be positive")
    groups: dict[str, list[Mapping[str, Any]]] = {}
    for example in examples:
        metadata = example.get("metadata")
        if not isinstance(metadata, Mapping) or not isinstance(metadata.get("kind"), str):
            raise SFTTrainingError("every example must have metadata.kind")
        groups.setdefault(metadata["kind"], []).append(example)
    if not groups:
        raise SFTTrainingError("SFT example collection must not be empty")

    def stable_key(example: Mapping[str, Any]) -> str:
        example_id = str(example.get("example_id", ""))
        return hashlib.sha256(f"{seed}:{example_id}".encode()).hexdigest()

    queues = {kind: sorted(items, key=stable_key) for kind, items in groups.items()}
    target_count = min(limit, sum(len(items) for items in queues.values()))
    selected: list[Mapping[str, Any]] = []
    while len(selected) < target_count:
        made_progress = False
        for kind in sorted(queues):
            if queues[kind] and len(selected) < limit:
                selected.append(queues[kind].pop(0))
                made_progress = True
        if not made_progress:
            raise SFTTrainingError("balanced selection exhausted before its fixed target")
    return tuple(selected)


def _render_ids(
    tokenizer: Any,
    messages: Sequence[Mapping[str, Any]],
    *,
    add_generation_prompt: bool,
    tools: Sequence[Mapping[str, Any]] | None = None,
) -> list[int]:
    template_kwargs = {
        "tokenize": True,
        "add_generation_prompt": add_generation_prompt,
        "enable_thinking": False,
    }
    if tools:
        template_kwargs["tools"] = list(tools)
    encoded = tokenizer.apply_chat_template(list(messages), **template_kwargs)
    input_ids = encoded["input_ids"] if isinstance(encoded, Mapping) else encoded
    if input_ids and isinstance(input_ids[0], list):
        if len(input_ids) != 1:
            raise SFTTrainingError("chat template unexpectedly returned multiple sequences")
        input_ids = input_ids[0]
    if not isinstance(input_ids, list) or any(not isinstance(item, int) for item in input_ids):
        raise SFTTrainingError("chat template did not return a flat integer token sequence")
    return input_ids


def encode_assistant_only_example(
    tokenizer: Any,
    example: Mapping[str, Any],
    *,
    max_length: int,
) -> dict[str, list[int]]:
    """Tokenize one chat and supervise only assistant content plus its end marker.

    For each assistant message, rendering the preceding history with a generation
    prompt must be an exact prefix of the complete conversation.  This invariant
    prevents an off-by-one mask from training on system/user/tool tokens.  Long
    examples are rejected rather than silently truncating away target tokens.
    """

    raw_messages = example.get("messages")
    if isinstance(raw_messages, (str, bytes)) or not isinstance(raw_messages, Sequence):
        raise SFTTrainingError("example.messages must be an array")
    messages: list[Mapping[str, Any]] = []
    for message in raw_messages:
        if not isinstance(message, Mapping):
            raise SFTTrainingError("every message must be an object")
        if message.get("role") not in {"system", "user", "assistant", "tool"}:
            raise SFTTrainingError("message has an unsupported role")
        if not isinstance(message.get("content"), str):
            raise SFTTrainingError("message content must be a string")
        messages.append(message)  # type: ignore[arg-type]
    if not messages or not any(message["role"] == "assistant" for message in messages):
        raise SFTTrainingError("example must contain at least one assistant message")
    raw_tools = example.get("tools")
    if raw_tools is None:
        tools = None
    elif isinstance(raw_tools, (str, bytes)) or not isinstance(raw_tools, Sequence):
        raise SFTTrainingError("example.tools must be an array")
    elif not all(isinstance(tool, Mapping) for tool in raw_tools):
        raise SFTTrainingError("every tool schema must be an object")
    else:
        tools = list(raw_tools)

    input_ids = _render_ids(
        tokenizer, messages, add_generation_prompt=False, tools=tools
    )
    if len(input_ids) > max_length:
        raise SFTTrainingError(
            f"example has {len(input_ids)} tokens, exceeding max_length={max_length}"
        )
    labels = [IGNORE_INDEX] * len(input_ids)
    for index, message in enumerate(messages):
        if message["role"] != "assistant":
            continue
        start_prefix = _render_ids(
            tokenizer, messages[:index], add_generation_prompt=True, tools=tools
        )
        end_prefix = _render_ids(
            tokenizer, messages[: index + 1], add_generation_prompt=False, tools=tools
        )
        if input_ids[: len(start_prefix)] != start_prefix:
            raise SFTTrainingError("assistant start boundary is not a chat-template prefix")
        if input_ids[: len(end_prefix)] != end_prefix:
            raise SFTTrainingError("assistant end boundary is not a chat-template prefix")
        if len(end_prefix) <= len(start_prefix):
            raise SFTTrainingError("assistant message produced no supervised tokens")
        labels[len(start_prefix) : len(end_prefix)] = input_ids[
            len(start_prefix) : len(end_prefix)
        ]
    if all(label == IGNORE_INDEX for label in labels):
        raise SFTTrainingError("example has no supervised assistant tokens")
    return {
        "input_ids": input_ids,
        "attention_mask": [1] * len(input_ids),
        "labels": labels,
    }


@dataclass(frozen=True, slots=True)
class AssistantOnlyCollator:
    pad_token_id: int

    def __call__(self, features: Sequence[Mapping[str, Sequence[int]]]) -> dict[str, Any]:
        import torch

        if not features:
            raise SFTTrainingError("cannot collate an empty batch")
        width = max(len(feature["input_ids"]) for feature in features)
        input_ids, attention_masks, labels = [], [], []
        for feature in features:
            padding = width - len(feature["input_ids"])
            input_ids.append(list(feature["input_ids"]) + [self.pad_token_id] * padding)
            attention_masks.append(list(feature["attention_mask"]) + [0] * padding)
            labels.append(list(feature["labels"]) + [IGNORE_INDEX] * padding)
        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_masks, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
        }


class _EncodedDataset:
    def __init__(self, rows: Sequence[Mapping[str, Sequence[int]]]) -> None:
        self._rows = tuple(rows)

    def __len__(self) -> int:
        return len(self._rows)

    def __getitem__(self, index: int) -> Mapping[str, Sequence[int]]:
        return self._rows[index]


def _mean_loss(model: Any, loader: Any, device: Any) -> float:
    import torch

    model.eval()
    total_loss = 0.0
    batches = 0
    with torch.no_grad():
        for batch in loader:
            batch = {name: value.to(device) for name, value in batch.items()}
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                loss = model(**batch).loss
            total_loss += float(loss.detach().cpu())
            batches += 1
    if batches == 0:
        raise SFTTrainingError("loss loader produced no batches")
    return total_loss / batches


def run_qlora_sft(
    config: SFTTrainingConfig,
    *,
    cache_dir: str | None = None,
) -> dict[str, Any]:
    """Run a real local QLoRA update and save the adapter plus measured losses."""

    import torch
    from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
    from torch.utils.data import DataLoader
    from transformers import AutoModelForMultimodalLM, AutoProcessor, BitsAndBytesConfig

    if not torch.cuda.is_available():
        raise RuntimeError("QLoRA smoke test requires a CUDA GPU")
    random.seed(config.seed)
    torch.manual_seed(config.seed)
    torch.cuda.manual_seed_all(config.seed)

    processor = AutoProcessor.from_pretrained(
        config.model_id, cache_dir=cache_dir, local_files_only=True
    )
    tokenizer = processor.tokenizer
    raw_examples = load_sft_examples(config.dataset_path)
    selected = select_balanced_examples(
        raw_examples, limit=config.sample_count, seed=config.seed
    )
    encoded = tuple(
        encode_assistant_only_example(tokenizer, example, max_length=config.max_length)
        for example in selected
    )
    pad_token_id = tokenizer.pad_token_id
    if pad_token_id is None:
        pad_token_id = tokenizer.eos_token_id
    if pad_token_id is None:
        raise SFTTrainingError("tokenizer must define pad_token_id or eos_token_id")
    collator = AssistantOnlyCollator(pad_token_id=pad_token_id)
    dataset = _EncodedDataset(encoded)
    eval_loader = DataLoader(dataset, batch_size=config.batch_size, collate_fn=collator)
    generator = torch.Generator().manual_seed(config.seed)
    train_loader = DataLoader(
        dataset,
        batch_size=config.batch_size,
        shuffle=True,
        generator=generator,
        collate_fn=collator,
    )

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForMultimodalLM.from_pretrained(
        config.model_id,
        cache_dir=cache_dir,
        local_files_only=True,
        quantization_config=quantization_config,
        device_map={"": 0},
        low_cpu_mem_usage=True,
    )
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    if config.adapter_path:
        model = PeftModel.from_pretrained(
            model,
            config.adapter_path,
            is_trainable=True,
            local_files_only=True,
        )
    else:
        model = get_peft_model(
            model,
            LoraConfig(
                r=config.lora_rank,
                lora_alpha=config.lora_alpha,
                lora_dropout=config.lora_dropout,
                bias="none",
                task_type="CAUSAL_LM",
                target_modules=list(config.target_modules),
            ),
        )
    trainable_parameters = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_parameters = sum(p.numel() for p in model.parameters())
    if trainable_parameters == 0:
        raise RuntimeError("LoRA injection produced zero trainable parameters")

    device = torch.device("cuda:0")
    optimizer = torch.optim.AdamW(
        (parameter for parameter in model.parameters() if parameter.requires_grad),
        lr=config.learning_rate,
    )
    torch.cuda.reset_peak_memory_stats(device)
    started = time.perf_counter()
    initial_loss = _mean_loss(model, eval_loader, device)
    model.train()
    optimizer.zero_grad(set_to_none=True)
    losses: list[float] = []
    saved_checkpoints: dict[str, str] = {}
    iterator = iter(train_loader)
    for step in range(1, config.max_steps + 1):
        try:
            batch = next(iterator)
        except StopIteration:
            iterator = iter(train_loader)
            batch = next(iterator)
        batch = {name: value.to(device) for name, value in batch.items()}
        with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
            loss = model(**batch).loss / config.gradient_accumulation_steps
        if not torch.isfinite(loss):
            raise RuntimeError(f"non-finite loss at step {step}")
        loss.backward()
        losses.append(float(loss.detach().cpu()) * config.gradient_accumulation_steps)
        if step % config.gradient_accumulation_steps == 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm)
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)
            if step in config.checkpoint_steps:
                checkpoint_dir = Path(config.output_dir).parent / f"adapter-step-{step}"
                checkpoint_dir.mkdir(parents=True, exist_ok=True)
                model.save_pretrained(checkpoint_dir)
                tokenizer.save_pretrained(checkpoint_dir)
                saved_checkpoints[str(step)] = str(checkpoint_dir)
        if step == 1 or step % 10 == 0 or step == config.max_steps:
            recent = losses[-min(10, len(losses)) :]
            print(f"step={step} mean_recent_loss={sum(recent) / len(recent):.6f}", flush=True)
    if config.max_steps % config.gradient_accumulation_steps:
        torch.nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm)
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)

    final_loss = _mean_loss(model, eval_loader, device)
    elapsed = time.perf_counter() - started
    peak_memory_mib = torch.cuda.max_memory_allocated(device) / (1024**2)
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    metrics = {
        "run_id": config.run_id,
        "status": "completed",
        "model_id": config.model_id,
        "training_method": "QLoRA NF4",
        "dataset_path": config.dataset_path,
        "starting_adapter": config.adapter_path,
        "selected_example_ids": [example.get("example_id") for example in selected],
        "selected_by_kind": {
            kind: sum(example["metadata"]["kind"] == kind for example in selected)
            for kind in sorted({example["metadata"]["kind"] for example in selected})
        },
        "sequence_lengths": [len(row["input_ids"]) for row in encoded],
        "supervised_tokens": [
            sum(label != IGNORE_INDEX for label in row["labels"]) for row in encoded
        ],
        "initial_loss": initial_loss,
        "final_loss": final_loss,
        "loss_reduction": initial_loss - final_loss,
        "loss_reduction_fraction": (
            (initial_loss - final_loss) / initial_loss if initial_loss else math.nan
        ),
        "step_losses": losses,
        "saved_checkpoints": saved_checkpoints,
        "trainable_parameters": trainable_parameters,
        "total_parameters": total_parameters,
        "peak_cuda_memory_mib": peak_memory_mib,
        "elapsed_seconds": elapsed,
        "config": asdict(config),
    }
    metrics_path = Path(config.metrics_path)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metrics


def run_qlora_overfit_smoke(
    config: SFTTrainingConfig,
    *,
    cache_dir: str | None = None,
) -> dict[str, Any]:
    """Backward-compatible name for the gated tiny-overfit entry point."""

    return run_qlora_sft(config, cache_dir=cache_dir)
