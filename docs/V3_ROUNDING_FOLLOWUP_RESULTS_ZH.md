# V3 单题舍入修订 Best-of-8 结果

## 为什么单独重测

`v3-public-ab005e597c33-arithmetic` 的精确结果是 `-33.829028...`，冻结 GT 是 `-33.8`，但原题没有明确要求保留一位小数。为避免把隐含标签规则写进训练数据，原题保持冻结，另建修订任务：

- 新 Task ID：`v3-public-ab005e597c33-arithmetic-rounding-revised-v1`
- 新增要求：`Round the percentage to one decimal place.`
- 数据：`data/generated/v3_rounding_followup_v1.jsonl`
- 数据 SHA-256：`9c8ade5afe670202a3853e5c73024e2f661f1d45613202ff1ed67a57ce8c0ce8`

## 实测设置与结果

- 起始策略：`Qwen/Qwen3.5-4B`
- 推理：NF4 4-bit
- 采样：Best-of-8，temperature 0.7，top-p 0.9，top-k 20
- 起始 seed：211
- pass@1：0/1
- pass@8：1/1
- 成功 candidate：1/8
- 模型加载：30.404 秒
- 搜索：18.128 秒
- CUDA 峰值：3400.2 MiB

## 成功轨迹审核

- candidate seed：911
- 工具公式：`(1441499 * 44.89 - 2049255 * 47.72) / (2049255 * 47.72) * 100`
- 工具结果：`-33.82902825746931`
- final：`-33.8`
- verifier：通过
- 语义审核：2009 总价值减 2008 总价值，再除以 2008 总价值并乘 100；符号、百分比尺度和一位小数舍入均与新题面一致。

## 数据归属结论

这条路径是起始策略真实采样得到的有效工具轨迹，因此：

- 修订任务及其成功轨迹进入 `search-discovered` 候选；
- 原始措辞不清的 task 不进入训练；
- 原先为该题生成的人工参考程序不进入 reference-program v2；
- 总候选保持 58 条，但来源边界更新为 Search-SFT 32 条、Reference-SFT 26 条。

原始运行文件保存在：
`outputs/search/qwen3_5_4b_v3_rounding_followup_best_of_8_v1/`。
