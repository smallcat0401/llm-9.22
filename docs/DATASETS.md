# Dataset provenance and split policy

## V3 seed screen v1

- Built before V3 mass generation to measure whether proposed seed relations
  have useful 4B search gaps.
- Frozen tasks: `data/generated/v3_seed_screen_v1.jsonl`.
- Composition: 31 reviewed public-table variants, 20 deterministic synthetic
  curriculum-v2 seeds, and 20 fresh GSM8K-train questions.
- The fresh GSM8K subset uses stable SHA-256 selection with seed 211 and excludes
  200 source questions used by earlier search or validation artifacts.
- Four CAGR variants and eight examples from historical validation/test
  families are marked diagnostic-only. Their trajectories are not eligible for
  training even when verified.
- This file is a search-screen input, not SFT data. Successful trajectories must
  pass a separate semantic and tool-path audit before conversion.
- Measured Best-of-8 results and the decision boundary are recorded in
  `docs/V3_SEED_SCREEN_RESULTS.md`.

### V3 zero-pass revision screen v2

- Human audit found eleven v1 zero-pass tasks whose wording, sign convention,
  direction, or rounding rule needed correction before failure attribution.
- The corrected tasks are stored separately at
  `data/generated/v3_zero_pass_revisions_v2.jsonl`; frozen v1 tasks and metrics
  were not overwritten.
- Source v1 SHA-256:
  `caee0cca45468395749e1c6fe49a0840b9aed0c179f49fc2b42a8c6a78235132`.
- Revision output SHA-256:
  `4cd22802d157024410039b3c9b7fc7b5046d9f307bd6116506786526e0a691e8`.
- This 11-row file is a search input, not SFT data.  Its 4B Best-of-8 re-screen
  produced four strict-success tasks, but semantic tool-path review retained
  only three as Search-SFT candidates.
- Results and the resulting Search-SFT/reference-program boundary are recorded
  in `docs/V3_REVISED_ZERO_PASS_RESULTS_ZH.md`.

### V3 zero-pass reference-program SFT

- The initial v1 candidate contained 27 train-only rows. Formula review found
  one implicit rounding rule; after a prompt clarification and fresh Best-of-8,
  that revised task produced a valid aligned search trajectory.
- The current reference branch therefore contains 26 rows. Every row replays a
  human-audited expression with the safe calculator and passes the verifier.
- Every row is labeled `trajectory_source=reference-program` and
  `search_discovered=false`; it must not be reported as search distillation.
- Native-tool ablation output:
  `data/generated/v3_zero_pass_reference_program_sft_v2.jsonl`, SHA-256
  `ace23ab46820dc972fd3ac87c3c778f5feea04bcf2f1334f26e4f50554d141db`.

### V3 reviewed custom-protocol SFT package v1

- All three primary packages use one JSON action protocol. Native structured
  tool rows remain a separate ablation and are not mixed into these files.
- Search-only output: `data/generated/v3_search_discovered_sft_custom_v1.jsonl`
  (32 rows; 27 tool-assisted and 5 direct-answer paths), SHA-256
  `5f4defa21c66afbc7d38e8bec02cde081e350bd64fa1d7326bcf28c174d247fb`.
- Reference-only output: `data/generated/v3_reference_program_sft_custom_v1.jsonl`
  (26 rows), SHA-256
  `132bd9dc881f5b87872d40f8febd9af44cf0ce80288177011401da713bd76829`.
- Mixed output: `data/generated/v3_mixed_sft_custom_v1.jsonl` (58 rows),
  SHA-256
  `9b3a7f1484308077b071dda98c552ee8c84532a76eec31c4c1fc3d7a7cc974ea`.
- Every mixed row retains `mixture_source`; reference rows are never described
  as search-discovered trajectories.
- Full provenance is stored in
  `artifacts/dataset_manifests/v3_sft_package_custom_v1.json` and explained in
  `docs/V3_SFT_PACKAGE_ZH.md`.

### V3 evaluation seed audit v0

- This is a pending human-review pack, not frozen validation/test data and not
  training data.
- It contains 24 candidates: 12 proposed validation and 12 proposed test rows.
  Each side has eight self-written seeds across four split-exclusive templates
  plus four unused public GSM8K source questions.
