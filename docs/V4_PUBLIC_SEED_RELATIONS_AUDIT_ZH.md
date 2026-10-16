# V4 公开表格种子关系扩充：中文审核稿

> 模型输入仍是英文。中文题意和中文表格只用于人工审核。

## 本批边界

- 原公开种子关系 family：13 个。
- 每个 family 新生成 6 道合成表格题，共 78 道。
- 保留的是数量关系，不复制、改写原公开数据表中的公司数值。
- 本审核快照中的任务保持 `review_status=pending`、`training_eligible=false`，
  用于保留批准前状态。
- 本批只属于 train family，没有使用 V3 validation/test 题生成变体。

## 审核记录

- 所有 78 道题已由项目所有者于 2026-10-06 审核通过。
- 批准后的任务另存为 `data/generated/v4_public_seed_relations_approved_v1.jsonl`。
- 批准只允许进入轨迹收集；本文件不是 SFT 数据。

## 审核重点

1. 表头、题意和公式引用的行列是否一致。
2. 括号、横线、百分比和正负方向是否明确。
3. 问题是否要求推导，但没有把计算步骤直接泄露在题面中。
4. 参考公式仅供离线校验，不会放入模型看到的用户问题。

## 加权平均

- Family：`v3-public-weighted_average-v1`
- 母题：`v3-public-cb26a8ffa95b-arithmetic`、`v3-public-ea79960b2b5e-arithmetic-revised-v2`
- 保留关系：数量×单价求和，再除以总数量。

### 1. `v4-review-public-weighted_average-000`

- 中文题意：按一月、二月的采购数量加权，所选月份的加权平均单价是多少？保留两位小数。
- 英文题意：Taking the units purchased in January and February into account, what was the unit-count-weighted average price across the selected months? Round to two decimals.
- 中文审核表：

| 期间 | 采购数量 | 平均单价 |
| --- | --- | --- |
| 一月 | 228,247 | $182.86 |
| 二月 | 164,962 | $140.80 |
| 三月 | 594,368 | $137.14 |

- 参考公式：`(228247*182.86+164962*140.80)/(228247+164962)`
- GT：`165.21`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-public-weighted_average-001`

- 中文题意：以一月、三月的采购数量作为权重，计算这些月份的加权平均采购价格，保留两位小数。
- 英文题意：Use the January and March purchase counts as weights. Calculate the weighted average purchase price for those months, rounded to two decimals.
- 中文审核表：

| 期间 | 采购数量 | 平均单价 |
| --- | --- | --- |
| 一月 | 619,690 | $43.64 |
| 二月 | 208,876 | $35.78 |
| 三月 | 788,402 | $38.40 |

- 参考公式：`(619690*43.64+788402*38.40)/(619690+788402)`
- GT：`40.71`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-public-weighted_average-002`

- 中文题意：按二月、三月的采购数量加权，所选月份的加权平均单价是多少？保留两位小数。
- 英文题意：Taking the units purchased in February and March into account, what was the unit-count-weighted average price across the selected months? Round to two decimals.
- 中文审核表：

| 期间 | 采购数量 | 平均单价 |
| --- | --- | --- |
| 一月 | 281,217 | $135.96 |
| 二月 | 311,658 | $115.57 |
| 三月 | 302,133 | $146.84 |

- 参考公式：`(311658*115.57+302133*146.84)/(311658+302133)`
- GT：`130.96`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-public-weighted_average-003`

- 中文题意：以一月、二月、三月的采购数量作为权重，计算这些月份的加权平均采购价格，保留两位小数。
- 英文题意：Use the January, February, and March purchase counts as weights. Calculate the weighted average purchase price for those months, rounded to two decimals.
- 中文审核表：

| 期间 | 采购数量 | 平均单价 |
| --- | --- | --- |
| 一月 | 251,514 | $117.22 |
| 二月 | 159,978 | $93.78 |
| 三月 | 621,382 | $132.46 |

- 参考公式：`(251514*117.22+159978*93.78+621382*132.46)/(251514+159978+621382)`
- GT：`122.76`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-public-weighted_average-004`

- 中文题意：按一月、三月的采购数量加权，所选月份的加权平均单价是多少？保留两位小数。
- 英文题意：Taking the units purchased in January and March into account, what was the unit-count-weighted average price across the selected months? Round to two decimals.
- 中文审核表：

| 期间 | 采购数量 | 平均单价 |
| --- | --- | --- |
| 一月 | 395,229 | $80.52 |
| 二月 | 896,117 | $88.57 |
| 三月 | 403,044 | $90.18 |

- 参考公式：`(395229*80.52+403044*90.18)/(395229+403044)`
- GT：`85.40`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-public-weighted_average-005`

- 中文题意：以一月、二月、三月的采购数量作为权重，计算这些月份的加权平均采购价格，保留两位小数。
- 英文题意：Use the January, February, and March purchase counts as weights. Calculate the weighted average purchase price for those months, rounded to two decimals.
- 中文审核表：

| 期间 | 采购数量 | 平均单价 |
| --- | --- | --- |
| 一月 | 534,219 | $228.98 |
| 二月 | 571,166 | $208.37 |
| 三月 | 788,286 | $247.30 |

- 参考公式：`(534219*228.98+571166*208.37+788286*247.30)/(534219+571166+788286)`
- GT：`230.39`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

## 汇总后百分比变化

- Family：`v3-public-aggregate_percent_change-v1`
- 母题：`v3-public-f2f32edba913-arithmetic`、`v3-public-e511f3abfa5e-arithmetic`、`v3-public-550b417fd1d0-arithmetic`
- 保留关系：先分别汇总指定行的新旧数值，再计算汇总值的百分比变化。

### 1. `v4-review-public-aggregate_percent_change-000`

- 中文题意：北区、南区的合计收入从 2022 年到 2023 年变化了百分之多少？保留两位小数。
- 英文题意：What was the percentage change in the combined revenue of the North and South divisions from 2022 to 2023? Round to two decimals.
- 中文审核表：

| 部门 | 2023 年收入 | 2022 年收入 |
| --- | --- | --- |
| 北区 | 3,846 | 4,421 |
| 南区 | 2,709 | 3,518 |
| 中区 | 1,062 | 900 |

- 参考公式：`((3846+2709)-(4421+3518))/(4421+3518)*100`
- GT：`-17.43`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-public-aggregate_percent_change-001`

- 中文题意：将北区、中区作为一个整体，其收入从 2022 年到 2023 年变化了百分之多少？保留两位小数。
- 英文题意：For the North and Central divisions taken together, how did revenue change in percentage terms from 2022 to 2023? Round to two decimals.
- 中文审核表：

| 部门 | 2023 年收入 | 2022 年收入 |
| --- | --- | --- |
| 北区 | 781 | 953 |
| 南区 | 1,711 | 1,391 |
| 中区 | 3,316 | 2,763 |

