"""Local-only reproduction of native parsing and generation boundaries (Tier B)."""

import json
from pathlib import Path

from trl.chat_template_utils import add_response_schema

from verifiable_posttraining.prompting import build_native_calculator_grpo_messages
from verifiable_posttraining.dataset import load_tasks_jsonl
from verifiable_posttraining.schemas import Split, TaskKind
from verifiable_posttraining.tools.calculator import calculator
from verifiable_posttraining.transformers_backend import TransformersPolicy


def main():
    import torch

    policy = TransformersPolicy.from_pretrained(
        "Qwen/Qwen3.5-0.8B", cache_dir="D:/huggingface-cache",
        adapter_path="outputs/sft/qwen3_5_0_8b_qlora_full_seed7/adapter",
        local_files_only=True,
    )
    add_response_schema(policy.processor)
    tokenizer = policy.processor.tokenizer
    prefix = "<|im_start|>assistant\n<think>\n\n</think>\n\n"
    report = {
        "tokenizer_eos": tokenizer.eos_token,
        "tokenizer_eos_id": tokenizer.eos_token_id,
        "generation_config": policy.model.generation_config.to_dict(),
        "parser_probes": [
            {"raw": raw, "parsed": tokenizer.parse_response(raw, prefix=prefix)}
            for raw in ["25<|im_end|>", "25<|im_end|><|endoftext|>"]
        ],
        "generation_probes": [],
    }
    task = next(t for t in load_tasks_jsonl("data/generated/pilot_tasks.jsonl")
                if t.split is Split.TEST and t.kind is TaskKind.CALCULATOR)
    messages = [m.to_dict() for m in build_native_calculator_grpo_messages(task)]
    inputs = policy.processor.apply_chat_template(
        messages, tools=[calculator], add_generation_prompt=True,
        tokenize=True, return_dict=True, return_tensors="pt", enable_thinking=False,
    ).to(policy._model_device())
    for mode, options in [
        ("existing_defaults", {}),
        ("tokenizer_eos", {"eos_token_id": tokenizer.eos_token_id,
                           "pad_token_id": tokenizer.pad_token_id}),
    ]:
        with torch.inference_mode():
            ids = policy.model.generate(**inputs, max_new_tokens=128, do_sample=False, **options)
        generated = ids[0, inputs["input_ids"].shape[-1]:].tolist()
        report["generation_probes"].append({
            "mode": mode, "token_ids": generated,
            "raw": tokenizer.decode(generated, skip_special_tokens=False),
            "parsed": tokenizer.parse_response(generated, prefix=inputs["input_ids"][0]),
        })
    output = Path("artifacts/representative_trajectories/native_parser_audit.json")
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
