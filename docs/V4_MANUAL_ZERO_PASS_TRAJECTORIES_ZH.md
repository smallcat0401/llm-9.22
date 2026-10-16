# V4 0/8 题手写轨迹候选（2026-10-06）

按照 [45 道失败题自审](V4_ZERO_PASS_AUDIT_ZH.md)，从后续 V4 **train** 题集中剔除四道题面不充分或业务语义不严谨的题：`public-midpoint_rate_application-000/003`、`public-multi_period_interest-002/004`。新版本 [158 道训练题](../data/generated/v4_train_tasks_curated_v2.jsonl)不包含它们；原 162 题文件、1296 条搜索结果和 pass@8 指标保留不变，供实验追溯。

对余下 **41 道 0/8 题**，逐题在 [构建代码](../scripts/build_v4_zero_pass_manual.py)里明确写了一条算术表达式。程序仅负责用安全计算器执行、按题目要求格式化答案、通过 verifier 检查，以及机械生成工具调用/观察/最终回答消息。表达式没有从任务的 `reference_expression` 字段自动读取。它们是 **Codex 助手编写的参考示范**，不是 4B 模型搜索出的轨迹，也不能声称已经经过用户人工确认。

下面每行都对应一条“assistant 调计算器 → tool 返回数值 → assistant 给最终数字”的轨迹。ID 省略统一前缀 `v4-review-`；最终答案由工具结果计算与四舍五入得到，而非直接复制 GT。

| 题 ID 后缀 | 手写计算器表达式 | 最终答案 |
| --- | --- | ---: |
| `curriculum-v2-sales-returns-003` | `(46 - 7) * 13 + 13 * 27 + 8` | 866 |
| `curriculum-v2-sales-returns-006` | `(43 - 8) * 12 + 18 * 26 + 41` | 929 |
| `curriculum-v2-sales-returns-010` | `(32 - 3) * 24 + 9 * 30 + 6` | 972 |
| `curriculum-v2-sales-returns-013` | `(38 - 8) * 10 + 7 * 23 + 34` | 495 |
| `curriculum-v2-required-score-007` | `5 * 69.6 - (71 + 59 + 62 + 73)` | 83 |
| `curriculum-v2-required-score-010` | `5 * 88.2 - (89 + 92 + 70 + 94)` | 96 |
| `curriculum-v2-required-score-014` | `5 * 73.2 - (83 + 61 + 64 + 63)` | 95 |
| `curriculum-v2-required-score-015` | `5 * 72.6 - (84 + 60 + 76 + 71)` | 72 |
| `curriculum-v2-cartons-damage-011` | `3 * 6 * 9 - 18 - 11` | 133 |
| `curriculum-v2-shared-bill-007` | `(12 * 40 + 80) / (12 - 3)` | 62.22 |
| `curriculum-v2-shared-bill-008` | `(14 * 41 + 50) / (14 - 2)` | 52.00 |
| `curriculum-v2-shared-bill-015` | `(8 * 25 + 45) / (8 - 3)` | 49.00 |
| `public-aggregate_percent_change-000` | `((3846 + 2709) - (4421 + 3518)) / (4421 + 3518) * 100` | −17.43 |
| `public-aggregate_percent_change-001` | `((781 + 3316) - (953 + 2763)) / (953 + 2763) * 100` | 10.25 |
| `public-aggregate_percent_change_with_loss-003` | `((734 + 0 + 1100 - 72) - (1137 + 206 + 531 - 206)) / (1137 + 206 + 531 - 206) * 100` | 5.64 |
| `public-average_growth_rate-000` | `((5697 - 7121) / 7121 + (6552 - 5697) / 5697) / 2 * 100` | −2.49 |
| `public-average_growth_rate-001` | `((2754 - 2203) / 2203 + (2479 - 2754) / 2754) / 2 * 100` | 7.51 |
| `public-average_growth_rate-002` | `((4097 - 4820) / 4820 + (3892 - 4097) / 4097) / 2 * 100` | −10.00 |
| `public-average_growth_rate-003` | `((8185 - 7441) / 7441 + (10640 - 8185) / 8185) / 2 * 100` | 20.00 |
| `public-average_growth_rate-004` | `((11271 - 8349) / 8349 + (9017 - 11271) / 11271) / 2 * 100` | 7.50 |
| `public-average_growth_rate-005` | `((7944 - 8635) / 8635 + (9692 - 7944) / 7944) / 2 * 100` | 7.00 |
| `public-derived_value_percent_change-002` | `((1038500 * 34.56) - (865417 * 23.67)) / (865417 * 23.67) * 100` | 75.21 |
| `public-derived_value_percent_change-004` | `((172963 * 76.16) - (262065 * 52.89)) / (262065 * 52.89) * 100` | −4.96 |
| `public-difference_of_averages-001` | `(2069 + 11523) / 2 - (16201 + 12190) / 2` | −7399.50 |
| `public-difference_of_averages-004` | `(19112 + 18547) / 2 - (9990 + 12854) / 2` | 7407.50 |
| `public-difference_of_averages-005` | `(3202 + 19603) / 2 - (18565 + 1985) / 2` | 1127.50 |
| `public-midpoint_rate_application-002` | `232 * (3.39 + 4.68) / 2 / 100` | 9.4 |
| `public-midpoint_rate_application-004` | `198 * (6.39 + 10.07) / 2 / 100` | 16.3 |
| `public-midpoint_rate_application-005` | `285 * (7.37 + 9.79) / 2 / 100` | 24.5 |
| `public-payout_ratio-000` | `58837 * 0.72 / 111691 * 100` | 37.93 |
| `public-payout_ratio-002` | `49938 * 0.31 / 30122 * 100` | 51.39 |
| `public-payout_ratio-004` | `26842 * 1.16 / 62728 * 100` | 49.64 |
| `public-ratio_of_aggregates-003` | `(4027 + 4423) / (6092 + 7872) * 100` | 60.51 |
| `public-signed_multi_value_average-000` | `(0 + 124 - 180 + 168) / 4` | 28.00 |
| `public-signed_multi_value_average-002` | `(-18 - 161 + 0 - 95) / 4` | −68.50 |
| `public-signed_multi_value_average-004` | `(-156 - 59 + 147 + 0) / 4` | −17.00 |
| `public-signed_multi_value_average-005` | `(-65 - 79 + 0 - 101) / 4` | −61.25 |
| `public-signed_percent_change-001` | `(280 - 162) / 162 * 100` | 72.84 |
| `public-signed_percent_change-003` | `(414 - 471) / 471 * 100` | −12.10 |
| `public-signed_percent_change-004` | `(64 - 71) / 71 * 100` | −9.86 |
| `public-signed_percent_change-005` | `(545 - 395) / 395 * 100` | 37.97 |

