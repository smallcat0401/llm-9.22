# V4 从原种子题直接扩充：中文审核稿

> 数据文件仍保留英文原题；本页中文仅供人工审核，不会作为模型训练输入。

## 后续审核记录

- 2026-10-05：项目所有者确认本页 84 道新增题全部审核通过。
- 已批准副本：`data/generated/v4_seed_derived_self_written_approved_v1.jsonl`。
- 下方 `pending` 描述和空复选框保留的是审核发生前的候选状态。
- 已批准文件仍只是任务集；生成并审核轨迹后才能形成 SFT 数据。

## 本批边界

- 母题 family：6 个。
- 每个 family 的母题：V3 已审核的 `000`、`001` 两题。
- 每个 family 的新增变体：14 题，使用生成器索引 `002`—`015`。
- 新增候选总数：84 题。
- 当前状态：`review_status=pending`、`training_eligible=false`，尚未并入 SFT。
- 只扩充历史 train family；旧 validation/test family 没有被挪入训练。

## 审核重点

1. 题意是否明确，但没有把解题公式直接写进题目。
2. 数值是否自然，答案是否处于合理范围。
3. 中文翻译是否准确表达英文原题；真正训练仍使用英文。
4. 参考公式只用于离线校验，不会放进用户问题。

## 销售、退货与固定服务费

- Family：`curriculum-v2-sales-returns`
- 扩充方式：保持母题数量关系，独立生成数值，并轮换三种措辞或场景。

### 已审核母题

- `curriculum-v2-sales-returns-000`：一家商店以每件 9 美元售出 18 件普通商品，并以每件 15 美元售出 7 件高档商品。顾客退回 2 件普通商品，商店另获得固定 11 美元服务费。净收入是多少？
  - 参考公式：`(18-2)*9+7*15+11`
  - GT：`260`
- `curriculum-v2-sales-returns-001`：一家商店以每件 10 美元售出 19 件普通商品，并以每件 16 美元售出 8 件高档商品。顾客退回 3 件普通商品，商店另获得固定 12 美元服务费。净收入是多少？
  - 参考公式：`(19-3)*10+8*16+12`
  - GT：`300`

### 新增待审核变体

#### 1. `v4-review-curriculum-v2-sales-returns-002`

- 中文题意：一家商店以每件 14 美元售出 45 件普通商品，并以每件 18 美元售出 20 件高档商品。顾客全额退回 4 件普通商品，商店另获得固定 27 美元服务费。净收入是多少？
- 英文原题：A store sold 45 regular items at $14 each and 20 premium items at $18 each. Customers returned 4 regular items for full refunds, and the store earned a fixed $27 service fee. What was net revenue?
- 参考公式：`(45-4)*14+20*18+27`
- GT：`961`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 2. `v4-review-curriculum-v2-sales-returns-003`

- 中文题意：一个市场摊位售出 46 件单价 13 美元的基础商品和 13 件单价 27 美元的升级商品。随后有 7 件基础商品全额退回；另有 8 美元服务收入。最终保留的收入是多少？
- 英文原题：A market booth recorded sales of 46 basic units at $13 apiece and 13 upgraded units at $27 apiece. Later, 7 basic units were returned for full refunds. Including a separate $8 service payment, what revenue remained?
- 参考公式：`(46-7)*13+13*27+8`
- GT：`866`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 3. `v4-review-curriculum-v2-sales-returns-004`

- 中文题意：一家网店售出并发出 38 件单价 18 美元的标准商品和 23 件单价 32 美元的豪华商品。网店对 4 件标准商品作全额退款，并另外收取固定 18 美元手续费。求网店净收入。
- 英文原题：An online seller sold and shipped 38 standard products at $18 each and 23 deluxe products at $32 each. It fully refunded 4 standard products and also collected a fixed $18 handling fee. Find the seller's net revenue.
- 参考公式：`(38-4)*18+23*32+18`
- GT：`1366`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 4. `v4-review-curriculum-v2-sales-returns-005`

- 中文题意：一家商店以每件 10 美元售出 58 件普通商品，并以每件 19 美元售出 18 件高档商品。顾客全额退回 8 件普通商品，商店另获得固定 6 美元服务费。净收入是多少？
- 英文原题：A store sold 58 regular items at $10 each and 18 premium items at $19 each. Customers returned 8 regular items for full refunds, and the store earned a fixed $6 service fee. What was net revenue?
- 参考公式：`(58-8)*10+18*19+6`
- GT：`848`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 5. `v4-review-curriculum-v2-sales-returns-006`

- 中文题意：一家网店售出并发出 43 件单价 12 美元的标准商品和 18 件单价 26 美元的豪华商品。网店对 8 件标准商品作全额退款，并另外收取固定 41 美元手续费。求网店净收入。
- 英文原题：An online seller sold and shipped 43 standard products at $12 each and 18 deluxe products at $26 each. It fully refunded 8 standard products and also collected a fixed $41 handling fee. Find the seller's net revenue.
- 参考公式：`(43-8)*12+18*26+41`
- GT：`929`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 6. `v4-review-curriculum-v2-sales-returns-007`

- 中文题意：一家网店售出并发出 55 件单价 16 美元的标准商品和 21 件单价 30 美元的豪华商品。网店对 7 件标准商品作全额退款，并另外收取固定 20 美元手续费。求网店净收入。
- 英文原题：An online seller sold and shipped 55 standard products at $16 each and 21 deluxe products at $30 each. It fully refunded 7 standard products and also collected a fixed $20 handling fee. Find the seller's net revenue.
- 参考公式：`(55-7)*16+21*30+20`
- GT：`1418`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 7. `v4-review-curriculum-v2-sales-returns-008`

- 中文题意：一家网店售出并发出 43 件单价 10 美元的标准商品和 19 件单价 15 美元的豪华商品。网店对 2 件标准商品作全额退款，并另外收取固定 21 美元手续费。求网店净收入。
- 英文原题：An online seller sold and shipped 43 standard products at $10 each and 19 deluxe products at $15 each. It fully refunded 2 standard products and also collected a fixed $21 handling fee. Find the seller's net revenue.
- 参考公式：`(43-2)*10+19*15+21`
- GT：`716`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 8. `v4-review-curriculum-v2-sales-returns-009`

