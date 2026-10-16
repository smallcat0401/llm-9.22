# V3 可训练成功轨迹中文审核页

> 状态：这28条原始候选已完成审核并进入 Search-SFT 打包；随后又加入3条修订题成功轨迹和1条舍入复测成功轨迹，最终 Search-SFT 为32条。数据尚未用于训练。

## 怎么审核

每题展示的是Best-of-8中被搜索器选中的第一条严格成功轨迹。请重点判断：

1. 中文题意是否与原英文任务一致；
2. 模型公式是否表达了正确的数量关系；
3. 工具返回值、final与GT是否一致；
4. 即使答案正确，轨迹是否适合教给模型；
5. 没有调用工具的轨迹只能作为数量推理数据，不能冒充工具调用数据。

## 总览

- 候选任务：28
- 公开审核题：8
- 自建V2题：12
- 新GSM8K-train题：8
- 选中轨迹未调用工具：5
- 已拒绝并移出本页：原第27题 `v3-gsm8k-train-5655-calculator`（英文题意有歧义）。
- 审核结论未填写前，不生成SFT数据。

## 1. 利息费用绝对金额的变化率

- **分组：** 公开审核题
- **Task ID：** `v3-public-2adfb9bf033b-arithmetic`
- **Family：** `v3-public-signed_percent_change-v1`
- **成功次数：** 2/8（选中第7次采样）
- **难度标记：** 🟠 稀有成功（适合搜索，但需重点核验）
- **是否调用工具：** 是
- **来源ID：** `858940e9-21f1-45db-acf2-21f298e367e5`

**中文题意：** 括号表示费用。按费用绝对金额计算：利息费用由2017年的14762增至2018年的28176。增加记正、减少记负，求百分比变化。

- **模型公式：** `(28176 - 14762) / 14762 * 100`
- **工具返回：** `90.86844601002574`
- **模型final：** `90.87`
- **GT：** `90.87`
- **允许误差：** `0.005`

<details>
<summary>查看原英文问题</summary>

Parentheses denote expenses. Using the absolute expense amounts, what was the percentage change in interest expense from 2017 to 2018? Report an increase as positive and a decrease as negative.

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 2. 四个福利修订额的算术平均

- **分组：** 公开审核题
- **Task ID：** `v3-public-42e42100b593-arithmetic`
- **Family：** `v3-public-signed_multi_value_average-v1`
- **成功次数：** 1/8（选中第5次采样）
- **难度标记：** 🟠 稀有成功（适合搜索，但需重点核验）
- **是否调用工具：** 是
- **来源ID：** `a018d9b5-a8ed-4b3d-b4cb-7fdf8692b17c`

**中文题意：** 2018和2019财年中，养老金福利修订额为-1.4、-0.6，其他福利修订额为0.8、17.2。求这四个数的算术平均值。

- **模型公式：** `(-1.4 + -0.6 + 0.8 + 17.2) / 4`
- **工具返回：** `4`
- **模型final：** `4`
- **GT：** `4.0`
- **允许误差：** `0.005`

<details>
<summary>查看原英文问题</summary>

For fiscal 2018 and 2019, what is the arithmetic mean of the four amendment amounts shown for pension benefits and other benefits?

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 3. 两年合并口径的长期债务占比

- **分组：** 公开审核题
- **Task ID：** `v3-public-7aca02f2885b-arithmetic`
- **Family：** `v3-public-ratio_of_aggregates-v1`
- **成功次数：** 1/8（选中第4次采样）
- **难度标记：** 🟠 稀有成功（适合搜索，但需重点核验）
- **是否调用工具：** 是
- **来源ID：** `IPG/2014/page_37.pdf-1`

**中文题意：** 2014与2013年的长期债务分别为1623.5和1129.8，总债务分别为1732.8和1662.5。按两年合并口径，求长期债务占总债务的百分比。

- **模型公式：** `(1623.5 + 1129.8) / (1732.8 + 1662.5) * 100`
- **工具返回：** `81.09150885046976`
- **模型final：** `81.09`
- **GT：** `81.09`
- **允许误差：** `0.005`

