# V4 test 母题扩充：中文审核稿

> 待审核候选，尚未冻结，尚未运行任何模型。英文题面将来给模型；中文、参考公式和 GT 只用于人工审核。

## 总体分组

- 原 V3 test：36 题，文件和哈希保持不变。
- 本轮：36 道原题各衍生 1 道，新增 36 道待审核候选。若全部通过，组合共 72 题。
- 自写母题衍生：32 道；4 道 GSM8K-test 母题衍生：4 道新写合成题。后者**不是**新 GSM8K 公开题，不能算作独立公开样本。
- 8 个 test-only family；与 train、validation 的 family 隔离。本轮只生成题目和 GT，不执行模型搜索或评估。
- 同一 family 的题互相关联；最终须报告每族成功数，也应分开报告原题与扩充题、原公开题与公开母题衍生题。

| 题族 | 原题 | 新题 | 合计 | 新题来源 |
| --- | ---: | ---: | ---: | --- |
| 流量套餐、超额费与税后租赁费 | 8 | 8 | 16 | 自写母题衍生 |
| 分路段油耗、过路费与抵用券 | 8 | 8 | 16 | 自写母题衍生 |
| 折扣购买与部分退款 | 8 | 8 | 16 | 自写母题衍生 |
| 加班、奖金、税与保险费 | 8 | 8 | 16 | 自写母题衍生 |
| 一次性借款费用与分期还款 | 1 | 1 | 2 | 公开母题衍生的合成题 |
| 买一件、第二件半价 | 1 | 1 | 2 | 公开母题衍生的合成题 |
| 订单小计、配送费与小费 | 1 | 1 | 2 | 公开母题衍生的合成题 |
| 分组正确率与加权得分 | 1 | 1 | 2 | 公开母题衍生的合成题 |
| **总计** | **36** | **36** | **72** | — |

## 审核边界

- 每道新题的参考公式已经用安全计算器重放，并与独立数量公式的计算结果核对。
- 计算自检不等于题意审核：仍需逐题确认英文/中文、单位、税费顺序、舍入与 GT。
- 全部新题为 `review_status=pending`、`evaluation_only=true`、`training_eligible=false`。未获审核通过不得合并冻结。
- test 仅用于最终评价；看过模型在 test 上的错题后，不得据此调训练再用同一 test 宣称独立提升。

## 流量套餐、超额费与税后租赁费

- Family：`v3-eval-test-subscription-overage-v1`

### 1. `v4-review-test-derived-subscription-overage-v1-000`

- 母题：`v3-eval-test-subscription-overage-v1-000`
- 来源类别：`self_written_extension`
- 中文题意：月度流量套餐费57美元，包含500GB；超出部分每GB收费0.16美元。用户用了760GB。套餐费和超额费用加收10%服务税，税后再加12美元设备租赁费。最终账单是多少？保留两位小数。
- 英文题意：A monthly data plan costs $57 and includes 500 GB. Extra usage costs $0.16 per GB. A customer uses 760 GB. A service tax of 10% applies to the plan and overage charges, while a $12 equipment rental is added after tax. What is the final bill? Round to two decimals.
- 参考公式：`(57+(760-500)*0.16)*(1+10/100)+12`
- GT：`120.46`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-test-derived-subscription-overage-v1-001`

- 母题：`v3-eval-test-subscription-overage-v1-001`
- 来源类别：`self_written_extension`
- 中文题意：月度流量套餐费64美元，包含600GB；超出部分每GB收费0.13美元。用户用了875GB。套餐费和超额费用加收11%服务税，税后再加14美元设备租赁费。最终账单是多少？保留两位小数。
- 英文题意：A monthly data plan costs $64 and includes 600 GB. Extra usage costs $0.13 per GB. A customer uses 875 GB. A service tax of 11% applies to the plan and overage charges, while a $14 equipment rental is added after tax. What is the final bill? Round to two decimals.
- 参考公式：`(64+(875-600)*0.13)*(1+11/100)+14`
- GT：`124.72`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-test-derived-subscription-overage-v1-002`