- 中文题意：一个市场摊位售出 38 件单价 10 美元的基础商品和 16 件单价 19 美元的升级商品。随后有 4 件基础商品全额退回；另有 34 美元服务收入。最终保留的收入是多少？
- 英文原题：A market booth recorded sales of 38 basic units at $10 apiece and 16 upgraded units at $19 apiece. Later, 4 basic units were returned for full refunds. Including a separate $34 service payment, what revenue remained?
- 参考公式：`(38-4)*10+16*19+34`
- GT：`678`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 9. `v4-review-curriculum-v2-sales-returns-010`

- 中文题意：一家网店售出并发出 32 件单价 24 美元的标准商品和 9 件单价 30 美元的豪华商品。网店对 3 件标准商品作全额退款，并另外收取固定 6 美元手续费。求网店净收入。
- 英文原题：An online seller sold and shipped 32 standard products at $24 each and 9 deluxe products at $30 each. It fully refunded 3 standard products and also collected a fixed $6 handling fee. Find the seller's net revenue.
- 参考公式：`(32-3)*24+9*30+6`
- GT：`972`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 10. `v4-review-curriculum-v2-sales-returns-011`

- 中文题意：一家商店以每件 20 美元售出 36 件普通商品，并以每件 29 美元售出 6 件高档商品。顾客全额退回 1 件普通商品，商店另获得固定 40 美元服务费。净收入是多少？
- 英文原题：A store sold 36 regular items at $20 each and 6 premium items at $29 each. Customers returned 1 regular item for full refunds, and the store earned a fixed $40 service fee. What was net revenue?
- 参考公式：`(36-1)*20+6*29+40`
- GT：`914`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 11. `v4-review-curriculum-v2-sales-returns-012`

- 中文题意：一家网店售出并发出 59 件单价 14 美元的标准商品和 7 件单价 26 美元的豪华商品。网店对 7 件标准商品作全额退款，并另外收取固定 17 美元手续费。求网店净收入。
- 英文原题：An online seller sold and shipped 59 standard products at $14 each and 7 deluxe products at $26 each. It fully refunded 7 standard products and also collected a fixed $17 handling fee. Find the seller's net revenue.
- 参考公式：`(59-7)*14+7*26+17`
- GT：`927`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 12. `v4-review-curriculum-v2-sales-returns-013`

- 中文题意：一个市场摊位售出 38 件单价 10 美元的基础商品和 7 件单价 23 美元的升级商品。随后有 8 件基础商品全额退回；另有 34 美元服务收入。最终保留的收入是多少？
- 英文原题：A market booth recorded sales of 38 basic units at $10 apiece and 7 upgraded units at $23 apiece. Later, 8 basic units were returned for full refunds. Including a separate $34 service payment, what revenue remained?
- 参考公式：`(38-8)*10+7*23+34`
- GT：`495`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 13. `v4-review-curriculum-v2-sales-returns-014`

- 中文题意：一家网店售出并发出 55 件单价 10 美元的标准商品和 25 件单价 21 美元的豪华商品。网店对 1 件标准商品作全额退款，并另外收取固定 20 美元手续费。求网店净收入。
- 英文原题：An online seller sold and shipped 55 standard products at $10 each and 25 deluxe products at $21 each. It fully refunded 1 standard product and also collected a fixed $20 handling fee. Find the seller's net revenue.
- 参考公式：`(55-1)*10+25*21+20`
- GT：`1085`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 14. `v4-review-curriculum-v2-sales-returns-015`

- 中文题意：一家商店以每件 21 美元售出 40 件普通商品，并以每件 34 美元售出 20 件高档商品。顾客全额退回 5 件普通商品，商店另获得固定 12 美元服务费。净收入是多少？
- 英文原题：A store sold 40 regular items at $21 each and 20 premium items at $34 each. Customers returned 5 regular items for full refunds, and the store earned a fixed $12 service fee. What was net revenue?
- 参考公式：`(40-5)*21+20*34+12`
- GT：`1427`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

## 先加价、再打折

- Family：`curriculum-v2-markup-discount`
- 扩充方式：保持母题数量关系，独立生成数值，并轮换三种措辞或场景。

### 已审核母题

- `curriculum-v2-markup-discount-000`：一件商品成本为 80 美元。价格先提高 25%，再对标价打 10% 的折扣。最终价格是多少？结果保留两位小数。
  - 参考公式：`80*(1+25/100)*(1-10/100)`
  - GT：`90.0`
- `curriculum-v2-markup-discount-001`：一件商品成本为 100 美元。价格先提高 30%，再对标价打 15% 的折扣。最终价格是多少？结果保留两位小数。
  - 参考公式：`100*(1+30/100)*(1-15/100)`
  - GT：`110.5`

### 新增待审核变体

#### 1. `v4-review-curriculum-v2-markup-discount-002`

- 中文题意：一件商品成本为 410 美元。价格先提高 12%，再对标价优惠 7%。最终价格是多少？结果保留两位小数。
- 英文原题：A product costs $410. Its price is increased by 12%, then the marked price is discounted by 7%. What is the final price? Round to two decimals.
- 参考公式：`410*(1+12/100)*(1-7/100)`
- GT：`427.06`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 2. `v4-review-curriculum-v2-markup-discount-003`

- 中文题意：零售商在一件成本为 210 美元的商品上加价 32% 得到标价。促销时再从标价中减去 25%。求促销价，保留两位小数。
- 英文原题：A retailer sets the list price of a $210 item by adding 32% to the cost. During a sale, the list price is reduced by 25%. Find the sale price, rounded to two decimals.
- 参考公式：`210*(1+32/100)*(1-25/100)`
- GT：`207.90`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 3. `v4-review-curriculum-v2-markup-discount-004`

