# RTX 4060 GPU run report

Date: 2026-09-23 to 2026-09-24  
GPU: NVIDIA GeForce RTX 4060  
Starting policy: `Qwen/Qwen3.5-0.8B`  
Seed: `7`

All numbers below are measured local runs. Adapter/checkpoint weights live under
Git-ignored `outputs/`; small configs, metrics, and this report are intended for Git.

## Environment

- Python 3.11.9
- PyTorch 2.11.0 + CUDA 12.8
- Transformers 5.17.0
- Accelerate 1.14.0
- PEFT 0.21.0
- TRL 1.13.0
- Datasets 5.0.1
- bitsandbytes 0.50.2

`pip check` reported no broken requirements. Missing Triton, `causal_conv1d`,
and `flash-linear-attention` produced performance warnings only; the supported
PyTorch fallback kernels were used.

## Search and SFT data

- Train Best-of-4: 150 tasks, 600 candidates.
- pass@1: 28/150 (18.67%).
- pass@4: 81/150 (54.00%).
- Path-aligned SFT set: 80 verified train-only trajectories.
- Composition: 13 no-tool, 37 calculator, 30 SQL; 67 contain tool messages.

## QLoRA SFT

The first 18-example smoke used learning rate `5e-4` and failed its gate:
mean loss changed from 0.14408 to 0.14606. It is retained as a failed run.

The corrected smoke used learning rate `1e-4`, batch size 2, accumulation 3,
and 180 micro-steps:

- mean loss: 0.13824 -> 0.00781 (94.35% reduction);
- trainable parameters: 5,411,328;
- peak allocated CUDA memory: 4,058 MiB;
- elapsed time: 162.3 seconds.

The historical run was configured for 80 examples, learning rate `1e-4`, batch
size 2, accumulation 4, and 160 micro-steps. A later audit found that a shrinking
queue termination bug selected only 41 rows (13 no-tool, 14 calculator, 14 SQL):

- mean loss: 0.14559 -> 0.02215 (84.79% reduction);
- trainable parameters: 5,411,328;
- peak allocated CUDA memory: 4,058 MiB;
- elapsed time: 104.2 seconds;
- adapter SHA-256: `25D2CEDC787232B19032F8A3C7C8A34CA0620C7D7CD36D11B7CE033FC2F45D26`.

The metrics above remain valid for the 41-row historical adapter, but it must
not be described as an 80-row training run. The selector was fixed and a new
full80 run confirmed 80/80 selected rows (13 no-tool, 37 calculator, 30 SQL):

- mean loss: 0.14333 -> 0.03013 (78.98% reduction);
- trainable parameters: 5,411,328;
- peak allocated CUDA memory: 4,057.5 MiB;
- elapsed time: 112.2 seconds;
- historical v3 result under the superseded `1e-6` percent tolerance: 53/75;
- corrected-tolerance offline rescore: 75/75 (25 no-tool, 25 calculator, 25 SQL).

Assistant-only labels were constructed from verified chat-template prefix
boundaries. System, user, tool, padding, and assistant-header tokens use label
`-100`. Over-length examples fail instead of silently truncating targets.

## Frozen external evaluation

The external set contains 100 deterministically selected GSM8K test questions,
each paired into no-tool and calculator-available conditions (200 tasks total).
It was never used for SFT or GRPO training. Both formal rows below use greedy
decoding, seed 7, 256 new tokens, five model turns, and four tool calls. The
post-SFT row is the historical audited 41-row adapter; corrected-full80 external
evaluation has not yet been run.

| Metric | Starting policy | Post-SFT |
|---|---:|---:|
| Strict task success | 0/200 (0%) | 24/200 (12%) |
| Verifier pass | 4/200 (2%) | 24/200 (12%) |
| Protocol errors | 200/200 (100%) | 10/200 (5%) |
| Tool-selection accuracy | 50% | 95% |
| No-tool strict success | 0/100 | 5/100 |
| Calculator strict success | 0/100 | 19/100 |