<details>
<summary>查看原英文问题</summary>

Using a combined 2013-and-2014 basis, what percentage of total debt was long-term debt?

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 4. 未拨备债务绝对金额的变化率

- **分组：** 公开审核题
- **Task ID：** `v3-public-9d6f397353af-arithmetic`
- **Family：** `v3-public-signed_percent_change-v1`
- **成功次数：** 2/8（选中第2次采样）
- **难度标记：** 🟠 稀有成功（适合搜索，但需重点核验）
- **是否调用工具：** 是
- **来源ID：** `27c35832-3665-49c5-98df-e669b51effaf`

**中文题意：** 括号表示负债。按负债绝对金额计算：未拨备债务由2018年的28变为2019年的30。金额增加记正、减少记负，求百分比变化。

- **模型公式：** `(30 - 28) / 28 * 100`
- **工具返回：** `7.142857142857143`
- **模型final：** `7.14`
- **GT：** `7.14`
- **允许误差：** `0.005`

<details>
<summary>查看原英文问题</summary>

Parentheses denote liabilities. Using the absolute liability amounts, what was the percentage change in unfunded obligations from 2018 to 2019? Report an increase as positive and a decrease as negative.

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 5. 保修成本绝对金额的变化率

- **分组：** 公开审核题
- **Task ID：** `v3-public-aa20ff7068b0-arithmetic`
- **Family：** `v3-public-signed_percent_change-v1`
- **成功次数：** 2/8（选中第2次采样）
- **难度标记：** 🟠 稀有成功（适合搜索，但需重点核验）
- **是否调用工具：** 否 ⚠️
- **来源ID：** `bc009826-d4f1-4c53-9e3c-0e6349e8b527`

**中文题意：** 括号表示成本。按成本绝对金额计算：已发生保修成本由2018年的26降至2019年的22。增加记正、减少记负，求百分比变化。

- **模型路径：** 未调用计算器，直接给出final。
- **模型final：** `-15.38`
- **GT：** `-15.38`
- **允许误差：** `0.005`

<details>
<summary>查看原英文问题</summary>

Parentheses denote costs. Using the absolute cost amounts, what was the percentage change in warranty costs incurred from 2018 to 2019? Report an increase as positive and a decrease as negative.

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 6. 3月至4月的加权平均回购价

- **分组：** 公开审核题
- **Task ID：** `v3-public-cb26a8ffa95b-arithmetic`
- **Family：** `v3-public-weighted_average-v1`
- **成功次数：** 1/8（选中第8次采样）
- **难度标记：** 🟠 稀有成功（适合搜索，但需重点核验）
- **是否调用工具：** 是
- **来源ID：** `347e3b8b-1982-4c53-a585-ab3001baed32`

**中文题意：** 3月回购58.0百万股（5800万股）、平均每股52.93美元；4月回购29.1百万股（2910万股）、平均每股54.41美元。按回购股数加权，求两个月合计的平均每股回购价格。

- **模型公式：** `(58.0 * 52.93 + 29.1 * 54.41) / (58.0 + 29.1)`
- **工具返回：** `53.42446613088404`
- **模型final：** `53.42`
- **GT：** `53.42`
- **允许误差：** `0.005`

<details>
<summary>查看原英文问题</summary>

What was the Average Price Paid per Share from March 2019 to April 2019?

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 7. 流动与非流动合同资产合计变化率

- **分组：** 公开审核题
- **Task ID：** `v3-public-e511f3abfa5e-arithmetic`
- **Family：** `v3-public-aggregate_percent_change-v1`
- **成功次数：** 1/8（选中第5次采样）
- **难度标记：** 🟠 稀有成功（适合搜索，但需重点核验）
- **是否调用工具：** 是
- **来源ID：** `2b937b8e-a4b1-425c-a381-d6eab14bcc09`

**中文题意：** 流动合同资产由169增至2350，非流动合同资产由507增至581。求合同资产合计余额从2018到2019年的百分比变化。

- **模型公式：** `(2350 + 581) / (169 + 507) * 100 - 100`
- **工具返回：** `333.57988165680473`
- **模型final：** `333.58%`
- **GT：** `333.58`
- **允许误差：** `0.005`