- 中文题意：一台设备起始价格为 210 美元，先加价 40%，然后按加价后的价格打 25% 的折扣。最终支付多少？保留两位小数。
- 英文原题：Equipment with a starting price of $210 is first marked up by 40%. A 25% discount is then applied to that marked price. What amount is paid? Round to two decimals.
- 参考公式：`210*(1+40/100)*(1-25/100)`
- GT：`220.50`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 4. `v4-review-curriculum-v2-markup-discount-005`

- 中文题意：一台设备起始价格为 360 美元，先加价 12%，然后按加价后的价格打 20% 的折扣。最终支付多少？保留两位小数。
- 英文原题：Equipment with a starting price of $360 is first marked up by 12%. A 20% discount is then applied to that marked price. What amount is paid? Round to two decimals.
- 参考公式：`360*(1+12/100)*(1-20/100)`
- GT：`322.56`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 5. `v4-review-curriculum-v2-markup-discount-006`

- 中文题意：一台设备起始价格为 165 美元，先加价 32%，然后按加价后的价格打 15% 的折扣。最终支付多少？保留两位小数。
- 英文原题：Equipment with a starting price of $165 is first marked up by 32%. A 15% discount is then applied to that marked price. What amount is paid? Round to two decimals.
- 参考公式：`165*(1+32/100)*(1-15/100)`
- GT：`185.13`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 6. `v4-review-curriculum-v2-markup-discount-007`

- 中文题意：零售商在一件成本为 260 美元的商品上加价 18% 得到标价。促销时再从标价中减去 15%。求促销价，保留两位小数。
- 英文原题：A retailer sets the list price of a $260 item by adding 18% to the cost. During a sale, the list price is reduced by 15%. Find the sale price, rounded to two decimals.
- 参考公式：`260*(1+18/100)*(1-15/100)`
- GT：`260.78`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 7. `v4-review-curriculum-v2-markup-discount-008`

- 中文题意：一台设备起始价格为 565 美元，先加价 40%，然后按加价后的价格打 10% 的折扣。最终支付多少？保留两位小数。
- 英文原题：Equipment with a starting price of $565 is first marked up by 40%. A 10% discount is then applied to that marked price. What amount is paid? Round to two decimals.
- 参考公式：`565*(1+40/100)*(1-10/100)`
- GT：`711.90`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 8. `v4-review-curriculum-v2-markup-discount-009`

- 中文题意：一台设备起始价格为 365 美元，先加价 12%，然后按加价后的价格打 25% 的折扣。最终支付多少？保留两位小数。
- 英文原题：Equipment with a starting price of $365 is first marked up by 12%. A 25% discount is then applied to that marked price. What amount is paid? Round to two decimals.
- 参考公式：`365*(1+12/100)*(1-25/100)`
- GT：`306.60`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 9. `v4-review-curriculum-v2-markup-discount-010`

- 中文题意：零售商在一件成本为 85 美元的商品上加价 12% 得到标价。促销时再从标价中减去 25%。求促销价，保留两位小数。
- 英文原题：A retailer sets the list price of a $85 item by adding 12% to the cost. During a sale, the list price is reduced by 25%. Find the sale price, rounded to two decimals.
- 参考公式：`85*(1+12/100)*(1-25/100)`
- GT：`71.40`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 10. `v4-review-curriculum-v2-markup-discount-011`

- 中文题意：一件商品成本为 240 美元。价格先提高 32%，再对标价优惠 25%。最终价格是多少？结果保留两位小数。
- 英文原题：A product costs $240. Its price is increased by 32%, then the marked price is discounted by 25%. What is the final price? Round to two decimals.
- 参考公式：`240*(1+32/100)*(1-25/100)`
- GT：`237.60`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 11. `v4-review-curriculum-v2-markup-discount-012`

- 中文题意：零售商在一件成本为 275 美元的商品上加价 12% 得到标价。促销时再从标价中减去 25%。求促销价，保留两位小数。
- 英文原题：A retailer sets the list price of a $275 item by adding 12% to the cost. During a sale, the list price is reduced by 25%. Find the sale price, rounded to two decimals.
- 参考公式：`275*(1+12/100)*(1-25/100)`
- GT：`231.00`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 12. `v4-review-curriculum-v2-markup-discount-013`

- 中文题意：一件商品成本为 300 美元。价格先提高 32%，再对标价优惠 7%。最终价格是多少？结果保留两位小数。
- 英文原题：A product costs $300. Its price is increased by 32%, then the marked price is discounted by 7%. What is the final price? Round to two decimals.
- 参考公式：`300*(1+32/100)*(1-7/100)`
- GT：`368.28`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 13. `v4-review-curriculum-v2-markup-discount-014`

- 中文题意：一台设备起始价格为 520 美元，先加价 12%，然后按加价后的价格打 25% 的折扣。最终支付多少？保留两位小数。
- 英文原题：Equipment with a starting price of $520 is first marked up by 12%. A 25% discount is then applied to that marked price. What amount is paid? Round to two decimals.
- 参考公式：`520*(1+12/100)*(1-25/100)`
- GT：`436.80`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 14. `v4-review-curriculum-v2-markup-discount-015`

- 中文题意：一台设备起始价格为 490 美元，先加价 12%，然后按加价后的价格打 10% 的折扣。最终支付多少？保留两位小数。
- 英文原题：Equipment with a starting price of $490 is first marked up by 12%. A 10% discount is then applied to that marked price. What amount is paid? Round to two decimals.
- 参考公式：`490*(1+12/100)*(1-10/100)`
- GT：`493.92`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

## 达到目标平均分所需成绩

- Family：`curriculum-v2-required-score`
- 扩充方式：保持母题数量关系，独立生成数值，并轮换三种措辞或场景。

### 已审核母题

- `curriculum-v2-required-score-000`：前四次考试成绩分别是 62、68、74、80。要使五次考试的平均分达到 75，第五次需要多少分？
  - 参考公式：`75*5-(62+68+74+80)`
  - GT：`91`
- `curriculum-v2-required-score-001`：前四次考试成绩分别是 63、69、75、81。要使五次考试的平均分达到 76，第五次需要多少分？
  - 参考公式：`76*5-(63+69+75+81)`
  - GT：`92`

### 新增待审核变体