- Public source indices are checked against the supplied prior search,
  validation, SFT, and external-evaluation artifacts. Synthetic reference
  expressions are replayed by the bounded calculator, and public expressions
  must also agree with the official public label.
- Machine-readable candidates:
  `data/review/v3_eval_seed_audit_v0.jsonl`.
- Chinese review view: `docs/V3_EVAL_SEED_AUDIT_ZH.md`.
- Manifest: `artifacts/dataset_manifests/v3_eval_seed_audit_v0.json`.
- No model run or dataset expansion is permitted until the wording, difficulty,
  formulas, and proposed split assignments are approved.

### Frozen V3 evaluation v1

- The reviewed seed templates were approved on 2026-10-05 and expanded into
  split-exclusive evaluation families.
- Validation: `data/generated/v3_validation_v1.jsonl` (36 tasks: 32 synthetic
  across four families plus four reviewed GSM8K-train questions), SHA-256
  `daa41fda27f3476c6a279993d94b29ca4a3b3d49259f3aaba5505f47ab6b1484`.
- Test: `data/generated/v3_test_v1.jsonl` (36 tasks: 32 synthetic across four
  different families plus four reviewed GSM8K-test questions), SHA-256
  `9e6613d6f11f3cdc38e90a5b0b6aeddf94b4378b96c5be04116af45e2cf82eae`.
- Validation and test families are disjoint from one another and from all 58
  rows in the V3 mixed SFT package. Every hidden reference expression passes
  safe-calculator replay and every task is marked `evaluation_only`.
- Validation may be used for checkpoint selection. Test must remain unopened
  until the selection rule has chosen a checkpoint.
- Full inputs, exclusions, family IDs, and output hashes are recorded in
  `artifacts/dataset_manifests/v3_evaluation_v1.json`.

## V4 seed-derived expansion

### Owner-approved self-written task candidates v1

- Directly derived from the six audited self-written TRAIN families in the V3
  seed screen. The reviewed parent rows use generator indices 000 and 001;
  the expansion uses 14 new variants per family.
- The 84 English tasks use deterministic seed 401, independently sampled
  parameters, and three relation-preserving wording or scene variants per
  family. Every reference expression passes safe-calculator replay.
- The owner approved all 84 tasks on 2026-10-05 after reviewing
  `docs/V4_SEED_DERIVED_AUDIT_ZH.md`.
- Approved task output:
  `data/generated/v4_seed_derived_self_written_approved_v1.jsonl`.
- Manifest and SHA-256:
  `artifacts/dataset_manifests/v4_seed_derived_self_written_approved_v1.json`.
- This is a task set, not an SFT dataset. A task may enter SFT only after a
  verified search trajectory or explicitly labelled reference-program
  trajectory is generated and audited.

### Owner-approved public-relation synthetic-table tasks v1

- Directly derived from the 13 reviewed public-table relation families present
  in the V3 mixed SFT package, with six new variants per family (78 total).
- The builders preserve the reviewed quantitative relations but construct new
  synthetic tables. They do not copy or numerically mutate the original public
  company tables.
- Structural variation includes changing selected months/divisions, moving
  loss and zero rows, varying sign patterns, adding a non-overlapping-period
  average comparison, and rotating several metrics and financial instruments.
- The owner approved all 78 tasks on 2026-10-06 after reviewing:
  `docs/V4_PUBLIC_SEED_RELATIONS_AUDIT_ZH.md`.
- Pre-approval English review candidates:
  `data/review/v4_public_seed_relations_audit_v0.jsonl`.
- Approved task output:
  `data/generated/v4_public_seed_relations_approved_v1.jsonl`.
- Manifest and SHA-256:
  `artifacts/dataset_manifests/v4_public_seed_relations_approved_v1.json`.
- Every formula passes safe-calculator replay and an independent relation
  oracle. Approval makes these tasks eligible for trajectory collection, not
  immediate SFT.
- No V3 validation or test family was used to create these train-family
  candidates.

### Combined approved V4 train task pool v1

- Combines the 84 approved self-written seed-derived tasks and the 78 approved
  public-relation synthetic-table tasks: 162 tasks across 19 TRAIN families.
