# V4 test 母题扩充 v1：中文审核稿

> **待审核，未冻结，未运行模型。** 英文题给模型；中文、公式和 GT 只供审核。
> v0 审核稿保留不动。v1 主要修正自写题只有一套句式、数字单调变大的问题。

## 数量和分组

- 原冻结 V3 test：36 道，不改题面或 GT。v1 对每道母题各新增一道待审核题。
- 新增 36 道：32 道自写题族扩充，4 道为 GSM8K-test 母题衍生的**新写合成题**。
- 若 36 道全部审核通过，拟组合 72 道；现在**尚未**把它们并入正式 test。
- 四个自写题族各用四种英文数量关系表述，每种两道；参数不按索引持续加大。
- 这些题仍沿用既有八个 test-only family，没有增加八种全新推理类型；同族题相关。

| 题族 | 原题 | 新题 | 拟合计 | 新题类别 |
| --- | ---: | ---: | ---: | --- |
| 流量套餐、超额费与税后租赁费 | 8 | 8 | 16 | 自写扩充 |
| 分路段油耗、过路费与抵用券 | 8 | 8 | 16 | 自写扩充 |
| 折扣购买与部分退款 | 8 | 8 | 16 | 自写扩充 |
| 加班、奖金、税与保险费 | 8 | 8 | 16 | 自写扩充 |
| 一次性借款费用与分期还款 | 1 | 1 | 2 | 公开母题衍生合成题 |
| 买一件、第二件半价 | 1 | 1 | 2 | 公开母题衍生合成题 |
| 订单小计、配送费与小费 | 1 | 1 | 2 | 公开母题衍生合成题 |
| 分组正确率与加权得分 | 1 | 1 | 2 | 公开母题衍生合成题 |
| **总计** | **36** | **36** | **72** | — |

## 自检与评估边界

- 每题的参考表达式已由安全计算器执行，GT 又由独立的 Decimal 数量公式计算；两者通过数值 verifier 比对。
- 新旧题 ID/题面不重复，36 道新题各有一条母题记录；与 V4 train、validation 的 family 不交叉。
- 要求保留两位小数的 GT 在本审核稿按两位显示；JSONL 仍按 numeric GT 存值，不检查最终答案的字面尾零。
- 原公开题仍是 4 道；衍生合成题不可报告为新 GSM8K 公开题或独立外部评估。
- 四个自写家族拟占 64/72，整体分数会偏向它们。最终请分别报告每族、原题/扩充题及公开原题/合成衍生题结果。
- 数值核对不能替代语义审核；请逐题检查中英题意、题面信息是否充分、税费顺序、单位和舍入。
- 审核前 `review_status=pending`，全部为 test-only 且 `training_eligible=false`；不得用于搜索、SFT、GRPO 或 checkpoint 选择。

## 流量套餐、超额费与税后租赁费

- Family：`v3-eval-test-subscription-overage-v1`

### 1. `v4-review-test-synthetic-subscription-overage-000`

- 母题：`v3-eval-test-subscription-overage-v1-000`
- 类别：`self_written_extension`；措辞变体：`1`
- 中文题意：月度流量套餐费49美元，包含350GB；超出部分每GB收费0.11美元。本月用了530GB。套餐与超额费用加收7%税，之后另加9美元设备租赁费。最终账单是多少？保留两位小数。
- 英文题意：A monthly data plan charges $49, covers 350 GB, and costs $0.11 per extra GB. Usage is 530 GB. Tax of 7% applies to the plan and overage charges; an equipment rental fee of $9 is added after tax. What is the final bill? Round to two decimals.
- 参考公式：`(49+(530-350)*0.11)*(1+7/100)+9`
- GT：`82.62`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-test-synthetic-subscription-overage-001`

- 母题：`v3-eval-test-subscription-overage-v1-001`
- 类别：`self_written_extension`；措辞变体：`2`
- 中文题意：用户在包含500GB、套餐费62美元的流量方案中用了655GB。额外流量每GB收费0.08美元。5%的税只加在套餐费和超额费上，12美元设备租赁费不计税。总共应付多少？保留两位小数。
- 英文题意：A customer uses 655 GB on a plan that includes 500 GB for $62. Additional GB cost $0.08 each. Tax of 5% is charged on the base plan plus the additional-usage charge, but not on the $12 rental fee. How much is due in total? Round to two decimals.
- 参考公式：`(62+(655-500)*0.08)*(1+5/100)+12`
- GT：`90.12`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-test-synthetic-subscription-overage-002`