- 参考公式：`((781+3316)-(953+2763))/(953+2763)*100`
- GT：`10.25`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-public-aggregate_percent_change-002`

- 中文题意：南区、中区的合计收入从 2022 年到 2023 年变化了百分之多少？保留两位小数。
- 英文题意：What was the percentage change in the combined revenue of the South and Central divisions from 2022 to 2023? Round to two decimals.
- 中文审核表：

| 部门 | 2023 年收入 | 2022 年收入 |
| --- | --- | --- |
| 北区 | 2,663 | 2,833 |
| 南区 | 2,731 | 1,845 |
| 中区 | 3,053 | 2,313 |

- 参考公式：`((2731+3053)-(1845+2313))/(1845+2313)*100`
- GT：`39.11`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-public-aggregate_percent_change-003`

- 中文题意：将北区、南区、中区作为一个整体，其收入从 2022 年到 2023 年变化了百分之多少？保留两位小数。
- 英文题意：For the North, South, and Central divisions taken together, how did revenue change in percentage terms from 2022 to 2023? Round to two decimals.
- 中文审核表：

| 部门 | 2023 年收入 | 2022 年收入 |
| --- | --- | --- |
| 北区 | 3,928 | 4,365 |
| 南区 | 2,906 | 2,018 |
| 中区 | 3,997 | 4,594 |

- 参考公式：`((3928+2906+3997)-(4365+2018+4594))/(4365+2018+4594)*100`
- GT：`-1.33`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-public-aggregate_percent_change-004`

- 中文题意：南区、中区的合计收入从 2022 年到 2023 年变化了百分之多少？保留两位小数。
- 英文题意：What was the percentage change in the combined revenue of the South and Central divisions from 2022 to 2023? Round to two decimals.
- 中文审核表：

| 部门 | 2023 年收入 | 2022 年收入 |
| --- | --- | --- |
| 北区 | 5,856 | 4,436 |
| 南区 | 483 | 549 |
| 中区 | 3,652 | 3,069 |

- 参考公式：`((483+3652)-(549+3069))/(549+3069)*100`
- GT：`14.29`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-public-aggregate_percent_change-005`

- 中文题意：将北区、南区、中区作为一个整体，其收入从 2022 年到 2023 年变化了百分之多少？保留两位小数。
- 英文题意：For the North, South, and Central divisions taken together, how did revenue change in percentage terms from 2022 to 2023? Round to two decimals.
- 中文审核表：

| 部门 | 2023 年收入 | 2022 年收入 |
| --- | --- | --- |
| 北区 | 3,750 | 3,409 |
| 南区 | 3,778 | 2,718 |
| 中区 | 1,435 | 2,208 |

- 参考公式：`((3750+3778+1435)-(3409+2718+2208))/(3409+2718+2208)*100`
- GT：`7.53`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

## 包含亏损和零值的汇总变化

- Family：`v3-public-aggregate_percent_change_with_loss-v1`
- 母题：`v3-public-c84b259d3bfe-arithmetic`
- 保留关系：括号按负数、横线按零处理，汇总全部行后计算百分比变化。

### 1. `v4-review-public-aggregate_percent_change_with_loss-000`

- 中文题意：括号表示经营亏损，横线表示零。汇总四个部门后，总经营利润从 2022 年到 2023 年变化了百分之多少？保留两位小数。
- 英文题意：Parentheses denote operating losses and the dash means zero. After aggregating all four divisions, what was the percentage change in total operating profit from 2022 to 2023? Round to two decimals.
- 中文审核表：

| 部门 | 2023 年经营利润 | 2022 年经营利润 |
| --- | --- | --- |
| 消费业务 | (86) | (106) |
| 工业业务 | 964 | 842 |
| 国际业务 | — | 240 |
| 传统业务 | 466 | 834 |

- 参考公式：`((-86+964+0+466)-(-106+842+240+834))/(-106+842+240+834)*100`
- GT：`-25.75`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-public-aggregate_percent_change_with_loss-001`

- 中文题意：将括号内数字视为亏损、横线视为零。将四个部门作为一个整体，经营利润从 2022 年到 2023 年的带方向百分比变化是多少？保留两位小数。
- 英文题意：Treat parenthesized figures as losses and the dash as zero. Considering all four divisions together, what was the signed percentage change in operating profit from 2022 to 2023? Round to two decimals.
- 中文审核表：

| 部门 | 2023 年经营利润 | 2022 年经营利润 |
| --- | --- | --- |
| 消费业务 | 331 | 575 |
| 工业业务 | (87) | (194) |
| 国际业务 | 744 | 912 |
| 传统业务 | — | 396 |

- 参考公式：`((331-87+744+0)-(575-194+912+396))/(575-194+912+396)*100`
- GT：`-41.50`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-public-aggregate_percent_change_with_loss-002`

- 中文题意：括号表示经营亏损，横线表示零。汇总四个部门后，总经营利润从 2022 年到 2023 年变化了百分之多少？保留两位小数。
- 英文题意：Parentheses denote operating losses and the dash means zero. After aggregating all four divisions, what was the percentage change in total operating profit from 2022 to 2023? Round to two decimals.
- 中文审核表：

| 部门 | 2023 年经营利润 | 2022 年经营利润 |
| --- | --- | --- |
| 消费业务 | — | 153 |
| 工业业务 | 938 | 817 |
| 国际业务 | (81) | (236) |
| 传统业务 | 684 | 617 |

- 参考公式：`((0+938-81+684)-(153+817-236+617))/(153+817-236+617)*100`
- GT：`14.06`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-public-aggregate_percent_change_with_loss-003`

- 中文题意：将括号内数字视为亏损、横线视为零。将四个部门作为一个整体，经营利润从 2022 年到 2023 年的带方向百分比变化是多少？保留两位小数。
- 英文题意：Treat parenthesized figures as losses and the dash as zero. Considering all four divisions together, what was the signed percentage change in operating profit from 2022 to 2023? Round to two decimals.
- 中文审核表：

| 部门 | 2023 年经营利润 | 2022 年经营利润 |
| --- | --- | --- |
| 消费业务 | 734 | 1,137 |
| 工业业务 | — | 206 |
| 国际业务 | 1,100 | 531 |
| 传统业务 | (72) | (206) |

- 参考公式：`((734+0+1100-72)-(1137+206+531-206))/(1137+206+531-206)*100`
- GT：`5.64`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-public-aggregate_percent_change_with_loss-004`

- 中文题意：括号表示经营亏损，横线表示零。汇总四个部门后，总经营利润从 2022 年到 2023 年变化了百分之多少？保留两位小数。
- 英文题意：Parentheses denote operating losses and the dash means zero. After aggregating all four divisions, what was the percentage change in total operating profit from 2022 to 2023? Round to two decimals.
- 中文审核表：

| 部门 | 2023 年经营利润 | 2022 年经营利润 |
| --- | --- | --- |
| 消费业务 | (75) | (183) |
| 工业业务 | 370 | 398 |
| 国际业务 | — | 288 |
| 传统业务 | 1,076 | 689 |