<details>
<summary>查看原英文问题</summary>

What is the percentage change of total balances of contract assets, including current and non-current, from 2018 to 2019?

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 8. 两个业务合计净销售额的增长率

- **分组：** 公开审核题
- **Task ID：** `v3-public-f2f32edba913-arithmetic`
- **Family：** `v3-public-aggregate_percent_change-v1`
- **成功次数：** 3/8（选中第2次采样）
- **难度标记：** 🟢 中间难度（优先审核）
- **是否调用工具：** 是
- **来源ID：** `d161e8c3-56f2-44bb-8c38-635fca79b1aa`

**中文题意：** International业务净销售额由2017年的816.0增至2018年的843.5；Refrigerated & Frozen由2652.7增至2753.0。求两个业务合计净销售额从2017到2018年的百分比变化。

- **模型公式：** `((843.5 + 2753.0) - (816.0 + 2652.7)) / (816.0 + 2652.7) * 100`
- **工具返回：** `3.684377432467495`
- **模型final：** `3.68%`
- **GT：** `3.68`
- **允许误差：** `0.005`

<details>
<summary>查看原英文问题</summary>

What is the percentage change in total net sales of International and Refrigerated & Frozen from the fiscal year 2017 to 2018?

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 9. 多层包装扣除损坏品（一）

- **分组：** 自建V2题
- **Task ID：** `v3-screen-curriculum-v2-cartons-damage-000`
- **Family：** `curriculum-v2-cartons-damage`
- **成功次数：** 4/8（选中第1次采样）
- **难度标记：** 🟢 中间难度（优先审核）
- **是否调用工具：** 是

**中文题意：** 3箱货物，每箱4包，每包6件。去掉5件损坏品和2件样品后，还剩多少件可销售商品？

- **模型公式：** `3 * 4 * 6 - 5 - 2`
- **工具返回：** `65`
- **模型final：** `65`
- **GT：** `65`
- **允许误差：** `1e-06`

<details>
<summary>查看原英文问题</summary>

A shipment has 3 cartons, 4 packs per carton, and 6 items per pack. After 5 damaged items and 2 sample items are removed, how many saleable items remain?

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 10. 多层包装扣除损坏品（二）

- **分组：** 自建V2题
- **Task ID：** `v3-screen-curriculum-v2-cartons-damage-001`
- **Family：** `curriculum-v2-cartons-damage`
- **成功次数：** 2/8（选中第4次采样）
- **难度标记：** 🟠 稀有成功（适合搜索，但需重点核验）
- **是否调用工具：** 是

**中文题意：** 4箱货物，每箱5包，每包7件。去掉6件损坏品和3件样品后，还剩多少件可销售商品？

- **模型公式：** `(4 * 5 * 7) - 6 - 3`
- **工具返回：** `131`
- **模型final：** `131`
- **GT：** `131`
- **允许误差：** `1e-06`

<details>
<summary>查看原英文问题</summary>

A shipment has 4 cartons, 5 packs per carton, and 7 items per pack. After 6 damaged items and 3 sample items are removed, how many saleable items remain?

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 11. 连续增长两年后扣费（一）

- **分组：** 自建V2题
- **Task ID：** `v3-screen-curriculum-v2-growth-fee-000`
- **Family：** `curriculum-v2-growth-fee`
- **成功次数：** 7/8（选中第1次采样）
- **难度标记：** 🟡 接近过易
- **是否调用工具：** 是

**中文题意：** 账户初始200美元，连续两年每年增长5%，然后一次性扣除8美元费用。求最终余额。

- **模型公式：** `200 * 1.05 * 1.05 - 8`
- **工具返回：** `212.5`
- **模型final：** `212.50`
- **GT：** `212.5`
- **允许误差：** `0.005`

<details>
<summary>查看原英文问题</summary>

An account starts with $200, grows by 5% in each of two years, then a one-time $8 fee is deducted. What is the balance? Round to two decimals.

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 12. 连续增长两年后扣费（二）

