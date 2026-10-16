# V3 4B QLoRA validation结果

## 结论摘要

公司GPU完成了Search-SFT、Reference-SFT和Mixed-SFT三个分支的三轮QLoRA训练，
并在冻结的36题validation上评估了每个分支的epoch 1、epoch 2和epoch 3，
共9个候选checkpoint。冻结test没有运行，也没有包含在返回包中。

按照训练前固定在`docs/V3_QLORA_PLAN_ZH.md`中的选择规则，9个候选中唯一第一名是：

- 分支：Mixed-SFT（32条search轨迹 + 26条reference-program轨迹）；
- checkpoint：epoch 3，即174 step后的最终adapter；
- validation严格成功：24/36；
- outcome verifier通过：24/36；
- 协议错误：0/36；
- 平均记录工具调用：1.0次/题；
- 工具执行失败：0次。

这个选择证明Mixed58 epoch 3在9个已训练候选中最好。返回元数据中的starting
policy写为`Qwen1/Qwen3.5-4B`，而冻结基线写为`Qwen/Qwen3.5-4B`。2026-10-05
由公司机器操作者确认：`Qwen1`只是本地文件夹名，目录内容仍是官方
`Qwen/Qwen3.5-4B`。因此将其记录为本地路径别名，而不是不同starting policy；
本轮checkpoint选择正式冻结为Mixed58 epoch 3。

## 返回文件与完整性

2026-10-05收到三个结果包：

| 文件 | SHA-256 |
|---|---|
| `dist/artifacts.zip` | `e7e778c63939b1f2189a0a8ab3af7a07dfd2cdf7b464f5ae3ca301fbeb1b7737` |
| `dist/eval.zip` | `b27248d87eaa398587979855ef632d2477aea0e2894ba3175efd42cefb142df2` |
| `dist/logs.zip` | `3074b3512292deae403cf745f3e1817f003d4389d0a063fd27fed1db51e0f8de` |

`artifacts.zip`包含三次训练指标和9次validation指标；`eval.zip`包含9次validation
的逐题记录；`logs.zip`包含训练日志。三个包均可正常枚举和解压。返回文件没有test记录。

## 三个训练分支

训练loss仅用于确认训练确实发生，不能代替未见题目的结果验证。

| 分支 | 数据量 | step | 初始loss | 最终loss | 降幅 | 峰值CUDA显存 | 用时 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Search-SFT | 32 | 96 | 0.07354 | 0.02441 | 66.81% | 8998.6 MiB | 96.3 s |
| Reference-SFT | 26 | 78 | 0.18914 | 0.00627 | 96.69% | 9467.0 MiB | 87.4 s |
| Mixed-SFT | 58 | 174 | 0.12536 | 0.02808 | 77.60% | 9467.0 MiB | 182.8 s |

## 9个validation候选

下表按照预登记规则排序。基线单独列出，不参与checkpoint选择。

| 排名 | 候选 | 严格成功 | Verifier通过 | 协议错误 | 平均工具调用 | 工具执行失败 |
|---:|---|---:|---:|---:|---:|---:|
| 1 | Mixed58 epoch 3 | 24/36 | 24/36 | 0 | 1.0000 | 0 |
| 2 | Reference26 epoch 1 | 23/36 | 23/36 | 0 | 1.0000 | 0 |
| 3 | Search32 epoch 1 | 23/36 | 23/36 | 3 | 1.3889 | 0 |
| 4 | Search32 epoch 3 | 20/36 | 20/36 | 0 | 0.8889 | 0 |
| 5 | Search32 epoch 2 | 19/36 | 19/36 | 0 | 0.9722 | 0 |
| 6 | Mixed58 epoch 2 | 19/36 | 19/36 | 3 | 0.9722 | 8 |
| 7 | Mixed58 epoch 1 | 17/36 | 17/36 | 0 | 1.0000 | 0 |
| 8 | Reference26 epoch 3 | 17/36 | 17/36 | 0 | 1.0000 | 8 |
| 9 | Reference26 epoch 2 | 16/36 | 16/36 | 0 | 1.0000 | 0 |
| - | 原冻结基线（模型标识不同） | 16/36 | 18/36 | 10 | 1.1944 | 0 |

结果不是随着epoch单调提高。例如Reference26从23降到16再回到17，Mixed58从17到19
再到24。这说明不能根据训练loss最低或训练轮数最多选模型，必须使用冻结validation。

## 第一名的family表现

| Validation family | 成功/题数 |
|---|---:|
| `tiered-commission-v1` | 8/8 |
| `restricted-grant-v1` | 7/8 |
| `fixed-basket-change-v1` | 7/8 |
| `rework-yield-v1` | 1/8 |
| `public-population-flow-v1` | 1/1 |
| `public-ratio-allocation-v1` | 0/1 |
| `public-weighted-demand-v1` | 0/1 |
| `public-tank-loss-recovery-v1` | 0/1 |

因此24/36并不是均匀能力提升。它主要来自分段提成、限定补助和固定篮子变化，
而返工回收率仍是明显短板，三道较复杂的公开组合题也全部失败。

## 第一名的失败归因

第一名的12道失败均不是计算器执行失败，也不是JSON协议错误：模型成功调用了计算器，
但构造了错误公式，或者没有忠实复制工具结果。

- `restricted-grant-v1-006`：把材料成本中的21%重复加回，属于公式构造错误。
- `fixed-basket-change-v1-007`：工具正确得到约`0.3871`，final却输出`38.71`，属于
  工具结果到最终答案的数量级抄写错误。
- `rework-yield-v1`七错六：把“仅恢复被拒品的一部分”错误写成对全部合格品乘
  `1 + recovery_rate`，属于系统性的集合/基数理解错误。
- `public-ratio-allocation-v1`：未先扣除A和C的人数并按2:1分配余数。
- `public-weighted-demand-v1`：没有对全部煎蛋数量统一乘2个鸡蛋。
- `public-tank-loss-recovery-v1`：算成当前水量，而题目要求距离满容量还缺多少。

这些错误支持下一轮扩充“数量关系多样性”和成对易错反例，而不支持继续重复同一批
提成模板。

## 模型路径别名核验

公司机器操作者已确认`Qwen1/Qwen3.5-4B`只是官方模型下载后的本地文件夹名。
训练、9个adapter validation和此前基线因而使用同一官方starting policy。
后续打包或复现时仍建议记录模型snapshot revision或权重哈希，避免仅靠可变目录名
辨认checkpoint，但这不再阻塞本轮选择。

当前状态：

- 已冻结Mixed58 epoch 3为9个adapter中的唯一胜者；
- validation严格成功由starting policy的16/36提高到24/36；
- test仍未打开，因此这里仍只报告validation结果，不能提前声称test提升。

## 扩充决策与test边界

2026-10-05决定继续扩充题目，因此暂不运行V3 frozen test。现有V3 validation已经用于
选择checkpoint并分析失败模式；如果这些失败模式用于设计V4训练题，它从此应视为
development/diagnostic集合，不能再作为V4的唯一checkpoint选择证据。

V4应先扩充train-only新families，再冻结一个新的、family-disjoint的V4 validation用于
checkpoint选择。仍未运行的V3 frozen test可以保留到最后一次评价，但前提是V4训练
families继续与它保持模板/family隔离，而且扩充过程不查看或针对其题目。若无法保证，
则必须另外冻结新的V4 final test。绝不能先查看test错题、据此训练，再在同一test上
报告“独立泛化提升”。