- 母题：`v3-eval-test-subscription-overage-v1-002`
- 来源类别：`self_written_extension`
- 中文题意：月度流量套餐费60美元，包含550GB；超出部分每GB收费0.17美元。用户用了835GB。套餐费和超额费用加收11%服务税，税后再加13美元设备租赁费。最终账单是多少？保留两位小数。
- 英文题意：A monthly data plan costs $60 and includes 550 GB. Extra usage costs $0.17 per GB. A customer uses 835 GB. A service tax of 11% applies to the plan and overage charges, while a $13 equipment rental is added after tax. What is the final bill? Round to two decimals.
- 参考公式：`(60+(835-550)*0.17)*(1+11/100)+13`
- GT：`133.38`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-test-derived-subscription-overage-v1-003`

- 母题：`v3-eval-test-subscription-overage-v1-003`
- 来源类别：`self_written_extension`
- 中文题意：月度流量套餐费67美元，包含650GB；超出部分每GB收费0.14美元。用户用了950GB。套餐费和超额费用加收12%服务税，税后再加15美元设备租赁费。最终账单是多少？保留两位小数。
- 英文题意：A monthly data plan costs $67 and includes 650 GB. Extra usage costs $0.14 per GB. A customer uses 950 GB. A service tax of 12% applies to the plan and overage charges, while a $15 equipment rental is added after tax. What is the final bill? Round to two decimals.
- 参考公式：`(67+(950-650)*0.14)*(1+12/100)+15`
- GT：`137.08`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-test-derived-subscription-overage-v1-004`

- 母题：`v3-eval-test-subscription-overage-v1-004`
- 来源类别：`self_written_extension`
- 中文题意：月度流量套餐费63美元，包含600GB；超出部分每GB收费0.18美元。用户用了910GB。套餐费和超额费用加收12%服务税，税后再加14美元设备租赁费。最终账单是多少？保留两位小数。
- 英文题意：A monthly data plan costs $63 and includes 600 GB. Extra usage costs $0.18 per GB. A customer uses 910 GB. A service tax of 12% applies to the plan and overage charges, while a $14 equipment rental is added after tax. What is the final bill? Round to two decimals.
- 参考公式：`(63+(910-600)*0.18)*(1+12/100)+14`
- GT：`147.06`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-test-derived-subscription-overage-v1-005`

- 母题：`v3-eval-test-subscription-overage-v1-005`
- 来源类别：`self_written_extension`
- 中文题意：月度流量套餐费70美元，包含700GB；超出部分每GB收费0.15美元。用户用了1025GB。套餐费和超额费用加收13%服务税，税后再加16美元设备租赁费。最终账单是多少？保留两位小数。
- 英文题意：A monthly data plan costs $70 and includes 700 GB. Extra usage costs $0.15 per GB. A customer uses 1025 GB. A service tax of 13% applies to the plan and overage charges, while a $16 equipment rental is added after tax. What is the final bill? Round to two decimals.
- 参考公式：`(70+(1025-700)*0.15)*(1+13/100)+16`
- GT：`150.19`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 7. `v4-review-test-derived-subscription-overage-v1-006`

- 母题：`v3-eval-test-subscription-overage-v1-006`
- 来源类别：`self_written_extension`
- 中文题意：月度流量套餐费66美元，包含650GB；超出部分每GB收费0.19美元。用户用了985GB。套餐费和超额费用加收13%服务税，税后再加15美元设备租赁费。最终账单是多少？保留两位小数。
- 英文题意：A monthly data plan costs $66 and includes 650 GB. Extra usage costs $0.19 per GB. A customer uses 985 GB. A service tax of 13% applies to the plan and overage charges, while a $15 equipment rental is added after tax. What is the final bill? Round to two decimals.
- 参考公式：`(66+(985-650)*0.19)*(1+13/100)+15`
- GT：`161.5`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 8. `v4-review-test-derived-subscription-overage-v1-007`

- 母题：`v3-eval-test-subscription-overage-v1-007`
- 来源类别：`self_written_extension`
- 中文题意：月度流量套餐费73美元，包含750GB；超出部分每GB收费0.16美元。用户用了1100GB。套餐费和超额费用加收14%服务税，税后再加17美元设备租赁费。最终账单是多少？保留两位小数。
- 英文题意：A monthly data plan costs $73 and includes 750 GB. Extra usage costs $0.16 per GB. A customer uses 1100 GB. A service tax of 14% applies to the plan and overage charges, while a $17 equipment rental is added after tax. What is the final bill? Round to two decimals.
- 参考公式：`(73+(1100-750)*0.16)*(1+14/100)+17`
- GT：`164.06`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

## 分路段油耗、过路费与抵用券

- Family：`v3-eval-test-route-cost-v1`

### 1. `v4-review-test-derived-route-cost-v1-000`

- 母题：`v3-eval-test-route-cost-v1-000`
- 来源类别：`self_written_extension`
- 中文题意：送货车在高速公路行驶300英里，油耗为每加仑30英里；在城市道路行驶216英里，油耗为每加仑24英里。油价每加仑4.20美元，另有26美元过路费，最后使用14美元出行抵用券。此次行程净成本是多少？
- 英文题意：A delivery van travels 300 miles on highways at 30 miles per gallon and 216 miles in cities at 24 miles per gallon. Fuel costs $4.20 per gallon. The route also has a $26 toll, and a travel voucher of $14 is applied to the total. What is the trip's net cost?
- 参考公式：`(300/30+216/24)*4.2+26-14`
- GT：`91.8`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-test-derived-route-cost-v1-001`

