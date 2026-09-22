# Verifiable Reasoning & Tool-Use Post-training

## 项目简介

本项目研究一个核心问题：

> 能否把测试时搜索（test-time search）偶尔发现的正确推理轨迹与工具调用轨迹，通过监督微调（SFT）和可验证奖励强化学习（RLVR / GRPO），进一步内化为模型更加稳定的单次推理能力？

项目的重点不是单纯“把模型训练起来”，而是建立一套完整、可复现、可验证的 LLM Post-training 实验流程。

---

## 实验主线

```text
starting policy
      ↓
best-of-N test-time search
      ↓
verified trajectories
      ↓
trajectory SFT
      ↓
GRPO / RLVR
      ↓
controlled evaluation
      ↓
ablation & error analysis
```

整体流程可以理解为：

```text
搜索
→ 验证
→ 构造训练轨迹
→ SFT
→ GRPO
→ 统一评测
→ 消融与错误分析
```

---

## 模型范围

项目使用两个不同规模的模型承担不同角色。

### 调试 / 开发模型

```text
Qwen/Qwen3.5-0.8B
```

主要用于：

- Baseline Evaluation；
- Best-of-N Search；
- 数据 pipeline 验证；
- SFT；
- SFT Evaluation；
- Reward Function 验证；
- GRPO smoke test；
- Logging / Checkpoint / Evaluation 验证。

0.8B 阶段的主要目标不是追求最高性能，而是：

> 验证整个 Post-training Pipeline 能否正确运行。

因此：

```text
0.8B = development model
     = pipeline validation
```

---

### 正式实验模型

```text
Qwen/Qwen3.5-4B
```

在 0.8B pipeline 稳定后，用于：

- Formal Baseline Evaluation；
- Best-of-N Search；
- Verified Trajectory Collection；
- Formal SFT；
- Post-SFT Evaluation；
- Controlled Comparison；
- Ablation；
- Error Analysis。

4B 阶段主要用于回答：

> 在更有能力的模型上，这套 Post-training 方法是否仍然能够产生稳定、可解释的提升？

因此：

```text
4B = formal experiment model
   = result validation
```

---
## 本地计算环境与实验范围

当前主要开发与实验环境为本地 Windows PC：

- GPU：NVIDIA GeForce RTX 4060
- 系统内存：16 GB
- 操作系统：Windows

受本地 GPU 显存与系统内存限制，本项目采用“小模型完成完整流程验证、较大模型承担正式实验”的计算策略。

### Qwen3.5-0.8B

计划在本地完成：

```text
✓ Baseline Evaluation
✓ Best-of-N Search
✓ SFT
✓ SFT Evaluation
✓ Reward Validation
✓ GRPO Smoke Test
✓ GRPO Evaluation
```

0.8B 用于验证完整训练流程。

### Qwen3.5-4B

计划完成：

```text
✓ Quantized Inference
✓ Best-of-N Search
✓ Formal Baseline Evaluation
✓ LoRA / QLoRA SFT
✓ Formal Evaluation
✓ Ablation
✓ Error Analysis
```

### 4B GRPO

正式 4B GRPO 不要求在 RTX 4060 上强行运行。

GRPO 首先使用 0.8B 验证：

```text
multi-response generation
→ reward computation
→ group-relative advantage
→ policy update
→ checkpoint
→ evaluation
```

如果后续获得额外 GPU 或云端算力，再考虑扩展到 4B GRPO。

详细实验设计见：

```text
docs/EXPERIMENT_DESIGN.md
```

---

## 项目结构

```text
.
├── configs/
│   └── models.toml
│
├── docs/
│   ├── EXPERIMENT_DESIGN.md
│   ├── FOUR_DAY_GPU_SPRINT.md
│   ├── GPU_HANDOFF.md
│   └── LEARNING_MAP.md
│
├── src/
│   └── verifiable_posttraining/
│       ├── __init__.py
│       ├── cli.py
│       ├── doctor.py
│       └── schemas.py
│
├── tests/
│   └── test_schemas.py
│
├── .env.example
├── .gitignore
├── AGENTS.md
├── PROJECT_CONTEXT.md
├── pyproject.toml
└── README.md
```

---

## 文档说明

### `docs/EXPERIMENT_DESIGN.md`

记录：

- 为什么使用 0.8B + 4B；
- Development Model 与 Formal Model 的分工；
- Search → SFT → GRPO 的实验逻辑；
- 计算资源约束；
- Ablation 设计；
- Evaluation 原则。

---

### `docs/GPU_HANDOFF.md`

记录 GPU 环境下的：

- 环境准备；
- 模型加载；
- 依赖安装；
- 实验运行方式；
- 常见问题。

---

### `docs/FOUR_DAY_GPU_SPRINT.md`

记录短期 GPU 实验计划与任务安排。

---

### `docs/LEARNING_MAP.md`

按照学习重要程度划分代码：

```text
A：必须掌握，并能独立写出核心逻辑

B：必须读懂，并能够修改

C：能够正确调用即可
```

---

### `PROJECT_CONTEXT.md`

记录项目整体背景、研究目标与当前进度，方便开发过程中快速恢复上下文。

---

### `AGENTS.md`

记录 Codex / Agent 在当前仓库中的开发规范与约束。

---

## 快速检查

当前工程底座无需安装完整训练依赖即可进行基础检查。

### Windows PowerShell

```powershell
$env:PYTHONPATH = "src"

python -m unittest discover -s tests -v

python -m verifiable_posttraining.cli doctor

python -m verifiable_posttraining.cli schema-demo
```

### Linux / WSL

```bash
PYTHONPATH=src python -m unittest discover -s tests -v

PYTHONPATH=src python -m verifiable_posttraining.cli doctor

PYTHONPATH=src python -m verifiable_posttraining.cli schema-demo
```

---

## 学习目标

这个项目不仅要求“代码能跑”，还要求能够真正解释核心 Post-training 流程。

重点掌握：

```text
数据如何构造
↓
为什么需要 Search
↓
如何筛选 Verified Trajectories
↓
SFT 学习了什么
↓
Reward 如何设计
↓
GRPO 如何利用 Reward 更新模型
↓
Evaluation 如何判断模型真的提升
```

详细学习要求见：

```text
docs/LEARNING_MAP.md
```

---

## 实验原则

正式实验应尽量保证：

```text
统一任务协议
统一 Evaluation 协议
受控变量
固定随机种子
保存原始输出
保存失败样例
可复现
```

最终不只关注一个 Accuracy 数字，还需要分析：

- 模型是否真的提升；
- 提升来自 Search、SFT 还是 GRPO；
- 哪类问题仍然失败；
- Reward 是否存在漏洞；
- 是否出现格式正确但推理错误；
- 是否出现过拟合或 reward hacking。

---

