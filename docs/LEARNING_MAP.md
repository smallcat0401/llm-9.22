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
- `src/verifiable_posttraining/doctor.py`: Tier C utility.
- `src/verifiable_posttraining/cli.py`: Tier C utility.
- `tests/test_schemas.py`: Tier A tests; explain why each invalid case is rejected.