- 母题：`v3-eval-test-route-cost-v1-001`
- 来源类别：`self_written_extension`
- 中文题意：送货车在高速公路行驶350英里，油耗为每加仑35英里；在城市道路行驶192英里，油耗为每加仑24英里。油价每加仑4.50美元，另有30美元过路费，最后使用16美元出行抵用券。此次行程净成本是多少？
- 英文题意：A delivery van travels 350 miles on highways at 35 miles per gallon and 192 miles in cities at 24 miles per gallon. Fuel costs $4.50 per gallon. The route also has a $30 toll, and a travel voucher of $16 is applied to the total. What is the trip's net cost?
- 参考公式：`(350/35+192/24)*4.5+30-16`
- GT：`95.0`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-test-derived-route-cost-v1-002`

- 母题：`v3-eval-test-route-cost-v1-002`
- 来源类别：`self_written_extension`
- 中文题意：送货车在高速公路行驶330英里，油耗为每加仑30英里；在城市道路行驶240英里，油耗为每加仑24英里。油价每加仑4.30美元，另有28美元过路费，最后使用15美元出行抵用券。此次行程净成本是多少？
- 英文题意：A delivery van travels 330 miles on highways at 30 miles per gallon and 240 miles in cities at 24 miles per gallon. Fuel costs $4.30 per gallon. The route also has a $28 toll, and a travel voucher of $15 is applied to the total. What is the trip's net cost?
- 参考公式：`(330/30+240/24)*4.3+28-15`
- GT：`103.3`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-test-derived-route-cost-v1-003`

- 母题：`v3-eval-test-route-cost-v1-003`
- 来源类别：`self_written_extension`
- 中文题意：送货车在高速公路行驶385英里，油耗为每加仑35英里；在城市道路行驶216英里，油耗为每加仑24英里。油价每加仑4.60美元，另有32美元过路费，最后使用17美元出行抵用券。此次行程净成本是多少？
- 英文题意：A delivery van travels 385 miles on highways at 35 miles per gallon and 216 miles in cities at 24 miles per gallon. Fuel costs $4.60 per gallon. The route also has a $32 toll, and a travel voucher of $17 is applied to the total. What is the trip's net cost?
- 参考公式：`(385/35+216/24)*4.6+32-17`
- GT：`107.0`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-test-derived-route-cost-v1-004`

- 母题：`v3-eval-test-route-cost-v1-004`
- 来源类别：`self_written_extension`
- 中文题意：送货车在高速公路行驶360英里，油耗为每加仑30英里；在城市道路行驶264英里，油耗为每加仑24英里。油价每加仑4.40美元，另有30美元过路费，最后使用16美元出行抵用券。此次行程净成本是多少？
- 英文题意：A delivery van travels 360 miles on highways at 30 miles per gallon and 264 miles in cities at 24 miles per gallon. Fuel costs $4.40 per gallon. The route also has a $30 toll, and a travel voucher of $16 is applied to the total. What is the trip's net cost?
- 参考公式：`(360/30+264/24)*4.4+30-16`
- GT：`115.2`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-test-derived-route-cost-v1-005`

