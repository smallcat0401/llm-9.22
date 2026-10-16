# V4 训练题完整搜索结果（2026-10-06）

本次只对已审核的 **162 道 V4 train 题**运行 Qwen3.5-4B 起始策略的 Best-of-8 搜索。模型以 NF4 4-bit 加载，未加载训练 adapter，也没有更新参数。validation 和 test 均未参与搜索。配置见 [V4 搜索协议](V4_SEARCH_PROTOCOL_ZH.md)，原始机器指标见 `artifacts/metrics/qwen3_5_4b_v4_train_best_of_8_seed509.json`。

| 指标 | 实测结果 | 含义 |
| --- | ---: | --- |
| 搜索候选 | 1296 | 162 题 × 每题 8 次 |
| pass@1 | 53/162 = 32.7% | 每题第一次采样就答对 |
| pass@8 | 117/162 = 72.2% | 每题八次中至少一次答对 |
| 绝对 search gain | 39.5 个百分点 | pass@8 − pass@1；不是微调提升 |
| 成功候选轨迹 | 459/1296 | 同一题的多次成功分别计入此数 |
| 全部失败的题 | 45/162 | 八次均未答对，不直接编造成功 SFT 轨迹 |
| 可重放的计算器工具轨迹 | 115 道题各取一条 | 才是本次新增的 SFT 候选 |

预先设定的搜索门槛是绝对 gain 至少 10 个百分点，且至少 30 道题能在八次内成功；这次两项均通过。该门槛只说明有可利用的搜索空间，**不代表微调后效果已经提升**。

按来源看，自建派生题 84 道，首试成功 36 道、八次内成功 72 道、可用工具轨迹 70 条；公开种子关系的派生题 78 道，对应为 17、45、45。两道“答案正确但没有干净工具路径”的题来自 `curriculum-v2-required-score`：候选先发生计算器语法错误，再给出正确最终答案。严格答案指标计入它们，但工具轨迹 SFT 不计入。`v3-public-average_growth_rate-v1` 家族 6 道题在八次内全部失败；不能把总体 72.2% 误读为各题型都已解决。

## 合并方案与边界

旧 V3 mixed SFT 为 58 条：32 条搜索发现轨迹、26 条参考程序轨迹，其中 53 条含工具消息、5 条直接作答。本次新增 115 条是从 V4 搜索结果中每题取一条严格成功、工具观察有效且计算器结果可重放的轨迹。两批合并后是 **173 条候选 SFT 样本**，其中 168 条含工具消息、5 条直接作答。已检查两批之间没有相同 task ID 或完全相同的用户题干；合并仍保留每条数据的来源标签。

- V4 新增样本：`data/review/v4_search_sft_candidates_v0/v4_new_sft_candidates.jsonl`
- V3+V4 合并候选：`data/review/v4_search_sft_candidates_v0/v3_plus_v4_sft_candidates.jsonl`
- 筛选计数、各 family 统计与输入/输出 SHA-256：`data/review/v4_search_sft_candidates_v0/manifest.json`
- 完整搜索原始记录：`outputs/search/qwen3_5_4b_v4_train_best_of_8_seed509/candidates.jsonl`

这些新增路径通过了结构、结果和计算器重放检查，但**尚需人工审查表达式是否真正符合题意**，所以 manifest 标为 `pending_semantic_path_review`、`train_ready=false`。不要直接把 173 条称作已审核训练集，更不要称作已经完成的新训练。V4-only 115 条与 V3+V4 173 条可作为后续对照；正式 4B SFT 应在合适 GPU 上进行，之后仅用 validation 选择 checkpoint，冻结 test 不参与选择。

复现搜索与候选打包：

```powershell
$env:PYTHONPATH='src'
.venv\Scripts\python.exe -u -m verifiable_posttraining.cli search-eval --model-id 'Qwen/Qwen3.5-4B' --cache-dir 'D:\huggingface-cache' --load-in-4bit --dataset 'data/generated/v4_train_task_candidates_approved_v1.jsonl' --split train --kind calculator --samples-per-task 8 --seed 509 --max-new-tokens 256 --max-model-turns 3 --max-tool-calls 2 --temperature 0.7 --top-p 0.9 --top-k 20 --min-search-gain 0.10 --min-verified-tasks 30 --run-id 'qwen3_5_4b_v4_train_best_of_8_seed509' --output-dir 'outputs/search/qwen3_5_4b_v4_train_best_of_8_seed509'
.venv\Scripts\python.exe scripts/package_v4_search_sft_candidates.py
```

代码层级：筛选中的 train-only、family 隔离、严格结果验证和计算器重放属于 `A - must hand-write`；搜索运行与数据打包属于 `B - must understand and modify`；路径与 CLI 包装属于 `C - use correctly`。新增筛选及现有 SFT 数据规则共 11 项单元测试通过。
