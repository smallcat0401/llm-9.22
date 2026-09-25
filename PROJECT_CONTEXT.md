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

The Qwen3.5-4B inference-only Search-Gap Gate is now complete on the local RTX
4060. On 100 paired condition-specific GSM8K-train tasks with eight samples per
task, strict trajectory pass@1 was 10/100 and pass@8 was 43/100 (+33 percentage
points). The calculator condition was 7/50 -> 29/50 and the no-tool condition
was 3/50 -> 14/50. The preregistered gate passed and yielded 43 selected verified
trajectories, 20 with executed calculator calls. The next step is to audit and
package the training set, freeze the post-SFT evaluation protocol, estimate
rented-GPU cost, and prepare a 4B QLoRA SFT config. The path-alignment audit over
all candidates identifies 40 SFT-eligible tasks (14 no-tool and 26 calculator);
use those rather than the generic 43-row search selection. Do not start 4B GRPO
until a controlled post-SFT evaluation demonstrates a credible gain.

The train-only search pool was then expanded with two additional source-disjoint
batches. Across 150 distinct GSM8K train source questions (300 paired tasks and
2,400 candidates), strict pass@1 is 43/300 and pass@8 is 131/300, a +29.3-point
aggregate gap. All three batches independently pass the gate. Path-aligned
curation yields a frozen 112-example SFT set (43 no-tool, 69 calculator with
real tool messages). Stop collecting more trajectories for the first SFT run;
the next work is frozen evaluation protocol plus rented-hardware QLoRA config.

The frozen 4B starting-policy test baseline is now measured at 38/200 strict
successes (11 no-tool, 27 calculator-condition), with 46/200 outcome verifier
passes, 22 protocol errors, and only 12 recorded tool calls. The formal
three-pass QLoRA config is `configs/sft_qwen3_5_4b_verified112_seed113.toml`.
Checkpoint choice must not use the frozen test result; select epoch 1/2/3 on a
separate validation screen, then compare the chosen adapter to this 38/200
baseline exactly once.

The separate validation screen is frozen and source-disjoint from all search
pools. Its starting-policy baseline is 23/100 strict success (8 no-tool, 15
calculator-condition), with 10 protocol errors. Select a checkpoint by the
preregistered rule in `docs/FOUR_B_SEARCH_GATE.md`, then open the frozen test.