#### 1. `v4-review-curriculum-v2-required-score-002`

- 中文题意：四项等权考核的成绩为 76、80、79、88。第五项考核需要多少分，才能使总平均分达到 79.6？
- 英文原题：Four equally weighted assessments produced scores of 76, 80, 79, 88. Determine the fifth assessment score required to make the overall average 79.6.
- 参考公式：`79.6*5-(76+80+79+88)`
- GT：`75`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 2. `v4-review-curriculum-v2-required-score-003`

- 中文题意：四项等权考核的成绩为 75、94、92、70。第五项考核需要多少分，才能使总平均分达到 82.6？
- 英文原题：Four equally weighted assessments produced scores of 75, 94, 92, 70. Determine the fifth assessment score required to make the overall average 82.6.
- 参考公式：`82.6*5-(75+94+92+70)`
- GT：`82`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 3. `v4-review-curriculum-v2-required-score-004`

- 中文题意：四项等权考核的成绩为 63、68、93、62。第五项考核需要多少分，才能使总平均分达到 76.2？
- 英文原题：Four equally weighted assessments produced scores of 63, 68, 93, 62. Determine the fifth assessment score required to make the overall average 76.2.
- 参考公式：`76.2*5-(63+68+93+62)`
- GT：`95`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 4. `v4-review-curriculum-v2-required-score-005`

- 中文题意：前四次考试成绩分别为 89、75、90、73。要使五次考试的平均分达到 78.4，第五次需要多少分？
- 英文原题：Four test scores are 89, 75, 90, 73. What fifth score is needed for an average of 78.4 across all five tests?
- 参考公式：`78.4*5-(89+75+90+73)`
- GT：`65`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 5. `v4-review-curriculum-v2-required-score-006`

- 中文题意：前四次考试成绩分别为 78、78、92、92。要使五次考试的平均分达到 86.2，第五次需要多少分？
- 英文原题：Four test scores are 78, 78, 92, 92. What fifth score is needed for an average of 86.2 across all five tests?
- 参考公式：`86.2*5-(78+78+92+92)`
- GT：`91`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 6. `v4-review-curriculum-v2-required-score-007`

- 中文题意：四项等权考核的成绩为 71、59、62、73。第五项考核需要多少分，才能使总平均分达到 69.6？
- 英文原题：Four equally weighted assessments produced scores of 71, 59, 62, 73. Determine the fifth assessment score required to make the overall average 69.6.
- 参考公式：`69.6*5-(71+59+62+73)`
- GT：`83`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 7. `v4-review-curriculum-v2-required-score-008`

- 中文题意：前四次考试成绩分别为 64、73、67、92。要使五次考试的平均分达到 77.6，第五次需要多少分？
- 英文原题：Four test scores are 64, 73, 67, 92. What fifth score is needed for an average of 77.6 across all five tests?
- 参考公式：`77.6*5-(64+73+67+92)`
- GT：`92`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 8. `v4-review-curriculum-v2-required-score-009`

- 中文题意：一名学生前四次小测成绩为 94、88、94、90。若五次小测的最终平均分需要达到 91.4，最后一次小测必须取得多少分？
- 英文原题：A student's first four quiz scores are 94, 88, 94, 90. To finish with a five-quiz average of 91.4, what score must the student earn on the last quiz?
- 参考公式：`91.4*5-(94+88+94+90)`
- GT：`91`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 9. `v4-review-curriculum-v2-required-score-010`

- 中文题意：前四次考试成绩分别为 89、92、70、94。要使五次考试的平均分达到 88.2，第五次需要多少分？
- 英文原题：Four test scores are 89, 92, 70, 94. What fifth score is needed for an average of 88.2 across all five tests?
- 参考公式：`88.2*5-(89+92+70+94)`
- GT：`96`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 10. `v4-review-curriculum-v2-required-score-011`

- 中文题意：前四次考试成绩分别为 80、64、86、60。要使五次考试的平均分达到 74.8，第五次需要多少分？
- 英文原题：Four test scores are 80, 64, 86, 60. What fifth score is needed for an average of 74.8 across all five tests?
- 参考公式：`74.8*5-(80+64+86+60)`
- GT：`84`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 11. `v4-review-curriculum-v2-required-score-012`

- 中文题意：前四次考试成绩分别为 91、61、60、85。要使五次考试的平均分达到 73.4，第五次需要多少分？
- 英文原题：Four test scores are 91, 61, 60, 85. What fifth score is needed for an average of 73.4 across all five tests?
- 参考公式：`73.4*5-(91+61+60+85)`
- GT：`70`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 12. `v4-review-curriculum-v2-required-score-013`

- 中文题意：四项等权考核的成绩为 80、65、66、66。第五项考核需要多少分，才能使总平均分达到 69.8？
- 英文原题：Four equally weighted assessments produced scores of 80, 65, 66, 66. Determine the fifth assessment score required to make the overall average 69.8.
- 参考公式：`69.8*5-(80+65+66+66)`
- GT：`72`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 13. `v4-review-curriculum-v2-required-score-014`

- 中文题意：四项等权考核的成绩为 83、61、64、63。第五项考核需要多少分，才能使总平均分达到 73.2？
- 英文原题：Four equally weighted assessments produced scores of 83, 61, 64, 63. Determine the fifth assessment score required to make the overall average 73.2.
- 参考公式：`73.2*5-(83+61+64+63)`
- GT：`95`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 14. `v4-review-curriculum-v2-required-score-015`

- 中文题意：四项等权考核的成绩为 84、60、76、71。第五项考核需要多少分，才能使总平均分达到 72.6？
- 英文原题：Four equally weighted assessments produced scores of 84, 60, 76, 71. Determine the fifth assessment score required to make the overall average 72.6.
- 参考公式：`72.6*5-(84+60+76+71)`
- GT：`72`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

## 多层包装扣除损坏品与样品

- Family：`curriculum-v2-cartons-damage`
- 扩充方式：保持母题数量关系，独立生成数值，并轮换三种措辞或场景。

### 已审核母题