The 10 remaining protocol failures were malformed calculator calls missing a
closing JSON brace. The result supports protocol/tool-use distillation, but the
low outcome accuracy shows that mathematical reasoning remains the bottleneck.

## Family-held-out internal test

The 75-task synthetic test has one unseen family per task kind (25 each).

Tables in the historical sections below retain the verifier used at run time.
The later percent-change audit showed that `1e-6` wrongly rejects conventional
two-decimal percentages; do not compare those historical totals with the
corrected-tolerance results in the final corrected branch.

| Metric | Starting policy | Post-SFT | Post-GRPO mini |
|---|---:|---:|---:|
| Strict task success | 18/75 (24.0%) | 28/75 (37.3%) | 29/75 (38.7%) |
| Protocol errors | 32/75 | 0/75 | 0/75 |
| No-tool success | 0/25 | 24/25 | 25/25 |
| Calculator success | 1/25 | 4/25 | 4/25 |
| SQL success | 17/25 | 0/25 | 0/25 |

The aggregate gain hides a severe SQL regression. All 25 post-SFT SQL calls
were executable but selected raw `units` rows instead of `SUM(units)`; the
model then emitted the row list as a scalar answer. The held-out prompt says
"Find units sold" rather than explicitly "total units across all regions",
which is a dataset ambiguity worth fixing in a future version, but this frozen
v1 result must remain reported as a failure.

## GRPO / RLVR smoke

The reward components are logged separately:

- numeric outcome: 1 only for a typed final answer accepted by the verifier;
- typed final format: 1 for a valid typed-final action, weighted by 0.1.

The two-step smoke observed one zero-variance group followed by one group with
one correct answer out of four. It changed 372 LoRA tensors; maximum absolute
parameter delta was `1.2207e-4`; peak allocated CUDA memory was 2,113 MiB.

A 20-step mini run changed the same 372 tensors and used 2,154 MiB peak memory,
but only 1/20 groups had non-zero reward variance. The other groups were all
correct or all wrong and therefore produced zero group-relative advantage.
The post-GRPO `+1/75` internal result is an observation, not evidence of a
stable RL improvement.

### Prompt v3 and dense-reward GRPO ablation

The frozen v1 result above is retained as a negative result. Prompt protocol
`v3-sql-scalar-aggregate` changes only the SQL instruction: the final answer
must be scalar, and multi-row contributions must be aggregated with
`SUM`/`COUNT`/`AVG`. With the original SFT adapter this restored held-out SQL
from 0/25 under v1 to 24/25 under v3.

Screening 50 train/no-tool tasks with Best-of-8 found four tasks absent from
the SFT set with mixed strict outcomes (1/8, 2/8, 3/8, and 5/8). Using only
these tasks with the original binary reward still produced non-zero group
variance on just 1/20 steps. This failed ablation is retained in
`qwen3_5_0_8b_grpo_curriculum_20step_seed17.json`.

A second ablation used 16 completions per group, temperature 1.8, learning
rate `1e-6`, and a bounded numeric-closeness auxiliary reward weighted by
0.25. Strict verifier success remains the primary reward; malformed outputs
receive zero closeness reward. This run achieved non-zero group reward variance
on 12/12 steps, changed 372 trainable tensors, and used 6,584.8 MiB peak CUDA
memory.

The controlled seed-17 internal comparison is:

| Metric | SFT v3 | Dense GRPO v3 |
|---|---:|---:|
| Strict task success | 52/75 (69.33%) | 53/75 (70.67%) |
| Protocol errors | 0/75 | 0/75 |
| No-tool success | 24/25 | 24/25 |
| Calculator success | 4/25 | 4/25 |
| SQL success | 24/25 | 25/25 |

The `+1/75` difference is a positive diagnostic and shows no measured
regression, but it is too small to establish stable RL generalization. It is
also on SQL even though GRPO trained only on no-tool tasks, so multi-seed
evaluation is required before attributing the difference to RL.

