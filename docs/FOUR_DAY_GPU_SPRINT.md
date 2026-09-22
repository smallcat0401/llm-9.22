# Four-day RTX 4060 sprint

## Scope

The sprint validates the training and evaluation pipeline. It does not attempt a
full 4B GRPO experiment.

## Day 1 - environment and one complete episode

Deliverables:

- hardware and software inventory;
- isolated Python environment;
- CPU tests passing;
- 0.8B checkpoint loaded;
- one normal generation;
- one parsed tool call;
- one tool observation returned to the model;
- one final answer scored by the verifier.

Stop rule: if an optional acceleration package blocks progress for more than two
hours, remove it and use the simplest Transformers path.

## Day 2 - pilot tasks, tools, and baseline

Deliverables:

- calculator, read-only SQLite, and constrained analysis tools;
- 300-500 deterministic pilot tasks;
- family-level train/validation/test split;
- gold answers accepted by the verifier;
- at least 100 debug-model baseline episodes;
- first metrics table and bad-case sample.

Do not proceed to training if the evaluation loop can crash on malformed model
output or if gold answers do not pass consistently.

## Day 3 - 0.8B QLoRA SFT

Deliverables:

- verified SFT examples;
- a 50-100-example overfit test;
- one small QLoRA SFT run;
- saved adapter and exact config;
- before/after evaluation using the same frozen test split.

Stop rule: if the tiny overfit test fails, debug formatting, masking, and labels;
do not move to GRPO.

## Day 4 - minimal GRPO and 4B search compatibility

Deliverables:

- a minimal 0.8B GRPO run with real parameter updates;
- reward and completion logs inspected for reward hacking;
- 4B checkpoint loaded in 4-bit mode if memory permits;
- 20-30 compatibility episodes;
- if stable, a small best-of-4 sample and pass@1/pass@4 report;
- complete backup and `GPU_RUN_REPORT.md`.

The 4B run may fall back to the 0.8B result if the laptop cannot load it safely.
That is a hardware finding, not a reason to fabricate or hide results.

