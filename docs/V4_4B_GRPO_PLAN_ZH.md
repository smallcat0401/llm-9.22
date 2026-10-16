# V4 4B 正式 GRPO 计划

## 实验问题

在同一个 V4 epoch-3 SFT adapter 上继续进行一次 train-only、可验证奖励 GRPO，
是否能提高冻结 validation 上的单次作答表现，同时不增加协议错误或工具误用？

对照只有两支：

- **A：SFT**——`qwen3_5_4b_v4_mixed213_seed113/adapter`。
- **C：SFT + GRPO**——从同一个 A adapter 出发训练 53 步后的 adapter。

没有匹配算力的 continued-SFT B 组，因此最后只能写“GRPO 后 checkpoint 相对 SFT
checkpoint 的变化”，不能严格声称提升一定来自 RL 而非额外参数更新。

## 冻结训练设置

| 项目 | 数值 |
|---|---:|
| train prompts | 53 |
| family | 16 |
| 每组 generations | 8 |
| 正式训练步数 | 53（每道题一组，一轮） |
| seed | 727 |
| learning rate | `1e-6` |
| temperature / top-p | `1.4 / 0.97` |
| max completion length | 128 |

奖励为：

```text
1.00 × verified final numeric outcome
0.25 × bounded numeric closeness
0.10 × typed final format
0.05 × completed calculator trace
0.50 × calculator result matches ground truth
```

最终答案正确性仍是主奖励。辅助奖励全部有界，不能代替 verifier 通过。

53 道题中有 51 道也出现在 SFT 数据里，2 道未出现。这是有意的同题继续优化，
不是 unseen generalization。该事实由配置中的 `allow_sft_task_overlap=true` 和
`expected_sft_overlap_count=51` 明确记录；训练数据及 SFT 数据均由 SHA-256 固定。

## 执行顺序

1. 校验 GRPO、SFT 和 validation 文件哈希。
2. 运行 CPU 约束测试。
3. 对 SFT adapter 运行 custom-protocol 与 native-tool validation。
4. 用两道中等难度题、每题 8 个 generations 做 2-step GRPO smoke。
5. smoke 必须发生真实参数更新且没有 OOM/NaN，之后才运行 53-step 正式 GRPO。
6. 对 GRPO adapter 重跑同样两套 validation。
7. 返回 adapter、metrics、日志与 validation records；仍不运行 test。

## Validation 选择规则

主指标是项目原有 custom JSON 协议的 strict task success。选择顺序预先固定为：

1. strict task success 较高者；
2. 若相同，选择 verifier pass 较高者；
3. 若仍相同，选择 protocol error 较少者；
4. 若仍相同，保留较简单的 SFT checkpoint A。

TRL native-tool validation 是协议迁移诊断，不覆盖主选择规则。结果分析还必须从
records 按 family 统计 macro-family 表现，不能只看 64 题 pooled accuracy。

只有按上述规则选定 A 或 C 后，才能在冻结 V4 test 上运行一次最终评价。

## 停止条件

- smoke OOM、NaN/Inf、零 trainable parameters 或零参数变化：停止，不自行改超参数。
- 正式训练 reward variance 全为零：结果无有效 GRPO 学习信号，停止并保留日志。
- validation 显示协议错误或工具失败明显增加：按预注册规则保留 A。
- 禁止把 validation/test 加入 GRPO，禁止根据 test 修改奖励或训练题。