- Output: `data/generated/v4_train_task_candidates_approved_v1.jsonl`.
- Manifest and SHA-256:
  `artifacts/dataset_manifests/v4_train_task_candidates_approved_v1.json`.
- This is still a task pool, not an SFT dataset. It contains no model outputs,
  tool observations, or verified trajectories. Search/reference-program
  collection and outcome verification must happen before any row enters SFT.

### Pending V4 validation public-family extension audit v0

- The frozen V3 validation set remains unchanged at 36 tasks: four
  self-written families with eight tasks each and four public families with one
  task each.
- This audit pack adds seven synthetic, relation-preserving candidates to each
  of those four public validation families: 28 pending rows total.
- If all rows are approved, a new V4 validation version can combine them with
  the unchanged V3 validation rows to form 64 tasks across eight families,
  with exactly eight tasks per family.
- Machine-readable audit candidates:
  `data/review/v4_validation_public_extension_audit_v0.jsonl`.
- Chinese audit view: `docs/V4_VALIDATION_EXTENSION_AUDIT_ZH.md`.
- Pending-audit manifest and hashes:
  `artifacts/dataset_manifests/v4_validation_public_extension_audit_v0.json`.
- All rows are validation-only, `review_status=pending`, and
  `training_eligible=false`. The frozen V3 test set is not read or modified.
- Self-audit checked all 28 prompt/formula/GT pairs, integral counts, and
  physically valid tank states. The Chinese audit view records these checks
  and the within-family similarity limit.

### Frozen V4 validation v1

- The owner completed review of the 28 extension rows on 2026-10-06 without
  requesting edits. The frozen V4 validation contains the unchanged 36 V3
  validation tasks plus those 28 approved synthetic tasks: 64 tasks across
  eight validation families, eight tasks per family.
- Output: `data/generated/v4_validation_v1.jsonl`, SHA-256
  `d62dc47ae7027de67c30521327d5f8afb6b88878ffddfe758843820da9093cf0`.
- Manifest: `artifacts/dataset_manifests/v4_validation_v1.json`.
- The output is evaluation-only. Its families are disjoint from the 162 V4
  train tasks and from the frozen V3 test families. V3 source files remain
  unchanged; the frozen test set has not been used for V4 model selection.
- Since V3 validation was already used for checkpoint selection, the 64-row
  V4 validation is not a fresh independent holdout. See
  `docs/V4_VALIDATION_FREEZE_ZH.md` for its usage boundary.

### Pending V4 test extension audit v0

- The frozen V3 test file stays unchanged at 36 tasks and its SHA-256 is
  checked before generating any extension. No test model outputs are consulted.
- One new, test-only candidate is derived from each of the 36 originals:
  32 self-written-family variants and four new **synthetic** relation variants
  inspired by the four GSM8K-test seeds. The latter are not new public GSM8K
  examples or independent external benchmark questions.
- If all 36 candidates pass owner review, the planned combined set has 72
  tasks across eight test-only families: four self-written families with 16
  each and four public-seed relation families with two each. Report results by
  family, original/extension cohort, and source provenance; within-family
  variants must not be presented as 72 independent reasoning types.
- Every candidate has an explicit parent ID, `review_status=pending`,
  `evaluation_only=true`, and `training_eligible=false`. Each hidden reference
  program is replayed with the bounded calculator and checked against an
  independently computed numerical result. Invalid parent counts, changed
  frozen-test hash, arithmetic mismatch, or train/validation family overlap
  aborts construction. Human wording/GT review is still required before freeze.
- Pending JSONL: `data/review/v4_test_extension_audit_v0.jsonl`; Chinese view:
  `docs/V4_TEST_EXTENSION_AUDIT_ZH.md`; manifest and input/output hashes:
  `artifacts/dataset_manifests/v4_test_extension_audit_v0.json`.
- Generator: `scripts/build_v4_test_extension_audit.py`. This creates only an
  audit pack, not a V4 frozen test set, and performs no evaluation or training.

### Revised pending V4 test extension audit v1

- The v0 audit artifacts above remain intact for provenance. Self-review found
  that all eight new self-written rows per family had one numeric-normalized
  English wording pattern and 31/32 new GT values exceeded the corresponding
  frozen family's old maximum. This offered little wording diversity and an
  avoidable near-monotone numeric shift.
