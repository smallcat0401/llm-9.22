# Learning map

逐步学习进度和问答摘要记录在 `docs/LEARNING_NOTES.md`。聊天只负责讲解与
提问，不作为唯一的学习记录。

## A - must hand-write and defend

You should be able to recreate the essential logic without copying the repo:

- `Task`, `ToolCall`, `Observation`, `TrajectoryStep`, and `Trajectory` invariants
- calculator parsing and its safety boundary
- read-only SQL restrictions
- answer normalization and tolerance checks
- outcome verifier and reward composition
- task success, invalid-call, over-tool, call-count, and pass@k metrics
- family-level split and leakage detection

For every Tier A component, prepare a short explanation of:

1. its inputs and outputs;
2. the invariants it protects;
3. one failure case;
4. how it is tested.

## B - must understand and modify

- environment reset/step/final lifecycle
- chat template and tool schema conversion
- trajectory serialization and replay
- dataset generation and filtering pipeline
- LoRA/QLoRA configuration
- SFT loss masking
- GRPO trainer/environment wiring
- experiment configuration, logging, and evaluation runner

You do not need to reproduce an entire trainer from memory, but you must be able
to change its data, sequence length, batch/accumulation, reward, and evaluation
behavior and predict the effect.

## C - use correctly

- Python packaging and generic command-line parsing
- standard Git/GitHub operations
- generic logging and chart styling
- framework boilerplate and deployment wrappers

Tier C is not "ignore it". You must know how to run and diagnose it, but there is
little interview value in memorizing it.

## Current files

- `src/verifiable_posttraining/schemas.py`: Tier A reference implementation.
- `src/verifiable_posttraining/tools/calculator.py`: Tier A safe arithmetic boundary.
- `src/verifiable_posttraining/tools/readonly_sqlite.py`: Tier A engine-enforced read-only SQL
  boundary, allowlists, and resource limits.
- `src/verifiable_posttraining/verifier.py`: Tier A numeric normalization and outcome verification.
- `src/verifiable_posttraining/calculator_analysis.py`: Tier A failure attribution separating
  missing calls, execution failures, wrong expression results, and bad final answers.
- `src/verifiable_posttraining/environment.py`: Tier B episode lifecycle with Tier A safety checks.
- `src/verifiable_posttraining/model_protocol.py`: Tier B model/action conversion with a
  Tier A untrusted-input boundary.
- `src/verifiable_posttraining/prompting.py`: Tier B framework-independent chat construction.
- `src/verifiable_posttraining/rollout.py`: Tier B multi-turn generation/environment loop.
- `src/verifiable_posttraining/transformers_backend.py`: Tier B Qwen/Transformers loading and
  generation adapter.
- `src/verifiable_posttraining/synthetic_db.py`: Tier B deterministic synthetic database fixture.
- `src/verifiable_posttraining/dataset.py`: Tier A deterministic task generation, family-level
  splitting, and leakage validation.
- `src/verifiable_posttraining/calculator_curriculum.py`: Tier A family-isolated multi-step
  calculator generation and reference-program replay; the SFT output is an explicit ablation,
  not a searched trajectory dataset.
- `src/verifiable_posttraining/metrics.py`: Tier A outcome, protocol, and tool-use metrics.
- `src/verifiable_posttraining/evaluation.py`: Tier B deterministic batch evaluation runner and
  auditable per-task records.
- `src/verifiable_posttraining/search.py`: Tier A Best-of-N success/selection metrics with a
  Tier B multi-sample rollout loop.
- `src/verifiable_posttraining/sft_data.py`: Tier A train-only trajectory validation and Tier B
  conversion to multi-turn SFT messages.
- `src/verifiable_posttraining/sft_training.py`: Tier B QLoRA configuration and training loop;
  its assistant-only label boundary is a Tier A training-data invariant.
- `src/verifiable_posttraining/reward.py`: Tier A typed-protocol and verified-outcome reward
  components; malformed or unverified completions never receive correctness reward.
- `src/verifiable_posttraining/grpo_training.py`: Tier B TRL/QLoRA GRPO smoke wiring and
  real-parameter-update audit.
- `src/verifiable_posttraining/native_tool_evaluation.py`: Tier B native tool loop,
  chat-EOS stopping, and raw-token logging; Tier A outcome/tool-assisted metric
  separation. A direct correct answer is an outcome success but not tool-assisted
  success. Tokens after the first chat EOS cannot replace that turn's answer.
- `scripts/audit_native_parser.py`: Tier B reproducible local generation/parser audit.
- `src/verifiable_posttraining/native_sft_data.py`: Tier A replay invariants for
  converting verified calculator trajectories into native structured tool calls.
  The stored observation, locally replayed expression, and hidden task answer must agree.
- `src/verifiable_posttraining/public_eval.py`: Tier A public-answer extraction, deterministic
  subset freezing, and evaluation-only provenance.
- `src/verifiable_posttraining/doctor.py`: Tier C utility.
- `src/verifiable_posttraining/cli.py`: Tier C utility.
- `tests/test_schemas.py`, `tests/test_calculator.py`, and `tests/test_verifier.py`:
  Tier A tests; explain why each invalid case is rejected.
- `tests/test_environment.py`: Tier B lifecycle tests; be able to predict every state transition.
- `tests/test_model_protocol.py`: protocol boundary tests; explain why malformed and ambiguous
  model outputs are rejected instead of repaired silently.
- `tests/test_prompting.py` and `tests/test_rollout.py`: prompt leakage and rollout lifecycle tests.
- `tests/test_transformers_backend.py`: generation slicing and sampling configuration tests.
- `tests/test_readonly_sqlite.py`: SQL safety and bounded-result tests.
- `tests/test_synthetic_db.py`: deterministic synthetic data and known-answer tests.
- `tests/test_dataset.py`: dataset size, determinism, split coverage, and leakage tests.
- `tests/test_metrics.py`: metric denominators and separation of outcome/protocol/tool behavior.
- `tests/test_evaluation.py`: batch order, seed assignment, progress, and input validation.
- `tests/test_search.py`: strict trajectory selection, independent seeds, and pass@k accounting.
- `tests/test_sft_data.py`: train-only enforcement, replay consistency, and deduplication.
- `tests/test_public_eval.py`: public data parsing, deterministic selection, and eval-only flags.
- `tests/test_sft_training.py`: assistant-only loss masking, balanced smoke sampling, truncation,
  and padding-label tests.
- `tests/test_reward.py`: separation of format and numeric-outcome rewards.