- 母题：`v3-eval-test-subscription-overage-v1-002`
- 类别：`self_written_extension`；措辞变体：`3`
- 中文题意：用户使用了420GB流量：前250GB按39美元套餐费计，超出部分每GB为0.16美元。流量费用合计加收9%税，另有不计税的6美元设备费。应付金额是多少？保留两位小数。
- 英文题意：For 420 GB of usage, a subscriber pays $39 for the first 250 GB and $0.16 for each GB above that allowance. The combined data charges incur 9% tax. An additional $6 equipment charge is not taxed. Find the amount payable to two decimals.
- 参考公式：`(39+(420-250)*0.16)*(1+9/100)+6`
- GT：`78.16`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-test-synthetic-subscription-overage-003`

- 母题：`v3-eval-test-subscription-overage-v1-003`
- 类别：`self_written_extension`；措辞变体：`4`
- 中文题意：账单含54美元的400GB套餐，超额部分每GB收0.10美元。本月用了610GB。套餐费与超额费需缴纳6%税，11美元租赁费不计税。账单是多少？保留两位小数。
- 英文题意：A bill includes a $54 plan with 400 GB, plus $0.10 per GB for usage beyond the allowance. This month the subscriber used 610 GB. Both data charges are subject to 6% tax; the $11 rental fee is not. What is the bill? Round to two decimals.
- 参考公式：`(54+(610-400)*0.10)*(1+6/100)+11`
- GT：`90.50`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-test-synthetic-subscription-overage-004`

- 母题：`v3-eval-test-subscription-overage-v1-004`
- 类别：`self_written_extension`；措辞变体：`1`
- 中文题意：月度流量套餐费58美元，包含450GB；超出部分每GB收费0.13美元。本月用了590GB。套餐与超额费用加收8%税，之后另加7美元设备租赁费。最终账单是多少？保留两位小数。
- 英文题意：A monthly data plan charges $58, covers 450 GB, and costs $0.13 per extra GB. Usage is 590 GB. Tax of 8% applies to the plan and overage charges; an equipment rental fee of $7 is added after tax. What is the final bill? Round to two decimals.
- 参考公式：`(58+(590-450)*0.13)*(1+8/100)+7`
- GT：`89.30`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-test-synthetic-subscription-overage-005`

- 母题：`v3-eval-test-subscription-overage-v1-005`
- 类别：`self_written_extension`；措辞变体：`2`
- 中文题意：用户在包含300GB、套餐费43美元的流量方案中用了485GB。额外流量每GB收费0.09美元。5%的税只加在套餐费和超额费上，10美元设备租赁费不计税。总共应付多少？保留两位小数。
- 英文题意：A customer uses 485 GB on a plan that includes 300 GB for $43. Additional GB cost $0.09 each. Tax of 5% is charged on the base plan plus the additional-usage charge, but not on the $10 rental fee. How much is due in total? Round to two decimals.
- 参考公式：`(43+(485-300)*0.09)*(1+5/100)+10`
- GT：`72.63`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 7. `v4-review-test-synthetic-subscription-overage-006`

- 母题：`v3-eval-test-subscription-overage-v1-006`
- 类别：`self_written_extension`；措辞变体：`3`
- 中文题意：用户使用了780GB流量：前550GB按67美元套餐费计，超出部分每GB为0.14美元。流量费用合计加收9%税，另有不计税的12美元设备费。应付金额是多少？保留两位小数。
- 英文题意：For 780 GB of usage, a subscriber pays $67 for the first 550 GB and $0.14 for each GB above that allowance. The combined data charges incur 9% tax. An additional $12 equipment charge is not taxed. Find the amount payable to two decimals.
- 参考公式：`(67+(780-550)*0.14)*(1+9/100)+12`
- GT：`120.13`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 8. `v4-review-test-synthetic-subscription-overage-007`

- 母题：`v3-eval-test-subscription-overage-v1-007`
- 类别：`self_written_extension`；措辞变体：`4`
- 中文题意：账单含47美元的375GB套餐，超额部分每GB收0.14美元。本月用了560GB。套餐费与超额费需缴纳6%税，8美元租赁费不计税。账单是多少？保留两位小数。
- 英文题意：A bill includes a $47 plan with 375 GB, plus $0.14 per GB for usage beyond the allowance. This month the subscriber used 560 GB. Both data charges are subject to 6% tax; the $8 rental fee is not. What is the bill? Round to two decimals.
- 参考公式：`(47+(560-375)*0.14)*(1+6/100)+8`
- GT：`85.27`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

## 分路段油耗、过路费与抵用券

- Family：`v3-eval-test-route-cost-v1`

### 1. `v4-review-test-synthetic-route-cost-000`

- 母题：`v3-eval-test-route-cost-v1-000`
- 类别：`self_written_extension`；措辞变体：`1`
- 中文题意：货车在高速公路行驶160英里，每加仑行驶32英里；市区行驶96英里，每加仑行驶24英里。油价每加仑3.95美元，另付16美元过路费，再抵扣9美元优惠券。行程净成本是多少？
- 英文题意：A van drives 160 highway miles at 32 miles per gallon and 96 city miles at 24 miles per gallon. Gas costs $3.95 per gallon. A toll of $16 is charged, then a voucher worth $9 is applied. What is the net cost of the trip?
- 参考公式：`(160/32+96/24)*3.95+16-9`
- GT：`42.55`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-test-synthetic-route-cost-001`