Two additional independent GRPO training seeds were then run with identical
data and hyperparameters:

| Training seed | Non-zero variance steps | Strict test success | By kind (no-tool / calculator / SQL) |
|---:|---:|---:|---:|
| 17 | 12/12 | 53/75 | 24 / 4 / 25 |
| 23 | 12/12 | 53/75 | 24 / 4 / 25 |
| 41 | 12/12 | 53/75 | 24 / 4 / 25 |

The SFT control is 52/75 (24 / 4 / 24). Thus the dense-reward configuration
reproduced both effective training signal and the same greedy test result in
3/3 training seeds. Because all runs use the same four-prompt curriculum and
the only test difference is one SQL task outside that curriculum, this remains
a small-scale repeatability result rather than evidence of broad RL
generalization.

### Broader no-tool GRPO run

The next run expanded the curriculum from four hand-screened tasks to all 37
train/no-tool tasks absent from the SFT dataset. It used one optimizer step per
prompt, 16 completions per group, training seed 29, and the same dense reward
weights and sampling configuration.

- non-zero group reward variance: 37/37 steps;
- changed trainable tensors: 372;
- peak allocated CUDA memory: 6,584.8 MiB;
- training time: 479.1 seconds;
- held-out greedy result: 53/75 (24 no-tool, 4 calculator, 25 SQL);
- protocol errors: 0/75.

Expanding no-tool training coverage preserved the reproducible 53/75 result
but did not improve no-tool or calculator accuracy beyond the four-prompt
curriculum. This identifies task coverage as the next bottleneck: calculator
and tool-use GRPO need an environment-aware rollout path before further
no-tool training is justified.

### Native calculator tool-use GRPO

**2026-09-24 audit correction:** the original native evaluator used document
EOS 248044 instead of chat EOS 248046. The response parser could replace a
valid answer with trailing `<|endoftext|>`. The native-v1 artifacts are
historical faulty-evaluator outputs and must not support model-capability
conclusions. See `artifacts/representative_trajectories/native_parser_audit.json`
for the exact token-level reproduction. Corrected v2 evaluations retain raw
tokens and score numeric outcomes independently of tool-assisted success.

The environment-aware path now uses TRL's native structured tool loop. The
safe calculator accepts one arithmetic expression, and rewards separately
track tool-trace validity, numeric outcome, numeric closeness, and typed-final
format. The formal local run used 13 train/calculator prompts absent from SFT,
8 completions per group, temperature 1.4, learning rate `1e-6`, and one epoch.
This historical GRPO branch starts from the audited 41-row SFT adapter.

- non-zero group reward variance: 13/13 steps;
- changed trainable tensors: 372;
- peak allocated CUDA memory: 5,137.4 MiB;
- training time: 238.9 seconds;
- custom-protocol v3 test: 53/75 (24 no-tool, 4 calculator, 25 SQL).

Because the original v3 evaluator uses a custom JSON action protocol, a second
held-out evaluator was added for Transformers-native structured tool calls. It
requires exactly one executed calculator call and a correct final numeric
answer. The test family is percent change; training calculator families were
average and discount.

| Corrected native-v2 held-out metric | SFT control | Post tool-GRPO |
|---|---:|---:|
| Greedy tool calls | 0/25 | 0/25 |
| Greedy numeric outcome success | 2/25 | 2/25 |
| Greedy tool-assisted success | 0/25 | 0/25 |
| Sampled tool calls (`temperature=1.4`, 100 episodes) | 19/100 | 19/100 |
| Successful tool executions | 17/100 | 18/100 |
| Sampled numeric outcome successes | 8/100 | 8/100 |
| Numeric outcome pass@4 | 3/25 | 3/25 |
| Tool-assisted pass@4 | 1/25 | 1/25 |

