import unittest

from verifiable_posttraining.grpo_probe import (
    GRPORewardProbeConfig,
    reward_probe_record,
    summarize_probe_records,
)
from verifiable_posttraining.native_tool_evaluation import NativeToolEpisodeResult
from verifiable_posttraining.schemas import Split, Task, TaskKind
from verifiable_posttraining.verifier import VerificationResult


def _config() -> GRPORewardProbeConfig:
    return GRPORewardProbeConfig(
        run_id="probe",
        model_id="model",
        adapter_path="adapter",
        dataset_path="tasks.jsonl",
        expected_dataset_sha256="0" * 64,
        expected_task_count=1,
        output_dir="output",
        metrics_path="metrics.json",
    )


def _task(task_id: str = "task-1") -> Task:
    return Task(
        task_id=task_id,
        split=Split.TRAIN,
        kind=TaskKind.CALCULATOR,
        prompt="Compute it",
        allowed_tools=("calculator",),
        ground_truth={"type": "number", "value": 120, "tolerance": 0},
        family_id="family-a",
    )


def _result(*, correct: bool) -> NativeToolEpisodeResult:
    predicted = 120.0 if correct else 20.0
    verification = VerificationResult(
        passed=correct,
        predicted_value=predicted,
        target_value=120.0,
        absolute_error=abs(predicted - 120.0),
        allowed_error=0.0,
    )
    tool_verification = VerificationResult(
        passed=correct,
        predicted_value=predicted,
        target_value=120.0,
        absolute_error=abs(predicted - 120.0),
        allowed_error=0.0,
    )
    return NativeToolEpisodeResult(
        task_id="task-1",
        messages=(
            {"role": "assistant", "tool_calls": [{"function": {"name": "calculator"}}]},
            {"role": "tool", "content": str(predicted)},
            {"role": "assistant", "content": '{"type":"final","answer":"120"}'},
        ),
        tool_called=True,
        tool_succeeded=True,
        tool_result_verification=tool_verification,
        typed_final=True,
        verification=verification,
    )


class GRPOProbeTests(unittest.TestCase):
    def test_correct_episode_receives_all_reward_components(self) -> None:
        record = reward_probe_record(_result(correct=True), _task(), sample_index=0, config=_config())

        self.assertAlmostEqual(record["reward"], 1.9)
        self.assertEqual(
            record["reward_components"],
            {
                "numeric_outcome": 1.0,
                "numeric_closeness": 1.0,
                "typed_final": 1.0,
                "calculator_trace": 1.0,
                "calculator_result": 1.0,
            },
        )

    def test_summary_detects_reward_and_outcome_variance(self) -> None:
        records = [
            reward_probe_record(_result(correct=value), _task(), sample_index=index, config=_config())
            for index, value in enumerate((True, False, True, False))
        ]

        summary = summarize_probe_records(records)

        self.assertEqual(summary["task_count"], 1)
        self.assertEqual(summary["episode_count"], 4)
        self.assertEqual(summary["nonzero_total_reward_variance_task_count"], 1)
        self.assertEqual(summary["nonzero_outcome_reward_variance_task_count"], 1)
        self.assertEqual(summary["candidate_task_ids"], ["task-1"])

    def test_summary_separates_all_correct_and_all_incorrect_groups(self) -> None:
        records = []
        for task_id, correct in (("all-right", True), ("all-wrong", False)):
            task = _task(task_id)
            for index in range(2):
                result = _result(correct=correct)
                result = NativeToolEpisodeResult(
                    task_id=task_id,
                    messages=result.messages,
                    tool_called=result.tool_called,
                    tool_succeeded=result.tool_succeeded,
                    tool_result_verification=result.tool_result_verification,
                    typed_final=result.typed_final,
                    verification=result.verification,
                )
                records.append(reward_probe_record(result, task, sample_index=index, config=_config()))

        summary = summarize_probe_records(records)

        self.assertEqual(summary["all_outcomes_correct_task_count"], 1)
        self.assertEqual(summary["all_outcomes_incorrect_task_count"], 1)
        self.assertEqual(summary["nonzero_outcome_reward_variance_task_count"], 0)


if __name__ == "__main__":
    unittest.main()