- 母题：`v3-eval-test-route-cost-v1-001`
- 类别：`self_written_extension`；措辞变体：`2`
- 中文题意：送货路线有270英里高速和144英里市区路段，油耗分别为每加仑30英里和24英里。每加仑油价4.25美元；另加20美元过路费、减去11美元出行抵扣。路线成本是多少？
- 英文题意：Fuel economy is 30 mpg on the highway and 24 mpg in the city. A delivery route covers 270 highway miles and 144 city miles. At $4.25 per gallon, plus a toll of $20 and minus a travel credit of $11, how much does the route cost?
- 参考公式：`(270/30+144/24)*4.25+20-11`
- GT：`72.75`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-test-synthetic-route-cost-002`

- 母题：`v3-eval-test-route-cost-v1-002`
- 类别：`self_written_extension`；措辞变体：`3`
- 中文题意：司机先在市区行驶105英里，每加仑可行驶21英里；再在高速行驶168英里，每加仑可行驶28英里。油价每加仑3.70美元，另加24美元过路费，最终用8美元券抵扣。行程净成本是多少？
- 英文题意：A driver travels 105 miles in town using one gallon per 21 miles, then 168 miles on the highway using one gallon per 28 miles. Fuel is $3.70 per gallon. After adding a $24 toll and using a voucher worth $8 against the total, what is the trip's net cost?
- 参考公式：`(168/28+105/21)*3.70+24-8`
- GT：`56.7`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-test-synthetic-route-cost-003`

