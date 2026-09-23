# Learning map

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
- `src/verifiable_posttraining/verifier.py`: Tier A numeric normalization and outcome verification.
- `src/verifiable_posttraining/environment.py`: Tier B episode lifecycle with Tier A safety checks.
- `src/verifiable_posttraining/model_protocol.py`: Tier B model/action conversion with a
  Tier A untrusted-input boundary.
- `src/verifiable_posttraining/prompting.py`: Tier B framework-independent chat construction.
- `src/verifiable_posttraining/rollout.py`: Tier B multi-turn generation/environment loop.
- `src/verifiable_posttraining/transformers_backend.py`: Tier B Qwen/Transformers loading and
  generation adapter.
- `src/verifiable_posttraining/doctor.py`: Tier C utility.
- `src/verifiable_posttraining/cli.py`: Tier C utility.
- `tests/test_schemas.py`, `tests/test_calculator.py`, and `tests/test_verifier.py`:
  Tier A tests; explain why each invalid case is rejected.
- `tests/test_environment.py`: Tier B lifecycle tests; be able to predict every state transition.
- `tests/test_model_protocol.py`: protocol boundary tests; explain why malformed and ambiguous
  model outputs are rejected instead of repaired silently.
- `tests/test_prompting.py` and `tests/test_rollout.py`: prompt leakage and rollout lifecycle tests.
- `tests/test_transformers_backend.py`: generation slicing and sampling configuration tests.
