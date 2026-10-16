# V3 SFT 数据打包说明

## 打包结果

这次只打包数据，尚未启动任何 SFT 训练。三个主包统一使用搜索环境的 custom JSON action 协议：

| 数据包 | 数量 | 工具轨迹 | 直接回答 | 用途 |
|---|---:|---:|---:|---|
| Search-SFT | 32 | 27 | 5 | 只研究搜索发现轨迹的蒸馏效果 |
| Reference-SFT | 26 | 26 | 0 | 只研究人工参考程序监督效果 |
| Mixed-SFT | 58 | 53 | 5 | 搜索轨迹与参考程序的联合训练 |

## 文件与哈希

### 搜索发现轨迹包

- `data/generated/v3_search_discovered_sft_custom_v1.jsonl`
- SHA-256：`5f4defa21c66afbc7d38e8bec02cde081e350bd64fa1d7326bcf28c174d247fb`
- 每条标记：`trajectory_source=search-discovered`、`search_discovered=true`
- 27条工具路径均重新执行 calculator，并要求回放值等于保存的 observation。
- 5条直接回答标记为 `path_type=direct-answer-on-calculator-available-task`，不能报告为工具调用监督。

32条原始选中轨迹另存为：

- `data/generated/v3_search_selected_trajectories_v1.jsonl`
- SHA-256：`76b7c192bec9cebbe8926848b363c9133f6a4b039a5e84a461d75c019b3669ee`

### 人工参考程序包

- `data/generated/v3_reference_program_sft_custom_v1.jsonl`
- SHA-256：`132bd9dc881f5b87872d40f8febd9af44cf0ce80288177011401da713bd76829`
- 每条标记：`trajectory_source=reference-program`、`search_discovered=false`
- 26条均经过安全计算器回放和 final verifier 校验。

### 混合包

- `data/generated/v3_mixed_sft_custom_v1.jsonl`
- SHA-256：`9b3a7f1484308077b071dda98c552ee8c84532a76eec31c4c1fc3d7a7cc974ea`
- 数量：58；其中53条带工具消息，5条直接回答。
- `mixture_source` 保留每条来自 `search-discovered` 还是 `reference-program`。
- 没有复制行来隐式改变采样权重。

### 总清单

- `artifacts/dataset_manifests/v3_sft_package_custom_v1.json`
- 记录全部输入与输出哈希、family分布、工具消息数量和来源计数。

## 为什么统一为 custom protocol

32条搜索轨迹来自项目自己的 JSON action 环境，例如：

```json
{"type":"tool_call","name":"calculator","arguments":{"expression":"..."}}
```

26条参考程序最初也生成过 native structured-tool 版本，但不能直接把两种协议混进同一训练文件。因此主实验把参考程序重新渲染成相同的 custom protocol。原 native 版本保留为单独消融，不进入这三个主包。

## 五条直接回答如何处理

这五条题目的 calculator 是“可用”而不是“必须调用”，模型通过直接 final 得到正确答案。因此：

- 它们属于真实搜索成功轨迹；
- 可以训练数量推理与 final 协议；
- 不能计入工具调用监督数量；
- 若实验目标改为“每题必须调用工具”，应使用27条工具子集，而不是整个32条包。

## 下一实验边界

至少比较：starting policy、Search-SFT（32条）、Reference-SFT（26条）和 Mixed-SFT（58条）。训练前还要冻结验证/测试集合、checkpoint选择规则、训练seed和配置，不能根据最终test结果反向选择训练包。
