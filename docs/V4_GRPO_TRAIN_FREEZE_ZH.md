# V4 4B GRPO 训练题冻结说明

## 结论

2026-10-08 将 V4 的正式 4B GRPO 训练提示冻结为 **53 道 train-only
calculator 题**。这一步只是固定训练输入，还没有进行 GRPO 参数更新，也没有产生
GRPO 后模型效果。

冻结文件：

- `data/generated/v4_grpo_train_outcome_variance_seed719_v1.jsonl`
- `artifacts/dataset_manifests/v4_grpo_train_outcome_variance_seed719_v1.json`

## 为什么是 53 道

V4 epoch-3 SFT adapter 在 158 道审核后的训练题上做了固定探测：每题以
temperature 1.4、seed 719 采样 8 次，共产生 1264 条轨迹。探测是
inference-only，`model_parameters_updated=false`。

结果如下：

| 分组 | 题数 | 是否进入正式 GRPO |
|---|---:|---|
| 8 次全部答对 | 103 | 否；组内 outcome reward 相同 |
| 8 次有对有错 | 53 | 是；存在 verified outcome reward 方差 |
| 8 次全部答错 | 2 | 否；组内没有 verifier 通过的正例 |

另有 3 道 8/8 答对题只有格式或辅助 reward 波动。加上两道 0/8 题，共 5 道题
虽然总 reward 有方差，但最终答案正确性没有方差，因此没有纳入第一轮正式 GRPO。

冻结标准只有一个：

> 在 seed 719 的八次采样中，至少一次最终数值通过 verifier，且至少一次未通过。

没有按 validation/test 表现选题，没有对 family 人为限额，也没有手工挑选看起来更好
的轨迹。

## 难度分布

53 道题中，每题八次采样的正确次数分布为：

| 正确次数 | 题数 |
|---:|---:|
| 1/8 | 1 |
| 2/8 | 6 |
| 3/8 | 4 |
| 4/8 | 5 |
| 5/8 | 6 |
| 6/8 | 12 |
| 7/8 | 19 |

这些题覆盖 16 个 train family。`required-score` 有 9 道，`shared-bill` 有
11 道，因此这是一套按当前模型弱点自然形成的训练集，不是 family 均匀抽样。正式
报告必须同时给出 validation/test 的总体指标和 macro-family 指标，避免大 family
掩盖小 family 的退化。

## 隔离边界

- 冻结题全部来自 `data/generated/v4_train_tasks_curated_v2.jsonl`。
- 输出中每道题均为 `split=train`、`kind=calculator`，只允许 calculator。
- 训练 family 与冻结的 V4 validation/test family 无交集。
- validation 和 test 没有参与 prompt 选择。
- test 仍然密封；GRPO checkpoint 只能用 validation 选择。

## 两道 0/8 题

两道 0/8 题的题意和 GT 经复核没有发现错误：

1. `required-score-002` 的正确关系是
   `79.6*5-(76+80+79+88)=75`；模型常误算当前四项平均数。
2. `aggregate_percent_change_with_loss-002` 的正确关系是先分别汇总两年，
   再计算 `(1541-1351)/1351*100=14.06`；模型常漏项或直接计算差额。

它们是真实弱点，但 8 条轨迹内没有 verifier 通过的正例。为了让首轮 GRPO 的主要
outcome reward 有明确组内对比，本版本不纳入。后续若要使用，应单独声明为
closeness-only ablation，不能与本次正式结果混写。

## 复现

```bash
python -m scripts.freeze_v4_grpo_train
```

脚本会核对原始 train 数据和 probe metrics 的 SHA-256、探测计数、任务 ID、split、
工具限制及 validation/test family 隔离。已有冻结文件内容若不同，脚本会拒绝覆盖。