- 母题：`v3-eval-test-route-cost-v1-003`
- 类别：`self_written_extension`；措辞变体：`4`
- 中文题意：配送行程包括220英里高速路段（每加仑22英里）和180英里市区路段（每加仑30英里）。油价每加仑4.10美元，另有17美元过路费，总费用再用12美元抵扣。最终成本是多少？
- 英文题意：A delivery trip has 220 highway miles (22 miles per gallon) and 180 city miles (30 miles per gallon). At $4.10 per gallon, what is the final fuel-and-toll cost after a $17 toll and a $12 credit toward the combined cost?
- 参考公式：`(220/22+180/30)*4.10+17-12`
- GT：`70.6`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-test-synthetic-route-cost-004`

- 母题：`v3-eval-test-route-cost-v1-004`
- 类别：`self_written_extension`；措辞变体：`1`
- 中文题意：货车在高速公路行驶195英里，每加仑行驶39英里；市区行驶128英里，每加仑行驶32英里。油价每加仑3.85美元，另付19美元过路费，再抵扣14美元优惠券。行程净成本是多少？
- 英文题意：A van drives 195 highway miles at 39 miles per gallon and 128 city miles at 32 miles per gallon. Gas costs $3.85 per gallon. A toll of $19 is charged, then a voucher worth $14 is applied. What is the net cost of the trip?
- 参考公式：`(195/39+128/32)*3.85+19-14`
- GT：`39.65`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-test-synthetic-route-cost-005`

- 母题：`v3-eval-test-route-cost-v1-005`
- 类别：`self_written_extension`；措辞变体：`2`
- 中文题意：送货路线有288英里高速和126英里市区路段，油耗分别为每加仑36英里和21英里。每加仑油价4.40美元；另加27美元过路费、减去10美元出行抵扣。路线成本是多少？
- 英文题意：Fuel economy is 36 mpg on the highway and 21 mpg in the city. A delivery route covers 288 highway miles and 126 city miles. At $4.40 per gallon, plus a toll of $27 and minus a travel credit of $10, how much does the route cost?
- 参考公式：`(288/36+126/21)*4.40+27-10`
- GT：`78.6`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 7. `v4-review-test-synthetic-route-cost-006`

- 母题：`v3-eval-test-route-cost-v1-006`
- 类别：`self_written_extension`；措辞变体：`3`
- 中文题意：司机先在市区行驶175英里，每加仑可行驶25英里；再在高速行驶240英里，每加仑可行驶30英里。油价每加仑4.05美元，另加25美元过路费，最终用16美元券抵扣。行程净成本是多少？
- 英文题意：A driver travels 175 miles in town using one gallon per 25 miles, then 240 miles on the highway using one gallon per 30 miles. Fuel is $4.05 per gallon. After adding a $25 toll and using a voucher worth $16 against the total, what is the trip's net cost?
- 参考公式：`(240/30+175/25)*4.05+25-16`
- GT：`69.75`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 8. `v4-review-test-synthetic-route-cost-007`

- 母题：`v3-eval-test-route-cost-v1-007`
- 类别：`self_written_extension`；措辞变体：`4`
- 中文题意：配送行程包括315英里高速路段（每加仑35英里）和160英里市区路段（每加仑20英里）。油价每加仑4.65美元，另有14美元过路费，总费用再用7美元抵扣。最终成本是多少？
- 英文题意：A delivery trip has 315 highway miles (35 miles per gallon) and 160 city miles (20 miles per gallon). At $4.65 per gallon, what is the final fuel-and-toll cost after a $14 toll and a $7 credit toward the combined cost?
- 参考公式：`(315/35+160/20)*4.65+14-7`
- GT：`86.05`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

## 折扣购买与部分退款

- Family：`v3-eval-test-partial-refund-v1`

### 1. `v4-review-test-synthetic-partial-refund-000`