- 母题：`v3-eval-test-route-cost-v1-005`
- 来源类别：`self_written_extension`
- 中文题意：送货车在高速公路行驶420英里，油耗为每加仑35英里；在城市道路行驶240英里，油耗为每加仑24英里。油价每加仑4.70美元，另有34美元过路费，最后使用18美元出行抵用券。此次行程净成本是多少？
- 英文题意：A delivery van travels 420 miles on highways at 35 miles per gallon and 240 miles in cities at 24 miles per gallon. Fuel costs $4.70 per gallon. The route also has a $34 toll, and a travel voucher of $18 is applied to the total. What is the trip's net cost?
- 参考公式：`(420/35+240/24)*4.70+34-18`
- GT：`119.4`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 7. `v4-review-test-derived-route-cost-v1-006`

- 母题：`v3-eval-test-route-cost-v1-006`
- 来源类别：`self_written_extension`
- 中文题意：送货车在高速公路行驶390英里，油耗为每加仑30英里；在城市道路行驶288英里，油耗为每加仑24英里。油价每加仑4.50美元，另有32美元过路费，最后使用17美元出行抵用券。此次行程净成本是多少？
- 英文题意：A delivery van travels 390 miles on highways at 30 miles per gallon and 288 miles in cities at 24 miles per gallon. Fuel costs $4.50 per gallon. The route also has a $32 toll, and a travel voucher of $17 is applied to the total. What is the trip's net cost?
- 参考公式：`(390/30+288/24)*4.5+32-17`
- GT：`127.5`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 8. `v4-review-test-derived-route-cost-v1-007`

- 母题：`v3-eval-test-route-cost-v1-007`
- 来源类别：`self_written_extension`
- 中文题意：送货车在高速公路行驶455英里，油耗为每加仑35英里；在城市道路行驶264英里，油耗为每加仑24英里。油价每加仑4.80美元，另有36美元过路费，最后使用19美元出行抵用券。此次行程净成本是多少？
- 英文题意：A delivery van travels 455 miles on highways at 35 miles per gallon and 264 miles in cities at 24 miles per gallon. Fuel costs $4.80 per gallon. The route also has a $36 toll, and a travel voucher of $19 is applied to the total. What is the trip's net cost?
- 参考公式：`(455/35+264/24)*4.8+36-19`
- GT：`132.2`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

## 折扣购买与部分退款

- Family：`v3-eval-test-partial-refund-v1`

### 1. `v4-review-test-derived-partial-refund-v1-000`

- 母题：`v3-eval-test-partial-refund-v1-000`
- 来源类别：`self_written_extension`
- 中文题意：顾客在全场优惠15%期间购买7件单价60美元的商品和6件单价85美元的商品，另付不可退的16美元配送费。之后退回1件85美元的商品，但因补货费只能退回该商品折后价的80%。顾客最终净支付多少？保留两位小数。
- 英文题意：A customer buys 7 items at $60 each and 6 items at $85 each during a 15%-off sale, plus a nonrefundable $16 delivery charge. The customer returns one $85 item but receives only 80% of that item's discounted price because of a restocking fee. What is the customer's final net payment? Round to two decimals.
- 参考公式：`(7*60+6*85)*(1-15/100)+16-85*(1-15/100)*80/100`
- GT：`748.7`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-test-derived-partial-refund-v1-001`

- 母题：`v3-eval-test-partial-refund-v1-001`
- 来源类别：`self_written_extension`
- 中文题意：顾客在全场优惠20%期间购买6件单价75美元的商品和7件单价50美元的商品，另付不可退的13美元配送费。之后退回1件50美元的商品，但因补货费只能退回该商品折后价的75%。顾客最终净支付多少？保留两位小数。
- 英文题意：A customer buys 6 items at $75 each and 7 items at $50 each during a 20%-off sale, plus a nonrefundable $13 delivery charge. The customer returns one $50 item but receives only 75% of that item's discounted price because of a restocking fee. What is the customer's final net payment? Round to two decimals.
- 参考公式：`(6*75+7*50)*(1-20/100)+13-50*(1-20/100)*75/100`
- GT：`623.0`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-test-derived-partial-refund-v1-002`

