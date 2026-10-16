# V4 验证集冻结说明

2026-10-06，用户表示已完成 [28 道新增题审核](V4_VALIDATION_EXTENSION_AUDIT_ZH.md)，未提出修改或删除。这 28 道题与原有 36 道 V3 验证题合并，形成新的 V4 验证集。原 V3 文件保留不变。

| 来源 | 数量 | 题族 |
| --- | ---: | ---: |
| 原 V3 验证题 | 36 | 8 |
| 新增公开关系合成题 | 28 | 原有 4 个公开题族，每族加 7 题 |
| V4 验证集合计 | 64 | 8 个题族，每族 8 题 |

- 题目文件：`data/generated/v4_validation_v1.jsonl`
- SHA-256：`d62dc47ae7027de67c30521327d5f8afb6b88878ffddfe758843820da9093cf0`
- 来源、数量和哈希清单：`artifacts/dataset_manifests/v4_validation_v1.json`
- 复现命令：`$env:PYTHONPATH='src'; .venv\Scripts\python.exe scripts/freeze_v4_validation.py`

冻结程序会核对三个输入文件的哈希，确认新增题仍是审核过的版本；再检查题目 ID、题族、split 和原 V3 测试题族的隔离。若目标文件已存在且内容不同，程序会拒绝覆盖。新增题的 `review_status` 变为 `owner_approved`，仍保留 `evaluation_only=true` 和 `training_eligible=false`。

这个 64 题集合用于 V4 验证和模型选择。原 36 道 V3 验证题曾用于选择 V3 checkpoint，因此不能把合并后的 64 题写成全新、未接触过的独立测试集。V3 冻结 test 的 36 题仍单独保留，不能根据它选模型或修改训练方案。

下一阶段先在 162 道 V4 train 候选题上测 4B 起始策略的 pass@1 / pass@N 和失败类型，再从可验证的成功轨迹中构建 SFT 数据。训练后在这 64 道验证题上比较，最终独立测试要遵守冻结测试协议。
