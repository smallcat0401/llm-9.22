# Repository instructions for coding agents

## Project objective

Build a reproducible post-training project that studies whether successful
reasoning and tool-use trajectories discovered by test-time search can be
distilled into a model and then improved with verifiable-reward RL.

The intended experimental line is:

`starting policy -> best-of-N search -> trajectory SFT -> GRPO/RLVR -> evaluation`

This is a model post-training project. Do not turn it into a second generic
LangGraph/RAG application.

## Truthfulness and data rules

- Never fabricate metrics, model outputs, GPU runs, or claimed improvements.
- Keep measured results separate from targets and examples.
- Use only synthetic or explicitly public data. Never add employer data,
  internship data, proprietary benchmarks, credentials, or personal documents.
- Do not call an instruction-tuned starting checkpoint a "base model". Use
  "starting policy" or "instruct baseline" unless a true `*-Base` checkpoint is
  used.
- Do not treat one expected tool path as the definition of correctness. Outcome
  verification is primary; path labels are diagnostic signals.
- Keep train, validation, and test families separated by template/family, not
  by random row splitting.

## Learning tiers

Every material implementation should be classified in documentation or code
review as one of:

- `A - must hand-write`: task/trajectory schemas, tool safety boundaries,
  verifier logic, reward logic, core metrics, and split-leakage rules.
- `B - must understand and modify`: environment loop, dataset pipeline,
  training configuration, LoRA/GRPO wiring, logging, and evaluation runners.
- `C - use correctly`: packaging, generic CLI glue, formatting, dashboards,
  and framework boilerplate.

When implementing Tier A code, explain invariants and failure cases. Do not hide
the core logic behind a large framework abstraction.

## Hardware scope

The temporary RTX 4060 laptop is for:

- the 0.8B end-to-end pipeline, including QLoRA SFT and a minimal GRPO smoke run;
- 4B 4-bit inference and a small baseline/best-of-N compatibility experiment.

Do not attempt a full 4B GRPO run on the 4060. Formal 4B SFT/RL experiments may
move to rented hardware after the pipeline is validated.

## Engineering rules

- Prefer deterministic seeds and machine-readable configs.
- Add or update tests for changes to schemas, tools, verifiers, and metrics.
- Pin the final working GPU environment after the first successful install.
- Never commit model weights, caches, large checkpoints, or secrets.
- Store small metrics and representative trajectories in Git; back up large
  adapters/checkpoints separately.
- Keep commands reproducible from a clean clone.

## Local Windows Python environment

- The project interpreter is `.venv\Scripts\python.exe` (Python 3.11.9).
- Its base interpreter is installed outside the repository under the current
  Windows user's `AppData\Local\Programs\Python\Python311` directory.
- A restricted coding-agent sandbox may report `No Python at ...` because it
  cannot read that external directory. This is a permission artifact, not
  evidence that Python or the virtual environment is missing.
- If a project Python command fails with that message, rerun the same command
  with the required sandbox escalation. Do not reinstall Python, recreate the
  virtual environment, or tell the owner that Python is missing before this
  elevated verification.
- Do not rely on `py -3.11` for agent checks on this machine; invoke the
  repository-local interpreter explicitly. VS Code should also select
  `.venv\Scripts\python.exe`.

## Current state

Phase 0 scaffold is present. Read `PROJECT_CONTEXT.md` and
`docs/FOUR_DAY_GPU_SPRINT.md` before starting GPU work.