- 参考公式：`((-75+370+0+1076)-(-183+398+288+689))/(-183+398+288+689)*100`
- GT：`15.02`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-public-aggregate_percent_change_with_loss-005`

- 中文题意：将括号内数字视为亏损、横线视为零。将四个部门作为一个整体，经营利润从 2022 年到 2023 年的带方向百分比变化是多少？保留两位小数。
- 英文题意：Treat parenthesized figures as losses and the dash as zero. Considering all four divisions together, what was the signed percentage change in operating profit from 2022 to 2023? Round to two decimals.
- 中文审核表：

| 部门 | 2023 年经营利润 | 2022 年经营利润 |
| --- | --- | --- |
| 消费业务 | 1,089 | 1,023 |
| 工业业务 | (180) | (255) |
| 国际业务 | 1,024 | 869 |
| 传统业务 | — | 357 |

- 参考公式：`((1089-180+1024+0)-(1023-255+869+357))/(1023-255+869+357)*100`
- GT：`-3.06`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

## 两个同比变化率的算术平均

- Family：`v3-public-average_growth_rate-v1`
- 母题：`v3-public-564f2d6051c0-arithmetic-revised-v2`、`v3-public-4b50d974aae5-arithmetic`、`v3-public-13b99cafff24-arithmetic-revised-v2`、`v3-public-776305a10cc6-arithmetic-revised-v2`
- 保留关系：分别计算相邻年度同比变化率，再求两个变化率的算术平均；不是 CAGR。

### 1. `v4-review-public-average_growth_rate-000`

- 中文题意：研发费用在 2017—2018 年和 2018—2019 年的两个同比变化率，其算术平均值是多少？保留两位小数。
- 英文题意：What is the arithmetic mean of the 2017-2018 and 2018-2019 year-on-year percentage changes in research expense? Round to two decimals.
- 中文审核表：

| 指标 | 2019 | 2018 | 2017 |
| --- | --- | --- | --- |
| 研发费用 | 6,552 | 5,697 | 7,121 |

- 参考公式：`(((5697-7121)/7121)+((6552-5697)/5697))/2*100`
- GT：`-2.49`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-public-average_growth_rate-001`

- 中文题意：线上销售额两个相邻年度百分比变化率的算术平均值是多少？这里求的不是 CAGR。保留两位小数。
- 英文题意：What was the arithmetic average of the two adjacent annual percentage changes in online sales? This is not CAGR. Round to two decimals.
- 中文审核表：

| 指标 | 2022 | 2021 | 2020 |
| --- | --- | --- | --- |
| 线上销售额 | 2,479 | 2,754 | 2,203 |

- 参考公式：`(((2754-2203)/2203)+((2479-2754)/2754))/2*100`
- GT：`7.51`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-public-average_growth_rate-002`

- 中文题意：能源消耗在 2021—2022 年和 2022—2023 年的两个同比变化率，其算术平均值是多少？保留两位小数。
- 英文题意：What is the arithmetic mean of the 2021-2022 and 2022-2023 year-on-year percentage changes in energy consumption? Round to two decimals.
- 中文审核表：

| 指标 | 2023 | 2022 | 2021 |
| --- | --- | --- | --- |
| 能源消耗 | 3,892 | 4,097 | 4,820 |

- 参考公式：`(((4097-4820)/4820)+((3892-4097)/4097))/2*100`
- GT：`-10.00`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-public-average_growth_rate-003`

- 中文题意：研发费用两个相邻年度百分比变化率的算术平均值是多少？这里求的不是 CAGR。保留两位小数。
- 英文题意：What was the arithmetic average of the two adjacent annual percentage changes in research expense? This is not CAGR. Round to two decimals.
- 中文审核表：

| 指标 | 2019 | 2018 | 2017 |
| --- | --- | --- | --- |
| 研发费用 | 10,640 | 8,185 | 7,441 |

- 参考公式：`(((8185-7441)/7441)+((10640-8185)/8185))/2*100`
- GT：`20.00`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-public-average_growth_rate-004`

- 中文题意：线上销售额在 2020—2021 年和 2021—2022 年的两个同比变化率，其算术平均值是多少？保留两位小数。
- 英文题意：What is the arithmetic mean of the 2020-2021 and 2021-2022 year-on-year percentage changes in online sales? Round to two decimals.
- 中文审核表：

| 指标 | 2022 | 2021 | 2020 |
| --- | --- | --- | --- |
| 线上销售额 | 9,017 | 11,271 | 8,349 |

- 参考公式：`(((11271-8349)/8349)+((9017-11271)/11271))/2*100`
- GT：`7.50`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-public-average_growth_rate-005`

- 中文题意：能源消耗两个相邻年度百分比变化率的算术平均值是多少？这里求的不是 CAGR。保留两位小数。
- 英文题意：What was the arithmetic average of the two adjacent annual percentage changes in energy consumption? This is not CAGR. Round to two decimals.
- 中文审核表：

| 指标 | 2023 | 2022 | 2021 |
| --- | --- | --- | --- |
| 能源消耗 | 9,692 | 7,944 | 8,635 |

- 参考公式：`(((7944-8635)/8635)+((9692-7944)/7944))/2*100`
- GT：`7.00`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

## 派生总价值的百分比变化

- Family：`v3-public-derived_value_percent_change-v1`
- 母题：`v3-public-ab005e597c33-arithmetic-rounding-revised-v1`、`v3-public-4a29948bb22b-arithmetic`
- 保留关系：每期先用数量×单位价值求总价值，再比较两个总价值。

### 1. `v4-review-public-derived_value_percent_change-000`

- 中文题意：根据未归属奖励的数量和每项奖励的公允价值，其总价值从 2022 年到 2023 年变化了百分之多少？保留两位小数。
- 英文题意：Based on the number of unvested awards and fair value per award, what was the percentage change in their total value from 2022 to 2023? Round to two decimals.
- 中文审核表：

| 期间 | 未归属奖励数量 | 每项奖励公允价值 |
| --- | --- | --- |
| 2022 年末 | 502,603 | $162.96 |
| 2023 年末 | 502,603 | $143.40 |

- 参考公式：`((502603*143.4)-(502603*162.96))/(502603*162.96)*100`
- GT：`-12.00`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-public-derived_value_percent_change-001`

- 中文题意：未归属奖励的总公允价值从 2022 年到 2023 年变化了百分之多少？请使用表中的奖励数量和每项奖励公允价值，并保留两位小数。
- 英文题意：How much did the total fair value of unvested awards change in percentage terms from 2022 to 2023? Use the counts and per-award values shown, and round to two decimals.
- 中文审核表：

| 期间 | 未归属奖励数量 | 每项奖励公允价值 |
| --- | --- | --- |
| 2022 年末 | 594,161 | $160.97 |
| 2023 年末 | 421,854 | $169.02 |

- 参考公式：`((421854*169.02)-(594161*160.97))/(594161*160.97)*100`
- GT：`-25.45`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-public-derived_value_percent_change-002`

