# Qwen3.5-4B Search-Gap Gate on RTX 4060

## Purpose

This is an inference-only go/no-go screen. It does not train the 4B model.
Formal 4B QLoRA SFT is allowed only when the predeclared search gate passes.

The primary gate is:

```text
absolute pass@N - pass@1 >= 0.10
and enough distinct tasks have at least one verified success
```

The screen uses only the official GSM8K `train` source. The existing GSM8K
`test` subset remains evaluation-only and must never be searched or trained on.

## Required local files

```text
D:\huggingface-cache\... Qwen/Qwen3.5-4B snapshot
data/external/gsm8k/train.jsonl
```

The CLI always uses `local_files_only=True`; running the screen cannot silently
start a model download.

## Build the frozen train-only screen

```powershell
$env:PYTHONPATH = "src"

python -m verifiable_posttraining.cli build-public-search-screen `
  --source data/external/gsm8k/train.jsonl `
  --output data/generated/gsm8k_search_screen_seed71.jsonl `
  --sample-size 100 `
  --seed 71
```

Each source problem produces a no-tool condition and a calculator-available
condition. Both are `train` rows with explicit source provenance.

## Stage A: compatibility probe

Run only ten tasks per condition and four samples per task. This checks model
loading, memory, latency, parsing, and verifier compatibility; it is not the
formal gate.

```powershell
python -m verifiable_posttraining.cli search-eval `
  --model-id Qwen/Qwen3.5-4B `
  --cache-dir D:\huggingface-cache `
  --load-in-4bit `
  --dataset data/generated/gsm8k_search_screen_seed71.jsonl `
  --split train `
  --limit-per-kind 10 `
  --samples-per-task 4 `
  --temperature 0.7 `
  --top-p 0.9 `
  --top-k 20 `
  --max-new-tokens 256 `
  --max-model-turns 3 `
  --max-tool-calls 2 `
  --min-search-gain 0.10 `
  --min-verified-tasks 5 `
  --run-id qwen3.5-4b-search-gap-probe-seed71 `
  --output-dir outputs/search/qwen3_5_4b_search_gap_probe_seed71
```

Stop if the model cannot remain inside the available memory, generation is
operationally unstable, or the verifier/parser rejects nearly every completion.

## Stage B: formal local gate

Only after Stage A is healthy, run 50 tasks per condition with eight samples.
This is 100 tasks and 800 candidate episodes, so it may take hours on a laptop.

```powershell
python -m verifiable_posttraining.cli search-eval `
  --model-id Qwen/Qwen3.5-4B `
  --cache-dir D:\huggingface-cache `
  --load-in-4bit `
  --dataset data/generated/gsm8k_search_screen_seed71.jsonl `
  --split train `
  --limit-per-kind 50 `
  --samples-per-task 8 `
  --temperature 0.7 `
  --top-p 0.9 `
  --top-k 20 `
  --max-new-tokens 256 `
  --max-model-turns 3 `
  --max-tool-calls 2 `
  --min-search-gain 0.10 `
  --min-verified-tasks 30 `
  --run-id qwen3.5-4b-search-gap-formal-seed71 `
  --output-dir outputs/search/qwen3_5_4b_search_gap_formal_seed71
```

The metrics file reports empirical pass@1, pass@2, pass@4, pass@8, verified
candidate yield, per-kind results, and the gate decision. Do not change the
threshold after observing the result.

## Decision

- `search_gate.passed = true`: curate verified trajectories, inspect failure
  composition, estimate rented-GPU SFT cost, and prepare the 4B QLoRA config.
- `search_gate.passed = false`: do not rent a GPU for this task recipe. Preserve
  the negative result and screen a different verifiable task family.
- Never use the GSM8K test set to decide whether to train.

## Measured result (seed 71)

The local Stage B run completed on the RTX 4060 with 800 candidate episodes.
The preregistered gate passed:

| Strict trajectory metric | pass@1 | pass@8 | Gain |
|---|---:|---:|---:|
| All condition-specific tasks (100) | 10/100 | 43/100 | +33 pp |
| No-tool condition (50) | 3/50 | 14/50 | +22 pp |
| Calculator-available condition (50) | 7/50 | 29/50 | +44 pp |

The prefix curve was 10/100 at one sample, 19/100 at two, 31/100 at four,
and 43/100 at eight. The run produced 100 strictly verified candidates and 43
selected trajectories (one per solved condition-specific task). Twenty selected
trajectories contain executed calculator calls.

SFT path-alignment is stricter than generic search selection. Re-auditing all
800 candidates found 72 aligned successes (24 no-tool and 48 calculator) across
40 distinct tasks (14 no-tool and 26 calculator). The final curation command
must select from all candidates, not blindly reuse the 43 generic selections,
because nine selected calculator-condition answers did not actually call the
tool and some later samples provide better aligned demonstrations.