- 母题：`v3-eval-test-partial-refund-v1-002`
- 来源类别：`self_written_extension`
- 中文题意：顾客在全场优惠15%期间购买8件单价65美元的商品和7件单价90美元的商品，另付不可退的17美元配送费。之后退回1件90美元的商品，但因补货费只能退回该商品折后价的80%。顾客最终净支付多少？保留两位小数。
- 英文题意：A customer buys 8 items at $65 each and 7 items at $90 each during a 15%-off sale, plus a nonrefundable $17 delivery charge. The customer returns one $90 item but receives only 80% of that item's discounted price because of a restocking fee. What is the customer's final net payment? Round to two decimals.
- 参考公式：`(8*65+7*90)*(1-15/100)+17-90*(1-15/100)*80/100`
- GT：`933.3`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-test-derived-partial-refund-v1-003`

- 母题：`v3-eval-test-partial-refund-v1-003`
- 来源类别：`self_written_extension`
- 中文题意：顾客在全场优惠20%期间购买7件单价80美元的商品和8件单价55美元的商品，另付不可退的14美元配送费。之后退回1件55美元的商品，但因补货费只能退回该商品折后价的75%。顾客最终净支付多少？保留两位小数。
- 英文题意：A customer buys 7 items at $80 each and 8 items at $55 each during a 20%-off sale, plus a nonrefundable $14 delivery charge. The customer returns one $55 item but receives only 75% of that item's discounted price because of a restocking fee. What is the customer's final net payment? Round to two decimals.
- 参考公式：`(7*80+8*55)*(1-20/100)+14-55*(1-20/100)*75/100`
- GT：`781.0`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-test-derived-partial-refund-v1-004`