- The revised audit still adds exactly one test-only candidate per frozen V3
  parent: 32 self-written variants plus four synthetic variants inspired by
  the GSM8K-test seeds. Each self-written family now has four wording patterns
  (two rows each), and the parameters are deliberately non-monotone. Only 2/32
  new self-written GT values exceed their old family's maximum. This improves
  within-family coverage, not the number of independent reasoning families.
- The four public-seed derivatives use explicitly synthetic task IDs and source
  labels; they are **not** counted as new public benchmark rows. The Chinese
  audit view prints monetary GT to two decimal places when requested, while
  the machine-readable target remains a numeric value.
- Input frozen-test SHA-256, parent coverage, calculator replay versus an
  independent Decimal oracle, prompt uniqueness, and train/validation family
  separation are checked before writing. Every new row remains
  `review_status=pending`, `evaluation_only=true`, and `training_eligible=false`.
  Human semantic review is required before any freeze; no model evaluation has
  been run on these candidates.
- Candidate JSONL: `data/review/v4_test_extension_audit_v1.jsonl`; Chinese
  review: `docs/V4_TEST_EXTENSION_AUDIT_V1_ZH.md`; manifest with input/output
  hashes: `artifacts/dataset_manifests/v4_test_extension_audit_v1.json`.
- Reproduce with `scripts/build_v4_test_extension_audit_v1.py`. If approved,
  the eventual combined set would contain 72 tasks in eight test-only families
  (four 16-row self-written families and four two-row public-seed families).
  Report family and source/cohort breakdowns rather than relying only on the
  72-row pooled score.

### Frozen V4 test v1

- The owner approved all 36 revised v1 extension candidates on 2026-10-06.
  The pending audit pack and its v0 predecessor remain unchanged as historical
  artifacts; approval is recorded in a separate frozen output.
- Output: `data/generated/v4_test_v1.jsonl`, 72 test-only tasks: the original
  frozen V3 36 rows unchanged, followed by 32 self-written extensions and four
  synthetic tasks derived from public test seed relations. The latter are **not**
  new public benchmark questions.
- SHA-256: `a0223c4517596007cf40e5cdd30e61e534f5f5dd4855af0f0042d106341be0bc`.
  Full provenance, counts, review-artifact hash, and source hashes are in
  `artifacts/dataset_manifests/v4_test_v1.json`.
- Each V3 parent has exactly one approved extension. The eight test families
  remain split-exclusive from V4 train and validation; four self-written
  families have 16 rows each and four public-seed families have two each.
  These are correlated variants within eight families, not 72 independent
  reasoning types.
- This file is evaluation-only and must not enter search, SFT, RL, prompt
  selection, or checkpoint selection. Run it once after selecting the final
  checkpoint using validation. Report results by family and V3/V4 cohort as
  well as pooled accuracy. No V4 test model result has yet been measured.
- Reproduce the freeze with `python -m scripts.freeze_v4_test`. Chinese handoff:
  `docs/V4_TEST_FREEZE_ZH.md`.

### V4 train-only Best-of-8 trajectory candidates

- Qwen3.5-4B starting policy searched the approved 162 V4 train tasks eight
  times each. Strict success was found for 117 tasks; 115 have a clean,
  replayed calculator path selected as one new SFT candidate per task.
- The staged V3+V4 merge has 58 old plus 115 new examples (173 total). Exact
  task IDs and user prompts are disjoint. Source labels remain separate.
- New paths are pending semantic formula review; the merged file is **not**
  training-ready. No validation or test example enters the merge.
- Measured metrics: `artifacts/metrics/qwen3_5_4b_v4_train_best_of_8_seed509.json`.
  Audit and staging: `docs/V4_SEARCH_RESULTS_ZH.md` and
  `data/review/v4_search_sft_candidates_v0/manifest.json`.

### V4 zero-pass manual reference candidates

- Review of all 45 train-side zero-pass tasks found four with insufficient or
  misleading financial wording. A new immutable-derived train version excludes
  those four: `data/generated/v4_train_tasks_curated_v2.jsonl` (158 tasks).
  The original 162-task search run and metrics remain unchanged.