- 中文题意：根据未归属奖励的数量和每项奖励的公允价值，其总价值从 2022 年到 2023 年变化了百分之多少？保留两位小数。
- 英文题意：Based on the number of unvested awards and fair value per award, what was the percentage change in their total value from 2022 to 2023? Round to two decimals.
- 中文审核表：

| 期间 | 未归属奖励数量 | 每项奖励公允价值 |
| --- | --- | --- |
| 2022 年末 | 865,417 | $23.67 |
| 2023 年末 | 1,038,500 | $34.56 |

- 参考公式：`((1038500*34.56)-(865417*23.67))/(865417*23.67)*100`
- GT：`75.21`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-public-derived_value_percent_change-003`

- 中文题意：未归属奖励的总公允价值从 2022 年到 2023 年变化了百分之多少？请使用表中的奖励数量和每项奖励公允价值，并保留两位小数。
- 英文题意：How much did the total fair value of unvested awards change in percentage terms from 2022 to 2023? Use the counts and per-award values shown, and round to two decimals.
- 中文审核表：

| 期间 | 未归属奖励数量 | 每项奖励公允价值 |
| --- | --- | --- |
| 2022 年末 | 110,462 | $188.90 |
| 2023 年末 | 119,299 | $266.35 |

- 参考公式：`((119299*266.35)-(110462*188.9))/(110462*188.9)*100`
- GT：`52.28`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-public-derived_value_percent_change-004`

- 中文题意：根据未归属奖励的数量和每项奖励的公允价值，其总价值从 2022 年到 2023 年变化了百分之多少？保留两位小数。
- 英文题意：Based on the number of unvested awards and fair value per award, what was the percentage change in their total value from 2022 to 2023? Round to two decimals.
- 中文审核表：

| 期间 | 未归属奖励数量 | 每项奖励公允价值 |
| --- | --- | --- |
| 2022 年末 | 262,065 | $52.89 |
| 2023 年末 | 172,963 | $76.16 |

- 参考公式：`((172963*76.16)-(262065*52.89))/(262065*52.89)*100`
- GT：`-4.96`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-public-derived_value_percent_change-005`

- 中文题意：未归属奖励的总公允价值从 2022 年到 2023 年变化了百分之多少？请使用表中的奖励数量和每项奖励公允价值，并保留两位小数。
- 英文题意：How much did the total fair value of unvested awards change in percentage terms from 2022 to 2023? Use the counts and per-award values shown, and round to two decimals.
- 中文审核表：

| 期间 | 未归属奖励数量 | 每项奖励公允价值 |
| --- | --- | --- |
| 2022 年末 | 605,292 | $134.27 |
| 2023 年末 | 665,821 | $197.38 |

- 参考公式：`((665821*197.38)-(605292*134.27))/(605292*134.27)*100`
- GT：`61.70`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

## 两个平均值之差

- Family：`v3-public-difference_of_averages-v1`
- 母题：`v3-public-993d968c025a-arithmetic-revised-v2`、`v3-public-9a63b89ea330-arithmetic`、`v3-public-af1f11d98652-arithmetic`、`v3-public-f5fdb156cd45-arithmetic-revised-v2`
- 保留关系：先计算两个指定平均值，再以前者减去后者并保留正负号。

### 1. `v4-review-public-difference_of_averages-000`

- 中文题意：用 2018—2019 两年平均收入减去 2017—2018 两年平均收入。增加记为正，减少记为负。
- 英文题意：Compute the 2018-2019 two-year average revenue minus the 2017-2018 two-year average revenue. Report an increase as positive and a decrease as negative.
- 中文审核表：

| 指标 | 2019 | 2018 | 2017 |
| --- | --- | --- | --- |
| 收入 | 12,003 | 17,115 | 13,084 |

- 参考公式：`(17115+12003)/2-(13084+17115)/2`
- GT：`-540.50`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-public-difference_of_averages-001`

- 中文题意：2022—2023 年处理业务的平均收入减去云业务的平均收入，结果是多少？保留正负号。
- 英文题意：What is the 2022-2023 average processing revenue minus the 2022-2023 average cloud revenue? Report a signed result.
- 中文审核表：

| 业务 | 2023 年收入 | 2022 年收入 |
| --- | --- | --- |
| 处理业务 | 11,523 | 2,069 |
| 云业务 | 12,190 | 16,201 |

- 参考公式：`(2069+11523)/2-(16201+12190)/2`
- GT：`-7399.50`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-public-difference_of_averages-002`

- 中文题意：2022—2023 年服务收入的平均值减去 2020—2021 年服务收入的平均值，结果是多少？保留正负号。
- 英文题意：What is the 2022-2023 average service revenue minus the 2020-2021 average service revenue? Report a signed result.
- 中文审核表：

| 指标 | 2023 | 2022 | 2021 | 2020 |
| --- | --- | --- | --- | --- |
| 服务收入 | 19,198 | 13,017 | 5,441 | 6,814 |

- 参考公式：`(13017+19198)/2-(6814+5441)/2`
- GT：`9980.00`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-public-difference_of_averages-003`

- 中文题意：用 2018—2019 两年平均收入减去 2017—2018 两年平均收入。增加记为正，减少记为负。
- 英文题意：Compute the 2018-2019 two-year average revenue minus the 2017-2018 two-year average revenue. Report an increase as positive and a decrease as negative.
- 中文审核表：

| 指标 | 2019 | 2018 | 2017 |
| --- | --- | --- | --- |
| 收入 | 4,519 | 11,602 | 12,418 |

- 参考公式：`(11602+4519)/2-(12418+11602)/2`
- GT：`-3949.50`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-public-difference_of_averages-004`

- 中文题意：2022—2023 年处理业务的平均收入减去云业务的平均收入，结果是多少？保留正负号。
- 英文题意：What is the 2022-2023 average processing revenue minus the 2022-2023 average cloud revenue? Report a signed result.
- 中文审核表：

| 业务 | 2023 年收入 | 2022 年收入 |
| --- | --- | --- |
| 处理业务 | 18,547 | 19,112 |
| 云业务 | 12,854 | 9,990 |

- 参考公式：`(19112+18547)/2-(9990+12854)/2`
- GT：`7407.50`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-public-difference_of_averages-005`

- 中文题意：2022—2023 年服务收入的平均值减去 2020—2021 年服务收入的平均值，结果是多少？保留正负号。
- 英文题意：What is the 2022-2023 average service revenue minus the 2020-2021 average service revenue? Report a signed result.
- 中文审核表：

| 指标 | 2023 | 2022 | 2021 | 2020 |
| --- | --- | --- | --- | --- |
| 服务收入 | 19,603 | 3,202 | 1,985 | 18,565 |