- 母题：`v3-eval-test-partial-refund-v1-004`
- 来源类别：`self_written_extension`
- 中文题意：顾客在全场优惠15%期间购买9件单价70美元的商品和8件单价95美元的商品，另付不可退的18美元配送费。之后退回1件95美元的商品，但因补货费只能退回该商品折后价的80%。顾客最终净支付多少？保留两位小数。
- 英文题意：A customer buys 9 items at $70 each and 8 items at $95 each during a 15%-off sale, plus a nonrefundable $18 delivery charge. The customer returns one $95 item but receives only 80% of that item's discounted price because of a restocking fee. What is the customer's final net payment? Round to two decimals.
- 参考公式：`(9*70+8*95)*(1-15/100)+18-95*(1-15/100)*80/100`
- GT：`1134.9`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-test-derived-partial-refund-v1-005`

- 母题：`v3-eval-test-partial-refund-v1-005`
- 来源类别：`self_written_extension`
- 中文题意：顾客在全场优惠20%期间购买8件单价85美元的商品和9件单价60美元的商品，另付不可退的15美元配送费。之后退回1件60美元的商品，但因补货费只能退回该商品折后价的75%。顾客最终净支付多少？保留两位小数。
- 英文题意：A customer buys 8 items at $85 each and 9 items at $60 each during a 20%-off sale, plus a nonrefundable $15 delivery charge. The customer returns one $60 item but receives only 75% of that item's discounted price because of a restocking fee. What is the customer's final net payment? Round to two decimals.
- 参考公式：`(8*85+9*60)*(1-20/100)+15-60*(1-20/100)*75/100`
- GT：`955.0`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 7. `v4-review-test-derived-partial-refund-v1-006`

- 母题：`v3-eval-test-partial-refund-v1-006`
- 来源类别：`self_written_extension`
- 中文题意：顾客在全场优惠15%期间购买10件单价75美元的商品和9件单价100美元的商品，另付不可退的19美元配送费。之后退回1件100美元的商品，但因补货费只能退回该商品折后价的80%。顾客最终净支付多少？保留两位小数。
- 英文题意：A customer buys 10 items at $75 each and 9 items at $100 each during a 15%-off sale, plus a nonrefundable $19 delivery charge. The customer returns one $100 item but receives only 80% of that item's discounted price because of a restocking fee. What is the customer's final net payment? Round to two decimals.
- 参考公式：`(10*75+9*100)*(1-15/100)+19-100*(1-15/100)*80/100`
- GT：`1353.5`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 8. `v4-review-test-derived-partial-refund-v1-007`

- 母题：`v3-eval-test-partial-refund-v1-007`
- 来源类别：`self_written_extension`
- 中文题意：顾客在全场优惠20%期间购买9件单价90美元的商品和10件单价65美元的商品，另付不可退的16美元配送费。之后退回1件65美元的商品，但因补货费只能退回该商品折后价的75%。顾客最终净支付多少？保留两位小数。
- 英文题意：A customer buys 9 items at $90 each and 10 items at $65 each during a 20%-off sale, plus a nonrefundable $16 delivery charge. The customer returns one $65 item but receives only 75% of that item's discounted price because of a restocking fee. What is the customer's final net payment? Round to two decimals.
- 参考公式：`(9*90+10*65)*(1-20/100)+16-65*(1-20/100)*75/100`
- GT：`1145.0`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

## 加班、奖金、税与保险费

- Family：`v3-eval-test-bonus-deduction-v1`

### 1. `v4-review-test-derived-bonus-deduction-v1-000`

- 母题：`v3-eval-test-bonus-deduction-v1-000`
- 来源类别：`self_written_extension`
- 中文题意：员工正常工作38小时、加班11小时，正常时薪28美元，加班时薪为正常时薪的1.5倍。绩效奖金等于正常工时工资的10%。全部税前收入扣除18%的税后，再扣54美元固定保险费。实发工资是多少？保留两位小数。
- 英文题意：An employee works 38 regular hours and 11 overtime hours at $28 per hour. Overtime pays 1.5 times the regular rate. A performance bonus equals 10% of regular-hour wages. After 18% tax on all gross pay, a fixed $54 insurance deduction is taken. What is take-home pay? Round to two decimals.
- 参考公式：`(38*28+11*28*1.5+38*28*10/100)*(1-18/100)-54`
- GT：`1284.57`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-test-derived-bonus-deduction-v1-001`

- 母题：`v3-eval-test-bonus-deduction-v1-001`
- 来源类别：`self_written_extension`
- 中文题意：员工正常工作40小时、加班9小时，正常时薪31美元，加班时薪为正常时薪的1.5倍。绩效奖金等于正常工时工资的12%。全部税前收入扣除20%的税后，再扣67美元固定保险费。实发工资是多少？保留两位小数。
- 英文题意：An employee works 40 regular hours and 9 overtime hours at $31 per hour. Overtime pays 1.5 times the regular rate. A performance bonus equals 12% of regular-hour wages. After 20% tax on all gross pay, a fixed $67 insurance deduction is taken. What is take-home pay? Round to two decimals.
- 参考公式：`(40*31+9*31*1.5+40*31*12/100)*(1-20/100)-67`
- GT：`1378.84`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-test-derived-bonus-deduction-v1-002`

- 母题：`v3-eval-test-bonus-deduction-v1-002`
- 来源类别：`self_written_extension`
- 中文题意：员工正常工作38小时、加班12小时，正常时薪29美元，加班时薪为正常时薪的1.5倍。绩效奖金等于正常工时工资的11%。全部税前收入扣除18%的税后，再扣57美元固定保险费。实发工资是多少？保留两位小数。
- 英文题意：An employee works 38 regular hours and 12 overtime hours at $29 per hour. Overtime pays 1.5 times the regular rate. A performance bonus equals 11% of regular-hour wages. After 18% tax on all gross pay, a fixed $57 insurance deduction is taken. What is take-home pay? Round to two decimals.
- 参考公式：`(38*29+12*29*1.5+38*29*11/100)*(1-18/100)-57`
- GT：`1374.08`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-test-derived-bonus-deduction-v1-003`