- **分组：** 自建V2题
- **Task ID：** `v3-screen-curriculum-v2-growth-fee-001`
- **Family：** `curriculum-v2-growth-fee`
- **成功次数：** 5/8（选中第2次采样）
- **难度标记：** 🟢 中间难度（优先审核）
- **是否调用工具：** 是

**中文题意：** 账户初始225美元，连续两年每年增长6%，然后一次性扣除9美元费用。求最终余额。

- **模型公式：** `225 * (1 + 0.06) * (1 + 0.06) - 9`
- **工具返回：** `243.81`
- **模型final：** `243.81`
- **GT：** `243.81`
- **允许误差：** `0.005`

<details>
<summary>查看原英文问题</summary>

An account starts with $225, grows by 6% in each of two years, then a one-time $9 fee is deducted. What is the balance? Round to two decimals.

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 13. 先加价再打折（一）

- **分组：** 自建V2题
- **Task ID：** `v3-screen-curriculum-v2-markup-discount-000`
- **Family：** `curriculum-v2-markup-discount`
- **成功次数：** 3/8（选中第3次采样）
- **难度标记：** 🟢 中间难度（优先审核）
- **是否调用工具：** 是

**中文题意：** 商品成本80美元，先加价25%，再对标价打九折。求最终价格，保留两位小数。

- **模型公式：** `80 * 1.25 * 0.9`
- **工具返回：** `90`
- **模型final：** `90.0`
- **GT：** `90.00`
- **允许误差：** `0.005`

<details>
<summary>查看原英文问题</summary>

A product costs $80. Its price is increased by 25%, then the marked price is discounted by 10%. What is the final price? Round to two decimals.

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 14. 先加价再打折（二）

- **分组：** 自建V2题
- **Task ID：** `v3-screen-curriculum-v2-markup-discount-001`
- **Family：** `curriculum-v2-markup-discount`
- **成功次数：** 6/8（选中第2次采样）
- **难度标记：** 🟢 中间难度（优先审核）
- **是否调用工具：** 是

**中文题意：** 商品成本100美元，先加价30%，再对标价打八五折。求最终价格，保留两位小数。

- **模型公式：** `100 * 1.30 * 0.85`
- **工具返回：** `110.5`
- **模型final：** `110.50`
- **GT：** `110.50`
- **允许误差：** `0.005`

<details>
<summary>查看原英文问题</summary>

A product costs $100. Its price is increased by 30%, then the marked price is discounted by 15%. What is the final price? Round to two decimals.

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 15. 反推第五次考试成绩（一）

- **分组：** 自建V2题
- **Task ID：** `v3-screen-curriculum-v2-required-score-000`
- **Family：** `curriculum-v2-required-score`
- **成功次数：** 2/8（选中第4次采样）
- **难度标记：** 🟠 稀有成功（适合搜索，但需重点核验）
- **是否调用工具：** 是

**中文题意：** 前四次成绩为62、68、74、80。若五次平均分需要达到75，第五次应得多少分？

- **模型公式：** `(75 * 5) - (62 + 68 + 74 + 80)`
- **工具返回：** `91`
- **模型final：** `91`
- **GT：** `91`
- **允许误差：** `1e-06`

<details>
<summary>查看原英文问题</summary>

Four test scores are 62, 68, 74, 80. What fifth score is needed for an average of 75 across all five tests?

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 16. 反推第五次考试成绩（二）

- **分组：** 自建V2题
- **Task ID：** `v3-screen-curriculum-v2-required-score-001`
- **Family：** `curriculum-v2-required-score`
- **成功次数：** 6/8（选中第1次采样）
- **难度标记：** 🟢 中间难度（优先审核）
- **是否调用工具：** 是

**中文题意：** 前四次成绩为63、69、75、81。若五次平均分需要达到76，第五次应得多少分？

- **模型公式：** `(76 * 5) - (63 + 69 + 75 + 81)`
- **工具返回：** `92`
- **模型final：** `92`
- **GT：** `92`
- **允许误差：** `1e-06`

<details>
<summary>查看原英文问题</summary>

Four test scores are 63, 69, 75, 81. What fifth score is needed for an average of 76 across all five tests?

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 17. 销售、退货与服务费（一）