- 参考公式：`(3202+19603)/2-(18565+1985)/2`
- GT：`1127.50`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

## 利率区间中点应用

- Family：`v3-public-midpoint_rate_application-v1`
- 母题：`v3-public-abe2824b6e81-arithmetic-revised-v2`
- 保留关系：先求利率上下限的中点，再乘名义金额。

### 1. `v4-review-public-midpoint_rate_application-000`

- 中文题意：使用所列利率区间的中点，估算年度利息费用（百万美元）。保留一位小数。
- 英文题意：Using the midpoint of the stated rate range, estimate the annual interest expense in millions of dollars. Round to one decimal place.
- 中文审核表：

| 工具 | 名义金额（百万美元） | 利率区间 |
| --- | --- | --- |
| 掉期组合 | 119.0 | 3.60%—7.30% |

- 参考公式：`119.0*((3.60+7.30)/2)/100`
- GT：`6.5`；容差：`0.05`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-public-midpoint_rate_application-001`

- 中文题意：使用利率区间的中点，该名义金额对应的年度利息成本是多少？以百万美元表示并保留一位小数。
- 英文题意：Using the rate-range midpoint, what annual interest cost does the notional amount imply? Report millions of dollars to one decimal place.
- 中文审核表：

| 工具 | 名义金额（百万美元） | 利率区间 |
| --- | --- | --- |
| 循环信贷额度 | 478.0 | 6.18%—7.12% |

- 参考公式：`478.0*((6.18+7.12)/2)/100`
- GT：`31.8`；容差：`0.05`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-public-midpoint_rate_application-002`

- 中文题意：使用所列利率区间的中点，估算年度利息费用（百万美元）。保留一位小数。
- 英文题意：Using the midpoint of the stated rate range, estimate the annual interest expense in millions of dollars. Round to one decimal place.
- 中文审核表：

| 工具 | 名义金额（百万美元） | 利率区间 |
| --- | --- | --- |
| 定期贷款 | 232.0 | 3.39%—4.68% |

- 参考公式：`232.0*((3.39+4.68)/2)/100`
- GT：`9.4`；容差：`0.05`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-public-midpoint_rate_application-003`

- 中文题意：使用利率区间的中点，该名义金额对应的年度利息成本是多少？以百万美元表示并保留一位小数。
- 英文题意：Using the rate-range midpoint, what annual interest cost does the notional amount imply? Report millions of dollars to one decimal place.
- 中文审核表：

| 工具 | 名义金额（百万美元） | 利率区间 |
| --- | --- | --- |
| 掉期组合 | 332.0 | 5.35%—6.63% |

- 参考公式：`332.0*((5.35+6.63)/2)/100`
- GT：`19.9`；容差：`0.05`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-public-midpoint_rate_application-004`

- 中文题意：使用所列利率区间的中点，估算年度利息费用（百万美元）。保留一位小数。
- 英文题意：Using the midpoint of the stated rate range, estimate the annual interest expense in millions of dollars. Round to one decimal place.
- 中文审核表：

| 工具 | 名义金额（百万美元） | 利率区间 |
| --- | --- | --- |
| 循环信贷额度 | 198.0 | 6.39%—10.07% |

- 参考公式：`198.0*((6.39+10.07)/2)/100`
- GT：`16.3`；容差：`0.05`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-public-midpoint_rate_application-005`

- 中文题意：使用利率区间的中点，该名义金额对应的年度利息成本是多少？以百万美元表示并保留一位小数。
- 英文题意：Using the rate-range midpoint, what annual interest cost does the notional amount imply? Report millions of dollars to one decimal place.
- 中文审核表：

| 工具 | 名义金额（百万美元） | 利率区间 |
| --- | --- | --- |
| 定期贷款 | 285.0 | 7.37%—9.79% |

- 参考公式：`285.0*((7.37+9.79)/2)/100`
- GT：`24.5`；容差：`0.05`
- 审核结论：□保留　□修改　□删除

## 多期利息累计

- Family：`v3-public-multi_period_interest-v1`
- 母题：`v3-public-4dff5a6c3f03-arithmetic`
- 保留关系：每次付款金额×每年付款次数×完整年数。

### 1. `v4-review-public-multi_period_interest-000`

- 中文题意：根据表中的付款安排，整个期限内累计支付多少百万美元利息？
- 英文题意：Based on the payment schedule shown, what is the total interest paid over the full term, in millions of dollars?
- 中文审核表：

| 付款安排 | 每次付款（百万美元） | 每年付款次数 | 完整年数 |
| --- | --- | --- | --- |
| 票据 | 22.4 | 2 | 12 |

- 参考公式：`22.4*2*12`
- GT：`537.6`；容差：`0.05`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-public-multi_period_interest-001`

- 中文题意：使用表中的每次付款额、每年付款次数和期限，累计支付的利息是多少百万美元？
- 英文题意：Using the amount, annual payment count, and term in the table, how many millions of dollars of interest are paid in total?
- 中文审核表：

| 付款安排 | 每次付款（百万美元） | 每年付款次数 | 完整年数 |
| --- | --- | --- | --- |
| 债券 | 23.9 | 2 | 15 |

- 参考公式：`23.9*2*15`
- GT：`717.0`；容差：`0.05`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-public-multi_period_interest-002`

- 中文题意：根据表中的付款安排，整个期限内累计支付多少百万美元利息？
- 英文题意：Based on the payment schedule shown, what is the total interest paid over the full term, in millions of dollars?
- 中文审核表：

| 付款安排 | 每次付款（百万美元） | 每年付款次数 | 完整年数 |
| --- | --- | --- | --- |
| 定期贷款 | 6.3 | 2 | 5 |

- 参考公式：`6.3*2*5`
- GT：`63.0`；容差：`0.05`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-public-multi_period_interest-003`

- 中文题意：使用表中的每次付款额、每年付款次数和期限，累计支付的利息是多少百万美元？
- 英文题意：Using the amount, annual payment count, and term in the table, how many millions of dollars of interest are paid in total?
- 中文审核表：

| 付款安排 | 每次付款（百万美元） | 每年付款次数 | 完整年数 |
| --- | --- | --- | --- |
| 票据 | 31.9 | 2 | 13 |

- 参考公式：`31.9*2*13`
- GT：`829.4`；容差：`0.05`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-public-multi_period_interest-004`

- 中文题意：根据表中的付款安排，整个期限内累计支付多少百万美元利息？
- 英文题意：Based on the payment schedule shown, what is the total interest paid over the full term, in millions of dollars?
- 中文审核表：

| 付款安排 | 每次付款（百万美元） | 每年付款次数 | 完整年数 |
| --- | --- | --- | --- |
| 债券 | 5.1 | 4 | 4 |

- 参考公式：`5.1*4*4`
- GT：`81.6`；容差：`0.05`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-public-multi_period_interest-005`