- `curriculum-v2-cartons-damage-000`：一批货有 3 个纸箱，每箱 4 包，每包 6 件商品。去掉 5 件损坏品和 2 件样品后，还剩多少件可售商品？
  - 参考公式：`3*4*6-5-2`
  - GT：`65`
- `curriculum-v2-cartons-damage-001`：一批货有 4 个纸箱，每箱 5 包，每包 7 件商品。去掉 6 件损坏品和 3 件样品后，还剩多少件可售商品？
  - 参考公式：`4*5*7-6-3`
  - GT：`131`

### 新增待审核变体

#### 1. `v4-review-curriculum-v2-cartons-damage-002`

- 中文题意：一份订单包含 4 个外箱，每个外箱装 8 个内包，每包 20 件。售前移除 9 件次品和 4 件展示品。还剩多少件可售？
- 英文原题：An order contains 4 outer cases, each holding 8 inner packs of 20 units. Before sale, 9 defective units and 4 demonstration units are removed. Find the number of units left for sale.
- 参考公式：`4*8*20-9-4`
- GT：`627`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 2. `v4-review-curriculum-v2-cartons-damage-003`

- 中文题意：一批货有 9 个纸箱，每箱 10 包，每包 6 件商品。去掉 7 件损坏品和 7 件样品后，还剩多少件可售商品？
- 英文原题：A shipment has 9 cartons, 10 packs per carton, and 6 items per pack. After 7 damaged items and 7 sample items are removed, how many saleable items remain?
- 参考公式：`9*10*6-7-7`
- GT：`526`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 3. `v4-review-curriculum-v2-cartons-damage-004`

- 中文题意：仓库收到 9 个货箱，每箱有 4 个小盒，每盒装 22 个零件。质检丢弃 19 个损坏零件，并另留 7 个作为样品。可销售多少个零件？
- 英文原题：A warehouse receives 9 crates. Each crate contains 4 boxes with 22 components in each box. Inspectors discard 19 damaged components, and 7 more are retained as samples. How many components can be sold?
- 参考公式：`9*4*22-19-7`
- GT：`766`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 4. `v4-review-curriculum-v2-cartons-damage-005`

- 中文题意：一批货有 3 个纸箱，每箱 4 包，每包 18 件商品。去掉 11 件损坏品和 6 件样品后，还剩多少件可售商品？
- 英文原题：A shipment has 3 cartons, 4 packs per carton, and 18 items per pack. After 11 damaged items and 6 sample items are removed, how many saleable items remain?
- 参考公式：`3*4*18-11-6`
- GT：`199`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 5. `v4-review-curriculum-v2-cartons-damage-006`

- 中文题意：仓库收到 5 个货箱，每箱有 10 个小盒，每盒装 18 个零件。质检丢弃 24 个损坏零件，并另留 12 个作为样品。可销售多少个零件？
- 英文原题：A warehouse receives 5 crates. Each crate contains 10 boxes with 18 components in each box. Inspectors discard 24 damaged components, and 12 more are retained as samples. How many components can be sold?
- 参考公式：`5*10*18-24-12`
- GT：`864`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 6. `v4-review-curriculum-v2-cartons-damage-007`

- 中文题意：仓库收到 4 个货箱，每箱有 6 个小盒，每盒装 9 个零件。质检丢弃 19 个损坏零件，并另留 9 个作为样品。可销售多少个零件？
- 英文原题：A warehouse receives 4 crates. Each crate contains 6 boxes with 9 components in each box. Inspectors discard 19 damaged components, and 9 more are retained as samples. How many components can be sold?
- 参考公式：`4*6*9-19-9`
- GT：`188`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 7. `v4-review-curriculum-v2-cartons-damage-008`

- 中文题意：一份订单包含 3 个外箱，每个外箱装 9 个内包，每包 6 件。售前移除 20 件次品和 5 件展示品。还剩多少件可售？
- 英文原题：An order contains 3 outer cases, each holding 9 inner packs of 6 units. Before sale, 20 defective units and 5 demonstration units are removed. Find the number of units left for sale.
- 参考公式：`3*9*6-20-5`
- GT：`137`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 8. `v4-review-curriculum-v2-cartons-damage-009`

- 中文题意：仓库收到 4 个货箱，每箱有 7 个小盒，每盒装 19 个零件。质检丢弃 23 个损坏零件，并另留 8 个作为样品。可销售多少个零件？
- 英文原题：A warehouse receives 4 crates. Each crate contains 7 boxes with 19 components in each box. Inspectors discard 23 damaged components, and 8 more are retained as samples. How many components can be sold?
- 参考公式：`4*7*19-23-8`
- GT：`501`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 9. `v4-review-curriculum-v2-cartons-damage-010`

- 中文题意：一批货有 3 个纸箱，每箱 8 包，每包 15 件商品。去掉 9 件损坏品和 2 件样品后，还剩多少件可售商品？
- 英文原题：A shipment has 3 cartons, 8 packs per carton, and 15 items per pack. After 9 damaged items and 2 sample items are removed, how many saleable items remain?
- 参考公式：`3*8*15-9-2`
- GT：`349`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 10. `v4-review-curriculum-v2-cartons-damage-011`

- 中文题意：一批货有 3 个纸箱，每箱 6 包，每包 9 件商品。去掉 18 件损坏品和 11 件样品后，还剩多少件可售商品？
- 英文原题：A shipment has 3 cartons, 6 packs per carton, and 9 items per pack. After 18 damaged items and 11 sample items are removed, how many saleable items remain?
- 参考公式：`3*6*9-18-11`
- GT：`133`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 11. `v4-review-curriculum-v2-cartons-damage-012`

- 中文题意：一份订单包含 6 个外箱，每个外箱装 8 个内包，每包 19 件。售前移除 18 件次品和 3 件展示品。还剩多少件可售？
- 英文原题：An order contains 6 outer cases, each holding 8 inner packs of 19 units. Before sale, 18 defective units and 3 demonstration units are removed. Find the number of units left for sale.
- 参考公式：`6*8*19-18-3`
- GT：`891`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 12. `v4-review-curriculum-v2-cartons-damage-013`

