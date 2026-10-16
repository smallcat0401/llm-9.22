# V4 validation公开family扩充：中文审核稿

> 模型输入为英文；中文题意、参考公式和GT只用于人工审核。
> 后续状态：用户于2026-10-06完成审核且未提出修改；28题已纳入 `data/generated/v4_validation_v1.jsonl`。下方空白勾选框保留初版审核格式。

## 为什么是28题

- 现有冻结validation共有36题。
- 4个自写family已经各有8题，共32题，不做修改。
- 另有4个公开family各只有1道原题。这里为每个family新增7道合成题，共28题。
- 若全部审核通过，后续V4 validation将是64题，即8个family各8题。
- 原36题不会被覆盖；冻结test也不会读取或修改。

## 提交人工审核时的状态（历史）

- 这28题全部为 `review_status=pending`。
- 全部为 `evaluation_only=true`、`training_eligible=false`。
- 它们不能进入SFT、GRPO或训练轨迹收集。
- 参考表达式通过安全计算器回放，并由独立关系公式复算。

## 本轮自检结论

- 逐题核对28道英文题、中文题、参考公式和GT：未发现题意与数值冲突。
- 比例分配7题：A、C、D、E数量均为正整数；加权需求7题：需求份数总量均为整数。
- 人口流动7题：自然增长明确为整个期间相对初始人口的增量，期末人口均为正数。
- 储罐7题：累计漏失小于容量，补充量小于漏失量，因此未出现空罐或补水溢出。
- 28道题的ID、英文题面均不重复；每个family的7道新增题GT各不相同；与V4 train及冻结test无family交叉。
- 注意：比例分配和储罐题使用固定参数组合；`seed=509`只会改变加权需求与人口流动的随机参数。
- 注意：同一family的7道题仍是同一种数量关系，主要检验该关系下的稳定性；V3验证题曾用于选择模型，合并后的64题不能称为全新独立holdout。
- 以上是冻结前的自检记录；审核完成后已生成独立的V4验证集，尚未用于V4模型评估。

## 嵌套比例分配

- Family：`v3-eval-val-public-ratio-allocation-v1`
- 原公开题：`v3-eval-val-gsm8k-6154`
- 保留关系：先确定两个已知类别，再把剩余数量按给定比例分配。

### 1. `v4-review-val-ratio-allocation-001`

- 中文题意：一个目录共有 96 条记录。A类占全部记录的二分之一，C类记录数是A类的二分之一。其余记录按 3:1 分给D类和E类。D类有多少条记录？
- 英文题意：A catalog contains 96 records. Category A contains one half of all records, and category C contains one half as many records as category A. All remaining records are assigned to D and E in a 3:1 ratio. How many records are assigned to D?
- 参考公式：`(96-(96*1/2)-((96*1/2)*1/2))*3/(3+1)`
- GT：`18`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-val-ratio-allocation-002`

- 中文题意：仓库要给 120 个包裹标记A、C、D或E。A类占全部包裹的三分之一，C类数量是A类的二分之一。剩余包裹按 2:1 分到D类和E类。D类有多少个？
- 英文题意：A warehouse labels 120 packages with A, C, D, or E. A labels account for one third of all packages, while C has one half the number of A. The rest are split between D and E in the ratio 2:1. How many packages receive label D?
- 参考公式：`(120-(120*1/3)-((120*1/3)*1/2))*2/(2+1)`
- GT：`40`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-val-ratio-allocation-003`

- 中文题意：一个目录共有 144 条记录。A类占全部记录的二分之一，C类记录数是A类的三分之一。其余记录按 3:1 分给D类和E类。D类有多少条记录？
- 英文题意：A catalog contains 144 records. Category A contains one half of all records, and category C contains one third as many records as category A. All remaining records are assigned to D and E in a 3:1 ratio. How many records are assigned to D?
- 参考公式：`(144-(144*1/2)-((144*1/2)*1/3))*3/(3+1)`
- GT：`36`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-val-ratio-allocation-004`

- 中文题意：仓库要给 180 个包裹标记A、C、D或E。A类占全部包裹的五分之二，C类数量是A类的二分之一。剩余包裹按 2:1 分到D类和E类。D类有多少个？
- 英文题意：A warehouse labels 180 packages with A, C, D, or E. A labels account for two fifths of all packages, while C has one half the number of A. The rest are split between D and E in the ratio 2:1. How many packages receive label D?
- 参考公式：`(180-(180*2/5)-((180*2/5)*1/2))*2/(2+1)`
- GT：`48`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-val-ratio-allocation-005`

