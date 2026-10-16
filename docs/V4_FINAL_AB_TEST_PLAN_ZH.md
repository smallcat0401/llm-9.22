# V4 4B SFT 与 GRPO 最终配对测试计划

## 目的

在尚未运行冻结 V4 test 的前提下，对两个已经固定、不会再更新的 checkpoint 做一次
最终配对评测：

- A：V4 SFT `qwen3_5_4b_v4_mixed213_seed113/adapter`；
- C：从 A 继续进行 53 步 GRPO 得到的
  `qwen3_5_4b_v4_outcome53_seed727/adapter`。

原计划依据 validation 只让一个 checkpoint 进入 test。为直接测量 GRPO 相对同一起点
SFT 的增量影响，在 test 仍未打开时，将最终评测修改为 A/C 各运行一次。这个修订发生
在 2026-10-08，且不能用于继续训练、调整 reward、修改题目或再次选择 checkpoint。

## 冻结设置

- 数据：`data/generated/v4_test_v1.jsonl`，72 道，仅 `test` split；
- 数据 SHA-256：
  `a0223c4517596007cf40e5cdd30e61e534f5f5dd4855af0f0042d106341be0bc`；
- seed：937；
- 解码：greedy；
- 两个 checkpoint 使用相同的模型、数据、prompt、token预算和评测代码；
- custom JSON 协议为主评测，native tool loop 为诊断评测；
- 每个 checkpoint、每个协议只运行一次。

## 报告规则

必须同时报告 A 和 C，不能只保留表现较好者。至少报告：

1. custom strict task success；
2. custom verifier pass、protocol error、tool selection；
3. native strict success、outcome pass、tool-result correctness、typed final；
4. pooled 结果、按 family 结果，以及原 V3 / V4 扩充 cohort 结果。

test 结果只能用于最终结论，不能用于后续训练、调参、改 reward、改数据或选择性重跑。