- 母题：`v3-eval-test-partial-refund-v1-000`
- 类别：`self_written_extension`；措辞变体：`1`
- 中文题意：顾客在全场优惠10%时买了4件单价35美元的商品、2件单价70美元的商品，并支付不退还的11美元配送费。后来退回一件原价70美元的商品，因补货费只退该商品折后价的85%。顾客最终净付款是多少？保留两位小数。
- 英文题意：A shopper buys 4 items at $35 each and 2 at $70 each in a 10%-off sale, and pays a nonrefundable $11 delivery fee. One $70 item is returned; only 85% of its sale price is refunded because of a restocking charge. What is the shopper's net payment? Round to two decimals.
- 参考公式：`(4*35+2*70)*(1-10/100)+11-70*(1-10/100)*85/100`
- GT：`209.45`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-test-synthetic-partial-refund-001`

- 母题：`v3-eval-test-partial-refund-v1-001`
- 类别：`self_written_extension`；措辞变体：`2`
- 中文题意：全场优惠25%时，订单有2件原价60美元的商品和4件原价25美元的商品；配送费8美元不退。随后退回一件原价25美元的商品，退款为该件折后价的70%。最终净付多少？保留两位小数。
- 英文题意：With a storewide discount of 25%, an order contains 2 units priced $60 and 4 units priced $25. Delivery adds $8 and is not refunded. The customer later returns one $25 unit and receives 70% of that unit's discounted price. How much has the customer paid in the end? Round to two decimals.
- 参考公式：`(2*60+4*25)*(1-25/100)+8-25*(1-25/100)*70/100`
- GT：`159.88`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-test-synthetic-partial-refund-002`

- 母题：`v3-eval-test-partial-refund-v1-002`
- 类别：`self_written_extension`；措辞变体：`3`
- 中文题意：5件单价32美元及3件单价54美元的商品均参加优惠15%活动。另付不可退的9美元运费。购买后退回一件原价54美元的商品，退款是其折后价的90%。最终净支出是多少？保留两位小数。
- 英文题意：A 15%-off promotion applies to 5 products at $32 and 3 products at $54. A $9 shipping charge cannot be recovered. After purchase, one $54 product is returned for a refund equal to 90% of its discounted price. Find the final net spending to two decimals.
- 参考公式：`(5*32+3*54)*(1-15/100)+9-54*(1-15/100)*90/100`
- GT：`241.39`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-test-synthetic-partial-refund-003`

- 母题：`v3-eval-test-partial-refund-v1-003`
- 类别：`self_written_extension`；措辞变体：`4`
- 中文题意：某人按原价优惠20%购买3件每件48美元的商品和2件每件80美元的商品。14美元配送费不退。退回一件原价80美元的商品后，只拿回该件折后价的75%。最后实际支付多少？保留两位小数。
- 英文题意：At 20% off, someone purchases 3 items normally costing $48 apiece and 2 normally costing $80 apiece. The $14 delivery charge is nonrefundable. On returning one $80 item, the buyer gets back 75% of its discounted price. What remains paid overall? Round to two decimals.
- 参考公式：`(3*48+2*80)*(1-20/100)+14-80*(1-20/100)*75/100`
- GT：`209.20`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-test-synthetic-partial-refund-004`

