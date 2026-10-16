# V3 seed-screen results

## Status

This is a measured starting-policy search screen, not a training result.
No trajectory in this run has been approved for SFT or GRPO.

The frozen task set is `data/generated/v3_seed_screen_v1.jsonl`.  It contains
71 tasks assembled before model evaluation:

- 31 reviewed public-table variants;
- 20 deterministic calculator-curriculum-v2 seeds;
- 20 fresh GSM8K-train questions that exclude 200 source questions used by
  earlier search or validation artifacts.

Four CAGR variants are no-tool diagnostics because the bounded calculator does
not support exponentiation or roots.  The other 67 tasks expose the calculator.

## Run

- Starting policy: `Qwen/Qwen3.5-4B`
- Loading: NF4 4-bit
- Sampling: Best-of-8, temperature 0.7, top-p 0.9, top-k 20
- Seed: 211
- Candidate episodes: 568
- Peak CUDA memory: 3497.9 MiB
- Model load time: 31.102 seconds
- Search time: 1202.332 seconds
- Artifacts: `outputs/search/qwen3_5_4b_v3_seed_best_of_8_v1/`

## Main result

The recorded rollout metric, not raw verifier agreement, defines success.

| Metric | Result |
|---|---:|
| pass@1 | 13/71 (18.31%) |
| pass@8 | 36/71 (50.70%) |
| absolute search gain | +32.39 percentage points |
| protocol-valid successful candidates | 138/568 (24.30%) |
| calculator pass@1 | 13/67 (19.40%) |
| calculator pass@8 | 36/67 (53.73%) |
| no-tool CAGR pass@1 | 0/4 |
| no-tool CAGR pass@8 | 0/4 |

The configured search gate passed, but this only establishes that a useful
search gap exists.  It does not approve every task or trajectory for training.

## Results by source group

| Source group | Tasks | pass@1 | pass@8 | 0/8 | 1-7/8 | 8/8 |
|---|---:|---:|---:|---:|---:|---:|
| Reviewed public | 31 | 0 | 8 | 23 | 8 | 0 |
| Self-written curriculum v2 | 20 | 8 | 19 | 1 | 16 | 3 |
| Fresh GSM8K train | 20 | 5 | 9 | 11 | 9 | 0 |

The self-written seeds have the strongest usable difficulty distribution.
The reviewed public questions do expose new weaknesses, but most are currently
too hard for this starting policy to supply verified trajectories.  The fresh
GSM8K sample is mixed: nine questions have a search gap and eleven are 0/8.

## Per-task success-count distribution

| Correct candidates out of 8 | Task count |
|---:|---:|
| 0 | 35 |
| 1 | 7 |
| 2 | 8 |
| 3 | 3 |
| 4 | 4 |
| 5 | 3 |
| 6 | 5 |
| 7 | 3 |
| 8 | 3 |

The 33 tasks in the 1-7/8 range are the useful search-gap region.  A 0/8 task
cannot contribute a verified trajectory in this run, while an 8/8 task does not
demonstrate a single-sample weakness that search can recover.

## Training-eligibility boundary

Eligibility was fixed before evaluation:

| Predeclared status | Tasks | pass@1 | pass@8 | 0/8 | 1-7/8 | 8/8 |
|---|---:|---:|---:|---:|---:|---:|
| Future training candidate | 59 | 11 | 29 | 30 | 28 | 1 |
| Diagnostic only | 12 | 2 | 7 | 5 | 5 | 2 |

The seven successful diagnostic-only tasks must not enter SFT.  They are four
CAGR diagnostics and eight examples from historical validation/test families.
The search runner selected one verified trajectory for each of 36 successful
tasks, of which 29 have predeclared training eligibility.

## Protocol and tool-use audit

- 527/568 candidates reached a syntactically valid final action.
- 41/568 ended in protocol errors.
- 138 candidates were both protocol-valid and outcome-correct.
- Of those 138, 118 used at least one tool and 20 answered correctly without a
  tool call.
- 23 malformed/protocol-error outputs happened to contain a number that matched
  the ground truth.  Their embedded `verification.passed` value is therefore
  true, but `rollout.task_success` is false.  They are not successful rollouts
  and must never be selected for training.

This distinction is important: outcome verification remains primary, but a
candidate must also be a valid completed episode before it can become a
trajectory.

## Decision before expansion

Do not mass-generate V3 tasks yet.  First audit the 29 training-eligible tasks
with at least one valid successful trajectory:

The human-readable Chinese checklist is
`docs/V3_TRAJECTORY_AUDIT_ZH.md`.

1. verify that the accepted final answer and any tool result agree;
2. inspect whether the expression reflects the intended quantity relation;
3. reject accidental verifier matches or semantically invalid paths;
4. label successful no-tool answers separately from genuine tool-use paths;
5. use the surviving 1-7/8 families as the basis for V3 expansion;
6. reduce or redesign 8/8 families, and review rather than automatically expand
   0/8 families.

Only after that audit should new family-disjoint train, validation, and test
templates be generated.  This run does not justify starting SFT immediately.

## Post-run human-review decisions

- `v3-gsm8k-train-5655-calculator` was rejected after review. Its English
  source says "3 boxes during weekdays", while the label assumes 3 boxes on
  each of five weekdays. It remains in the frozen v1 run for auditability but
  is excluded from the SFT-candidate review page and future expansion.
- For the two markup-then-discount examples, canonical ground truth remains
  numeric (`90.0` and `110.5`), while the human review view displays the
  requested precision as `90.00` and `110.50`. JSON numbers do not preserve
  insignificant trailing zeros.