- 中文题意：一个目录共有 200 条记录。A类占全部记录的四分之一，C类记录数是A类的二分之一。其余记录按 3:2 分给D类和E类。D类有多少条记录？
- 英文题意：A catalog contains 200 records. Category A contains one quarter of all records, and category C contains one half as many records as category A. All remaining records are assigned to D and E in a 3:2 ratio. How many records are assigned to D?
- 参考公式：`(200-(200*1/4)-((200*1/4)*1/2))*3/(3+2)`
- GT：`75`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-val-ratio-allocation-006`

- 中文题意：仓库要给 210 个包裹标记A、C、D或E。A类占全部包裹的五分之二，C类数量是A类的二分之一。剩余包裹按 3:1 分到D类和E类。D类有多少个？
- 英文题意：A warehouse labels 210 packages with A, C, D, or E. A labels account for two fifths of all packages, while C has one half the number of A. The rest are split between D and E in the ratio 3:1. How many packages receive label D?
- 参考公式：`(210-(210*2/5)-((210*2/5)*1/2))*3/(3+1)`
- GT：`63`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 7. `v4-review-val-ratio-allocation-007`

- 中文题意：一个目录共有 240 条记录。A类占全部记录的三分之一，C类记录数是A类的四分之一。其余记录按 4:3 分给D类和E类。D类有多少条记录？
- 英文题意：A catalog contains 240 records. Category A contains one third of all records, and category C contains one quarter as many records as category A. All remaining records are assigned to D and E in a 4:3 ratio. How many records are assigned to D?
- 参考公式：`(240-(240*1/3)-((240*1/3)*1/4))*4/(4+3)`
- GT：`80`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

## 多组加权需求

- Family：`v3-eval-val-public-weighted-demand-v1`
- 原公开题：`v3-eval-val-gsm8k-0839`
- 保留关系：各组人数乘以人均份数，加入备用量后再换算为原料单位。

### 1. `v4-review-val-weighted-demand-001`

- 中文题意：一场餐饮活动中，A组有86人且每人需要半份，B组有52人且每人需要1份，C组有92人且每人需要1.5份，D组有38人且每人需要2份。主办方另准备 18 份备用餐。每份需要 3 个原料单位。总共需要多少个原料单位？
- 英文题意：For a catered event, 86 people in Group A need half a portion each, 52 people in Group B need one portion each, 92 people in Group C need one and a half portions each, 38 people in Group D need two portions each. The organizer adds 18 extra portions. Each portion uses 3 ingredient units. How many ingredient units are required in total?
- 参考公式：`((86*1/2+52*1/1+92*3/2+38*2/1)+18)*3`
- GT：`981`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-val-weighted-demand-002`

- 中文题意：某供餐服务的需求为：A组有88人且每人需要半份，B组有116人且每人需要1份，C组有56人且每人需要2份，D组有42人且每人需要1.5份。再加入 26 份缓冲量后，每份消耗 3 个供应单位。共需多少个供应单位？
- 英文题意：A meal service has the following demand: 88 people in Group A need half a portion each, 116 people in Group B need one portion each, 56 people in Group C need two portions each, 42 people in Group D need one and a half portions each. After including a buffer of 26 portions, it uses 3 supply units per portion. Find the total number of supply units needed.
- 参考公式：`((88*1/2+116*1/1+56*2/1+42*3/2)+26)*3`
- GT：`1083`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-val-weighted-demand-003`

- 中文题意：一场餐饮活动中，A组有80人且每人需要1份，B组有46人且每人需要1.5份，C组有126人且每人需要2份，D组有126人且每人需要半份。主办方另准备 21 份备用餐。每份需要 4 个原料单位。总共需要多少个原料单位？
- 英文题意：For a catered event, 80 people in Group A need one portion each, 46 people in Group B need one and a half portions each, 126 people in Group C need two portions each, 126 people in Group D need half a portion each. The organizer adds 21 extra portions. Each portion uses 4 ingredient units. How many ingredient units are required in total?
- 参考公式：`((80*1/1+46*3/2+126*2/1+126*1/2)+21)*4`
- GT：`1940`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-val-weighted-demand-004`

