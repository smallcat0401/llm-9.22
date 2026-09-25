# Dataset provenance and split policy

## Synthetic pilot tasks

- Generated locally by deterministic code in `dataset.py`.
- Training trajectories may only originate from the synthetic `train` split.
- Synthetic validation and test tasks must never enter SFT or RL training data.

### Native calculator SFT derivative

- Source: the 37 calculator rows in the 80-row path-aligned train-only SFT set.
- Families: 21 `calculator-average-v1`, 16 `calculator-discount-v1`.
- Conversion replays the stored expression with the safe local calculator.
- The replayed result, stored observation, final answer, and hidden train-task
  ground truth must agree before a row is emitted.
- Output: `data/generated/sft_native_calculator_seed7.jsonl`.
- No validation/test task and no generated teacher answer is added.

## Multi-step calculator curriculum

- Generated locally by deterministic code in `calculator_curriculum.py`.
- Version 2 has 120 tasks across 10 disjoint families: 72 train, 24 validation,
  and 24 test. Family assignments are explicit and no template crosses splits.
- The 72-row SFT derivative uses safe-calculator replay of synthetic reference
  expressions. It is labeled `reference-program-native-calculator-v1` and is an
  oracle/reference-program ablation, not a Best-of-N trajectory collection.
- Validation and test rows never enter SFT. GSM8K rows are not consulted when
  generating prompts, expressions, or answers.
- Version 1 is retained as a failed difficulty-screening artifact: native37
  scored 24/24 zero-shot, so it was not used for training.
- The first v2 validation wording used the ambiguous verb `supplies` while its
  reference expression subtracted water. Those 12/24 results are retained as a
  superseded audit artifact. The prompt was corrected to explicitly say that
  water is drained; no training row changed.

### Final calculator holdout v1

- Generated before model evaluation and then frozen at
  `data/generated/calculator_final_holdout_v1.jsonl`.
- Contains 36 evaluation-only test tasks across three new families. None is
  eligible for SFT or RL data generation.
- SHA-256:
  `35fea2c45e3dedce50310238e859e47b159148562e5949255c8255d3a924de84`.
- It was evaluated once for native37 and once for the validation-selected
  mixed-replay step-20 checkpoint. It must not now be used for model selection.

## GSM8K external evaluation

- Upstream: `openai/grade-school-math`.
- Configuration: original main test JSONL.
- License: MIT.
- Upstream file: `grade_school_math/data/test.jsonl`.
- Expected upstream examples: 1,319.
- Expected SHA-256: `3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14`.
- Local source path: `data/external/gsm8k/test.jsonl`.
- Frozen subset: 100 source questions selected by stable SHA-256 ranking with seed 7.
- Conditions: each selected question becomes one no-tool task and one calculator-enabled task.
- Total external evaluation tasks: 200.

The entire GSM8K subset is evaluation-only. It must not be used for Best-of-N
trajectory collection, SFT, GRPO, prompt-example selection, or hyperparameter
tuning. GSM8K is a widely used benchmark and may have appeared in modern model
pretraining; results must therefore be described as standardized external
evaluation, not as proof of contamination-free generalization.

### GSM8K train-only search screen

- Source: the official `grade_school_math/data/train.jsonl` file.
- A stable SHA-256 ranking with seed 71 freezes 100 source questions.
- Verified local source: 7,473 records, SHA-256
  `17f347dc51477c50d4efb83959dbb7c56297aba886e5544ee2aaed3024813465`.
- Each source question has paired no-tool and calculator-available conditions.
- Every row is marked `train` with explicit `source_split=train` provenance.
- These rows exist only to measure the 4B search gap and, if the gate passes,
  supply verified train trajectories. They never enter final evaluation.
- Reproduction and stopping rules are in `docs/FOUR_B_SEARCH_GATE.md`.
- Frozen generated task SHA-256:
  `4a846b00eb3e61516274e4350d7db0023924fb59236be3ccc27946e2dd05f4cb`.
