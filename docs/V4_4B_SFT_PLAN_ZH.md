# V4 4B SFT：已批准数据与上机计划

## 现在已完成什么

用户于 2026-10-06 认可新增轨迹自检，并同意先排除一条“首步错误、后来纠正”的搜索轨迹。正式训练输入冻结为 `data/generated/v4_sft_custom_approved_v1.jsonl`，213 条；SHA-256 为 `52c6f559156f3c8655516602e0d4a97431e200539d1bbda5880c890bdef497ad`。来源：V3 已审 58 条、V4 模型搜索 114 条、助理编写的参考轨迹 41 条。后者不是模型自行搜索的结果。

脚本 `scripts/freeze_v4_sft.py` 从 213 条待审派生文件生成独立的批准版本。旧文件、原始 214 条合并包、Best-of-8 指标均不变。它检查源哈希、train-only、与 validation/test 题族隔离、V3 消息保持原样、新增轨迹的工具观察值和最终答案。来源及输出哈希见 `artifacts/dataset_manifests/v4_sft_custom_approved_v1.json`。任务/verifier/隔离属于 `A - must hand-write`；数据封装和训练配置属于 `B - must understand and modify`；命令调度属于 `C - use correctly`。

## 训练方案

使用 `Qwen/Qwen3.5-4B` **instruct 起始策略**重新做 QLoRA SFT，不从 V3 adapter 续训。这样才能把 V4 数据的训练结果与同一个起点比较；它不是 `*-Base` checkpoint。

| 用途 | 配置 | 数据 | 步数 |
| --- | --- | ---: | ---: |
| 环境冒烟 | `configs/sft_qwen3_5_4b_v4_mixed213_smoke_seed113.toml` | 抽取 4 条 | 2 微步 |
| 正式 SFT | `configs/sft_qwen3_5_4b_v4_mixed213_seed113.toml` | 全部 213 条 | 639 微步 |

正式训练为三轮完整的数据遍历，batch size 1、梯度累积 3，因此每轮 213 微步／71 次优化器更新。第 213、426 微步和最终第 639 微步各保存一个 adapter。LoRA rank 16、alpha 32、学习率 1e-4，沿用 V3 的主要设置；累积步数从 2 改为 3，是为了使 213 条的每轮恰好在一次优化器更新结束。`max_length=1536` 是长度上限，不代表每条都会填充到该长度。这个调整尚无效果证据，不能称作调优结果。

公司 GPU 上先核对数据 SHA-256、Python/Transformers/PEFT/CUDA 环境和模型文件。训练入口只从本地加载模型文件，需提供公司机器实际可读的缓存目录。先运行不加载模型权重的全量 token 编码预检，确认全部 213 条均不超过 1536 token；再运行冒烟配置，确认 4-bit 模型加载、反向传播、有限 loss、adapter 保存都成功。失败就停下排查，不能直接加步数掩盖问题。随后运行正式配置：

```bash
export PYTHONPATH=src
python -m scripts.preflight_v4_sft --config configs/sft_qwen3_5_4b_v4_mixed213_seed113.toml --cache-dir /path/to/model-cache
python -m verifiable_posttraining.cli sft-train --config configs/sft_qwen3_5_4b_v4_mixed213_smoke_seed113.toml --cache-dir /path/to/model-cache
python -m verifiable_posttraining.cli sft-train --config configs/sft_qwen3_5_4b_v4_mixed213_seed113.toml --cache-dir /path/to/model-cache
```

以上是**待执行命令，不是已完成的训练**。模型缓存、输出目录和指标路径均须确认落在有空间的公司机器磁盘上；不要提交模型权重或大 checkpoint。

## 验证与测试边界

在训练前或后，先记录相同设置下的 Qwen3.5-4B 起始策略对冻结的 V4 validation（64 题）的基线。正式训练后，只评估 epoch 1、2、3 的三个 checkpoint，按预先固定的顺序选择：严格任务成功数高者优先；并列时 verifier 通过数高者；再并列时协议错误少者；再并列时平均工具调用少者；仍并列选较早 epoch。记录每个 family 的结果，并与起始策略及 V3 winner 在相同数据上的表现区分。V4 validation 中 36 道原 V3 题此前用于模型选择，因此它不是全新的无偏 holdout。

只在选定最终 checkpoint 后，对 `data/generated/v4_test_v1.jsonl` 的 72 题做一次最终评估。V4 test 不能拿来调参、挑 epoch、重写训练样本或继续扩题。目前没有 V4 SFT、V4 validation 扩充部分或 V4 test 的模型成绩。

213 条是混合数据，不是纯 Best-of-8 蒸馏。若其表现改善，不能把全部提升归因于 114 条搜索轨迹；若以后要分离搜索与手写参考轨迹的贡献，需另做匹配消融。