- 中文题意：某供餐服务的需求为：A组有44人且每人需要半份，B组有68人且每人需要1份，C组有76人且每人需要1.5份，D组有74人且每人需要2份。再加入 17 份缓冲量后，每份消耗 2 个供应单位。共需多少个供应单位？
- 英文题意：A meal service has the following demand: 44 people in Group A need half a portion each, 68 people in Group B need one portion each, 76 people in Group C need one and a half portions each, 74 people in Group D need two portions each. After including a buffer of 17 portions, it uses 2 supply units per portion. Find the total number of supply units needed.
- 参考公式：`((44*1/2+68*1/1+76*3/2+74*2/1)+17)*2`
- GT：`738`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-val-weighted-demand-005`

- 中文题意：一场餐饮活动中，A组有140人且每人需要半份，B组有40人且每人需要1份，C组有98人且每人需要2份，D组有26人且每人需要1.5份。主办方另准备 17 份备用餐。每份需要 5 个原料单位。总共需要多少个原料单位？
- 英文题意：For a catered event, 140 people in Group A need half a portion each, 40 people in Group B need one portion each, 98 people in Group C need two portions each, 26 people in Group D need one and a half portions each. The organizer adds 17 extra portions. Each portion uses 5 ingredient units. How many ingredient units are required in total?
- 参考公式：`((140*1/2+40*1/1+98*2/1+26*3/2)+17)*5`
- GT：`1810`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-val-weighted-demand-006`

- 中文题意：某供餐服务的需求为：A组有92人且每人需要1份，B组有28人且每人需要1.5份，C组有90人且每人需要2份，D组有88人且每人需要半份。再加入 20 份缓冲量后，每份消耗 3 个供应单位。共需多少个供应单位？
- 英文题意：A meal service has the following demand: 92 people in Group A need one portion each, 28 people in Group B need one and a half portions each, 90 people in Group C need two portions each, 88 people in Group D need half a portion each. After including a buffer of 20 portions, it uses 3 supply units per portion. Find the total number of supply units needed.
- 参考公式：`((92*1/1+28*3/2+90*2/1+88*1/2)+20)*3`
- GT：`1134`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 7. `v4-review-val-weighted-demand-007`

- 中文题意：一场餐饮活动中，A组有68人且每人需要半份，B组有48人且每人需要1份，C组有86人且每人需要1.5份，D组有136人且每人需要2份。主办方另准备 12 份备用餐。每份需要 4 个原料单位。总共需要多少个原料单位？
- 英文题意：For a catered event, 68 people in Group A need half a portion each, 48 people in Group B need one portion each, 86 people in Group C need one and a half portions each, 136 people in Group D need two portions each. The organizer adds 12 extra portions. Each portion uses 4 ingredient units. How many ingredient units are required in total?
- 参考公式：`((68*1/2+48*1/1+86*3/2+136*2/1)+12)*4`
- GT：`1980`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

## 期间增长与逐年流动

- Family：`v3-eval-val-public-population-flow-v1`
- 原公开题：`v3-eval-val-gsm8k-4495`
- 保留关系：期间自然增长按初始人口计算，迁入迁出按每年重复发生。

### 1. `v4-review-val-population-flow-001`

- 中文题意：某地区初始有 160,000 名居民。在随后 8 年内，出生与死亡合计带来的自然净增长等于初始人口的 8%。这 8 年中每年有 1,600 人迁出、500 人迁入。8 年后人口是多少？
- 英文题意：A region starts with 160,000 residents. Over the next 8 years, births and deaths together produce a net natural increase equal to 8% of the initial population. During each of those years, 1,600 residents move out and 500 move in. What is the population after 8 years?
- 参考公式：`160000*(1+8/100)-1600*8+500*8`
- GT：`164000`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-val-population-flow-002`

- 中文题意：某行政区初始人口为 100,000。在 5 年期间，自然增长总量等于初始人口的 25%；每年迁入 3,000 人、迁出 1,600 人。期末人口是多少？
- 英文题意：The initial population of a district is 100,000. Across a 5-year period, its total natural growth is 25% of that initial population. Net migration is determined by 3,000 arrivals and 1,600 departures per year. Find the population at the end of the period.
- 参考公式：`100000*(1+25/100)-1600*5+3000*5`
- GT：`132000`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-val-population-flow-003`