- 中文题意：一批货有 5 个纸箱，每箱 4 包，每包 9 件商品。去掉 21 件损坏品和 12 件样品后，还剩多少件可售商品？
- 英文原题：A shipment has 5 cartons, 4 packs per carton, and 9 items per pack. After 21 damaged items and 12 sample items are removed, how many saleable items remain?
- 参考公式：`5*4*9-21-12`
- GT：`147`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 13. `v4-review-curriculum-v2-cartons-damage-014`

- 中文题意：一份订单包含 9 个外箱，每个外箱装 9 个内包，每包 14 件。售前移除 14 件次品和 11 件展示品。还剩多少件可售？
- 英文原题：An order contains 9 outer cases, each holding 9 inner packs of 14 units. Before sale, 14 defective units and 11 demonstration units are removed. Find the number of units left for sale.
- 参考公式：`9*9*14-14-11`
- GT：`1109`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

#### 14. `v4-review-curriculum-v2-cartons-damage-015`

- 中文题意：一批货有 4 个纸箱，每箱 9 包，每包 10 件商品。去掉 23 件损坏品和 5 件样品后，还剩多少件可售商品？
- 英文原题：A shipment has 4 cartons, 9 packs per carton, and 10 items per pack. After 23 damaged items and 5 sample items are removed, how many saleable items remain?
- 参考公式：`4*9*10-23-5`
- GT：`332`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

## 部分人免单后的账单平摊

- Family：`curriculum-v2-shared-bill`
- 扩充方式：保持母题数量关系，独立生成数值，并轮换三种措辞或场景。

### 已审核母题

- `curriculum-v2-shared-bill-000`：一行 6 人用餐，每人的餐费为 14 美元，另有 20 美元包间费。其中 1 人不用付款，其余人平均承担全部账单。每位付款者应付多少？结果保留两位小数。
  - 参考公式：`(6*14+20)/(6-1)`
  - GT：`20.8`
- `curriculum-v2-shared-bill-001`：一行 7 人用餐，每人的餐费为 15 美元，另有 22 美元包间费。其中 2 人不用付款，其余人平均承担全部账单。每位付款者应付多少？结果保留两位小数。
  - 参考公式：`(7*15+22)/(7-2)`
  - GT：`25.4`

### 新增待审核变体

#### 1. `v4-review-curriculum-v2-shared-bill-002`

- 中文题意：一场宴会有 13 人参加，每人费用 44 美元，另加固定场地费 55 美元。因其中 1 人免单，其余人平均承担全部费用。每人应付多少？保留两位小数。
- 英文原题：A banquet serves 13 attendees at $44 per person and adds a fixed $55 venue charge. Because 1 attendee is not charged, the remaining attendees share every cost equally. Find each paying attendee's share to two decimals.
- 参考公式：`(13*44+55)/(13-1)`
- GT：`52.25`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 2. `v4-review-curriculum-v2-shared-bill-003`

- 中文题意：一行 12 人用餐，每人的餐费为 28 美元，另有 30 美元包间费。其中 3 人不用付款，其余人平均承担全部账单。每位付款者应付多少？保留两位小数。
- 英文原题：A group of 12 people has meals costing $28 per person plus a $30 room charge. 3 guests pay nothing, so the others split the entire bill equally. How much does each paying person owe? Round to two decimals.
- 参考公式：`(12*28+30)/(12-3)`
- GT：`40.67`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 3. `v4-review-curriculum-v2-shared-bill-004`

- 中文题意：一场宴会有 14 人参加，每人费用 15 美元，另加固定场地费 100 美元。因其中 2 人免单，其余人平均承担全部费用。每人应付多少？保留两位小数。
- 英文原题：A banquet serves 14 attendees at $15 per person and adds a fixed $100 venue charge. Because 2 attendees are not charged, the remaining attendees share every cost equally. Find each paying attendee's share to two decimals.
- 参考公式：`(14*15+100)/(14-2)`
- GT：`25.83`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 4. `v4-review-curriculum-v2-shared-bill-005`

- 中文题意：共有 8 人参加团队晚餐，每人餐费 17 美元，包间另收 75 美元。团队替 1 位受邀者承担费用，其余人均摊全部账单。每位付款者应付多少？保留两位小数。
- 英文原题：At a team dinner for 8 people, food costs $17 for each attendee and a private room costs $75. The group covers the total cost for 1 invited guest, while everyone else divides the full bill equally. What does each payer owe? Round to two decimals.
- 参考公式：`(8*17+75)/(8-1)`
- GT：`30.14`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 5. `v4-review-curriculum-v2-shared-bill-006`

- 中文题意：一场宴会有 14 人参加，每人费用 23 美元，另加固定场地费 90 美元。因其中 3 人免单，其余人平均承担全部费用。每人应付多少？保留两位小数。
- 英文原题：A banquet serves 14 attendees at $23 per person and adds a fixed $90 venue charge. Because 3 attendees are not charged, the remaining attendees share every cost equally. Find each paying attendee's share to two decimals.
- 参考公式：`(14*23+90)/(14-3)`
- GT：`37.45`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 6. `v4-review-curriculum-v2-shared-bill-007`

- 中文题意：共有 12 人参加团队晚餐，每人餐费 40 美元，包间另收 80 美元。团队替 3 位受邀者承担费用，其余人均摊全部账单。每位付款者应付多少？保留两位小数。
- 英文原题：At a team dinner for 12 people, food costs $40 for each attendee and a private room costs $80. The group covers the total cost for 3 invited guests, while everyone else divides the full bill equally. What does each payer owe? Round to two decimals.
- 参考公式：`(12*40+80)/(12-3)`
- GT：`62.22`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 7. `v4-review-curriculum-v2-shared-bill-008`

- 中文题意：共有 14 人参加团队晚餐，每人餐费 41 美元，包间另收 50 美元。团队替 2 位受邀者承担费用，其余人均摊全部账单。每位付款者应付多少？保留两位小数。
- 英文原题：At a team dinner for 14 people, food costs $41 for each attendee and a private room costs $50. The group covers the total cost for 2 invited guests, while everyone else divides the full bill equally. What does each payer owe? Round to two decimals.
- 参考公式：`(14*41+50)/(14-2)`
- GT：`52.00`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 8. `v4-review-curriculum-v2-shared-bill-009`

