# V4 test v1：审核通过后的冻结说明

你已审核并批准 `docs/V4_TEST_EXTENSION_AUDIT_V1_ZH.md` 中新增的 36 道题，未要求继续修改。冻结程序没有改动原 V3 test 或待审核的 v0/v1 文件，而是另存为 `data/generated/v4_test_v1.jsonl`。

| 来源 | 数量 | 用途 |
| --- | ---: | --- |
| 原冻结 V3 test | 36 | 原样保留 |
| V4 自写题族扩充 | 32 | 审核通过的新合成题 |
| V4 公开母题关系衍生 | 4 | 审核通过的新合成题，不算新公开 benchmark 题 |
| **合计** | **72** | **只做最终测试** |

它们仍属于原来的八个 test-only 题族：四个自写题族各 16 道，四个公开母题关系题族各 2 道。不是 72 种独立的推理类型，同一题族里的题也并非统计独立。日后报告要分别列出题族和“原 V3／新增 V4”两组的正确率，不能只报一个总分。

冻结时检查了：输入哈希、每道新题对应且只对应一道母题、test 与 train/validation 题族不交叉、题面不重复，以及新题参考公式经安全计算器重算后与 GT 一致。这里的公式检查保证数值自洽，不等于模型已经会做；审核题意则以你的审阅为准。

- 冻结数据 SHA-256：`a0223c4517596007cf40e5cdd30e61e534f5f5dd4855af0f0042d106341be0bc`
- 完整来源和分组：`artifacts/dataset_manifests/v4_test_v1.json`
- PowerShell 可复现命令：`$env:PYTHONPATH='src'; .venv\Scripts\python.exe -m scripts.freeze_v4_test`。

**现在还没有跑 V4 test，也没有新的测试成绩。** 应先用 validation 确定最终 checkpoint 和评估规则，再对这个冻结集做一次最终测试。不要用 test 调参、挑 checkpoint、生成训练轨迹或继续改题；如果日后发现题目问题，应记录问题并另建新版本，保留这版及其历史。
