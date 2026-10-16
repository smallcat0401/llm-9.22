"""Evaluate Qwen/Transformers native calculator tool calling on held-out tasks."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import time
from typing import Any, Mapping, Protocol, Sequence

from .dataset import load_tasks_jsonl
from .model_protocol import FinalAnswer, parse_model_action
from .prompting import build_native_calculator_grpo_messages
from .schemas import Split, Task, TaskKind
from .tools.calculator import CalculatorError, calculator
from .transformers_backend import GenerationSettings, TransformersPolicy
from .verifier import VerificationResult, verify_numeric_answer


def parse_native_response(tokenizer: Any, token_ids: Sequence[int], prefix: Any) -> Mapping[str, Any]:
    """Tier B: parse only the first assistant turn, never content after its EOS.

    A trailing document-EOS can overwrite the answer in the upstream parser.
    Keep the chat EOS itself, since it closes the parser's content field.
    """
    ids = list(token_ids)
    if tokenizer.eos_token_id in ids:
        ids = ids[:ids.index(tokenizer.eos_token_id) + 1]
    try:
        parsed = tokenizer.parse_response(ids, prefix=prefix, tools=[calculator])
    except (ValueError, TypeError):
        # Malformed model output is a scored failure, not a crashed evaluation.
        return {"role": "assistant", "content": "", "parse_error": True}
    if not isinstance(parsed, Mapping):
        return {"role": "assistant", "content": "", "parse_error": True}
    return dict(parsed)


class NativeMessagePolicy(Protocol):
    def generate_message(
        self,
        messages: Sequence[Mapping[str, Any]],
        *,
        seed: int,
    ) -> Mapping[str, Any]: ...


class TransformersNativeToolPolicy:
    """Thin adapter exposing parsed native messages from TransformersPolicy."""

    def __init__(
        self,
        policy: TransformersPolicy,
        *,
        do_sample: bool = False,
        temperature: float = 1.0,
        top_p: float = 1.0,
    ) -> None:
        from trl.chat_template_utils import add_response_schema

        self.policy = policy
        self.do_sample = do_sample
        self.temperature = temperature
        self.top_p = top_p
        self.generation_traces: list[dict[str, Any]] = []
        # GRPOTrainer performs this setup internally. Standalone evaluation must
        # attach the matching parser explicitly before calling parse_response.
        add_response_schema(self.policy.processor)

    def generate_message(
        self,
        messages: Sequence[Mapping[str, Any]],
        *,
        seed: int,
    ) -> Mapping[str, Any]:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        inputs = self.policy.processor.apply_chat_template(
            list(messages),
            tools=[calculator],
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
            enable_thinking=False,
        )
        device = self.policy._model_device()
        inputs = {
            name: value.to(device) if hasattr(value, "to") else value
            for name, value in inputs.items()
        }
        input_length = inputs["input_ids"].shape[-1]
        with torch.inference_mode():
            sampling = (
                {"temperature": self.temperature, "top_p": self.top_p}
                if self.do_sample
                else {}
            )
            generated = self.policy.model.generate(
                **inputs,
                max_new_tokens=self.policy.settings.max_new_tokens,
                do_sample=self.do_sample,
                eos_token_id=self.policy.processor.tokenizer.eos_token_id,
                pad_token_id=self.policy.processor.tokenizer.pad_token_id,
                **sampling,
            )
        new_tokens = generated[0, input_length:]
        tokenizer = self.policy.processor.tokenizer
        parsed = parse_native_response(
            tokenizer, new_tokens.tolist(), inputs["input_ids"][0],
        )
        self.generation_traces.append({
            "seed": seed,
            "messages": list(messages),
            "prompt_token_ids": inputs["input_ids"][0].tolist(),
            "generated_token_ids": new_tokens.tolist(),
            "raw_response": tokenizer.decode(new_tokens, skip_special_tokens=False),
            "parsed_response": dict(parsed),
        })
        return dict(parsed)


@dataclass(frozen=True, slots=True)
class NativeToolEpisodeResult:
    task_id: str
    messages: tuple[Mapping[str, Any], ...]
    tool_called: bool
    tool_succeeded: bool
    tool_result_verification: VerificationResult | None
    typed_final: bool
    verification: VerificationResult

    @property
    def task_success(self) -> bool:
        return (
            self.tool_called
            and self.tool_succeeded
            and self.tool_result_verification is not None
            and self.tool_result_verification.passed
            and self.verification.passed
        )


def _final_answer(content: Any) -> tuple[Any, bool]:
    if not isinstance(content, str) or not content.strip():
        return "", False
    try:
        parsed = parse_model_action(content)
    except ValueError:
        return content, False
    if parsed.ok and isinstance(parsed.action, FinalAnswer):
        return parsed.action.answer, True
    return content, False


def run_native_calculator_episode(
    task: Task,
    policy: NativeMessagePolicy,
    *,
    seed: int,
) -> NativeToolEpisodeResult:
    """Run exactly one native calculator call followed by one final response."""

    messages: list[Mapping[str, Any]] = [
        message.to_dict() for message in build_native_calculator_grpo_messages(task)
    ]
    first = dict(policy.generate_message(messages, seed=seed))
    messages.append(first)
    tool_calls = first.get("tool_calls")
    tool_called = isinstance(tool_calls, list) and bool(tool_calls)
    tool_succeeded = False
    tool_result_verification = None
    if (tool_called and len(tool_calls) == 1
            and isinstance(tool_calls[0], Mapping)
            and isinstance(tool_calls[0].get("function"), Mapping)):
        function = tool_calls[0].get("function", {})
        arguments = function.get("arguments", {})
        if function.get("name") == "calculator" and isinstance(arguments, Mapping):
            try:
                if set(arguments) != {"expression"}:
                    raise CalculatorError("invalid_arguments", "expected expression only")
                result = calculator(arguments["expression"])
                tool_succeeded = True
                tool_result_verification = verify_numeric_answer(
                    result, task.ground_truth
                )
                tool_content = str(result)
            except (CalculatorError, TypeError, ValueError) as exc:
                tool_content = json.dumps({"error": str(exc)}, ensure_ascii=False)
            messages.append(
                {"role": "tool", "name": "calculator", "content": tool_content}
            )

    if tool_succeeded:
        final = dict(policy.generate_message(messages, seed=seed + 1))
        messages.append(final)
        answer, typed_final = (
            _final_answer(final.get("content")) if not final.get("tool_calls") else ("", False)
        )
    elif not tool_calls:
        # Tier A: outcome correctness is independent of tool-path compliance.
        # A correct direct answer counts for outcome, not tool-assisted success.
        answer, typed_final = _final_answer(first.get("content"))
    else:
        answer, typed_final = "", False
    verification = verify_numeric_answer(answer, task.ground_truth)
    return NativeToolEpisodeResult(
        task_id=task.task_id,
        messages=tuple(messages),
        tool_called=tool_called,
        tool_succeeded=tool_succeeded,
        tool_result_verification=tool_result_verification,
        typed_final=typed_final,
        verification=verification,
    )


def evaluate_native_calculator(
    tasks: Sequence[Task],
    policy: NativeMessagePolicy,
    *,
    seed: int,
    num_samples: int = 1,
) -> tuple[NativeToolEpisodeResult, ...]:
    results = []
    for index, task in enumerate(tasks):
        task_results = []
        for sample_index in range(num_samples):
            result = run_native_calculator_episode(
                task,
                policy,
                seed=seed + index * 100 + sample_index * 2,
            )
            results.append(result)
            task_results.append(result)
        print(
            f"[{index + 1}/{len(tasks)}] {task.task_id}: "
            f"tool_ok={sum(item.tool_succeeded for item in task_results)}/{num_samples} "
            f"success={sum(item.task_success for item in task_results)}/{num_samples}",
            flush=True,
        )
    return tuple(results)


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser; an adapter is optional for starting-policy evals."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-id", default="Qwen/Qwen3.5-0.8B")
    parser.add_argument("--cache-dir")
    parser.add_argument(
        "--adapter-path",
        help="optional PEFT adapter; omit it to evaluate the starting policy",
    )
    parser.add_argument("--dataset", default="data/generated/pilot_tasks.jsonl")
    parser.add_argument(
        "--split",
        choices=(Split.VALIDATION.value, Split.TEST.value),
        default=Split.TEST.value,
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--metrics-artifact")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--max-new-tokens", type=int, default=128)
    parser.add_argument("--num-samples", type=int, default=1)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument(
        "--load-in-4bit",
        action="store_true",
        help="load the starting model in NF4, then attach the adapter if provided",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.num_samples < 1:
        parser.error("--num-samples must be positive")
    if args.num_samples > 1 and args.temperature <= 0:
        parser.error("--temperature must be positive for sampled evaluation")

    tasks = tuple(
        task
        for task in load_tasks_jsonl(args.dataset)
        if task.split is Split(args.split) and task.kind is TaskKind.CALCULATOR
    )
    if not tasks:
        raise ValueError("no held-out calculator tasks selected")
    started = time.perf_counter()
    base_policy = TransformersPolicy.from_pretrained(
        args.model_id,
        cache_dir=args.cache_dir,
        adapter_path=args.adapter_path,
        local_files_only=True,
        load_in_4bit=args.load_in_4bit,
        settings=GenerationSettings(max_new_tokens=args.max_new_tokens),
    )
    load_seconds = time.perf_counter() - started
    evaluation_started = time.perf_counter()
    native_policy = TransformersNativeToolPolicy(
            base_policy,
            do_sample=args.num_samples > 1,
            temperature=args.temperature,
            top_p=args.top_p,
        )
    results = evaluate_native_calculator(
        tasks,
        native_policy,
        seed=args.seed,
        num_samples=args.num_samples,
    )
    evaluation_seconds = time.perf_counter() - evaluation_started

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "generation_traces.jsonl").open("w", encoding="utf-8") as file:
        for trace in native_policy.generation_traces:
            file.write(json.dumps(trace, ensure_ascii=False) + "\n")
    with (output_dir / "records.jsonl").open("w", encoding="utf-8", newline="\n") as file:
        for result in results:
            file.write(
                json.dumps(
                    {
                        "task_id": result.task_id,
                        "messages": list(result.messages),
                        "tool_called": result.tool_called,
                        "tool_succeeded": result.tool_succeeded,
                        "tool_result_verification": (
                            {
                                "passed": result.tool_result_verification.passed,
                                "predicted_value": result.tool_result_verification.predicted_value,
                                "target_value": result.tool_result_verification.target_value,
                                "error_code": result.tool_result_verification.error_code,
                            }
                            if result.tool_result_verification is not None
                            else None
                        ),
                        "typed_final": result.typed_final,
                        "task_success": result.task_success,
                        "verification": {
                            "passed": result.verification.passed,
                            "predicted_value": result.verification.predicted_value,
                            "target_value": result.verification.target_value,
                            "error_code": result.verification.error_code,
                        },
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n"
            )
    report = {
        "run_id": args.run_id,
        "model_id": args.model_id,
        "adapter_path": args.adapter_path,
        "load_in_4bit": args.load_in_4bit,
        "protocol": "transformers-native-calculator-v2-chat-eos",
        "seed": args.seed,
        "max_new_tokens_per_turn": args.max_new_tokens,
        "eos_token_id": base_policy.processor.tokenizer.eos_token_id,
        "task_count": len(tasks),
        "split": args.split,
        "num_samples": args.num_samples,
        "episode_count": len(results),
        "decoding": "sample" if args.num_samples > 1 else "greedy",
        "temperature": args.temperature if args.num_samples > 1 else None,
        "top_p": args.top_p if args.num_samples > 1 else None,
        "tool_called_count": sum(result.tool_called for result in results),
        "tool_succeeded_count": sum(result.tool_succeeded for result in results),
        "tool_result_correct_count": sum(
            result.tool_result_verification is not None
            and result.tool_result_verification.passed
            for result in results
        ),
        "outcome_success_count": sum(result.verification.passed for result in results),
        "outcome_pass_at_n_count": len({
            result.task_id for result in results if result.verification.passed
        }),
        "typed_final_count": sum(result.typed_final for result in results),
        "task_success_count": sum(result.task_success for result in results),
        "episode_success_rate": sum(result.task_success for result in results) / len(results),
        "task_pass_at_n_count": sum(
            any(result.task_success for result in results if result.task_id == task.task_id)
            for task in tasks
        ),
        "task_pass_at_n_rate": sum(
            any(result.task_success for result in results if result.task_id == task.task_id)
            for task in tasks
        )
        / len(tasks),
        "load_seconds": load_seconds,
        "evaluation_seconds": evaluation_seconds,
    }
    (output_dir / "metrics.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if args.metrics_artifact:
        metrics_artifact = Path(args.metrics_artifact)
        metrics_artifact.parent.mkdir(parents=True, exist_ok=True)
        metrics_artifact.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