Day 1 is complete on the local RTX 4060: the 0.8B starting policy completed a
real calculator tool episode. Day 2 now has a 300-task deterministic pilot set,
family-level splits, calculator and read-only SQL tools, gold-answer checks, and
a measured 102-episode debug baseline. Full train-split Best-of-4 produced 600
candidates and solved 81/150 tasks versus 28/150 at sample one. A train-only
81-example candidate SFT set has been structurally replayed and validated. The
next checkpoint is to freeze a small public external evaluation set, then apply
explicit path-quality curation before starting SFT. The GSM8K adapter and freeze
tests are implemented. A verified 100-question GSM8K subset has been frozen into
200 paired tasks, and the pre-SFT baseline is recorded: 0/200 strict successes,
4/200 verifier passes, with all 200 outputs violating the typed action protocol.
Path-aligned curation selected 80 train-only SFT examples from 600 search
candidates, with no missing tools on tool tasks and no over-tooling on no-tool
tasks. The QLoRA smoke configuration and explicit assistant-only label masking
are implemented and unit-tested. The corrected 18-example QLoRA smoke reduced
loss by 94.35%. The historical run configured for 80 examples reduced loss by
84.79%, but a later audit showed that it actually selected only 41 rows. Frozen
external strict success for that historical adapter moved from 0/200 to 24/200 while protocol errors fell
from 200/200 to 10/200. On the 75-task family-held-out internal test, aggregate
success moved from 18 to 28, but SQL regressed from 17/25 to 0/25; preserve this
negative result. A real 0.8B GRPO smoke changed 372 adapter tensors, but the
20-step mini run had non-zero group reward variance on only 1/20 steps, so its
29/75 result is not evidence of stable RL improvement. See
`docs/GPU_RUN_REPORT.md` for the measured handoff.
The frozen v1 failure is retained, while prompt protocol v3 adds an explicit
SQL scalar/aggregation requirement. Under v3 and seed 17, the SFT adapter
scores 52/75 (no-tool 24, calculator 4, SQL 24). A dense-reward GRPO ablation
uses four train/no-tool tasks absent from SFT, 16 completions per group, and a
bounded numeric-closeness auxiliary reward. It produced non-zero reward
variance on 12/12 steps and scored 53/75 (24, 4, 25) under the same evaluation.
Treat the one-task difference as a positive diagnostic, not a demonstrated
stable gain. The next evidence step is multi-seed evaluation and broader GRPO
training prompts before any formal 4B RL run.
Training-seed replications 23 and 41 are now complete. Together with seed 17,
all three runs had non-zero group reward variance on 12/12 steps and all three
greedy evaluations scored 53/75 with the same kind breakdown (24 no-tool,
4 calculator, 25 SQL), versus the SFT control's 52/75. This establishes
repeatability under the current four-prompt curriculum, but not broad
generalization. The next experiment should broaden train-only GRPO prompts.
A broader seed-29 run then used all 37 train/no-tool tasks absent from SFT for
one epoch. All 37/37 groups had non-zero reward variance; 372 adapter tensors
changed; peak allocated CUDA memory was 6,584.8 MiB. Its greedy test result
remained 53/75 (24 no-tool, 4 calculator, 25 SQL). Broader no-tool coverage
therefore preserved the result but did not improve it. The next technical
bottleneck is verifiable calculator/tool-use GRPO rather than more no-tool
repetition.
Native calculator tool-use GRPO is now implemented with TRL's structured
multi-turn tool loop. A 13-prompt seed-35 run had non-zero reward variance on
13/13 steps, changed 372 adapter tensors, used 5,137.4 MiB peak CUDA memory,
and completed in 238.9 seconds. It did not improve the frozen custom-protocol
test (still 53/75, with calculator 4/25). An audit then found that native
evaluator v1 used document EOS 248044 instead of chat EOS 248046; trailing
`<|endoftext|>` overwrote valid parsed answers. All native-v1 metrics are marked
invalid. Corrected v2 evaluation on the unseen percent-change family gives the
same result for SFT and post-GRPO: greedy outcome 2/25 and tool-assisted success
0/25; temperature-1.4 outcome pass@4 3/25 and tool-assisted pass@4 1/25. SFT
made 19 calls in 100 sampled episodes (17 executed); post-GRPO made 19 (18
executed). Preserve this as a controlled negative result: the pipeline and
limited native capability are demonstrated, but the 13-step adapter has no
measured advantage over SFT. Broader calculator families and stronger
tool-result-to-final supervision are the next 0.8B experiment.
An SFT selection audit then found that the historical configuration requested
80 examples but `select_balanced_examples` stopped after 41 because its loop
compared selected rows against a shrinking remaining-row count. Historical
losses and evaluations remain measured results for that 41-row adapter; all
downstream historical GRPO adapters inherit it. The selector now fixes its
target before mutation and has an all-rows regression test. A corrected full80
run selected 80/80 (13 no-tool, 37 calculator, 30 SQL), reduced loss by 78.98%,
and historically scored 53/75 under the superseded strict percent tolerance.
Continuing that adapter on all 37 replayed
native calculator trajectories reduced native-data loss by 67.05%. On the
held-out percent-change family, greedy structured calls moved 0/25 -> 25/25.
A later verifier audit found that the original 1e-6 tolerance rejected correctly
rounded two-decimal percentages. With the family tolerance corrected to 0.005,
greedy effective tool-path success is 0/25 -> 25/25 and sampled effective-tool-
path pass@4 is 2/25 -> 24/25. The native37 sampled records still contain 32/100
wrong-expression-result episodes. Offline rescoring puts corrected full80 and
native37 at 75/75 on the now-saturated internal suite, with zero protocol errors.
This corrected full80 -> native37 branch is the current formal baseline.
On the matched v3 GSM8K paired evaluation, corrected full80 scored 20/200
(4 no-tool, 16 calculator; 12 protocol errors), while full80 -> native37 scored
21/200 (5 no-tool, 16 calculator; 11 protocol errors). The calculator result is
flat, so native SFT improved structured tool use but not external mathematical
accuracy. Formula construction/reasoning is the next data and reward target.
A result-aware calculator reward was then added and a 13-step seed-47 GRPO run
started from native37. Six of 13 groups had non-zero reward variance; 372 adapter
tensors changed; peak CUDA memory was 3,982.0 MiB. On percent-change sample@4,
effective successful episodes improved 65/100 -> 72/100, while effective pass@4
remained 24/25. Greedy stayed 25/25. GSM8K regressed 21/200 -> 20/200 and
calculator accuracy 16/100 -> 15/100. Treat this as local sampling-stability
evidence only, not broad GRPO generalization.
A separately generated multi-step calculator curriculum v2 contains 10 explicit
family-level splits (72 train, 24 validation, 24 test) and never uses GSM8K test
content. A reference-program SFT ablation from native37 reduced train loss from
0.20533 to 0.000057, but validation stayed 12/24. Test moved 2/24 -> 12/24 only
because mixture concentration improved 0/12 -> 12/12, while overtime take-home
regressed 2/12 -> 0/12 and four tool executions failed. This is heterogeneous
skill transfer and a failed validation gate; retain native37 as the formal
branch and do not use the curriculum adapter as the next GRPO starting point.
An audit then found the v2 validation phrase `supplies ... liters per day` was
ambiguous relative to a subtracting reference expression. After correcting only
the validation wording to explicit draining, native37 scored 21/24. A 109-row
mixed replay run (37 native + 72 curriculum train rows) saved checkpoints at 20
and 40 steps; corrected validation selected step-20 at 23/24 versus 22/24 for
step-40. A newly frozen 36-task, three-family holdout moved 4/36 -> 6/36, while
the old percent-change family remained 25/25. Paired GSM8K moved 21/200 ->
22/200 (calculator 16 -> 18, no-tool 5 -> 4). These are weak, heterogeneous
positive results rather than evidence of stable broad improvement. Stop this
branch here and keep native37 as the conservative formal baseline; retain the
mixed step-20 adapter as an ablation candidate.