- 母题：`v3-eval-test-bonus-deduction-v1-003`
- 来源类别：`self_written_extension`
- 中文题意：员工正常工作40小时、加班10小时，正常时薪32美元，加班时薪为正常时薪的1.5倍。绩效奖金等于正常工时工资的13%。全部税前收入扣除20%的税后，再扣70美元固定保险费。实发工资是多少？保留两位小数。
- 英文题意：An employee works 40 regular hours and 10 overtime hours at $32 per hour. Overtime pays 1.5 times the regular rate. A performance bonus equals 13% of regular-hour wages. After 20% tax on all gross pay, a fixed $70 insurance deduction is taken. What is take-home pay? Round to two decimals.
- 参考公式：`(40*32+10*32*1.5+40*32*13/100)*(1-20/100)-70`
- GT：`1471.12`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-test-derived-bonus-deduction-v1-004`

- 母题：`v3-eval-test-bonus-deduction-v1-004`
- 来源类别：`self_written_extension`
- 中文题意：员工正常工作38小时、加班13小时，正常时薪30美元，加班时薪为正常时薪的1.5倍。绩效奖金等于正常工时工资的12%。全部税前收入扣除18%的税后，再扣60美元固定保险费。实发工资是多少？保留两位小数。
- 英文题意：An employee works 38 regular hours and 13 overtime hours at $30 per hour. Overtime pays 1.5 times the regular rate. A performance bonus equals 12% of regular-hour wages. After 18% tax on all gross pay, a fixed $60 insurance deduction is taken. What is take-home pay? Round to two decimals.
- 参考公式：`(38*30+13*30*1.5+38*30*12/100)*(1-18/100)-60`
- GT：`1466.68`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-test-derived-bonus-deduction-v1-005`

- 母题：`v3-eval-test-bonus-deduction-v1-005`
- 来源类别：`self_written_extension`
- 中文题意：员工正常工作40小时、加班11小时，正常时薪33美元，加班时薪为正常时薪的1.5倍。绩效奖金等于正常工时工资的14%。全部税前收入扣除20%的税后，再扣73美元固定保险费。实发工资是多少？保留两位小数。
- 英文题意：An employee works 40 regular hours and 11 overtime hours at $33 per hour. Overtime pays 1.5 times the regular rate. A performance bonus equals 14% of regular-hour wages. After 20% tax on all gross pay, a fixed $73 insurance deduction is taken. What is take-home pay? Round to two decimals.
- 参考公式：`(40*33+11*33*1.5+40*33*14/100)*(1-20/100)-73`
- GT：`1566.44`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 7. `v4-review-test-derived-bonus-deduction-v1-006`

- 母题：`v3-eval-test-bonus-deduction-v1-006`
- 来源类别：`self_written_extension`
- 中文题意：员工正常工作38小时、加班14小时，正常时薪31美元，加班时薪为正常时薪的1.5倍。绩效奖金等于正常工时工资的13%。全部税前收入扣除18%的税后，再扣63美元固定保险费。实发工资是多少？保留两位小数。
- 英文题意：An employee works 38 regular hours and 14 overtime hours at $31 per hour. Overtime pays 1.5 times the regular rate. A performance bonus equals 13% of regular-hour wages. After 18% tax on all gross pay, a fixed $63 insurance deduction is taken. What is take-home pay? Round to two decimals.
- 参考公式：`(38*31+14*31*1.5+38*31*13/100)*(1-18/100)-63`
- GT：`1562.35`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

### 8. `v4-review-test-derived-bonus-deduction-v1-007`