- **分组：** 自建V2题
- **Task ID：** `v3-screen-curriculum-v2-sales-returns-000`
- **Family：** `curriculum-v2-sales-returns`
- **成功次数：** 2/8（选中第1次采样）
- **难度标记：** 🟠 稀有成功（适合搜索，但需重点核验）
- **是否调用工具：** 是

**中文题意：** 售出18件普通商品，每件9美元；7件高级商品，每件15美元。退回2件普通商品，另收入11美元服务费。求净收入。

- **模型公式：** `(18 * 9) + (7 * 15) - (2 * 9) + 11`
- **工具返回：** `260`
- **模型final：** `260`
- **GT：** `260`
- **允许误差：** `1e-06`

<details>
<summary>查看原英文问题</summary>

A store sold 18 regular items at $9 each and 7 premium items at $15 each. Customers returned 2 regular items, and the store also earned a fixed $11 service fee. What was net revenue?

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 18. 销售、退货与服务费（二）

- **分组：** 自建V2题
- **Task ID：** `v3-screen-curriculum-v2-sales-returns-001`
- **Family：** `curriculum-v2-sales-returns`
- **成功次数：** 5/8（选中第2次采样）
- **难度标记：** 🟢 中间难度（优先审核）
- **是否调用工具：** 是

**中文题意：** 售出19件普通商品，每件10美元；8件高级商品，每件16美元。退回3件普通商品，另收入12美元服务费。求净收入。

- **模型公式：** `(19 * 10) + (8 * 16) - (3 * 10) + 12`
- **工具返回：** `300`
- **模型final：** `300`
- **GT：** `300`
- **允许误差：** `1e-06`

<details>
<summary>查看原英文问题</summary>

A store sold 19 regular items at $10 each and 8 premium items at $16 each. Customers returned 3 regular items, and the store also earned a fixed $12 service fee. What was net revenue?

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 19. 含免单者的均摊账单（一）

- **分组：** 自建V2题
- **Task ID：** `v3-screen-curriculum-v2-shared-bill-000`
- **Family：** `curriculum-v2-shared-bill`
- **成功次数：** 8/8（选中第1次采样）
- **难度标记：** ⚪ 8/8全对（可能过易）
- **是否调用工具：** 是

**中文题意：** 6人的餐费为每人14美元，另有20美元房间费。其中1人不付款，其余人平摊全部账单。每位付款者应付多少？

- **模型公式：** `(6 * 14 + 20) / 5`
- **工具返回：** `20.8`
- **模型final：** `20.80`
- **GT：** `20.8`
- **允许误差：** `0.005`

<details>
<summary>查看原英文问题</summary>

A group of 6 people has meals costing $14 per person plus a $20 room charge. 1 guests pay nothing, so the others split the entire bill equally. How much does each paying person owe? Round to two decimals.

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 20. 含免单者的均摊账单（二）

- **分组：** 自建V2题
- **Task ID：** `v3-screen-curriculum-v2-shared-bill-001`
- **Family：** `curriculum-v2-shared-bill`
- **成功次数：** 7/8（选中第1次采样）
- **难度标记：** 🟡 接近过易
- **是否调用工具：** 是

**中文题意：** 7人的餐费为每人15美元，另有22美元房间费。其中2人不付款，其余人平摊全部账单。每位付款者应付多少？

- **模型公式：** `(7 * 15 + 22) / (7 - 2)`
- **工具返回：** `25.4`
- **模型final：** `25.40`
- **GT：** `25.4`
- **允许误差：** `0.005`

<details>
<summary>查看原英文问题</summary>

A group of 7 people has meals costing $15 per person plus a $22 room charge. 2 guests pay nothing, so the others split the entire bill equally. How much does each paying person owe? Round to two decimals.

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 21. 按打购买鸡蛋

- **分组：** 新GSM8K-train题
- **Task ID：** `v3-gsm8k-train-0535-calculator`
- **Family：** `v3-gsm8k-public-train-calculator-v1`
- **成功次数：** 4/8（选中第2次采样）
- **难度标记：** 🟢 中间难度（优先审核）
- **是否调用工具：** 是
- **GSM8K source_index：** `535`