- 中文题意：使用表中的每次付款额、每年付款次数和期限，累计支付的利息是多少百万美元？
- 英文题意：Using the amount, annual payment count, and term in the table, how many millions of dollars of interest are paid in total?
- 中文审核表：

| 付款安排 | 每次付款（百万美元） | 每年付款次数 | 完整年数 |
| --- | --- | --- | --- |
| 定期贷款 | 10.8 | 4 | 14 |

- 参考公式：`10.8*4*14`
- GT：`604.8`；容差：`0.05`
- 审核结论：□保留　□修改　□删除

## 股利支付率

- Family：`v3-public-payout_ratio-v1`
- 母题：`v3-public-244426e00be4-arithmetic`
- 保留关系：流通股数×每股股利得到股利总额，再除以可供分红净利润。

### 1. `v4-review-public-payout_ratio-000`

- 中文题意：根据表中数值，普通股股利支付率是多少？以百分比表示并保留两位小数。
- 英文题意：Based on the values shown, what was the common dividend payout ratio? Return a percentage rounded to two decimals.
- 中文审核表：

| 指标 | 数值 |
| --- | --- |
| 流通普通股（千股） | 58,837 |
| 每股普通股股利 | $0.72 |
| 可供分红净利润（千美元） | 111,691 |

- 参考公式：`(58837*0.72)/111691*100`
- GT：`37.93`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-public-payout_ratio-001`

- 中文题意：根据流通股数、每股股利和可供分红净利润，作为普通股股利支付的金额占可供分红净利润的百分比是多少？保留两位小数。
- 英文题意：Based on shares outstanding, dividend per share, and income available for dividends, what percentage of available income was paid as common dividends? Round to two decimals.
- 中文审核表：

| 指标 | 数值 |
| --- | --- |
| 流通普通股（千股） | 55,911 |
| 每股普通股股利 | $1.24 |
| 可供分红净利润（千美元） | 144,014 |

- 参考公式：`(55911*1.24)/144014*100`
- GT：`48.14`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-public-payout_ratio-002`

- 中文题意：根据表中数值，普通股股利支付率是多少？以百分比表示并保留两位小数。
- 英文题意：Based on the values shown, what was the common dividend payout ratio? Return a percentage rounded to two decimals.
- 中文审核表：

| 指标 | 数值 |
| --- | --- |
| 流通普通股（千股） | 49,938 |
| 每股普通股股利 | $0.31 |
| 可供分红净利润（千美元） | 30,122 |

- 参考公式：`(49938*0.31)/30122*100`
- GT：`51.39`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-public-payout_ratio-003`

- 中文题意：根据流通股数、每股股利和可供分红净利润，作为普通股股利支付的金额占可供分红净利润的百分比是多少？保留两位小数。
- 英文题意：Based on shares outstanding, dividend per share, and income available for dividends, what percentage of available income was paid as common dividends? Round to two decimals.
- 中文审核表：

| 指标 | 数值 |
| --- | --- |
| 流通普通股（千股） | 77,818 |
| 每股普通股股利 | $0.92 |
| 可供分红净利润（千美元） | 275,915 |

- 参考公式：`(77818*0.92)/275915*100`
- GT：`25.95`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-public-payout_ratio-004`

- 中文题意：根据表中数值，普通股股利支付率是多少？以百分比表示并保留两位小数。
- 英文题意：Based on the values shown, what was the common dividend payout ratio? Return a percentage rounded to two decimals.
- 中文审核表：

| 指标 | 数值 |
| --- | --- |
| 流通普通股（千股） | 26,842 |
| 每股普通股股利 | $1.16 |
| 可供分红净利润（千美元） | 62,728 |

- 参考公式：`(26842*1.16)/62728*100`
- GT：`49.64`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-public-payout_ratio-005`

- 中文题意：根据流通股数、每股股利和可供分红净利润，作为普通股股利支付的金额占可供分红净利润的百分比是多少？保留两位小数。
- 英文题意：Based on shares outstanding, dividend per share, and income available for dividends, what percentage of available income was paid as common dividends? Round to two decimals.
- 中文审核表：

| 指标 | 数值 |
| --- | --- |
| 流通普通股（千股） | 26,600 |
| 每股普通股股利 | $1.02 |
| 可供分红净利润（千美元） | 66,701 |

- 参考公式：`(26600*1.02)/66701*100`
- GT：`40.68`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

## 汇总值之比

- Family：`v3-public-ratio_of_aggregates-v1`
- 母题：`v3-public-7aca02f2885b-arithmetic`
- 保留关系：先跨年度汇总分子和分母，再计算百分比。

### 1. `v4-review-public-ratio_of_aggregates-000`

- 中文题意：合并计算 2022 年和 2023 年，长期债务占总债务的百分比是多少？保留两位小数。
- 英文题意：On a combined 2022-and-2023 basis, what percentage of total debt was long-term debt? Round to two decimals.
- 中文审核表：

| 债务指标 | 2023 | 2022 |
| --- | --- | --- |
| 长期债务 | 5,608 | 2,621 |
| 总债务 | 6,946 | 3,542 |

- 参考公式：`(2621+5608)/(3542+6946)*100`
- GT：`78.46`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-public-ratio_of_aggregates-001`

- 中文题意：将 2022 年和 2023 年合并考虑，可再生能源产量占总产量的百分比是多少？保留两位小数。
- 英文题意：Across 2022 and 2023 together, what share of total output consisted of renewable output? Express the result as a percentage rounded to two decimals.
- 中文审核表：

| 产量指标 | 2023 | 2022 |
| --- | --- | --- |
| 可再生能源产量 | 466 | 6,609 |
| 总产量 | 2,025 | 6,961 |

- 参考公式：`(6609+466)/(6961+2025)*100`
- GT：`78.73`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-public-ratio_of_aggregates-002`

- 中文题意：合并计算 2022 年和 2023 年，加急货件占总货件的百分比是多少？保留两位小数。
- 英文题意：On a combined 2022-and-2023 basis, what percentage of total shipments was express shipments? Round to two decimals.
- 中文审核表：

| 货运指标 | 2023 | 2022 |
| --- | --- | --- |
| 加急货件 | 262 | 1,331 |
| 总货件 | 3,692 | 4,309 |

- 参考公式：`(1331+262)/(4309+3692)*100`
- GT：`19.91`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-public-ratio_of_aggregates-003`

- 中文题意：将 2022 年和 2023 年合并考虑，长期债务占总债务的百分比是多少？保留两位小数。
- 英文题意：Across 2022 and 2023 together, what share of total debt consisted of long-term debt? Express the result as a percentage rounded to two decimals.
- 中文审核表：

| 债务指标 | 2023 | 2022 |
| --- | --- | --- |
| 长期债务 | 4,423 | 4,027 |
| 总债务 | 7,872 | 6,092 |