- 母题：`v3-eval-test-partial-refund-v1-004`
- 类别：`self_written_extension`；措辞变体：`1`
- 中文题意：顾客在全场优惠12%时买了2件单价45美元的商品、5件单价30美元的商品，并支付不退还的7美元配送费。后来退回一件原价30美元的商品，因补货费只退该商品折后价的80%。顾客最终净付款是多少？保留两位小数。
- 英文题意：A shopper buys 2 items at $45 each and 5 at $30 each in a 12%-off sale, and pays a nonrefundable $7 delivery fee. One $30 item is returned; only 80% of its sale price is refunded because of a restocking charge. What is the shopper's net payment? Round to two decimals.
- 参考公式：`(2*45+5*30)*(1-12/100)+7-30*(1-12/100)*80/100`
- GT：`197.08`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-test-synthetic-partial-refund-005`

- 母题：`v3-eval-test-partial-refund-v1-005`
- 类别：`self_written_extension`；措辞变体：`2`
- 中文题意：全场优惠18%时，订单有4件原价52美元的商品和2件原价68美元的商品；配送费10美元不退。随后退回一件原价68美元的商品，退款为该件折后价的65%。最终净付多少？保留两位小数。
- 英文题意：With a storewide discount of 18%, an order contains 4 units priced $52 and 2 units priced $68. Delivery adds $10 and is not refunded. The customer later returns one $68 unit and receives 65% of that unit's discounted price. How much has the customer paid in the end? Round to two decimals.
- 参考公式：`(4*52+2*68)*(1-18/100)+10-68*(1-18/100)*65/100`
- GT：`255.84`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 7. `v4-review-test-synthetic-partial-refund-006`

- 母题：`v3-eval-test-partial-refund-v1-006`
- 类别：`self_written_extension`；措辞变体：`3`
- 中文题意：3件单价38美元及4件单价42美元的商品均参加优惠22%活动。另付不可退的13美元运费。购买后退回一件原价42美元的商品，退款是其折后价的85%。最终净支出是多少？保留两位小数。
- 英文题意：A 22%-off promotion applies to 3 products at $38 and 4 products at $42. A $13 shipping charge cannot be recovered. After purchase, one $42 product is returned for a refund equal to 85% of its discounted price. Find the final net spending to two decimals.
- 参考公式：`(3*38+4*42)*(1-22/100)+13-42*(1-22/100)*85/100`
- GT：`205.11`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 8. `v4-review-test-synthetic-partial-refund-007`

- 母题：`v3-eval-test-partial-refund-v1-007`
- 类别：`self_written_extension`；措辞变体：`4`
- 中文题意：某人按原价优惠10%购买5件每件28美元的商品和3件每件75美元的商品。12美元配送费不退。退回一件原价75美元的商品后，只拿回该件折后价的70%。最后实际支付多少？保留两位小数。
- 英文题意：At 10% off, someone purchases 5 items normally costing $28 apiece and 3 normally costing $75 apiece. The $12 delivery charge is nonrefundable. On returning one $75 item, the buyer gets back 70% of its discounted price. What remains paid overall? Round to two decimals.
- 参考公式：`(5*28+3*75)*(1-10/100)+12-75*(1-10/100)*70/100`
- GT：`293.25`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

## 加班、奖金、税与保险费

- Family：`v3-eval-test-bonus-deduction-v1`

### 1. `v4-review-test-synthetic-bonus-deduction-000`

- 母题：`v3-eval-test-bonus-deduction-v1-000`
- 类别：`self_written_extension`；措辞变体：`1`
- 中文题意：员工正常工作40小时，正常时薪25美元；加班6小时，加班时薪是正常时薪的1.5倍。奖金为正常工时工资的7%。全部税前收入先扣19%税，再扣45美元保险费。实发工资是多少？保留两位小数。
- 英文题意：An employee works 40 regular hours at $25 per hour and 6 overtime hours at 1.5 times that rate. A bonus is 7% of regular-hour wages. A 19% tax is taken from all gross earnings; then $45 insurance is deducted. What is take-home pay? Round to two decimals.
- 参考公式：`(40*25+6*25*1.5+40*25*7/100)*(1-19/100)-45`
- GT：`1003.95`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-test-synthetic-bonus-deduction-001`

- 母题：`v3-eval-test-bonus-deduction-v1-001`
- 类别：`self_written_extension`；措辞变体：`2`
- 中文题意：员工按每小时29美元领取37小时正常工资；另有9小时加班，时薪为正常时薪的1.5倍，奖金占正常工资的5%。全部税前收入扣21%税后，再扣38美元保险费。净工资是多少？保留两位小数。
- 英文题意：Regular pay covers 37 hours at $29 hourly. The worker also has 9 overtime hours paid at 1.5 times the hourly rate and a bonus of 5% of regular pay. After 21% tax on the entire gross amount and a further $38 insurance deduction, what is net pay? Round to two decimals.
- 参考公式：`(37*29+9*29*1.5+37*29*5/100)*(1-21/100)-38`
- GT：`1161.34`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-test-synthetic-bonus-deduction-002`

- 母题：`v3-eval-test-bonus-deduction-v1-002`
- 类别：`self_written_extension`；措辞变体：`3`
- 中文题意：正常工作42小时、加班4小时，正常时薪22美元，加班时薪为其2倍。另加相当于正常工时工资10%的奖金。全部税前收入需缴纳17%税，税后工资还要扣54美元保险费。实发工资是多少？保留两位小数。
- 英文题意：For 42 normal hours and 4 overtime hours, the normal hourly wage is $22 and overtime pays 2 times as much. Add a bonus equal to 10% of wages from normal hours. The entire gross pay is subject to 17% tax; $54 insurance is deducted from post-tax pay. Find take-home pay to two decimals.
- 参考公式：`(42*22+4*22*2+42*22*10/100)*(1-17/100)-54`
- GT：`935.69`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-test-synthetic-bonus-deduction-003`

