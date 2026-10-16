"""Minimal 0.8B GRPO smoke run with verifiable numeric rewards."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import time
import tomllib
from typing import Any, Mapping

from .dataset import load_tasks_jsonl
from .prompting import build_initial_messages, build_native_calculator_grpo_messages
from .reward import (
    calculator_result_rewards,
    calculator_trace_rewards,
    numeric_closeness_rewards,
    numeric_outcome_rewards,
    tool_numeric_closeness_rewards,
    tool_numeric_outcome_rewards,
    tool_typed_final_rewards,
    typed_final_rewards,
)
from .schemas import Split, TaskKind
from .sft_training import load_sft_examples


@dataclass(frozen=True, slots=True)
class GRPOSmokeConfig:
    run_id: str
    model_id: str
    adapter_path: str
    dataset_path: str
    sft_dataset_path: str
    output_dir: str
    metrics_path: str
    expected_dataset_sha256: str = ""
    expected_sft_dataset_sha256: str = ""
    expected_dataset_task_count: int = 0
    expected_sft_overlap_count: int | None = None
    allow_sft_task_overlap: bool = False
    seed: int = 7
    prompt_count: int = 8
    max_steps: int = 2
    num_generations: int = 4
    max_completion_length: int = 96
    learning_rate: float = 1e-5
    temperature: float = 1.0
    top_p: float = 0.95
    format_reward_weight: float = 0.1
    closeness_reward_weight: float = 0.0
    tool_trace_reward_weight: float = 0.0
    tool_result_reward_weight: float = 0.0
    task_kind: str = "no_tool"
    enable_calculator_tool: bool = False
    log_completions: bool = False
    num_completions_to_print: int = 4
    task_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "prompt_count",
            "max_steps",
            "num_generations",
            "max_completion_length",
            "num_completions_to_print",
        ):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        if self.learning_rate <= 0 or self.temperature <= 0:
            raise ValueError("learning_rate and temperature must be positive")
        if not 0 < self.top_p <= 1:
            raise ValueError("top_p must be in (0, 1]")
        if self.format_reward_weight < 0:
            raise ValueError("format_reward_weight must be non-negative")
        if self.closeness_reward_weight < 0:
            raise ValueError("closeness_reward_weight must be non-negative")
        if self.tool_trace_reward_weight < 0:
            raise ValueError("tool_trace_reward_weight must be non-negative")
        if self.tool_result_reward_weight < 0:
            raise ValueError("tool_result_reward_weight must be non-negative")
        if self.task_kind not in {"no_tool", "calculator"}:
            raise ValueError("task_kind must be 'no_tool' or 'calculator'")
        if self.enable_calculator_tool != (self.task_kind == "calculator"):
            raise ValueError("enable_calculator_tool must be true exactly for calculator tasks")
        if len(set(self.task_ids)) != len(self.task_ids):
            raise ValueError("task_ids must be unique")
        if self.task_ids and len(self.task_ids) != self.prompt_count:
            raise ValueError("task_ids length must equal prompt_count")
        if self.expected_dataset_task_count < 0:
            raise ValueError("expected_dataset_task_count must be non-negative")
        if self.expected_sft_overlap_count is not None and self.expected_sft_overlap_count < 0:
            raise ValueError("expected_sft_overlap_count must be non-negative")
        for name in ("expected_dataset_sha256", "expected_sft_dataset_sha256"):
            value = getattr(self, name)
            if value and (len(value) != 64 or any(character not in "0123456789abcdef" for character in value)):
                raise ValueError(f"{name} must be a lowercase SHA-256 hex digest")
        if self.allow_sft_task_overlap and not self.expected_dataset_sha256:
            raise ValueError("allow_sft_task_overlap requires a frozen dataset hash")


def load_grpo_smoke_config(path: str | Path) -> GRPOSmokeConfig:
    payload = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    section = payload.get("grpo")
    if not isinstance(section, Mapping):
        raise ValueError("config must contain a [grpo] table")
    values = dict(section)
    if "task_ids" in values:
        values["task_ids"] = tuple(values["task_ids"])
    return GRPOSmokeConfig(**values)


def _stable_key(seed: int, task_id: str) -> str:
    return hashlib.sha256(f"{seed}:{task_id}".encode()).hexdigest()


def _sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_grpo_smoke_rows(config: GRPOSmokeConfig) -> tuple[dict[str, Any], ...]:
    """Build the configured train prompt set under explicit SFT-overlap rules.

    The default preserves the historical held-out-prompt behavior.  Formal
    outcome-variance GRPO may opt into SFT prompt overlap only when the input
    dataset is pinned by SHA-256; this is recorded as replay-on-train, not new
    data or an independent generalization test.
    """

    if config.expected_dataset_sha256:
        actual = _sha256(config.dataset_path)
        if actual != config.expected_dataset_sha256:
            raise ValueError(
                f"GRPO dataset hash mismatch: {actual} != {config.expected_dataset_sha256}"
            )
    if config.expected_sft_dataset_sha256:
        actual = _sha256(config.sft_dataset_path)
        if actual != config.expected_sft_dataset_sha256:
            raise ValueError(
                "SFT dataset hash mismatch: "
                f"{actual} != {config.expected_sft_dataset_sha256}"
            )

    sft_task_ids = {
        str(example["metadata"]["task_id"])
        for example in load_sft_examples(config.sft_dataset_path)
    }
    dataset_tasks = load_tasks_jsonl(config.dataset_path)
    if (
        config.expected_dataset_task_count
        and len(dataset_tasks) != config.expected_dataset_task_count
    ):
        raise ValueError(
            "unexpected GRPO dataset task count: "
            f"{len(dataset_tasks)} != {config.expected_dataset_task_count}"
        )
    eligible = [
        task
        for task in dataset_tasks
        if task.split is Split.TRAIN
        and task.kind is TaskKind(config.task_kind)
    ]
    overlap_ids = {task.task_id for task in eligible} & sft_task_ids
    if (
        config.expected_sft_overlap_count is not None
        and len(overlap_ids) != config.expected_sft_overlap_count
    ):
        raise ValueError(
            "unexpected GRPO/SFT task overlap: "
            f"{len(overlap_ids)} != {config.expected_sft_overlap_count}"
        )
    candidates = (
        eligible
        if config.allow_sft_task_overlap
        else [task for task in eligible if task.task_id not in sft_task_ids]
    )
    by_id = {task.task_id: task for task in candidates}
    if config.task_ids:
        missing = [task_id for task_id in config.task_ids if task_id not in by_id]
        if missing:
            raise ValueError(
                "configured task_ids are unavailable, wrong-kind/non-train, or disallowed by "
                "the SFT-overlap policy (for example, already in SFT): "
                + ", ".join(missing)
            )
        selected = [by_id[task_id] for task_id in config.task_ids]
    else:
        candidates.sort(key=lambda task: _stable_key(config.seed, task.task_id))
        selected = candidates[: config.prompt_count]
    if len(selected) < config.prompt_count:
        raise ValueError("not enough eligible train tasks for configured GRPO prompt count")
    return tuple(
        {
            "prompt": [
                message.to_dict()
                for message in (
                    build_native_calculator_grpo_messages(task)
                    if config.enable_calculator_tool
                    else build_initial_messages(task)
                )
            ],
            "ground_truth": dict(task.ground_truth),
            "task_id": task.task_id,
        }
        for task in selected
    )


def _trainable_snapshot(model: Any) -> dict[str, Any]:
    return {
        name: parameter.detach().float().cpu().clone()
        for name, parameter in model.named_parameters()
        if parameter.requires_grad
    }


def run_grpo_smoke(
    config: GRPOSmokeConfig, *, cache_dir: str | None = None
) -> dict[str, Any]:
    import torch
    from datasets import Dataset
    from peft import PeftModel, prepare_model_for_kbit_training
    from transformers import AutoModelForMultimodalLM, AutoProcessor, BitsAndBytesConfig
    from trl import GRPOConfig, GRPOTrainer

    from .tools.calculator import calculator

    if not torch.cuda.is_available():
        raise RuntimeError("GRPO smoke test requires a CUDA GPU")
    torch.manual_seed(config.seed)
    torch.cuda.manual_seed_all(config.seed)
    rows = build_grpo_smoke_rows(config)
    dataset = Dataset.from_list(list(rows))
    processor = AutoProcessor.from_pretrained(
        config.model_id, cache_dir=cache_dir, local_files_only=True
    )
    processor.tokenizer.padding_side = "left"
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForMultimodalLM.from_pretrained(
        config.model_id,
        cache_dir=cache_dir,
        local_files_only=True,
        quantization_config=quantization,
        device_map={"": 0},
        low_cpu_mem_usage=True,
    )
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    model = PeftModel.from_pretrained(
        model,
        config.adapter_path,
        is_trainable=True,
        local_files_only=True,
    )
    before = _trainable_snapshot(model)
    trainable_parameters = sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
    if trainable_parameters == 0:
        raise RuntimeError("GRPO model has zero trainable parameters")

    training_args = GRPOConfig(
        output_dir=str(Path(config.output_dir).parent / "trainer_state"),
        max_steps=config.max_steps,
        per_device_train_batch_size=config.num_generations,
        gradient_accumulation_steps=1,
        learning_rate=config.learning_rate,
        max_grad_norm=1.0,
        bf16=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        save_strategy="no",
        logging_steps=1,
        logging_first_step=True,
        report_to="none",
        seed=config.seed,
        data_seed=config.seed,
        num_generations=config.num_generations,
        generation_batch_size=config.num_generations,
        max_completion_length=config.max_completion_length,
        temperature=config.temperature,
        top_p=config.top_p,
        beta=0.0,
        loss_type="grpo",
        scale_rewards="group",
        mask_truncated_completions=True,
        chat_template_kwargs={"enable_thinking": False},
        max_tool_calling_iterations=1 if config.enable_calculator_tool else None,
        log_completions=config.log_completions,
        num_completions_to_print=config.num_completions_to_print,
    )
    if config.enable_calculator_tool:
        reward_funcs = [
            tool_numeric_outcome_rewards,
            tool_numeric_closeness_rewards,
            tool_typed_final_rewards,
            calculator_trace_rewards,
            calculator_result_rewards,
        ]
        reward_weights = [
            1.0,
            config.closeness_reward_weight,
            config.format_reward_weight,
            config.tool_trace_reward_weight,
            config.tool_result_reward_weight,
        ]
        tools = [calculator]
    else:
        reward_funcs = [numeric_outcome_rewards, numeric_closeness_rewards, typed_final_rewards]
        reward_weights = [1.0, config.closeness_reward_weight, config.format_reward_weight]
        tools = None
    trainer = GRPOTrainer(
        model=model,
        reward_funcs=reward_funcs,
        args=training_args,
        train_dataset=dataset,
        processing_class=processor,
        tools=tools,
    )
    trainer.reward_weights = torch.tensor(reward_weights, dtype=torch.float32)
    torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    train_result = trainer.train()
    elapsed = time.perf_counter() - started

    changed_tensors = 0
    max_parameter_delta = 0.0
    for name, parameter in model.named_parameters():
        if name not in before:
            continue
        delta = float((parameter.detach().float().cpu() - before[name]).abs().max())
        if delta > 0:
            changed_tensors += 1
            max_parameter_delta = max(max_parameter_delta, delta)
    if changed_tensors == 0:
        raise RuntimeError("GRPO completed without changing any trainable parameter")

    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_dir)
    processor.tokenizer.save_pretrained(output_dir)
    selected_task_ids = [row["task_id"] for row in rows]
    sft_task_ids = {
        str(example["metadata"]["task_id"])
        for example in load_sft_examples(config.sft_dataset_path)
    }
    log_history = trainer.state.log_history
    reward_std_entries = [entry for entry in log_history if "reward_std" in entry]
    metrics = {
        "run_id": config.run_id,
        "status": "completed",
        "model_id": config.model_id,
        "starting_adapter": config.adapter_path,
        "selected_task_ids": selected_task_ids,
        "selected_sft_overlap_task_ids": [
            task_id for task_id in selected_task_ids if task_id in sft_task_ids
        ],
        "dataset_sha256": _sha256(config.dataset_path),
        "sft_dataset_sha256": _sha256(config.sft_dataset_path),
        "trainable_parameters": trainable_parameters,
        "changed_trainable_tensors": changed_tensors,
        "max_parameter_delta": max_parameter_delta,
        "peak_cuda_memory_mib": torch.cuda.max_memory_allocated() / (1024**2),
        "elapsed_seconds": elapsed,
        "train_metrics": dict(train_result.metrics),
        "log_history": log_history,
        "observed_reward_variance_steps": len(reward_std_entries),
        "nonzero_reward_variance_steps": sum(
            float(entry["reward_std"]) > 0 for entry in reward_std_entries
        ),
        "zero_reward_variance_steps": sum(
            float(entry["reward_std"]) == 0 for entry in reward_std_entries
        ),
        "reward_weights": {
            "numeric_outcome": 1.0,
            "numeric_closeness": config.closeness_reward_weight,
            "typed_final": config.format_reward_weight,
            "calculator_trace": config.tool_trace_reward_weight,
            "calculator_result": config.tool_result_reward_weight,
        },
        "config": asdict(config),
    }
    metrics_path = Path(config.metrics_path)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metrics