机器产物与状态：

- [含原英文题、算式、工具值和答案的逐题审核 JSONL](../data/review/v4_manual_zero_pass_v1/manual_program_review.jsonl)
- [41 条标准轨迹记录](../data/review/v4_manual_zero_pass_v1/assistant_authored_trajectories.jsonl)
- [41 条 custom-protocol SFT 样本](../data/review/v4_manual_zero_pass_v1/manual_sft_custom.jsonl)
- [214 条合并候选](../data/review/v4_manual_zero_pass_v1/v3_v4_search_plus_manual_sft_candidates.jsonl)：旧 58 + V4 搜索 115 + 本次参考示范 41；保留三种来源标签。
- [SHA-256、计数和排除清单](../artifacts/dataset_manifests/v4_manual_zero_pass_v1.json)

**当前仍非可直接训练的最终集**：新增 41 条标为 `pending_owner_review`，之前 115 条搜索轨迹的语义审核也尚未完成。正式训练前应先确认上表的题意与表达式；不要将这 41 条计为“模型自己搜索成功”。原 V4 搜索的 0/8 与 pass@8 结果不因人工示范出现而改变。

后续若比较训练效果，保留不含这 41 条的 173 条分支作对照（其中旧 V3 部分本来就有 26 条参考程序轨迹）；214 条分支进一步加入本次助手编写的参考轨迹。两者都不是“纯搜索蒸馏”，不能将全部收益归因于搜索轨迹。

代码层级：题目剔除、逐题表达式、train/validation 隔离、工具执行与 verifier 检查属于 `A - must hand-write`；机械打包和实验配置属于 `B - must understand and modify`。对应的新旧规则共 15 项单元测试通过。
