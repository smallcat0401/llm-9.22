# V4 最终测试：起始策略补充对照

日期：2026-10-08

## 原因

首次冻结测试只比较了两个已经固定的 checkpoint：V4 SFT 与 V4 GRPO，遗漏了未加载任何 adapter 的 Qwen3.5-4B 起始策略。为了完整报告

`起始策略 -> SFT -> GRPO`

这条后训练实验线，现补充一次起始策略对照。

这不是新的模型选择实验，也不允许根据已经看到的 SFT/GRPO test 结果修改模型、数据、提示或解码参数。

## 固定条件

- 数据：冻结的 `data/generated/v4_test_v1.jsonl`，共 72 题；
- 起始策略：与 SFT、GRPO 相同的 Qwen3.5-4B checkpoint，不加载任何 adapter；
- seed：937；
- 解码：greedy；
- custom 协议：`max_new_tokens=256`、`max_model_turns=3`、`max_tool_calls=2`；
- native 协议：`max_new_tokens=128`；
- 每种协议只运行一次；
- 结果按总计、family 和 V3/V4 cohort 与已有 SFT、GRPO 结果配对报告。

## 解释边界

该对照是在 SFT/GRPO 冻结测试已经完成后补充的，必须在报告中如实标注为 post-hoc baseline addendum。补测完成后不得据此继续训练、调参、编辑测试题或选择性重跑失败题。