- 中文题意：一行 14 人用餐，每人的餐费为 18 美元，另有 40 美元包间费。其中 3 人不用付款，其余人平均承担全部账单。每位付款者应付多少？保留两位小数。
- 英文原题：A group of 14 people has meals costing $18 per person plus a $40 room charge. 3 guests pay nothing, so the others split the entire bill equally. How much does each paying person owe? Round to two decimals.
- 参考公式：`(14*18+40)/(14-3)`
- GT：`26.55`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 9. `v4-review-curriculum-v2-shared-bill-010`

- 中文题意：一场宴会有 7 人参加，每人费用 27 美元，另加固定场地费 50 美元。因其中 1 人免单，其余人平均承担全部费用。每人应付多少？保留两位小数。
- 英文原题：A banquet serves 7 attendees at $27 per person and adds a fixed $50 venue charge. Because 1 attendee is not charged, the remaining attendees share every cost equally. Find each paying attendee's share to two decimals.
- 参考公式：`(7*27+50)/(7-1)`
- GT：`39.83`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 10. `v4-review-curriculum-v2-shared-bill-011`

- 中文题意：一场宴会有 8 人参加，每人费用 44 美元，另加固定场地费 95 美元。因其中 2 人免单，其余人平均承担全部费用。每人应付多少？保留两位小数。
- 英文原题：A banquet serves 8 attendees at $44 per person and adds a fixed $95 venue charge. Because 2 attendees are not charged, the remaining attendees share every cost equally. Find each paying attendee's share to two decimals.
- 参考公式：`(8*44+95)/(8-2)`
- GT：`74.50`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 11. `v4-review-curriculum-v2-shared-bill-012`

- 中文题意：一场宴会有 7 人参加，每人费用 26 美元，另加固定场地费 80 美元。因其中 3 人免单，其余人平均承担全部费用。每人应付多少？保留两位小数。
- 英文原题：A banquet serves 7 attendees at $26 per person and adds a fixed $80 venue charge. Because 3 attendees are not charged, the remaining attendees share every cost equally. Find each paying attendee's share to two decimals.
- 参考公式：`(7*26+80)/(7-3)`
- GT：`65.50`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 12. `v4-review-curriculum-v2-shared-bill-013`

- 中文题意：共有 8 人参加团队晚餐，每人餐费 45 美元，包间另收 85 美元。团队替 1 位受邀者承担费用，其余人均摊全部账单。每位付款者应付多少？保留两位小数。
- 英文原题：At a team dinner for 8 people, food costs $45 for each attendee and a private room costs $85. The group covers the total cost for 1 invited guest, while everyone else divides the full bill equally. What does each payer owe? Round to two decimals.
- 参考公式：`(8*45+85)/(8-1)`
- GT：`63.57`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 13. `v4-review-curriculum-v2-shared-bill-014`

- 中文题意：一场宴会有 11 人参加，每人费用 21 美元，另加固定场地费 95 美元。因其中 1 人免单，其余人平均承担全部费用。每人应付多少？保留两位小数。
- 英文原题：A banquet serves 11 attendees at $21 per person and adds a fixed $95 venue charge. Because 1 attendee is not charged, the remaining attendees share every cost equally. Find each paying attendee's share to two decimals.
- 参考公式：`(11*21+95)/(11-1)`
- GT：`32.60`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 14. `v4-review-curriculum-v2-shared-bill-015`

- 中文题意：共有 8 人参加团队晚餐，每人餐费 25 美元，包间另收 45 美元。团队替 3 位受邀者承担费用，其余人均摊全部账单。每位付款者应付多少？保留两位小数。
- 英文原题：At a team dinner for 8 people, food costs $25 for each attendee and a private room costs $45. The group covers the total cost for 3 invited guests, while everyone else divides the full bill equally. What does each payer owe? Round to two decimals.
- 参考公式：`(8*25+45)/(8-3)`
- GT：`49.00`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

## 连续两年增长后扣固定费用

- Family：`curriculum-v2-growth-fee`
- 扩充方式：保持母题数量关系，独立生成数值，并轮换三种措辞或场景。

### 已审核母题

- `curriculum-v2-growth-fee-000`：一个账户初始有 200 美元，连续两年每年增长 5%，之后一次性扣除 8 美元费用。余额是多少？结果保留两位小数。
  - 参考公式：`200*(1+5/100)*(1+5/100)-8`
  - GT：`212.5`
- `curriculum-v2-growth-fee-001`：一个账户初始有 225 美元，连续两年每年增长 6%，之后一次性扣除 9 美元费用。余额是多少？结果保留两位小数。
  - 参考公式：`225*(1+6/100)*(1+6/100)-9`
  - GT：`243.81`

### 新增待审核变体

#### 1. `v4-review-curriculum-v2-growth-fee-002`

- 中文题意：一个账户初始有 600 美元，第一年增长 6%，第二年增长 7%，之后一次性扣除 59 美元费用。余额是多少？保留两位小数。
- 英文原题：An account starts with $600, grows by 6% in the first year and 7% in the second year, then a one-time $59 fee is deducted. What is the balance? Round to two decimals.
- 参考公式：`600*(1+6/100)*(1+7/100)-59`
- GT：`621.52`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 2. `v4-review-curriculum-v2-growth-fee-003`

- 中文题意：一个账户初始有 525 美元，第一年增长 3%，第二年增长 11%，之后一次性扣除 30 美元费用。余额是多少？保留两位小数。
- 英文原题：An account starts with $525, grows by 3% in the first year and 11% in the second year, then a one-time $30 fee is deducted. What is the balance? Round to two decimals.
- 参考公式：`525*(1+3/100)*(1+11/100)-30`
- GT：`570.23`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 3. `v4-review-curriculum-v2-growth-fee-004`