- 参考公式：`(4027+4423)/(6092+7872)*100`
- GT：`60.51`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-public-ratio_of_aggregates-004`

- 中文题意：合并计算 2022 年和 2023 年，可再生能源产量占总产量的百分比是多少？保留两位小数。
- 英文题意：On a combined 2022-and-2023 basis, what percentage of total output was renewable output? Round to two decimals.
- 中文审核表：

| 产量指标 | 2023 | 2022 |
| --- | --- | --- |
| 可再生能源产量 | 2,000 | 2,562 |
| 总产量 | 6,890 | 4,869 |

- 参考公式：`(2562+2000)/(4869+6890)*100`
- GT：`38.80`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-public-ratio_of_aggregates-005`

- 中文题意：将 2022 年和 2023 年合并考虑，加急货件占总货件的百分比是多少？保留两位小数。
- 英文题意：Across 2022 and 2023 together, what share of total shipments consisted of express shipments? Express the result as a percentage rounded to two decimals.
- 中文审核表：

| 货运指标 | 2023 | 2022 |
| --- | --- | --- |
| 加急货件 | 2,093 | 3,061 |
| 总货件 | 3,068 | 3,369 |

- 参考公式：`(3061+2093)/(3369+3068)*100`
- GT：`80.07`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

## 两个派生价值之比

- Family：`v3-public-ratio_of_derived_values-v1`
- 母题：`v3-public-aa133d54fab4-arithmetic`
- 保留关系：分子、分母分别由数量×单位价值形成，再求比值。

### 1. `v4-review-public-ratio_of_derived_values-000`

- 中文题意：结算数量用括号表示流出，计算时使用其数量的绝对值。授予单位的总价值与结算单位的总价值之比是多少？比值保留两位小数。
- 英文题意：The settled count is shown in parentheses to indicate an outflow; use its absolute count. What is the ratio of the total value of units granted to the total value of units settled? Round the ratio to two decimals.
- 中文审核表：

| 活动 | 单位数量 | 每单位公允价值 |
| --- | --- | --- |
| 授予 | 1,312,036 | $6.30 |
| 结算 | (1,383,292) | $7.43 |

- 参考公式：`(1312036*6.3)/(1383292*7.43)`
- GT：`0.80`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-public-ratio_of_derived_values-001`

- 中文题意：括号中的结算数量按绝对数量处理。根据表中的数量和公允价值，授予单位总价值与结算单位总价值之比是多少？比值保留两位小数。
- 英文题意：Treat the parenthesized settled count as an absolute quantity. Using the counts and fair values shown, what is the ratio of total value granted to total value settled? Round to two decimals.
- 中文审核表：

| 活动 | 单位数量 | 每单位公允价值 |
| --- | --- | --- |
| 授予 | 1,067,705 | $7.13 |
| 结算 | (662,965) | $12.31 |

- 参考公式：`(1067705*7.13)/(662965*12.31)`
- GT：`0.93`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-public-ratio_of_derived_values-002`

- 中文题意：结算数量用括号表示流出，计算时使用其数量的绝对值。授予单位的总价值与结算单位的总价值之比是多少？比值保留两位小数。
- 英文题意：The settled count is shown in parentheses to indicate an outflow; use its absolute count. What is the ratio of the total value of units granted to the total value of units settled? Round the ratio to two decimals.
- 中文审核表：

| 活动 | 单位数量 | 每单位公允价值 |
| --- | --- | --- |
| 授予 | 638,891 | $3.96 |
| 结算 | (1,001,108) | $5.40 |

- 参考公式：`(638891*3.96)/(1001108*5.4)`
- GT：`0.47`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-public-ratio_of_derived_values-003`

- 中文题意：括号中的结算数量按绝对数量处理。根据表中的数量和公允价值，授予单位总价值与结算单位总价值之比是多少？比值保留两位小数。
- 英文题意：Treat the parenthesized settled count as an absolute quantity. Using the counts and fair values shown, what is the ratio of total value granted to total value settled? Round to two decimals.
- 中文审核表：

| 活动 | 单位数量 | 每单位公允价值 |
| --- | --- | --- |
| 授予 | 724,430 | $6.21 |
| 结算 | (768,634) | $6.29 |

- 参考公式：`(724430*6.21)/(768634*6.29)`
- GT：`0.93`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-public-ratio_of_derived_values-004`

- 中文题意：结算数量用括号表示流出，计算时使用其数量的绝对值。授予单位的总价值与结算单位的总价值之比是多少？比值保留两位小数。
- 英文题意：The settled count is shown in parentheses to indicate an outflow; use its absolute count. What is the ratio of the total value of units granted to the total value of units settled? Round the ratio to two decimals.
- 中文审核表：

| 活动 | 单位数量 | 每单位公允价值 |
| --- | --- | --- |
| 授予 | 750,971 | $12.16 |
| 结算 | (568,335) | $8.86 |

- 参考公式：`(750971*12.16)/(568335*8.86)`
- GT：`1.81`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-public-ratio_of_derived_values-005`

- 中文题意：括号中的结算数量按绝对数量处理。根据表中的数量和公允价值，授予单位总价值与结算单位总价值之比是多少？比值保留两位小数。
- 英文题意：Treat the parenthesized settled count as an absolute quantity. Using the counts and fair values shown, what is the ratio of total value granted to total value settled? Round to two decimals.
- 中文审核表：

| 活动 | 单位数量 | 每单位公允价值 |
| --- | --- | --- |
| 授予 | 346,875 | $7.50 |
| 结算 | (935,716) | $7.84 |

- 参考公式：`(346875*7.5)/(935716*7.84)`
- GT：`0.35`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

## 带符号多值平均

- Family：`v3-public-signed_multi_value_average-v1`
- 母题：`v3-public-42e42100b593-arithmetic`、`v3-public-9f547636b5b4-arithmetic-revised-v2`、`v3-public-fee44b520741-arithmetic`
- 保留关系：括号视为负数、横线视为零，再求多个值的算术平均。

### 1. `v4-review-public-signed_multi_value_average-000`

- 中文题意：括号表示负数，横线表示零。四个修订金额的算术平均值是多少？保留两位小数。
- 英文题意：Parentheses denote negative amounts and the dash means zero. What is the arithmetic mean of the four amendment amounts? Round to two decimals.
- 中文审核表：

| 指标 | 养老金 2023 | 养老金 2022 | 其他福利 2023 | 其他福利 2022 |
| --- | --- | --- | --- | --- |
| 修订金额 | — | 124 | (180) | 168 |

- 参考公式：`(0+124-180+168)/4`
- GT：`28.00`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-public-signed_multi_value_average-001`

- 中文题意：将括号内修订金额按负数处理、横线按零处理，再对四个金额求平均。带符号结果保留两位小数。
- 英文题意：Interpret parenthesized amendments as negative and the dash as zero, then average all four displayed amounts. Round the signed result to two decimals.
- 中文审核表：