**中文题意：** Tim买了3打鸡蛋，每个鸡蛋0.50美元。一共支付多少美元？

- **模型公式：** `3 * 12 * 0.50`
- **工具返回：** `18`
- **模型final：** `18`
- **GT：** `18`
- **允许误差：** `1e-06`

<details>
<summary>查看原英文问题</summary>

Tim buys 3 dozen eggs.  Eggs cost $.50 each.  How much did he pay for eggs?

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 22. 反推原有狗粮重量

- **分组：** 新GSM8K-train题
- **Task ID：** `v3-gsm8k-train-0544-calculator`
- **Family：** `v3-gsm8k-public-train-calculator-v1`
- **成功次数：** 4/8（选中第1次采样）
- **难度标记：** 🟢 中间难度（优先审核）
- **是否调用工具：** 否 ⚠️
- **GSM8K source_index：** `544`

**中文题意：** Elise买了一袋15千克和一袋10千克狗粮，此时共有40千克。购买前原有多少千克？

- **模型路径：** 未调用计算器，直接给出final。
- **模型final：** `15`
- **GT：** `15`
- **允许误差：** `1e-06`

<details>
<summary>查看原英文问题</summary>

Elise is buying more dog food. She buys a 15kg bag then another 10kg bag, and she now has 40kg of dog food. How many kilograms of dog food did Elise already have?

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 23. 游戏中有趣内容时长

- **分组：** 新GSM8K-train题
- **Task ID：** `v3-gsm8k-train-2502-calculator`
- **Family：** `v3-gsm8k-public-train-calculator-v1`
- **成功次数：** 4/8（选中第1次采样）
- **难度标记：** 🟢 中间难度（优先审核）
- **是否调用工具：** 否 ⚠️
- **GSM8K source_index：** `2502`

**中文题意：** 游戏承诺100小时内容，其中80%是枯燥刷取；扩展包再增加30小时有趣内容。总共有多少小时有趣内容？

- **模型路径：** 未调用计算器，直接给出final。
- **模型final：** `50`
- **GT：** `50`
- **允许误差：** `1e-06`

<details>
<summary>查看原英文问题</summary>

James gets bored with his game so decides to play a different one.  That game promises 100 hours of gameplay but 80% of that is boring grinding.  However, the expansion does add another 30 hours of enjoyable gameplay.  How much enjoyable gameplay does James get?

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 24. 两人每小时销量差

- **分组：** 新GSM8K-train题
- **Task ID：** `v3-gsm8k-train-3229-calculator`
- **Family：** `v3-gsm8k-public-train-calculator-v1`
- **成功次数：** 7/8（选中第1次采样）
- **难度标记：** 🟡 接近过易
- **是否调用工具：** 是
- **GSM8K source_index：** `3229`

**中文题意：** Stanley每小时卖4杯柠檬水，Carl每小时卖7杯。3小时内Carl比Stanley多卖多少杯？

- **模型公式：** `(7 - 4) * 3`
- **工具返回：** `9`
- **模型final：** `9`
- **GT：** `9`
- **允许误差：** `1e-06`

<details>
<summary>查看原英文问题</summary>

Stanley sold 4 cups of lemonade an hour. His brother, Carl, sold 7 cups of lemonade an hour. How many more cups did Carl sell than Stanley in 3 hours?

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 25. 两天制作与吃掉的布朗尼

- **分组：** 新GSM8K-train题
- **Task ID：** `v3-gsm8k-train-3946-calculator`
- **Family：** `v3-gsm8k-public-train-calculator-v1`
- **成功次数：** 1/8（选中第8次采样）
- **难度标记：** 🟠 稀有成功（适合搜索，但需重点核验）
- **是否调用工具：** 否 ⚠️
- **GSM8K source_index：** `3946`

**中文题意：** 第一天做2打布朗尼，父亲吃8块、女儿吃4块。第二天又做2打并加入剩余部分。台面上共有多少块？

