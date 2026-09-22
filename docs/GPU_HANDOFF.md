# RTX 4060 handoff checklist

## Before installing anything

Record the following in a local note. Do not commit hostnames, usernames, serial
numbers, or other identifying information.

```powershell
nvidia-smi
Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory
Get-PSDrive -PSProvider FileSystem
wsl --status
```

If Linux is already available, also record:

```bash
uname -a
python3 --version
df -h
```

## Repository workflow

```bash
git clone https://github.com/smallcat0401/llm-post-training.git
cd llm-post-training
git switch -c gpu-spike
```

Run the dependency-free checks before installing GPU packages:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m verifiable_posttraining.cli doctor
PYTHONPATH=src python -m verifiable_posttraining.cli schema-demo
```

## GPU environment principles

- Prefer WSL2 Ubuntu or native Linux.
- Start with Transformers/PyTorch SDPA. Do not spend Day 1 compiling
  FlashAttention.
- Do not install vLLM until basic Transformers generation works.
- Use a dedicated virtual environment.
- After the first successful run, freeze exact installed versions into a lock or
  requirements snapshot and commit that text file.
- Model caches and checkpoints must remain outside Git.

## Account safety

- Use a private repository.
- Never place tokens in shell history or source files.
- Use environment variables or the Hugging Face login helper.
- Sign out and remove stored credentials before returning the computer.

## Before access ends

- Push every source/config change.
- Record the final commit hash.
- Back up adapters, checkpoints, raw trajectories, metrics, and logs separately.
- Confirm the repository is reproducible from a fresh clone.
- Write `GPU_RUN_REPORT.md` with commands, observed VRAM, runtime, failures, and
  actual results.