- 中文题意：一个基金初始有 1450 美元，第一年增长 9%，第二年再增长 6%。两次增长后扣除 39 美元管理费。求最终余额，保留两位小数。
- 英文原题：A fund initially contains $1450. It increases by 9% during year one and by 6% during year two. After both increases, an administration charge of $39 is removed. Find the final balance to two decimals.
- 参考公式：`1450*(1+9/100)*(1+6/100)-39`
- GT：`1636.33`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 4. `v4-review-curriculum-v2-growth-fee-005`

- 中文题意：一个基金初始有 925 美元，第一年增长 5%，第二年再增长 3%。两次增长后扣除 27 美元管理费。求最终余额，保留两位小数。
- 英文原题：A fund initially contains $925. It increases by 5% during year one and by 3% during year two. After both increases, an administration charge of $27 is removed. Find the final balance to two decimals.
- 参考公式：`925*(1+5/100)*(1+3/100)-27`
- GT：`973.39`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 5. `v4-review-curriculum-v2-growth-fee-006`

- 中文题意：一笔 1100 美元的投资第一年收益率为 10%，第二年在新余额基础上收益 7%，之后支付固定费用 12 美元。还剩多少钱？保留两位小数。
- 英文原题：An investment of $1100 earns 10% in its first year. The resulting balance then earns 7% in the next year, after which a fixed $12 charge is paid. What amount remains? Round to two decimals.
- 参考公式：`1100*(1+10/100)*(1+7/100)-12`
- GT：`1282.70`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 6. `v4-review-curriculum-v2-growth-fee-007`

- 中文题意：一个账户初始有 450 美元，第一年增长 6%，第二年增长 6%，之后一次性扣除 20 美元费用。余额是多少？保留两位小数。
- 英文原题：An account starts with $450, grows by 6% in the first year and 6% in the second year, then a one-time $20 fee is deducted. What is the balance? Round to two decimals.
- 参考公式：`450*(1+6/100)*(1+6/100)-20`
- GT：`485.62`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 7. `v4-review-curriculum-v2-growth-fee-008`

- 中文题意：一笔 650 美元的投资第一年收益率为 12%，第二年在新余额基础上收益 9%，之后支付固定费用 52 美元。还剩多少钱？保留两位小数。
- 英文原题：An investment of $650 earns 12% in its first year. The resulting balance then earns 9% in the next year, after which a fixed $52 charge is paid. What amount remains? Round to two decimals.
- 参考公式：`650*(1+12/100)*(1+9/100)-52`
- GT：`741.52`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 8. `v4-review-curriculum-v2-growth-fee-009`

- 中文题意：一个基金初始有 1350 美元，第一年增长 3%，第二年再增长 8%。两次增长后扣除 41 美元管理费。求最终余额，保留两位小数。
- 英文原题：A fund initially contains $1350. It increases by 3% during year one and by 8% during year two. After both increases, an administration charge of $41 is removed. Find the final balance to two decimals.
- 参考公式：`1350*(1+3/100)*(1+8/100)-41`
- GT：`1460.74`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 9. `v4-review-curriculum-v2-growth-fee-010`

- 中文题意：一笔 550 美元的投资第一年收益率为 12%，第二年在新余额基础上收益 4%，之后支付固定费用 23 美元。还剩多少钱？保留两位小数。
- 英文原题：An investment of $550 earns 12% in its first year. The resulting balance then earns 4% in the next year, after which a fixed $23 charge is paid. What amount remains? Round to two decimals.
- 参考公式：`550*(1+12/100)*(1+4/100)-23`
- GT：`617.64`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 10. `v4-review-curriculum-v2-growth-fee-011`

- 中文题意：一个账户初始有 200 美元，第一年增长 11%，第二年增长 10%，之后一次性扣除 49 美元费用。余额是多少？保留两位小数。
- 英文原题：An account starts with $200, grows by 11% in the first year and 10% in the second year, then a one-time $49 fee is deducted. What is the balance? Round to two decimals.
- 参考公式：`200*(1+11/100)*(1+10/100)-49`
- GT：`195.20`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 11. `v4-review-curriculum-v2-growth-fee-012`

- 中文题意：一笔 1075 美元的投资第一年收益率为 4%，第二年在新余额基础上收益 12%，之后支付固定费用 40 美元。还剩多少钱？保留两位小数。
- 英文原题：An investment of $1075 earns 4% in its first year. The resulting balance then earns 12% in the next year, after which a fixed $40 charge is paid. What amount remains? Round to two decimals.
- 参考公式：`1075*(1+4/100)*(1+12/100)-40`
- GT：`1212.16`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 12. `v4-review-curriculum-v2-growth-fee-013`

- 中文题意：一个基金初始有 825 美元，第一年增长 4%，第二年再增长 10%。两次增长后扣除 41 美元管理费。求最终余额，保留两位小数。
- 英文原题：A fund initially contains $825. It increases by 4% during year one and by 10% during year two. After both increases, an administration charge of $41 is removed. Find the final balance to two decimals.
- 参考公式：`825*(1+4/100)*(1+10/100)-41`
- GT：`902.80`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 13. `v4-review-curriculum-v2-growth-fee-014`

- 中文题意：一个基金初始有 750 美元，第一年增长 10%，第二年再增长 9%。两次增长后扣除 8 美元管理费。求最终余额，保留两位小数。
- 英文原题：A fund initially contains $750. It increases by 10% during year one and by 9% during year two. After both increases, an administration charge of $8 is removed. Find the final balance to two decimals.
- 参考公式：`750*(1+10/100)*(1+9/100)-8`
- GT：`891.25`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

#### 14. `v4-review-curriculum-v2-growth-fee-015`

- 中文题意：一笔 1500 美元的投资第一年收益率为 12%，第二年在新余额基础上收益 9%，之后支付固定费用 40 美元。还剩多少钱？保留两位小数。
- 英文原题：An investment of $1500 earns 12% in its first year. The resulting balance then earns 9% in the next year, after which a fixed $40 charge is paid. What amount remains? Round to two decimals.
- 参考公式：`1500*(1+12/100)*(1+9/100)-40`
- GT：`1791.20`；容差：`0.005`
- 审核结论：□保留　□修改　□删除
