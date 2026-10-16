# V3 正式评估协议

## 已冻结的数据

| 集合 | 数量 | 自写题 | 公开题 | 用途 |
|---|---:|---:|---:|---|
| validation | 36 | 32 | 4 | 选择训练分支和 checkpoint |
| test | 36 | 32 | 4 | 只做最终比较 |

- Validation：`data/generated/v3_validation_v1.jsonl`
- Test：`data/generated/v3_test_v1.jsonl`
- 清单：`artifacts/dataset_manifests/v3_evaluation_v1.json`

两个 split 各有四个独立的自写模板和四道独立公开题，题族没有交叉；它们与 58 条 V3 SFT 数据也没有题族交叉。所有题均为 calculator 条件，用于同时观察数量推理、协议遵循和工具调用。

## 使用顺序

```text
4B starting policy
        ↓
只运行 validation 基线
        ↓
训练 Search-SFT / Reference-SFT / Mixed-SFT
        ↓
在 validation 上选择训练分支与 checkpoint
        ↓
选择完成后才打开 test
        ↓
在同一协议下比较 starting policy 与选中 adapter
```

## 防止 test 反向污染决策

- 不用 test 选择训练步数、学习率、LoRA 参数或 SFT 分支。
- 不根据 test 错题补训练数据后继续声称它仍是同一个独立测试集。
- 如果查看 test 后修改数据或配置，必须另建新版本的最终测试集。
- 当前尚未运行 V3 test，也没有 V3 test 指标。4B starting policy 的
  validation 基线已记录在 `docs/V3_VALIDATION_BASELINE_ZH.md`。

## 主要报告指标

1. 最终答案通过率（outcome verification）。
2. 严格任务成功率：协议合法且答案通过。
3. 协议错误数及错误类型。
4. 工具调用率、工具执行成功率和错误表达式数量。
5. 每个题族的结果，避免总分掩盖某个题族退化。

路径与参考公式只用于错误分析，不把“必须使用某个唯一公式”当成正确答案的定义。