The training run is valid as a pipeline test: every group supplied reward
variance and real structured tool calls were executed. It is nevertheless a
controlled negative result. The adapter did not move tool calling into greedy
behavior and produced the same corrected outcome and tool-assisted pass@4 as
the SFT control. Inspection of the raw-token traces shows limited but real
native capability: direct numeric answers and one complete successful tool
episode. Other samples include incorrect percent-change expressions and wrong
final answers. Broader calculator-family coverage and stronger
tool-result-to-final supervision should be tested at 0.8B before attributing a
benefit to calculator GRPO.

### Corrected full80 and native calculator SFT

The fixed selector enabled a controlled SFT comparison from the true full80
adapter. All 37 verified calculator trajectories were replayed into Qwen-native
structured conversations. Conversion requires the stored observation, safe
calculator replay, final answer, and hidden train-task answer to agree. No test
row or generated teacher answer is used.

The native continuation selected 37/37 rows, used learning rate `5e-5` for 80
micro-steps, reduced native-data loss from 0.03948 to 0.01301 (67.05%), used
4,459.8 MiB peak CUDA memory, and took 123.5 seconds.

| Corrected held-out metric | Full80 control | Full80 -> native37 |
|---|---:|---:|
| Greedy native tool calls | 0/25 | 25/25 |
| Greedy effective tool-path success | 0/25 | 25/25 |
| Sampled native tool calls | 7/100 | 100/100 |
| Successful sampled tool executions | 5/100 | 97/100 |
| Sampled effective tool-path pass@4 | 2/25 | 24/25 |
| Custom-protocol v3 corrected rescore | 75/75 | 75/75 |
| v3 by kind (no-tool / calculator / SQL) | 25 / 25 / 25 | 25 / 25 / 25 |
| GSM8K paired v3 success | 20/200 | 21/200 |
| GSM8K by kind (no-tool / calculator) | 4 / 16 | 5 / 16 |
| GSM8K protocol errors | 12/200 | 11/200 |

The first report used the global `1e-6` tolerance and incorrectly rejected 22
correctly rounded two-decimal percentage answers in the native37 greedy run.
The table above uses the corrected family tolerance (`0.005`) and an offline
rescore of the unchanged saved generations. Native trajectory SFT reliably
teaches structured calculator use without a measured regression on the existing
75-task suite. In the native37 sampled records, 32/100 episodes still have a
wrong expression result. The matched external comparison is effectively flat
and GSM8K calculator success remains 16/100 for both adapters, so broader
formula selection and mathematical reasoning remain the limiting factors.

### Result-aware calculator GRPO from native37

The new `calculator_result` reward checks the calculator's returned scalar
against the hidden target before considering the final answer. A 13-step run
from native37 used weight `0.5` for this signal, 8 generations per group, and
the 13 remaining train/calculator tasks absent from SFT:

- non-zero group reward variance: 6/13 steps;
- changed trainable tensors: 372;
- peak allocated CUDA memory: 3,982.0 MiB;
- training time: 133.1 seconds.

| Evaluation | Native37 control | Post-GRPO seed47 |
|---|---:|---:|
| Native greedy effective success | 25/25 | 25/25 |
| Native sampled effective episodes | 65/100 | 72/100 |
| Native sampled effective pass@4 | 24/25 | 24/25 |
| Native sampled numeric outcome episodes | 70/100 | 80/100 |
| Native sampled numeric outcome pass@4 | 24/25 | 25/25 |
| Corrected internal v3 | 75/75 | 75/75 |
| GSM8K paired | 21/200 | 20/200 |
| GSM8K calculator | 16/100 | 15/100 |
| GSM8K protocol errors | 11/200 | 10/200 |

The sampled in-family stability gain is measurable, but pass@4 is unchanged and
external accuracy is slightly worse. This run does not establish broad GRPO
generalization. The 7/13 zero-variance groups also show that the remaining
synthetic train prompts are too easy for efficient further RL.

### Multi-step calculator curriculum v2

An independent deterministic curriculum was added without consulting GSM8K
test content. Ten families are explicitly isolated into 72 train, 24 validation,
and 24 test tasks. The SFT derivative uses replayed synthetic reference programs,
so this run is an oracle/reference-program ablation rather than search
distillation. An easier v1 screen scored 24/24 zero-shot and was rejected before
training.

