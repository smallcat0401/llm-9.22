# V4 搜索 45 道 0/8 训练题自审（2026-10-06）

审查范围：`outputs/search/qwen3_5_4b_v4_train_best_of_8_seed509/candidates.jsonl` 中八次采样均未通过严格 verifier 的 45 道 V4 **train** 题。逐题对照了英文原题、表格、GT、参数与全部 360 条模型输出；再用不依赖存储 `reference_expression` 的各题型运算，从参数独立重算并按要求的小数位取整。45 道的重算值均与 GT 相符。这里的“正确”仅指算数与题面直接给出的数量关系；金融业务术语另作审查。

总体结论：**没有发现数值 GT 算错**。但 4 道题有应先改题面的语义风险：两道将普通“付款额”直接视作全部为利息，两道将掉期组合的名义本金乘利率中点直接称为利息费用。后一判断也与 [美国 CFTC 对利率互换的说明](https://www.cftc.gov/MarketReports/SwapsReports/DataDictionary/index.htm)一致：互换涉及支付与收取两个利率现金流，只有名义本金和一个利率区间不能确定净费用。这 4 道 GT 都是给定参考假设下的正确乘积，不能当作题面充分推出的、无争议的财务答案。另有 1 道跨年债务存量的汇总比率在数学上明确可算，但金融语义不够自然，建议后续润色。不要因 0/8 自动认定其余 41 道题有错。

所有候选仍按原始严格协议计分：45 道均为 0/8。不过其中 **8 道至少一次得到与 GT 一致的计算器结果**，却没有有效的最终输出；45 道中 19 道出现过协议错误，共 54 条协议错误候选。因此 0/8 混有推理失败、工具路径失败和结构化输出失败，不能笼统说成“看不懂题”。

以下 ID 均省略公共前缀 `v4-review-`。✅ 表示未发现题目或 GT 的实质问题；⚠️ 表示题面需修订。证据列是输出中的代表性错误，不代表每次采样都相同。

| 题 ID 后缀 | GT | 审核 | 8 次输出中的关键证据 |
| --- | ---: | --- | --- |
| `curriculum-v2-sales-returns-003` | 866 | ✅ | 多次把另收的 8 美元服务费减掉，得到 850。 |
| `curriculum-v2-sales-returns-006` | 929 | ✅ | 4 次算式和工具值都是 929，最终 JSON 的数字后多了引号而被拒。 |
| `curriculum-v2-sales-returns-010` | 972 | ✅ | 2 次工具值 972，最终 JSON 格式错误。 |
| `curriculum-v2-sales-returns-013` | 495 | ✅ | 把另收的 34 美元服务费减掉，得到 427。 |
| `curriculum-v2-required-score-007` | 83 | ✅ | 把带未知数和等号的方程发给只支持算术的计算器，或列式错误。 |
| `curriculum-v2-required-score-010` | 96 | ✅ | 多次输出目标总分 441，而不是减去已知四次分数。 |
| `curriculum-v2-required-score-014` | 95 | ✅ | 有一次文字推导出 95，却未按唯一 JSON 对象协议提交；其他候选列式错误。 |
| `curriculum-v2-required-score-015` | 72 | ✅ | 把已知分数与目标总分相加、再取平均，未解出第五次分数。 |
| `curriculum-v2-cartons-damage-011` | 133 | ✅ | 6 次计算器值都是 133，但最终 JSON 均格式错误。 |
| `curriculum-v2-shared-bill-007` | 62.22 | ✅ | 有效付款者是 12−3=9 人；输出曾把总额除以 12 或 3。 |
| `curriculum-v2-shared-bill-008` | 52.00 | ✅ | 应由 14−2=12 人分摊，输出常除以 14。 |
| `curriculum-v2-shared-bill-015` | 49.00 | ✅ | 应由 8−3=5 人分摊，输出常除以 8。 |
| `public-aggregate_percent_change-000` | −17.43 | ✅ | 曾正确算出约 −17.4329%，但后续格式错误；另一候选误用两年合计作分母。 |
| `public-aggregate_percent_change-001` | 10.25 | ✅ | 题目只选 North+Central；候选把 South 也纳入，得到 13.73%。 |
| `public-aggregate_percent_change_with_loss-003` | 5.64 | ✅ | 2022 合计 1668，2023 合计 1762；八次均直接给负数，未见有效工具算式。 |
| `public-average_growth_rate-000` | −2.49 | ✅ | 一次工具结果约 −0.02495 是小数比率，最终未转为 −2.49%。 |
| `public-average_growth_rate-001` | 7.51 | ✅ | 八次均直接给错误数字；题目已明确不是 CAGR。 |
| `public-average_growth_rate-002` | −10.00 | ✅ | 一次工具值约 −0.1000，最终报 −0.10，漏乘 100。 |
| `public-average_growth_rate-003` | 20.00 | ✅ | 八次均直接答错；两段年增长率分别约 10% 与 30%。 |
| `public-average_growth_rate-004` | 7.50 | ✅ | 多次正确算出小数比率约 0.075，却报 0.08 而非 7.50%。 |
| `public-average_growth_rate-005` | 7.00 | ✅ | 一次正确算出比率约 0.0700，最终报 0.07 而非 7.00%。 |
| `public-derived_value_percent_change-002` | 75.21 | ✅ | 需比较两年各自“数量×每份公允价值”的总值；八次直接答案均不符。 |
| `public-derived_value_percent_change-004` | −4.96 | ✅ | 一次工具值约 −4.9619%，最终 JSON 格式错误。 |
| `public-difference_of_averages-001` | −7399.50 | ✅ | 加工业务均值减云业务均值；八次直接答案均不符。 |
| `public-difference_of_averages-004` | 7407.50 | ✅ | 目标应为正；八次直接给负值。 |
| `public-difference_of_averages-005` | 1127.50 | ✅ | 后两年均值减前两年均值；多数直接输出负值。 |
| `public-midpoint_rate_application-000` | 6.5 | ⚠️ | `Swap portfolio` 的名义本金及利率范围不足以定义真实年度利息费用；算式 119×5.45%≈6.5 仅在附加假设下成立。候选直接答错。 |
| `public-midpoint_rate_application-002` | 9.4 | ✅ | Term loan、本金与利率区间中点的估算关系清楚；八次直接答案均不符。 |
| `public-midpoint_rate_application-003` | 19.9 | ⚠️ | 同样使用 `Swap portfolio` 的不严谨业务表述。候选有把利率区间差当中点、或漏除 100。 |
| `public-midpoint_rate_application-004` | 16.3 | ✅ | Revolving facility 的简单估算关系清楚；八次直接答案均不符。 |
| `public-midpoint_rate_application-005` | 24.5 | ✅ | 多次工具结果 2445.3，恰为漏除 100 的数量级错误。 |
| `public-multi_period_interest-002` | 63.0 | ⚠️ | 表头只说 `Payment amount`，未明确每笔付款全是利息；GT 以 6.3×2×5 计算。模型常答 31.5，另外忽略了每年两次。 |
| `public-multi_period_interest-004` | 81.6 | ⚠️ | 同一付款性质缺失；GT 以 5.1×4×4 计算。模型常答 20.4，忽略了四年期限。 |
| `public-payout_ratio-000` | 37.93 | ✅ | 千股×每股股利得到千美元股利，再除同单位净利润；八次答案均不符。 |
| `public-payout_ratio-002` | 51.39 | ✅ | 曾将净利润除股数，未正确形成股利总额/净利润。 |
| `public-payout_ratio-004` | 49.64 | ✅ | 八次答案集中约 1.99，未按股利支付率公式计算。 |
| `public-ratio_of_aggregates-003` | 60.51 | ✅* | 两年数值汇总后的比率为 (4027+4423)/(6092+7872)。债务是存量，跨年相加作“合并占比”在财务语义上略别扭；不构成数值 GT 错，但建议未来换成流量指标。 |
| `public-signed_multi_value_average-000` | 28.00 | ✅ | 括号为负、破折号为零；八次直接输出均不符。 |
| `public-signed_multi_value_average-002` | −68.50 | ✅ | 多次把括号中的负数当正数，输出 +68.50。 |
| `public-signed_multi_value_average-004` | −17.00 | ✅ | 两次工具值 −17 正确，但最终 JSON 格式错误；其他候选忽略负号。 |
| `public-signed_multi_value_average-005` | −61.25 | ✅ | 三次工具值 −61.25 正确，但最终 JSON 格式错误；另有候选取绝对值。 |
| `public-signed_percent_change-001` | 72.84 | ✅ | 绝对费用由 162 增至 280，应报正增长；八次直接答案不符。 |
| `public-signed_percent_change-003` | −12.10 | ✅ | 一次工具算出约 −12.1019%，最终 JSON 格式错误。 |
| `public-signed_percent_change-004` | −9.86 | ✅ | 多次用 (71−64)/71 得 +9.86%，把下降的符号反了。 |
| `public-signed_percent_change-005` | 37.97 | ✅ | 绝对费用由 395 增至 545，应报正增长；多数直接输出负值。 |

建议处理：先**不要**把 45 道全部当作“模型不会的高质量难题”或直接写人工轨迹。将 4 道 ⚠️ 题另存修订版本、明确每笔付款为利息并把掉期换为确实可用“本金×利率”估算的工具；不要把完整公式写入题目。修订后重审 GT，再决定是否重新搜索。其余题可以保留原题；协议错误应单独分析，不能靠改 GT 修复。任何修订都不要覆盖本次冻结搜索记录。