An outcome-only audit found 14/100 -> 48/100. The five-task difference at
pass@8 comes from numerically correct answers emitted through malformed protocol
messages. Those rows remain outcome-correct diagnostics but are excluded from
the verified training set. This distinction prevents a correct number inside an
invalid action from being mislabeled as a valid tool-use trajectory.

Because the 100 tasks are paired conditions over 50 source questions, a second
diagnostic collapses each pair: either-condition strict success moves from 9/50
to 32/50. This is not substituted for the preregistered gate; it is reported to
make the effective number of independent source problems explicit.

Runtime was 1,086.765 seconds after a 32.622-second model load, with 3,329.5 MiB
peak CUDA memory. The tracked summary is
`artifacts/metrics/qwen3_5_4b_search_gap_formal_seed71.json`; raw outputs remain
under the Git-ignored `outputs/search/qwen3_5_4b_search_gap_formal_seed71/`.

The gate authorizes preparation of a rented-GPU 4B QLoRA SFT experiment. It is
evidence that searchable correct trajectories exist, not yet evidence that SFT
will improve pass@1.

## Train-only expansion

Two additional source-disjoint batches were run before renting a GPU. Batch 2
used the remaining 50 source questions in the seed-71 screen; batch 3 used 50
questions from a seed-97 screen that explicitly excludes all 100 seed-71 source
questions.

| Batch | Strict pass@1 | Strict pass@8 | Gain | Path-aligned SFT rows |
|---|---:|---:|---:|---:|
| Seed 71, first 50 sources | 10/100 | 43/100 | +33 pp | 40 |
| Seed 73, next 50 sources | 19/100 | 42/100 | +23 pp | 32 |
| Seed 97, disjoint 50 sources | 14/100 | 46/100 | +32 pp | 40 |
| Aggregate | 43/300 | 131/300 | +29.3 pp | 112 |

The aggregate covers 150 distinct GSM8K train source questions, 300 paired
condition-specific tasks, and 2,400 candidate episodes. Calculator pass@1 ->
pass@8 is 29/150 -> 88/150; no-tool is 14/150 -> 43/150. All three batches
independently pass the search gate, so the original signal is reproducible
across disjoint source questions.

The merged SFT dataset contains 112 examples: 43 no-tool and 69 calculator
examples, with tool messages present in all 69 calculator examples. Its SHA-256
is `7195515c94f5dc46616a33331147c7c9337953f77bf6e4b8e3d48b384c509b58`.
The tracked aggregate report is
`artifacts/metrics/qwen3_5_4b_search_expansion_aggregate.json`.

## Frozen external baseline and SFT handoff

Before any 4B training, the NF4 starting policy was evaluated once on the
existing frozen 100-question GSM8K test subset under paired no-tool and
calculator-available conditions. Strict success was 38/200 (19%): 11/100
no-tool and 27/100 calculator-condition tasks. Outcome verification passed
46/200, while 22/200 episodes ended in protocol errors. Only 12 tool calls were
recorded, so calculator-condition success must not be misreported as 27 genuine
tool-use successes.

This frozen baseline is stored in
`artifacts/metrics/qwen3_5_4b_gsm8k_external_baseline_seed107.json`. The first
formal rental-GPU configuration is
`configs/sft_qwen3_5_4b_verified112_seed113.toml`. It saves adapters after one,
two, and three dataset passes. Choose among these checkpoints using a separate
train-source validation screen; report the frozen test comparison only after
checkpoint selection is fixed.

The validation screen is now frozen at
`data/generated/gsm8k_train_validation_seed131.jsonl` (SHA-256
`0f955420159fd4d58e5c1a961fe6aa4f53f4ebbbec6f7bb783ac23c890fb5c07`).
Its 50 source questions exclude all 200 questions in the two search-screen
pools. The starting-policy validation baseline is 23/100 strict successes:
8/50 no-tool and 15/50 calculator-condition, with 10 protocol errors and seven
recorded tool calls.

Checkpoint selection is preregistered as follows:

1. A checkpoint is eligible only if no-tool validation is at least 7/50 and
   protocol errors are at most 10/100.
2. Among eligible checkpoints, maximize total strict validation success.
3. Break ties by calculator-condition strict success, then fewer protocol
   errors, then the earlier checkpoint.
4. After selection, evaluate exactly that checkpoint on the frozen test set.

For a clear positive final result, target at least 48/200 strict test successes
(a +5 percentage-point absolute gain over 38/200), no-tool at least 11/100, and
protocol errors no greater than 22/200. Smaller changes remain reportable but
must be described as weak or inconclusive rather than a demonstrated gain.