Starting from native37, the 72-row v2 SFT run used 120 steps at `5e-5`:

- mean loss: 0.20533 -> 0.000057 (99.97% reduction);
- peak allocated CUDA memory: 4,857.2 MiB;
- elapsed time: 364.8 seconds.

| Family-isolated evaluation | Native37 | Post-curriculum SFT |
|---|---:|---:|
| Validation total | 12/24 | 12/24 |
| Test total | 2/24 | 12/24 |
| Test overtime take-home | 2/12 | 0/12 |
| Test mixture concentration | 0/12 | 12/12 |
| Test tool execution failures | 0/24 | 4/24 |

The original validation wording was later found to be internally ambiguous:
`supplies` implied adding water while the reference expression subtracted it.
Those 12/24 results are retained but superseded. With the wording corrected to
explicitly say `drained`, native37 scores 21/24.

### Mixed replay and frozen final holdout

To reduce forgetting, the 37 native trajectories were mixed with the 72
curriculum train rows. A 40-step run at `2e-5` saved a step-20 checkpoint. Loss
fell 0.14302 -> 0.04368, peak allocation was 4,857.2 MiB, and elapsed time was
74.8 seconds. Corrected validation selected step-20 without consulting test:

| Corrected validation | Native37 | Step 20 | Step 40 |
|---|---:|---:|---:|
| Total | 21/24 | **23/24** | 22/24 |

A new 36-task, three-family holdout was then frozen and evaluated exactly once
per compared checkpoint (SHA-256 `35fea2c4...924de84`):

| Fresh holdout | Native37 | Mixed step-20 |
|---|---:|---:|
| Tiered utility | 2/12 | 5/12 |
| Event net cost | 0/12 | 1/12 |
| Service/tax/tip | 2/12 | 0/12 |
| Total | 4/36 | **6/36** |
| Tool execution failures | 3 | 5 |

The old percent-change check stayed 25/25 for both, so replay prevented measured
forgetting on that family. On paired GSM8K, native37 -> step-20 changed total
accuracy 21/200 -> 22/200, calculator 16/100 -> 18/100, no-tool 5/100 -> 4/100,
and protocol errors 11 -> 8. The gain is small and heterogeneous, while most
failures remain wrong expressions (25/36 on the new holdout and 73/100 on the
GSM8K calculator condition). This is weak positive ablation evidence, not a
stable broad improvement; no further training is justified from this result.

## Reproduction commands

```powershell
$env:PYTHONPATH = "src"

python -m verifiable_posttraining.cli sft-overfit-smoke `
  --config configs/sft_tiny_overfit_v2.toml `
  --cache-dir D:\huggingface-cache

python -m verifiable_posttraining.cli sft-train `
  --config configs/sft_full80_corrected_seed7.toml `
  --cache-dir D:\huggingface-cache

python -m verifiable_posttraining.cli build-native-calculator-sft-data

python -m verifiable_posttraining.cli sft-train `
  --config configs/sft_native_calculator_full37_from_full80_seed43.toml `
  --cache-dir D:\huggingface-cache

python -m verifiable_posttraining.cli grpo-smoke `
  --config configs/grpo_smoke.toml `
  --cache-dir D:\huggingface-cache

python -m verifiable_posttraining.cli grpo-smoke `
  --config configs/grpo_mini_seed7.toml `
  --cache-dir D:\huggingface-cache

python -m verifiable_posttraining.cli grpo-smoke `
  --config configs/grpo_dense_ablation_seed17.toml `
  --cache-dir D:\huggingface-cache

python -m verifiable_posttraining.cli grpo-smoke `
  --config configs/grpo_calculator_tool_seed35.toml `
  --cache-dir D:\huggingface-cache

python -m verifiable_posttraining.cli grpo-smoke `
  --config configs/grpo_calculator_result_from_native37_seed47.toml `
  --cache-dir D:\huggingface-cache

python -m verifiable_posttraining.native_tool_evaluation `
  --model-id Qwen/Qwen3.5-0.8B `
  --cache-dir D:\huggingface-cache `
  --adapter-path outputs/grpo/qwen3_5_0_8b_calculator_tool_13step_seed35/adapter `
  --dataset data/generated/pilot_tasks.jsonl `
  --output-dir outputs/eval/native-calculator-post-grpo `
  --run-id native-calculator-post-grpo `
  --num-samples 4 --temperature 1.4 --top-p 0.97