- 中文题意：某地区初始有 180,000 名居民。在随后 8 年内，出生与死亡合计带来的自然净增长等于初始人口的 20%。这 8 年中每年有 2,700 人迁出、2,200 人迁入。8 年后人口是多少？
- 英文题意：A region starts with 180,000 residents. Over the next 8 years, births and deaths together produce a net natural increase equal to 20% of the initial population. During each of those years, 2,700 residents move out and 2,200 move in. What is the population after 8 years?
- 参考公式：`180000*(1+20/100)-2700*8+2200*8`
- GT：`212000`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-val-population-flow-004`

- 中文题意：某行政区初始人口为 160,000。在 10 年期间，自然增长总量等于初始人口的 25%；每年迁入 2,200 人、迁出 3,000 人。期末人口是多少？
- 英文题意：The initial population of a district is 160,000. Across a 10-year period, its total natural growth is 25% of that initial population. Net migration is determined by 2,200 arrivals and 3,000 departures per year. Find the population at the end of the period.
- 参考公式：`160000*(1+25/100)-3000*10+2200*10`
- GT：`192000`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-val-population-flow-005`

- 中文题意：某地区初始有 180,000 名居民。在随后 10 年内，出生与死亡合计带来的自然净增长等于初始人口的 18%。这 10 年中每年有 500 人迁出、3,400 人迁入。10 年后人口是多少？
- 英文题意：A region starts with 180,000 residents. Over the next 10 years, births and deaths together produce a net natural increase equal to 18% of the initial population. During each of those years, 500 residents move out and 3,400 move in. What is the population after 10 years?
- 参考公式：`180000*(1+18/100)-500*10+3400*10`
- GT：`241400`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-val-population-flow-006`

- 中文题意：某行政区初始人口为 130,000。在 12 年期间，自然增长总量等于初始人口的 8%；每年迁入 2,000 人、迁出 2,600 人。期末人口是多少？
- 英文题意：The initial population of a district is 130,000. Across a 12-year period, its total natural growth is 8% of that initial population. Net migration is determined by 2,000 arrivals and 2,600 departures per year. Find the population at the end of the period.
- 参考公式：`130000*(1+8/100)-2600*12+2000*12`
- GT：`133200`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 7. `v4-review-val-population-flow-007`

- 中文题意：某地区初始有 190,000 名居民。在随后 10 年内，出生与死亡合计带来的自然净增长等于初始人口的 15%。这 10 年中每年有 2,000 人迁出、700 人迁入。10 年后人口是多少？
- 英文题意：A region starts with 190,000 residents. Over the next 10 years, births and deaths together produce a net natural increase equal to 15% of the initial population. During each of those years, 2,000 residents move out and 700 move in. What is the population after 10 years?
- 参考公式：`190000*(1+15/100)-2000*10+700*10`
- GT：`205500`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

## 多阶段损失与部分恢复

- Family：`v3-eval-val-public-tank-loss-recovery-v1`
- 原公开题：`v3-eval-val-gsm8k-4967`
- 保留关系：从满容量开始经历两段损失和一段补充，求距离重新装满的缺口。

### 1. `v4-review-val-tank-loss-recovery-001`

- 中文题意：一个容量为 500,000 加仑且初始装满的储罐，先以每小时 25,000 加仑漏失 4 小时，再以每小时 12,000 加仑漏失 5 小时。修复后以每小时 30,000 加仑补充 3 小时。距离重新装满还差多少加仑？
- 英文题意：A 500,000-gallon storage tank is initially full. It leaks at 25,000 gallons per hour for 4 hours, then at 12,000 gallons per hour for 5 more hours. After repair, it is refilled at 30,000 gallons per hour for 3 hours. How many gallons short of full is it?
- 参考公式：`500000-(500000-25000*4-12000*5+30000*3)`
- GT：`70000`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 2. `v4-review-val-tank-loss-recovery-002`

- 中文题意：一个初始装满的蓄水池容量为 600,000 加仑。两阶段分别以每小时 30,000 加仑漏失 5 小时、每小时 8,000 加仑漏失 6 小时，之后又以每小时 40,000 加仑补充 4 小时。还需补充多少加仑才能达到容量？
- 英文题意：An initially full reservoir holds 600,000 gallons. Two leaks remove 30,000 gallons per hour for 5 hours and then 8,000 gallons per hour for 6 hours. A later refill adds 40,000 gallons per hour for 4 hours. What volume is still needed to reach capacity?
- 参考公式：`600000-(600000-30000*5-8000*6+40000*4)`
- GT：`38000`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 3. `v4-review-val-tank-loss-recovery-003`

- 中文题意：一个容量为 400,000 加仑且初始装满的燃料罐，先以每小时 18,000 加仑漏失 6 小时，再以每小时 7,000 加仑漏失 8 小时。修复后以每小时 25,000 加仑补充 4 小时。距离重新装满还差多少加仑？
- 英文题意：A 400,000-gallon fuel tank is initially full. It leaks at 18,000 gallons per hour for 6 hours, then at 7,000 gallons per hour for 8 more hours. After repair, it is refilled at 25,000 gallons per hour for 4 hours. How many gallons short of full is it?
- 参考公式：`400000-(400000-18000*6-7000*8+25000*4)`
- GT：`64000`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 4. `v4-review-val-tank-loss-recovery-004`

- 中文题意：一个初始装满的储罐容量为 750,000 加仑。两阶段分别以每小时 40,000 加仑漏失 4 小时、每小时 15,000 加仑漏失 6 小时，之后又以每小时 50,000 加仑补充 3 小时。还需补充多少加仑才能达到容量？
- 英文题意：An initially full storage tank holds 750,000 gallons. Two leaks remove 40,000 gallons per hour for 4 hours and then 15,000 gallons per hour for 6 hours. A later refill adds 50,000 gallons per hour for 3 hours. What volume is still needed to reach capacity?
- 参考公式：`750000-(750000-40000*4-15000*6+50000*3)`
- GT：`100000`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 5. `v4-review-val-tank-loss-recovery-005`

- 中文题意：一个容量为 300,000 加仑且初始装满的蓄水池，先以每小时 20,000 加仑漏失 3 小时，再以每小时 9,000 加仑漏失 5 小时。修复后以每小时 15,000 加仑补充 4 小时。距离重新装满还差多少加仑？
- 英文题意：A 300,000-gallon reservoir is initially full. It leaks at 20,000 gallons per hour for 3 hours, then at 9,000 gallons per hour for 5 more hours. After repair, it is refilled at 15,000 gallons per hour for 4 hours. How many gallons short of full is it?
- 参考公式：`300000-(300000-20000*3-9000*5+15000*4)`
- GT：`45000`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 6. `v4-review-val-tank-loss-recovery-006`

- 中文题意：一个初始装满的燃料罐容量为 900,000 加仑。两阶段分别以每小时 45,000 加仑漏失 5 小时、每小时 20,000 加仑漏失 4 小时，之后又以每小时 60,000 加仑补充 4 小时。还需补充多少加仑才能达到容量？
- 英文题意：An initially full fuel tank holds 900,000 gallons. Two leaks remove 45,000 gallons per hour for 5 hours and then 20,000 gallons per hour for 4 hours. A later refill adds 60,000 gallons per hour for 4 hours. What volume is still needed to reach capacity?
- 参考公式：`900000-(900000-45000*5-20000*4+60000*4)`
- GT：`65000`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除

### 7. `v4-review-val-tank-loss-recovery-007`

- 中文题意：一个容量为 650,000 加仑且初始装满的储罐，先以每小时 32,000 加仑漏失 6 小时，再以每小时 11,000 加仑漏失 7 小时。修复后以每小时 42,000 加仑补充 5 小时。距离重新装满还差多少加仑？
- 英文题意：A 650,000-gallon storage tank is initially full. It leaks at 32,000 gallons per hour for 6 hours, then at 11,000 gallons per hour for 7 more hours. After repair, it is refilled at 42,000 gallons per hour for 5 hours. How many gallons short of full is it?
- 参考公式：`650000-(650000-32000*6-11000*7+42000*5)`
- GT：`59000`；容差：`1e-06`
- 审核结论：□保留　□修改　□删除