- 母题：`v3-eval-test-bonus-deduction-v1-007`
- 来源类别：`self_written_extension`
- 中文题意：员工正常工作40小时、加班12小时，正常时薪34美元，加班时薪为正常时薪的1.5倍。绩效奖金等于正常工时工资的15%。全部税前收入扣除20%的税后，再扣76美元固定保险费。实发工资是多少？保留两位小数。
- 英文题意：An employee works 40 regular hours and 12 overtime hours at $34 per hour. Overtime pays 1.5 times the regular rate. A performance bonus equals 15% of regular-hour wages. After 20% tax on all gross pay, a fixed $76 insurance deduction is taken. What is take-home pay? Round to two decimals.
- 参考公式：`(40*34+12*34*1.5+40*34*15/100)*(1-20/100)-76`
- GT：`1664.8`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

## 一次性借款费用与分期还款

- Family：`v3-eval-test-public-loan-repayment-v1`

### 1. `v4-review-test-derived-gsm8k-1213`

- 母题：`v3-eval-test-gsm8k-1213`
- 来源类别：`public_seed_derived_synthetic`
- 中文题意：玛雅借了480美元，同意偿还本金并一次性支付相当于原本金5%的费用。前14个月每月底各还30美元，第15个月付清余额。第15个月需付多少？
- 英文题意：Maya borrowed $480 and agreed to repay the original loan plus a one-time fee equal to 5% of the original amount. She pays $30 at the end of each of the first 14 months and clears the remaining balance in month 15. How much does she pay in month 15?
- 参考公式：`480*(1+5/100)-30*14`
- GT：`84.0`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

## 买一件、第二件半价

- Family：`v3-eval-test-public-bogo-purchase-v1`

### 1. `v4-review-test-derived-gsm8k-1070`

- 母题：`v3-eval-test-gsm8k-1070`
- 来源类别：`public_seed_derived_synthetic`
- 中文题意：面包店每批用2磅黄油，计划做4批。黄油每磅5美元；每买两磅，其中第二磅半价。所需黄油总共要付多少钱？
- 英文题意：A bakery uses 2 pounds of butter for each batch and plans 4 batches. Butter costs $5 per pound. For every two pounds bought, the second pound is half price. How much will the bakery pay for all the butter it needs?
- 参考公式：`(2*4/2)*(5+5/2)`
- GT：`30.0`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

## 订单小计、配送费与小费

- Family：`v3-eval-test-public-delivery-fee-v1`

### 1. `v4-review-test-derived-gsm8k-0137`

- 母题：`v3-eval-test-gsm8k-0137`
- 来源类别：`public_seed_derived_synthetic`
- 中文题意：订单有3份单价8.25美元的卷饼、2杯单价2.50美元的饮料和4块单价1.25美元的饼干。食物与饮料小计加收15%配送费，之后再加4美元小费。总费用是多少？保留两位小数。
- 英文题意：An order contains 3 wraps at $8.25 each, 2 drinks at $2.50 each, and 4 cookies at $1.25 each. A 15% delivery fee is charged on the food and drink subtotal, then a $4 tip is added. What is the total cost? Round to two decimals.
- 参考公式：`(3*8.25+2*2.5+4*1.25)*(1+15/100)+4`
- GT：`43.96`；容差：`0.005`
- 审核结论：□保留　□修改　□删除

## 分组正确率与加权得分

- Family：`v3-eval-test-public-weighted-test-score-v1`

### 1. `v4-review-test-derived-gsm8k-0876`

- 母题：`v3-eval-test-gsm8k-0876`
- 来源类别：`public_seed_derived_synthetic`
- 中文题意：一场测验有15道每题1分的选择题、10道每题1分的判断题和8道每题4分的长答题。学生在这三组中分别答对80%、70%和75%。共得多少分？
- 英文题意：A quiz has 15 multiple-choice questions worth 1 point each, 10 true/false questions worth 1 point each, and 8 long-answer questions worth 4 points each. A student answers 80%, 70%, and 75% of those three groups correctly, respectively. How many points does the student earn?
- 参考公式：`15*80/100+10*70/100+8*75/100*4`
- GT：`43.0`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除