- 母题：`v3-eval-test-bonus-deduction-v1-003`
- 类别：`self_written_extension`；措辞变体：`4`
- 中文题意：某工资周期正常工作35小时，每小时27美元；另加班12小时，时薪为正常时薪的1.25倍。绩效奖只按正常工时工资的8%算。税前工资整体先扣20%税，然后再减固定44美元保险费。实发多少？保留两位小数。
- 英文题意：A pay period includes 35 hours at $27/hour, plus 12 hours at 1.25 times the regular rate. The performance bonus is 8% of regular-hours pay only. Deduct 20% tax from the full pre-tax pay and then a fixed $44 insurance charge. How much is paid out? Round to two decimals.
- 参考公式：`(35*27+12*27*1.25+35*27*8/100)*(1-20/100)-44`
- GT：`1096.48`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-test-synthetic-bonus-deduction-004`

- 母题：`v3-eval-test-bonus-deduction-v1-004`
- 类别：`self_written_extension`；措辞变体：`1`
- 中文题意：员工正常工作40小时，正常时薪31美元；加班3小时，加班时薪是正常时薪的1.5倍。奖金为正常工时工资的12%。全部税前收入先扣23%税，再扣60美元保险费。实发工资是多少？保留两位小数。
- 英文题意：An employee works 40 regular hours at $31 per hour and 3 overtime hours at 1.5 times that rate. A bonus is 12% of regular-hour wages. A 23% tax is taken from all gross earnings; then $60 insurance is deducted. What is take-home pay? Round to two decimals.
- 参考公式：`(40*31+3*31*1.5+40*31*12/100)*(1-23/100)-60`
- GT：`1116.79`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-test-synthetic-bonus-deduction-005`

- 母题：`v3-eval-test-bonus-deduction-v1-005`
- 类别：`self_written_extension`；措辞变体：`2`
- 中文题意：员工按每小时24美元领取38小时正常工资；另有8小时加班，时薪为正常时薪的2倍，奖金占正常工资的6%。全部税前收入扣16%税后，再扣49美元保险费。净工资是多少？保留两位小数。
- 英文题意：Regular pay covers 38 hours at $24 hourly. The worker also has 8 overtime hours paid at 2 times the hourly rate and a bonus of 6% of regular pay. After 16% tax on the entire gross amount and a further $49 insurance deduction, what is net pay? Round to two decimals.
- 参考公式：`(38*24+8*24*2+38*24*6/100)*(1-16/100)-49`
- GT：`1085.60`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 7. `v4-review-test-synthetic-bonus-deduction-006`

- 母题：`v3-eval-test-bonus-deduction-v1-006`
- 类别：`self_written_extension`；措辞变体：`3`
- 中文题意：正常工作36小时、加班10小时，正常时薪26美元，加班时薪为其1.5倍。另加相当于正常工时工资9%的奖金。全部税前收入需缴纳22%税，税后工资还要扣32美元保险费。实发工资是多少？保留两位小数。
- 英文题意：For 36 normal hours and 10 overtime hours, the normal hourly wage is $26 and overtime pays 1.5 times as much. Add a bonus equal to 9% of wages from normal hours. The entire gross pay is subject to 22% tax; $32 insurance is deducted from post-tax pay. Find take-home pay to two decimals.
- 参考公式：`(36*26+10*26*1.5+36*26*9/100)*(1-22/100)-32`
- GT：`1067.99`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 8. `v4-review-test-synthetic-bonus-deduction-007`