| 指标 | 养老金 2023 | 养老金 2022 | 其他福利 2023 | 其他福利 2022 |
| --- | --- | --- | --- | --- |
| 修订金额 | 79 | — | (151) | (50) |

- 参考公式：`(79+0-151-50)/4`
- GT：`-30.50`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-public-signed_multi_value_average-002`

- 中文题意：括号表示负数，横线表示零。四个修订金额的算术平均值是多少？保留两位小数。
- 英文题意：Parentheses denote negative amounts and the dash means zero. What is the arithmetic mean of the four amendment amounts? Round to two decimals.
- 中文审核表：

| 指标 | 养老金 2023 | 养老金 2022 | 其他福利 2023 | 其他福利 2022 |
| --- | --- | --- | --- | --- |
| 修订金额 | (18) | (161) | — | (95) |

- 参考公式：`(-18-161+0-95)/4`
- GT：`-68.50`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-public-signed_multi_value_average-003`

- 中文题意：将括号内修订金额按负数处理、横线按零处理，再对四个金额求平均。带符号结果保留两位小数。
- 英文题意：Interpret parenthesized amendments as negative and the dash as zero, then average all four displayed amounts. Round the signed result to two decimals.
- 中文审核表：

| 指标 | 养老金 2023 | 养老金 2022 | 其他福利 2023 | 其他福利 2022 |
| --- | --- | --- | --- | --- |
| 修订金额 | — | (135) | 19 | 154 |

- 参考公式：`(0-135+19+154)/4`
- GT：`9.50`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-public-signed_multi_value_average-004`

- 中文题意：括号表示负数，横线表示零。四个修订金额的算术平均值是多少？保留两位小数。
- 英文题意：Parentheses denote negative amounts and the dash means zero. What is the arithmetic mean of the four amendment amounts? Round to two decimals.
- 中文审核表：

| 指标 | 养老金 2023 | 养老金 2022 | 其他福利 2023 | 其他福利 2022 |
| --- | --- | --- | --- | --- |
| 修订金额 | (156) | (59) | 147 | — |

- 参考公式：`(-156-59+147+0)/4`
- GT：`-17.00`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-public-signed_multi_value_average-005`

- 中文题意：将括号内修订金额按负数处理、横线按零处理，再对四个金额求平均。带符号结果保留两位小数。
- 英文题意：Interpret parenthesized amendments as negative and the dash as zero, then average all four displayed amounts. Round the signed result to two decimals.
- 中文审核表：

| 指标 | 养老金 2023 | 养老金 2022 | 其他福利 2023 | 其他福利 2022 |
| --- | --- | --- | --- | --- |
| 修订金额 | (65) | (79) | — | (101) |

- 参考公式：`(-65-79+0-101)/4`
- GT：`-61.25`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

## 负数展示下的绝对金额变化

- Family：`v3-public-signed_percent_change-v1`
- 母题：`v3-public-9d6f397353af-arithmetic`、`v3-public-2adfb9bf033b-arithmetic`、`v3-public-aa20ff7068b0-arithmetic`
- 保留关系：括号仅表示费用或负债；先取绝对金额，再计算有方向的百分比变化。

### 1. `v4-review-public-signed_percent_change-000`

- 中文题意：括号表示费用。使用费用的绝对金额，利息费用从 2022 年到 2023 年变化了百分之多少？增加记为正，减少记为负，保留两位小数。
- 英文题意：Parentheses denote expense amounts. Using their absolute magnitudes, what was the percentage change in interest expense from 2022 to 2023? Report an increase as positive and a decrease as negative. Round to two decimals.
- 中文审核表：

| 指标 | 2023 | 2022 |
| --- | --- | --- |
| 利息收入 | 32 | 50 |
| 利息费用 | (58) | (118) |

- 参考公式：`(58-118)/118*100`
- GT：`-50.85`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-public-signed_percent_change-001`

- 中文题意：保修费用行以括号显示。比较 2022 年和 2021 年的绝对金额，计算带方向的百分比变化，保留两位小数。
- 英文题意：The warranty expense row is shown in parentheses. Compare its absolute 2022 amount with the absolute 2021 amount and report the signed percentage change to two decimals.
- 中文审核表：

| 指标 | 2022 | 2021 |
| --- | --- | --- |
| 服务收入 | 157 | 193 |
| 保修费用 | (280) | (162) |

- 参考公式：`(280-162)/162*100`
- GT：`72.84`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-public-signed_percent_change-002`

- 中文题意：括号表示费用。使用费用的绝对金额，退货处理成本从 2023 年到 2024 年变化了百分之多少？增加记为正，减少记为负，保留两位小数。
- 英文题意：Parentheses denote expense amounts. Using their absolute magnitudes, what was the percentage change in return-processing cost from 2023 to 2024? Report an increase as positive and a decrease as negative. Round to two decimals.
- 中文审核表：

| 指标 | 2024 | 2023 |
| --- | --- | --- |
| 退货费收入 | 154 | 37 |
| 退货处理成本 | (132) | (264) |

- 参考公式：`(132-264)/264*100`
- GT：`-50.00`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-public-signed_percent_change-003`

- 中文题意：利息费用行以括号显示。比较 2023 年和 2022 年的绝对金额，计算带方向的百分比变化，保留两位小数。
- 英文题意：The interest expense row is shown in parentheses. Compare its absolute 2023 amount with the absolute 2022 amount and report the signed percentage change to two decimals.
- 中文审核表：

| 指标 | 2023 | 2022 |
| --- | --- | --- |
| 利息收入 | 109 | 70 |
| 利息费用 | (414) | (471) |

- 参考公式：`(414-471)/471*100`
- GT：`-12.10`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-public-signed_percent_change-004`

- 中文题意：括号表示费用。使用费用的绝对金额，保修费用从 2021 年到 2022 年变化了百分之多少？增加记为正，减少记为负，保留两位小数。
- 英文题意：Parentheses denote expense amounts. Using their absolute magnitudes, what was the percentage change in warranty expense from 2021 to 2022? Report an increase as positive and a decrease as negative. Round to two decimals.
- 中文审核表：

| 指标 | 2022 | 2021 |
| --- | --- | --- |
| 服务收入 | 130 | 145 |
| 保修费用 | (64) | (71) |

- 参考公式：`(64-71)/71*100`
- GT：`-9.86`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-public-signed_percent_change-005`

- 中文题意：退货处理成本行以括号显示。比较 2024 年和 2023 年的绝对金额，计算带方向的百分比变化，保留两位小数。
- 英文题意：The return-processing cost row is shown in parentheses. Compare its absolute 2024 amount with the absolute 2023 amount and report the signed percentage change to two decimals.
- 中文审核表：

| 指标 | 2024 | 2023 |
| --- | --- | --- |
| 退货费收入 | 76 | 95 |
| 退货处理成本 | (545) | (395) |

- 参考公式：`(545-395)/395*100`
- GT：`37.97`；容差：`0.005`
- 审核结论：□保留　□修改　□删除
