# Project context and handoff

## Owner goal

The owner is a first-year data-science master's student preparing for LLM
post-training / Agentic RL internships. Existing strengths include financial
domain knowledge, LLM benchmark/evaluation experience, traditional ML, and an
agentic financial-report RAG project. The missing evidence is hands-on model
training, GPU debugging, reward design, and rigorous controlled experiments.

This repository must close that gap without pretending to be frontier-scale
research.

## Core research question

Can correct reasoning and tool-use trajectories found by best-of-N sampling be
distilled into the model's single-sample behavior, and can verifiable-reward RL
improve it further without increasing tool misuse or inference cost?

## Planned task families

1. No-tool reasoning: the correct behavior is to answer without a tool.
2. Calculator: exact arithmetic and percentages.
3. Read-only SQL: query a synthetic SQLite database.
4. SQL -> constrained analysis: query first, then compute a statistic.

Retrieval is postponed because the owner already has a RAG project. Arbitrary
Python execution is also postponed; the first environment exposes a constrained
analysis API instead.

## Evaluation principles

- Final task outcome is the primary correctness signal.
- Tool/path agreement is diagnostic because more than one path may be valid.
- Report pass@k separately from verifier-selected best-of-k.
- Track task success, exact/tolerant answer accuracy, tool selection, argument
  validity, invalid calls, over-tool rate, average calls, tokens, and latency.
- Never train on external benchmark test sets.

## Model and compute decisions

- Use `Qwen/Qwen3.5-0.8B` for compatibility and pipeline debugging.
- Treat `Qwen/Qwen3.5-4B` as a candidate until text-only SFT/GRPO compatibility
  has been demonstrated.
- The temporary RTX 4060 laptop is assumed to have about 8 GB VRAM, pending
  `nvidia-smi` confirmation.
- On the 4060, run 0.8B end to end and 4B only in 4-bit inference/search mode.
- Rent larger GPUs only after the search and SFT hypotheses survive checkpoints.

## Budget checkpoints

- Temporary 4060 work: no GPU rental cost.
- 4B formal QLoRA SFT: rent only after the 0.8B pipeline is valid.
- 4B GRPO: rent only after search produces a meaningful pass@k gap and SFT gives
  a credible improvement.
- Target total paid compute: CNY 400-700; hard cap CNY 800 unless the owner makes
  a new explicit decision.

## Current next step

Use the four-day 4060 sprint. First run the CPU tests and `doctor`, record the
hardware, then complete Day 1 in `docs/FOUR_DAY_GPU_SPRINT.md`.