- 母题：`v3-eval-test-bonus-deduction-v1-007`
- 类别：`self_written_extension`；措辞变体：`4`
- 中文题意：某工资周期正常工作41小时，每小时30美元；另加班5小时，时薪为正常时薪的1.25倍。绩效奖只按正常工时工资的11%算。税前工资整体先扣18%税，然后再减固定55美元保险费。实发多少？保留两位小数。
- 英文题意：A pay period includes 41 hours at $30/hour, plus 5 hours at 1.25 times the regular rate. The performance bonus is 11% of regular-hours pay only. Deduct 18% tax from the full pre-tax pay and then a fixed $55 insurance charge. How much is paid out? Round to two decimals.
- 参考公式：`(41*30+5*30*1.25+41*30*11/100)*(1-18/100)-55`
- GT：`1218.30`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

## 一次性借款费用与分期还款

- Family：`v3-eval-test-public-loan-repayment-v1`

### 1. `v4-review-test-synthetic-public-loan-repayment-000`

- 母题：`v3-eval-test-gsm8k-1213`
- 类别：`public_seed_derived_synthetic`；措辞变体：`1`
- 中文题意：玛雅借了480美元，同意偿还本金并一次性支付相当于原本金5%的费用。前14个月每月底各还30美元，第15个月付清余额。第15个月需付多少？
- 英文题意：Maya borrowed $480 and agreed to repay the original loan plus a one-time fee equal to 5% of the original amount. She pays $30 at the end of each of the first 14 months and clears the remaining balance in month 15. How much does she pay in month 15?
- 参考公式：`480*(1+5/100)-30*14`
- GT：`84.0`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

## 买一件、第二件半价

- Family：`v3-eval-test-public-bogo-purchase-v1`

### 1. `v4-review-test-synthetic-public-bogo-purchase-000`

- 母题：`v3-eval-test-gsm8k-1070`
- 类别：`public_seed_derived_synthetic`；措辞变体：`1`
- 中文题意：面包店每批用2磅黄油，计划做4批。黄油每磅5美元；每买两磅，其中第二磅半价。所需黄油总共要付多少钱？
- 英文题意：A bakery uses 2 pounds of butter for each batch and plans 4 batches. Butter costs $5 per pound. For every two pounds bought, the second pound is half price. How much will the bakery pay for all the butter it needs?
- 参考公式：`(2*4/2)*(5+5/2)`
- GT：`30.0`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

## 订单小计、配送费与小费

- Family：`v3-eval-test-public-delivery-fee-v1`

### 1. `v4-review-test-synthetic-public-delivery-fee-000`

- 母题：`v3-eval-test-gsm8k-0137`
- 类别：`public_seed_derived_synthetic`；措辞变体：`1`
- 中文题意：订单有3份单价8.25美元的卷饼、2杯单价2.50美元的饮料和4块单价1.25美元的饼干。食物与饮料小计加收15%配送费，之后再加4美元小费。总费用是多少？保留两位小数。
- 英文题意：An order contains 3 wraps at $8.25 each, 2 drinks at $2.50 each, and 4 cookies at $1.25 each. A 15% delivery fee is charged on the food and drink subtotal, then a $4 tip is added. What is the total cost? Round to two decimals.
- 参考公式：`(3*8.25+2*2.5+4*1.25)*(1+15/100)+4`
- GT：`43.96`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

## 分组正确率与加权得分

- Family：`v3-eval-test-public-weighted-test-score-v1`

### 1. `v4-review-test-synthetic-public-weighted-test-score-000`

- 母题：`v3-eval-test-gsm8k-0876`
- 类别：`public_seed_derived_synthetic`；措辞变体：`1`
- 中文题意：一场测验有15道每题1分的选择题、10道每题1分的判断题和8道每题4分的长答题。学生在这三组中分别答对80%、70%和75%。共得多少分？
- 英文题意：A quiz has 15 multiple-choice questions worth 1 point each, 10 true/false questions worth 1 point each, and 8 long-answer questions worth 4 points each. A student answers 80%, 70%, and 75% of those three groups correctly, respectively. How many points does the student earn?
- 参考公式：`15*80/100+10*70/100+8*75/100*4`
- GT：`43.0`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除