- The other 41 have explicit assistant-authored calculator programs, replayed
  through the local environment and independently checked by the verifier.
  They are labeled reference demonstrations, not search successes or human-
  approved examples.
- The V3 58 + V4 search 115 + manual reference 41 merge is a 214-row **staged**
  SFT candidate set; owner semantic review remains before training.
- See `docs/V4_MANUAL_ZERO_PASS_TRAJECTORIES_ZH.md` and
  `artifacts/dataset_manifests/v4_manual_zero_pass_v1.json`.

### V4 SFT path curation v1

- A read-only path audit found one search-success trajectory that begins with
  an incorrect calculator expression and only then self-corrects:
  `v4-review-curriculum-v2-required-score-002`. The owner agreed to exclude it
  from imitation training; the raw search record and measured Best-of-8
  statistics are unchanged.
- The immutable-derived staged candidate file is
  `data/review/v4_sft_paths_curated_v1/sft_candidates_213.jsonl`: 58 prior V3,
  114 V4 search-discovered, and 41 assistant-authored reference examples. SHA-256:
  `bb07a16e90d0100bb3cc3a2c375b72b437bd39c15b2460f29015d811fe059422`.
- This remains `train_ready=false`. Agreement to exclude one flawed path is not
  blanket approval of the remaining new paths or a completed 4B training run.
  Provenance and source hashes are in
  `artifacts/dataset_manifests/v4_sft_paths_curated_v1.json`; review notes are
  in `docs/V4_SFT_PATH_CURATION_ZH.md`.
- Reproduce with `scripts/curate_v4_sft_paths.py`. Exact source checks, the
  rejected action's failure case, and train-only/source-count invariants are
  Tier A; the JSONL packaging is Tier B/C glue.

### Owner-approved V4 SFT v1

- The owner accepted the path audit of the remaining candidates on 2026-10-06.
  The separate approved file is `data/generated/v4_sft_custom_approved_v1.jsonl`
  (213 rows), SHA-256
  `52c6f559156f3c8655516602e0d4a97431e200539d1bbda5880c890bdef497ad`.
- Composition remains 58 V3-reviewed, 114 V4 search-discovered, and 41
  assistant-authored reference paths. These sources remain explicitly labeled;
  the reference paths must not be called model-discovered successes.
- The freeze replays every new tool observation, verifies every new final
  answer against its approved train task, and rejects validation/test family
  overlap. The prior staged inputs and original search measurements remain
  unchanged. Full hashes and approval status are in
  `artifacts/dataset_manifests/v4_sft_custom_approved_v1.json`.
- Formal V4 4B SFT configuration and evaluation boundary are documented in
  `docs/V4_4B_SFT_PLAN_ZH.md`. Freezing training data is not a training run.

### Frozen V4 GRPO outcome-variance train prompts v1

- The selected V4 epoch-3 SFT adapter completed an inference-only reward probe
  over all 158 curated train tasks, with eight samples per task and seed 719.
  The probe produced 53 tasks with both verifier-passing and verifier-failing
  final numeric outcomes in the same group.
- Those 53 tasks are frozen at
  `data/generated/v4_grpo_train_outcome_variance_seed719_v1.jsonl`. The
  selection uses all and only nonzero numeric-outcome-variance groups; it does
  not use validation/test results or impose a post-hoc family cap.
- The 103 all-correct tasks and two all-incorrect tasks have no numeric-outcome
  group variance. Three additional all-correct tasks have only auxiliary or
  format reward variance. None of those 108 tasks enters this first formal
  GRPO prompt set.
- All rows remain calculator-only `train` tasks and their 16 family IDs are
  disjoint from frozen V4 validation and test. The set is weakness-weighted,
  not family-balanced, so formal evaluation must include macro-family metrics.
- Full selection counts, hashes, task IDs, and interpretation limits are in
  `artifacts/dataset_manifests/v4_grpo_train_outcome_variance_seed719_v1.json`;
  Chinese audit notes are in `docs/V4_GRPO_TRAIN_FREEZE_ZH.md`.
- Reproduce with `python -m scripts.freeze_v4_grpo_train`. This freeze is not a
  GRPO training run and does not claim improvement.

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