```

## Decision

The RTX 4060 has validated the complete 0.8B pipeline, including real QLoRA,
native tool SFT, result-aware GRPO, and external evaluation. The corrected
native37 branch reaches 25/25 greedy effective tool paths, while result-aware
GRPO improves sampled effective episodes from 65/100 to 72/100. However, the
internal 75-task set is saturated and GSM8K slightly regresses from 21/200 to
20/200. The later mixed-replay curriculum ablation passes its corrected
validation gate and moves a fresh holdout 4/36 -> 6/36 plus GSM8K 21/200 ->
22/200, but the gains are small and family-dependent. A stable broad SFT or RL
gain is therefore not established. Further work should improve semantic
expression construction and replicate gains across seeds before spending money
on formal 4B work. Full 4B GRPO remains out of local hardware scope.

## Qwen3.5-4B local search gate

The later inference-only 4B gate used 50 official GSM8K train questions, each
rendered under no-tool and calculator-available conditions. Eight samples per
condition produced 800 candidate episodes. Strict trajectory pass@1 was 10/100
and pass@8 was 43/100, a measured +33 percentage-point search gap. The
calculator condition moved 7/50 -> 29/50 and the no-tool condition moved 3/50
-> 14/50. This passed the preregistered +10-point / 30-solved-task gate.

The run selected 43 verified trajectories, including 20 with executed tool
calls. A separate outcome-only audit measured 14/100 -> 48/100; 30 candidate
episodes had the correct numeric answer but an invalid protocol message and are
not eligible for SFT. Peak CUDA memory was 3,329.5 MiB and search time was
1,086.765 seconds. This justifies preparing formal 4B QLoRA SFT on rented
hardware, while full 4B GRPO remains out of scope until SFT improves a frozen
evaluation set.

Path-quality re-selection over all candidates yields 40 SFT-eligible tasks:
14 clean no-tool demonstrations and 26 calculator demonstrations with executed,
successful tool calls. This is the training-set target; the generic set of 43
search selections is retained for search accounting but must not be used as-is
for SFT.

Before renting hardware, two more source-disjoint search batches expanded the
evidence and training pool. Across all three batches, strict pass@1 was 43/300
and pass@8 was 131/300 (+29.3 percentage points). Each batch independently
passed the gate with gains of +33, +23, and +32 points. Path-aligned curation
produced 112 unique train examples: 43 no-tool and 69 calculator trajectories,
all 69 with actual tool messages. This is now the frozen 4B QLoRA input; further
train-data search is not required before the first controlled SFT run.

The pre-training 4B baseline on the frozen paired GSM8K test subset is 38/200
strict successes: 11/100 no-tool and 27/100 calculator-condition. Outcome-only
verification is 46/200, protocol errors are 22/200, and only 12 tool calls were
recorded. The post-SFT claim must therefore report strict success, outcome-only
success, protocol errors, and actual tool-use metrics separately. The formal
config uses 112 examples for three passes and saves epoch-1 and epoch-2 adapters
before the final epoch-3 adapter.

A separate 50-question, paired train-source validation screen excludes every
source question in both search pools. Its starting-policy baseline is 23/100
strict successes (8 no-tool, 15 calculator-condition), 27/100 outcome passes,
10 protocol errors, and seven recorded tool calls. Checkpoint selection uses
this validation set only; the frozen test remains sealed until a checkpoint is
selected.