- **模型路径：** 未调用计算器，直接给出final。
- **模型final：** `36`
- **GT：** `36`
- **允许误差：** `1e-06`

<details>
<summary>查看原英文问题</summary>

Mother made 2 dozen brownies and placed them on the kitchen counter to cool.  Father smelled the brownies, came into the kitchen and ate 8 of them. Then, their daughter, Mooney, wandered into the kitchen and ate 4 of the brownies. The next morning, Mother made another two dozen brownies and added them to those remaining from the day before.  After that, how many brownies were on the counter?

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 26. 薯片袋数的增减

- **分组：** 新GSM8K-train题
- **Task ID：** `v3-gsm8k-train-5525-calculator`
- **Family：** `v3-gsm8k-public-train-calculator-v1`
- **成功次数：** 6/8（选中第1次采样）
- **难度标记：** 🟢 中间难度（优先审核）
- **是否调用工具：** 否 ⚠️
- **GSM8K source_index：** `5525`

**中文题意：** Abie原有20袋薯片，送给朋友4袋，又在商店买了6袋。最后有多少袋？

- **模型路径：** 未调用计算器，直接给出final。
- **模型final：** `22`
- **GT：** `22`
- **允许误差：** `1e-06`

<details>
<summary>查看原英文问题</summary>

Abie had 20 bags of chips. She gave 4 bags to her friend and bought another 6 bags of chips in the store. How many bags of chips does Abie have in the end?

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 27. 同日往返两个相反方向的地点

- **分组：** 新GSM8K-train题
- **Task ID：** `v3-gsm8k-train-6486-calculator`
- **Family：** `v3-gsm8k-public-train-calculator-v1`
- **成功次数：** 2/8（选中第4次采样）
- **难度标记：** 🟠 稀有成功（适合搜索，但需重点核验）
- **是否调用工具：** 是
- **GSM8K source_index：** `6486`

**中文题意：** Janet从家向东30英里看皮肤科，又要从家向西50英里看妇科。同一天完成两次看诊并分别返回家中，汽车每加仑行驶20英里。共用多少加仑汽油？

- **模型公式：** `(30 + 50 + 30 + 50) / 20`
- **工具返回：** `8`
- **模型final：** `8`
- **GT：** `8`
- **允许误差：** `1e-06`

<details>
<summary>查看原英文问题</summary>

Janet has to drive 30 miles east from home to see her dermatologist and 50 miles west from home to see her gynecologist. If she has appointments with both doctors on the same day, how many gallons of gas does she use driving to both appointments and back home again, if her car gets 20 miles per gallon?

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

## 28. 两类外星学生的脚趾总数

- **分组：** 新GSM8K-train题
- **Task ID：** `v3-gsm8k-train-6511-calculator`
- **Family：** `v3-gsm8k-public-train-calculator-v1`
- **成功次数：** 1/8（选中第1次采样）
- **难度标记：** 🟠 稀有成功（适合搜索，但需重点核验）
- **是否调用工具：** 是
- **GSM8K source_index：** `6511`

**中文题意：** 每个Hoopit有4只手，每只手3个脚趾；每个Neglart有5只手，每只手2个脚趾。校车载7个Hoopit和8个Neglart，共有多少个脚趾？

- **模型公式：** `(7 * 3 * 4) + (8 * 2 * 5)`
- **工具返回：** `164`
- **模型final：** `164`
- **GT：** `164`
- **允许误差：** `1e-06`

<details>
<summary>查看原英文问题</summary>

On the planet Popton, there are two races of beings: the Hoopits and Neglarts.  Each Hoopit has 3 toes on each of their 4 hands, while each Neglart only has 2 toes on each of their 5 hands. If a Popton automated driverless school bus always carries 7 Hoopit students and 8 Neglart students, how many toes are on the Popton school bus?

</details>

### 人工审核

- [ ] 中文题意与英文来源一致
- [ ] 题目无歧义且没有泄露解法
- [ ] 模型公式/直接推理在语义上正确
- [ ] 工具结果、final和GT一致
- [ ] 轨迹不是偶然命中或verifier漏洞
- [ ] 批准进入SFT候选
- **审核备注：**

---

