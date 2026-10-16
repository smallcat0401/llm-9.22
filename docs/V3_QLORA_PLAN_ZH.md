# V3 4B QLoRA 对照实验计划

## 目的

在相同的 Qwen3.5-4B starting policy、训练超参数和评估协议下，只改变
SFT 轨迹来源，比较：

1. Best-of-8 搜索发现的成功轨迹能否改善单次生成；
2. 人工审核的参考程序轨迹能否教授搜索完全失败的关系；
3. 两种来源混合是否优于任一单独来源。

这三次运行是小样本消融实验，不应表述为大规模能力训练。

## 三个训练分支

| 分支 | 数据 | 数量 | 三轮微步数 | epoch 1/2 checkpoint |
|---|---|---:|---:|---|
| Search-SFT | `v3_search_discovered_sft_custom_v1.jsonl` | 32 | 96 | 32、64 |
| Reference-SFT | `v3_reference_program_sft_custom_v1.jsonl` | 26 | 78 | 26、52 |
| Mixed-SFT | `v3_mixed_sft_custom_v1.jsonl` | 58 | 174 | 58、116 |

每个分支都从同一个未微调的 instruct starting policy 开始，不能让
Reference 或 Mixed 接着 Search adapter 继续训练。Mixed 中保留32条搜索轨迹与26条
参考轨迹的自然比例，不复制任何一类样本。

## 固定训练设置

- starting policy：`Qwen/Qwen3.5-4B`
- 方法：NF4 4-bit QLoRA
- seed：113
- batch size：1
- gradient accumulation：2（有效batch为2）
- learning rate：`1e-4`
- LoRA rank/alpha：16/32
- LoRA dropout：0
- 最大梯度范数：1.0
- 最大序列长度：1280
- 每个分支：完整遍历自身数据3次

长度1280来自训练前的真实tokenizer预检：Search最大931，Reference最大1065，
Mixed最大1065。旧的1024上限会拒绝一条Reference样本，因此不能继续使用。

这里采用的是“样本曝光次数匹配”：每条轨迹都学习三遍。Mixed数据更多，因此其总
优化步数和计算量也更多；最终报告必须披露这一点，不能称为严格的等计算量比较。
如果主实验出现值得追踪的差异，再增加相同optimizer-step数量的compute-matched消融。

## 配置文件

- `configs/sft_qwen3_5_4b_v3_search32_seed113.toml`
- `configs/sft_qwen3_5_4b_v3_reference26_seed113.toml`
- `configs/sft_qwen3_5_4b_v3_mixed58_seed113.toml`

正式运行时显式使用D盘模型缓存，例如：

```powershell
.venv\Scripts\python.exe -m verifiable_posttraining.cli sft-train `
  --config configs\sft_qwen3_5_4b_v3_search32_seed113.toml `
  --cache-dir D:\huggingface-cache
```

其余两个分支只替换`--config`。三组应使用同一软件环境与同类GPU，并保存环境清单。

## 本机4B兼容性实测（非正式训练）

2026-10-05在本机RTX 4060 8GB上完成了一次独立的1样本、1步QLoRA冒烟测试。
这是Tier B训练管线兼容性检查，不是模型效果实验，也不进入三个正式分支的结果比较。

- 配置：`configs/sft_qwen3_5_4b_v3_local_smoke_seed113.toml`
- 数据：Search-SFT中由seed 113确定选择的1条calculator轨迹
- 实际序列长度：625 token；监督assistant token：71
- 初始loss：`0.070946`
- 1步后的loss：`0.016092`
- 可训练参数：32,464,896
- 峰值CUDA显存：7,695.8 MiB（GPU总显存8,188 MiB）
- 训练及两次loss测量耗时：57.14秒
- adapter已成功写入D盘项目目录，指标写入
  `artifacts/metrics/qwen3_5_4b_v3_local_smoke_seed113.json`

这证明本机能够完成4B NF4模型加载、LoRA注入、assistant-only loss、反向传播、
优化器更新和adapter序列化。但只训练625-token样本时显存已接近上限，而正式数据最长
1065 token，因此不得把这次成功外推为三组正式训练可在8GB显存上稳定运行。正式三分支
仍使用更大显存的租用GPU。

## 训练前停止规则

先用少量样本做一次独立的过拟合/兼容性检查。如果出现以下任一情况，停止正式三分支
训练并修复，不通过增加训练步数掩盖问题：

- 任意样本无法通过assistant-only编码；
- LoRA注入后可训练参数为0；
- loss出现NaN或Inf；
- 小规模检查中loss没有明显下降；
- checkpoint、指标或adapter写入了C盘；
- 三个分支实际加载的starting policy或超参数不一致。

## Validation选择与Test边界

起始策略validation基线为严格成功16/36、verifier通过18/36、协议错误10/36。
训练后评估三个分支各自的epoch 1、epoch 2和epoch 3，共9个候选adapter。

选择规则预先固定为：

1. 最大化36题validation的严格任务成功数；
2. 若并列，选择verifier通过数更多者；
3. 再并列，选择协议错误更少者；
4. 再并列，选择平均工具调用更少者；
5. 仍并列时选择更早epoch；若不同分支仍并列，报告并列而不查看test破局。

只有完成上述选择并冻结唯一checkpoint后，才能第一次运行
`data/generated/v3_test_v1.jsonl`。Test不得用于修改学习率、步数、LoRA参数、
训练数据或分支选择。
