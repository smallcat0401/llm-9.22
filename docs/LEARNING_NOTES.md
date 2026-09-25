# LLM Post-training 学习笔记

这份文档是本项目的“学习主线”。它不依赖聊天记录，可以从头读到尾；聊天只用来提问、讲解和检查你的理解。

项目研究的问题是：测试时多采样能偶尔找到正确答案时，能否把这些经过验证的轨迹整理成监督数据，通过 SFT 提升单次生成能力，再通过可验证奖励的 GRPO 做进一步优化？

```text
starting policy
    -> Best-of-N search
    -> verified trajectories
    -> trajectory SFT / QLoRA
    -> GRPO / RLVR
    -> controlled evaluation
```

最重要的不是背框架 API，而是理解每个箭头两侧的数据是什么、什么条件下可以进入下一阶段，以及怎样证明结果可信。

---

## 0. 如何使用这份笔记

每次只学习一章，按以下循环进行：

1. 先读“核心解释”，建立整体认识。
2. 按“代码阅读顺序”打开源文件和测试。
3. 不看仓库，完成“手敲练习”。
4. 用自己的话回答“自测问题”。
5. 在聊天中用 `学习 03：为什么不能直接比较字符串？` 这样的格式提问。
6. 学懂后，把自己的总结写进“我的复述”。

学习等级：

- **A — 必须手写并能答辩**：核心研究逻辑，不能只会调用。
- **B — 必须读懂并能修改**：训练和实验管线，不要求背出框架代码。
- **C — 会正确使用和排错**：工程胶水，面试价值较低。

不要把“代码跑通”等同于“实验假设成立”。本项目有三种证据：

- **工程证据**：程序能运行、轨迹可回放、参数真的更新。
- **训练证据**：训练集 loss 或 reward 发生预期变化。
- **泛化证据**：未参与训练和选模的测试集指标提升。

只有第三种才能支持“模型能力提升”的结论。

### 学习进度

| 编号 | 主题 | 等级 | 建议时间 | 状态 |
|---|---|---:|---:|---|
| 01 | Task 与 Trajectory Schema | A | 2–3 小时 | 未开始 |
| 02 | Calculator 安全边界 | A | 2–3 小时 | 未开始 |
| 03 | Verifier 与数值归一化 | A | 2–3 小时 | 未开始 |
| 04 | Protocol、Environment 与 Rollout | A/B | 4–6 小时 | 未开始 |
| 05 | Dataset、family split 与数据泄漏 | A/B | 4–6 小时 | 未开始 |
| 06 | Best-of-N Search 与 pass@k | A/B | 3–4 小时 | 未开始 |
| 07 | Verified Trajectory 与 SFT 数据 | A/B | 4–6 小时 | 未开始 |
| 08 | Assistant-only Loss、LoRA 与 QLoRA | A/B | 5–8 小时 | 未开始 |
| 09 | Reward、GRPO 与受控评测 | A/B | 6–10 小时 | 未开始 |

完整理解通常需要约 35–50 小时。若还要独立重写核心组件、跑实验并解释失败案例，建议按 2–4 周安排。

---

## 1. 先看懂整个项目中的对象

```text
Task
  │ 题目、任务类型、允许工具、隐藏答案、数据划分
  ▼
Rollout / Episode
  │ 模型输出 action，环境解析并执行工具
  ▼
Trajectory
  │ ToolCall + Observation + Final Answer
  ▼
Verifier
  │ 只判断最终结果是否正确
  ▼
Search result
  │ 同一 Task 采样 N 条 Trajectory
  ▼
Verified SFT example
  │ 通过结果、协议、回放和路径质量检查
  ▼
SFT adapter
  │ 学习成功轨迹里的 assistant token
  ▼
GRPO update
  │ 同一 prompt 多次生成，按可验证 reward 做组内比较
  ▼
Frozen evaluation
    在未参与训练或选模的数据上做最终比较
```

术语约定：

- **starting policy**：训练前的指令模型。本项目使用 instruct checkpoint，不能误称为 base model。
- **trajectory**：从题目开始，到若干工具调用、工具结果和最终回答结束的完整交互记录。
- **strict success**：最终结果正确，而且输出协议和交互生命周期合法。
- **outcome success**：只看最后答案是否正确，不代表协议或工具行为合格。
- **verified trajectory**：经验证器和结构检查确认可用的轨迹，不等于人工证明每一步推理都完美。

---

## 01 — Task 与 Trajectory Schema

### 本章目标

理解项目最底层的数据合同，并能手写精简版 `Task`、`ToolCall`、`Observation`、`TrajectoryStep` 和 `Trajectory`。

### 代码阅读顺序

1. `src/verifiable_posttraining/schemas.py`
2. `tests/test_schemas.py`

### 核心解释

`Task` 描述“要解决什么”：

- `task_id`：一条任务的唯一编号。
- `family_id`：题目模板或生成家族，用于防止同模板泄漏到不同 split。
- `split`：train、validation 或 test。
- `kind`：no-tool、calculator、SQL 等任务类型。
- `prompt`：模型可见的问题。
- `ground_truth`：验证器使用的隐藏标准答案，不能泄漏到 prompt。
- `allowed_tools`：本题允许调用的工具集合。

`ToolCall` 是模型提出的调用请求；`Observation` 是环境实际执行后的结果。两者通过 `call_id` 配对。`TrajectoryStep` 把一对调用和观察绑定起来，`Trajectory` 再把所有 step 和最后答案组成完整轨迹。

主要不变量：

- ID 和 prompt 不能为空。
- `allowed_tools` 不能重复。
- no-tool 任务不能声明工具。
- 成功 observation 不能同时携带错误码；失败 observation 必须携带错误码。
- step 的 call ID 必须与 observation 的 call ID 相同。
- trajectory 内 step 下标必须是连续的 `0, 1, 2, ...`。
- 同一 trajectory 不能重复使用 call ID。

注意：schema 只保证它明确实现的结构约束。它禁止 no-tool 任务带工具，但并不在 `Task` 中穷尽检查所有“任务类型与工具”的语义关系。更强的约束会在 dataset、environment 和 SFT curation 层继续检查。不要把不存在的校验说成已经实现。

`to_dict` / `from_dict` 不只是方便存 JSON。它们让轨迹可以落盘、加载、回放和审计，是可复现性的基础。

### 手敲练习

不复制仓库，手写最小 dataclass：

1. 一个 no-tool 的 `2 + 3` 任务。
2. 一个允许 calculator 的百分比任务。
3. 一条 calculator `ToolCall` 和成功 `Observation`。
4. 两个应被拒绝的反例：call ID 不匹配、step index 不连续。

### 自测问题

1. `task_id` 与 `family_id` 的职责有什么不同？
2. ground truth 为什么要保存，却不能放进 prompt？
3. observation 为什么不能只存自由文本？
4. 为什么下标和 call ID 都需要检查？
5. 哪些约束由 schema 保证，哪些需要上层保证？

### 完成标准

能画出五个对象的关系，并为每个对象说明输入、输出、不变量、一个失败案例和一个测试。

### 我的复述

> 待填写。

---

## 02 — Calculator 安全边界

### 本章目标

理解为什么工具执行器必须把模型输出当成不可信输入，以及如何只开放需要的算术能力。

### 代码阅读顺序

1. `src/verifiable_posttraining/tools/calculator.py`
2. `tests/test_calculator.py`

### 核心解释

绝不能对模型生成的表达式直接调用 Python `eval()`。模型输出可能包含函数调用、属性访问、文件读取或任意代码。calculator 先用 AST 解析表达式，再只允许白名单节点：数字常量、`+ - * /`、一元正负号。

它拒绝名称、函数调用、属性、下标、列表、幂运算等无关语法。此外，表达式长度、AST 节点数和结果绝对值均受限。

计算使用 `Decimal`，减少二进制浮点在十进制金额和百分比上的意外误差。执行失败不会让整个进程崩溃，而是转为结构化失败 `Observation`，带稳定错误码供指标和错误分析使用。

```text
untrusted expression
    -> parse AST
    -> validate every node against allowlist
    -> bounded Decimal evaluation
    -> success/failure Observation
```

“能解析”不等于“允许执行”；解析后的递归白名单校验才是关键。

典型失败：

- `__import__('os').system(...)`：包含名称、调用和属性，必须拒绝。
- `1 / 0`：语法合法但执行失败，返回失败 observation。
- 超长表达式：可能消耗资源，在执行前拒绝。
- `10 ** 1000000`：幂运算不在能力范围，直接拒绝。
- NaN 或无穷：不能成为可信数值结果。

### 手敲练习

手写只支持 `+ - * /` 的递归 AST evaluator，加入白名单、除零处理、最大长度或节点数、统一错误类型。为正常表达式、函数调用、除零和超长输入各写一个测试。

### 自测问题

1. AST 解析本身为什么还不安全？
2. 为什么工具错误要变成 observation，而不是直接抛到主程序？
3. `Decimal` 解决了什么，又没有解决什么？
4. 语法白名单和资源限制分别防什么？

### 完成标准

能解释“最小权限工具”的设计，并能指出新增运算符时应修改的校验、执行和测试位置。

### 我的复述

> 待填写。

---

## 03 — Verifier 与数值归一化

### 本章目标

掌握“最终答案是否正确”的判定，并理解 outcome correctness 与 protocol correctness 为什么必须分开。

### 代码阅读顺序

1. `src/verifiable_posttraining/verifier.py`
2. `tests/test_verifier.py`
3. `src/verifiable_posttraining/calculator_analysis.py`
4. `tests/test_calculator_analysis.py`

### 核心解释

模型可能输出 `The answer is 1,234.5`、科学计数法或百分数。验证器先抽取并归一化数值，再与标准答案比较。

重要规则：

- 最终答案必须能抽取出**恰好一个**数值。
- 支持逗号、科学计数法和百分号等表示。
- `25%` 按 25 个百分点处理，而不是自动变成 0.25；语义由任务定义。
- 布尔值、NaN、无穷和零个/多个歧义数字被拒绝。
- 数值比较使用绝对与相对容差：

```text
allowed_error = max(abs_tolerance, relative_tolerance * abs(target))
pass iff abs(prediction - target) <= allowed_error
```

绝对容差保护接近零的答案；相对容差让大数值拥有合理的比例误差。

Verifier 只回答“结果对不对”，不应强制唯一工具路径。因此要区分：

- verifier pass：数值结果正确；
- protocol valid：输出能按规定解析；
- strict task success：结果正确且整个 rollout 合法；
- tool-assisted success：确实成功使用了工具，且结果正确。

项目曾发现 `1e-6` 容差会误杀正确保留两位小数的百分比答案，后来按任务族修正为 `0.005`。错误判分器会让训练奖励和评测结论一起失真。

### 手敲练习

写一个 `verify_numeric(prediction, target, abs_tol, rel_tol)`，覆盖整数、小数、负数、逗号、科学计数法、零/一/多个数字、大数相对容差、近零绝对容差、NaN 和 infinity。

### 自测问题

1. 为什么不能只做字符串完全相等？
2. 为什么不能随便取回答中的“最后一个数字”？
3. verifier pass 和 strict success 差在哪里？
4. 为什么容差要与答案精度一致？
5. verifier 有漏洞时，GRPO 会发生什么？

### 完成标准

能独立写出归一化和容差公式，并解释一个 false positive 和一个 false negative 的来源。

### 我的复述

> 待填写。

---

## 04 — Protocol、Environment 与 Rollout

### 本章目标

理解模型、工具环境和验证器如何组成多轮 episode，并能预测每一步状态变化。

### 代码阅读顺序

1. `src/verifiable_posttraining/model_protocol.py`
2. `tests/test_model_protocol.py`
3. `src/verifiable_posttraining/prompting.py`
4. `src/verifiable_posttraining/environment.py`
5. `tests/test_environment.py`
6. `src/verifiable_posttraining/rollout.py`
7. `tests/test_rollout.py`
8. `src/verifiable_posttraining/transformers_backend.py`

### 模型协议

自定义协议要求模型每轮输出一个 JSON action：工具调用或最终答案。解析器采用严格规则：只接受一个 JSON 对象；拒绝重复 key、非标准数值常量和额外字段；两种 action 各有精确字段集合；缺失 call ID 时生成确定性默认 ID。

严格解析是为了避免静默修复改变实验含义。若脚本偷偷从格式错误文本中猜答案，protocol error 指标就失效。

### Environment 生命周期

```text
reset(task)
  -> active episode
step(tool_call)
  -> 权限、预算、重复检查
  -> 执行工具
  -> 记录 step + observation
finish(final_answer)
  -> verifier
  -> closed episode
```

关键约束：reset 前不能 step，finish 后不能继续；只能调用允许且存在的工具；重复 call ID 和超预算调用要拒绝；rejected call 不伪装成正常 step，但进入诊断计数；episode 只能 finish 一次。

### Rollout 循环

`run_episode` 的流程是：构造不泄漏答案的 messages；policy 生成；parser 解析；tool action 交给环境并把 observation 加回上下文；final action 交给 verifier；超过最大轮数则失败。

每轮使用可复现的派生 seed。`raw_outputs` 必须保存，因为解析结构不能替代原始模型证据。如果原始输出协议错误，即使文本中碰巧有正确数字，outcome 可能通过，`task_success` 仍应为 false。

项目还实现了原生结构化工具调用。曾经因使用 document EOS 而非 chat EOS，使有效答案后的 token 覆盖解析结果，原生评测 v1 被作废。这说明 token-level 停止条件也是评测协议的一部分。

### 手敲练习

不用 Transformers，写一个 fake policy：第一轮返回 calculator call，第二轮根据 observation 返回 final。跟踪 messages、state、trajectory 和 verification，再加入非法 JSON、未授权工具、超过最大轮数三个分支。

### 自测问题

1. policy、parser、environment、tool、verifier 各自负责什么？
2. rejected call 为什么不写成成功 step，但仍要计数？
3. raw output 为什么不可省略？
4. 正确数字在 malformed JSON 中为什么不算 strict success？
5. chat EOS 配错为什么会让评测无效？

### 完成标准

能画出完整状态机，并对一串模型输出判断 termination reason、steps、protocol error 和 task success。

### 我的复述

> 待填写。

---

## 05 — Dataset、family split 与数据泄漏

### 本章目标

理解任务如何生成、为什么不能随机按行切分，以及公开数据的用途。

### 代码阅读顺序

1. `src/verifiable_posttraining/dataset.py`
2. `tests/test_dataset.py`
3. `src/verifiable_posttraining/synthetic_db.py`
4. `src/verifiable_posttraining/public_eval.py`
5. `tests/test_public_eval.py`
6. `docs/DATASETS.md`

### 核心解释

同一模板替换数字后的题目高度相似。随机按行切 train/test 会让测试集出现训练模板的换皮版本，指标虚高。因此按 `family_id` 分组切分：同一家族只能在一个 split。

```text
train families       -> search / SFT / GRPO
validation families  -> 选 checkpoint、调少量配置
test families        -> 最终比较，不能反复查看后继续调参
public benchmark     -> 外部泛化评测，绝不进入训练
```

确定性生成还要固定 seed、稳定 ID，并检查 family 覆盖。数据库任务使用合成 SQLite fixture，让内容和正确答案可重建，而不是依赖私有数据。

GSM8K 等公开数据用于防止只在自制模板上得到漂亮结果，并检验跨分布迁移。它不是 teacher model。公开数据提供题目和答案；本项目核心训练数据主要来自 starting policy 自己 Best-of-N 采样后由 verifier 筛选的成功轨迹，更接近 rejection sampling / self-improvement。

### 泄漏检查清单

- family 集合在 train/validation/test 之间两两不相交。
- task ID 唯一。
- test 题目不参与 search、SFT 或 GRPO。
- validation 只用于选模，不用于最终泛化结论。
- 外部 benchmark 标注为 evaluation-only。
- SFT task 必须来自 train split。

### 手敲练习

构造 5 个 family、每个 10 道换数字题。分别做随机按行切分和按 family 切分，检查相似模板是否跨 split。

### 自测问题

1. 固定 seed 为什么不能挽救错误的按行切分？
2. validation 和 test 有什么本质区别？
3. 公开数据为什么不能直接全部拿来训练？
4. 本项目 verified trajectory 是谁生成、谁判分的？
5. synthetic data 的优势和风险是什么？

### 完成标准

能写 family leakage 检查，并为每个数据来源说明允许和禁止用途。

### 我的复述

> 待填写。

---

## 06 — Best-of-N Search 与 pass@k

### 本章目标

理解 search gap 为什么是 trajectory SFT 的前提，以及 pass@1、pass@k、candidate yield 各说明什么。

### 代码阅读顺序

1. `src/verifiable_posttraining/search.py`
2. `tests/test_search.py`
3. `docs/FOUR_B_SEARCH_GATE.md`

### 核心解释

对同一道题用不同 seed 生成 N 条轨迹：

```text
task
  ├─ candidate 1 -> fail
  ├─ candidate 2 -> fail
  ├─ candidate 3 -> verified success  <- SFT 候选
  └─ candidate 4 -> fail
```

- `pass@1`：每题只看第一个候选时的成功率，近似单次采样基线。
- `pass@k`：前 k 个候选中至少一个成功的任务比例。
- `search gap = pass@N - pass@1`：模型是否“偶尔知道，但单次不稳定”。
- `verified candidate yield`：全部候选中的严格成功轨迹比例。

项目每题取第一条 strict success，不凭主观文本质量挑选。候选 seed 由全局 seed、task index 和 sample index 确定性派生。

如果 pass@N 与 pass@1 几乎相同，就没有足够的“偶尔正确”能力可蒸馏。应先调整任务难度、prompt、模型或数据，而非盲目 SFT。

### 本项目的真实 4B 证据

3 个来源隔离批次，共 300 个 paired-condition train tasks、2,400 个候选：

- strict pass@1：43/300 = 14.3%；
- strict pass@8：131/300 = 43.7%；
- search gap：+29.3 个百分点；
- 三批都通过预先规定的 gate。

这证明存在明显 search gap，支持构建 SFT 数据；它不证明 SFT 必然能把 pass@8 完整压缩到 pass@1。

### 常见误读

- pass@8 高不等于单次部署表现高，它使用 8 倍采样预算。
- 存在正确候选不等于部署时能在不知道答案的情况下挑出来。
- outcome pass@k 和 strict pass@k 不能混报。
- search 数据不能来自最终 test。
- 不能只汇报最成功的批次。

### 手敲练习

给 5 道题、每题 4 个布尔成功标记，手算 pass@1、pass@2、pass@4 和 yield。再写函数计算 prefix pass@k curve，分母始终用任务数。

### 自测问题

1. pass@k 的分母为什么是任务数？
2. search gap 大意味着什么、不意味着什么？
3. 为什么选择 strict success？
4. verifier 在训练期知道答案，部署期怎么办？
5. 为什么 gate 应在看结果前规定？

### 完成标准

能根据候选矩阵手算 pass@k，并判断 search 实验是否支持进入 SFT。

### 我的复述

> 待填写。

---

## 07 — Verified Trajectory 与 SFT 数据

### 本章目标

理解“搜索成功”为什么不能直接训练，以及如何转成可审计的多轮 chat supervision。

### 代码阅读顺序

1. `src/verifiable_posttraining/sft_data.py`
2. `tests/test_sft_data.py`
3. `src/verifiable_posttraining/native_sft_data.py`
4. `tests/test_native_sft_data.py`
5. `src/verifiable_posttraining/calculator_curriculum.py`

### 四层筛选

一条 SFT 轨迹至少要通过：

1. **来源检查**：只能来自 train split，task ID 不重复。
2. **结果检查**：strict success 且 verifier pass。
3. **回放一致性**：raw tool call、保存的 step 和本地重放结果一致。
4. **路径质量检查**：no-tool 题不能乱用工具；tool 题要有成功的允许调用，不能含 rejected call。

因此 `verified outcome != automatically SFT-eligible trajectory`。例如先调用不存在的工具、随后猜对答案，可能 outcome 正确，却不适合教模型。

no-tool 样例通常是 `system -> user -> assistant(final)`；calculator 样例是 `system -> user -> assistant(tool call) -> tool(observation) -> assistant(final)`。`raw_outputs` 数量必须与 step、final 对齐，转换时不能脑补更漂亮的调用。

原生工具格式还有更强不变量：存储 observation、本地重放表达式结果、隐藏 ground truth 必须一致。

### 本项目的真实数据

4B 的 2,400 个 search candidates 最终整理出 112 条冻结 SFT examples：43 条 no-tool，69 条 calculator（含真实工具消息）。少于 131 个 pass@8 成功任务，是因为 path alignment 和回放检查淘汰了不适合作监督的数据。

项目也有由参考程序构造的 calculator curriculum。它是受控消融，必须标为 reference-program supervision，不能冒充 searched trajectories。

### 手敲练习

构造 6 条候选：正确直答、错误直答、正确工具轨迹、调用失败后猜对、未授权工具后猜对、observation 被篡改。分别判断 outcome、strict、path-aligned、SFT-eligible。

### 自测问题

1. verifier pass 为什么不足以成为 SFT 数据？
2. 为什么必须回放 tool call？
3. calculator 题直接答对是否是 outcome success？是否一定适合作 tool SFT？
4. 为什么每题通常只选第一条合格轨迹？
5. reference 与 searched trajectory 的结论边界有何不同？

### 完成标准

能实现小型 curation 函数，并为每个拒绝原因给机器可读标签。

### 我的复述

> 待填写。

---

## 08 — Assistant-only Loss、LoRA 与 QLoRA

### 本章目标

理解 SFT 优化哪些 token，LoRA/QLoRA 为什么省显存，以及 training loss 能证明什么。

### 代码阅读顺序

1. `src/verifiable_posttraining/sft_training.py`
2. `tests/test_sft_training.py`
3. `configs/sft_full80_corrected_seed7.toml`
4. `configs/sft_qwen3_5_4b_verified112_seed113.toml`

### Assistant-only loss

多轮轨迹中只训练 assistant 行为：

```text
system tokens       -> -100（忽略）
user tokens         -> -100（忽略）
assistant tokens    -> token id（计算 loss）
tool-result tokens  -> -100（忽略）
assistant final     -> token id（计算 loss）
padding             -> -100（忽略）
```

项目分别渲染“此前历史 + generation prompt”和“加入当前 assistant 后的历史”，用精确前缀边界定位 assistant token。前缀不一致就报错，避免 off-by-one 误训练 user/tool token。超长样例直接拒绝，不静默截掉最终答案。

### LoRA 与 QLoRA

LoRA 令 `W' = W + BA`，其中低秩 `r` 远小于原矩阵维度。冻结原模型，只训练 A、B，减少可训练参数和优化器状态。rank 控制容量，alpha 控制缩放，target modules 决定插入层。

QLoRA 再以 4-bit 加载冻结权重。本项目使用 NF4、double quantization、bf16 计算和 gradient checkpointing。要分清：

- 4-bit：基础权重存储/加载；
- LoRA：参数高效更新；
- bf16：计算精度；
- gradient accumulation：多个 micro-batch 模拟较大 batch；
- gradient checkpointing：用额外计算换显存。

### 训练循环

固定 seed并选择数据；制作 assistant-only labels；4-bit 加载并注入 LoRA；forward/backward；到 accumulation 边界再裁剪和 optimizer step；保存 checkpoint、adapter 和 metrics；在同一训练数据上测训练前后 loss。

`max_steps` 是 micro-step 数，optimizer updates 受 accumulation 影响，checkpoint 必须与更新边界对齐。

### 训练 loss 的边界

训练 loss 下降只证明模型更会预测训练轨迹中的 assistant token，不能证明未见题准确率提升、推理变强、工具行为不退化或没有记忆。

项目曾有 selector bug：配置希望选 80 条，实际只选 41 条。loss 和评测仍是真实测量，但必须标为“41-row historical adapter”。因此日志必须保存实际 `selected_example_ids` 和类型统计，不能只信配置。

4B 的 112 条数据若训练三遍，可在 112、224、336 step 保存 epoch 1/2/3 checkpoint。应在独立 validation 上选 checkpoint，再对选中项打开 frozen test；不能用 test 挑 epoch。

### 手敲练习

1. 给 `system-user-assistant-tool-assistant` token 序列手工写 labels。
2. 计算 batch=1、accumulation=4、max_steps=40 的 optimizer update 数。
3. 写 collator：input padding 用 pad ID，label padding 用 -100。
4. 解释把 tool observation 纳入 loss 会导致什么。

### 自测问题

1. 为什么只训练 assistant token？
2. LoRA 与 QLoRA 的差别是什么？
3. rank、alpha、target modules 分别影响什么？
4. training loss 大降为什么 test 仍可能不涨？
5. 为什么保存实际选中 ID？
6. 为什么不能用 frozen test 选 checkpoint？

### 完成标准

能读懂 SFT config，预测显存/速度/更新次数方向，并能正确标注 supervised token。

### 我的复述

> 待填写。

---

## 09 — Reward、GRPO 与受控评测

### 本章目标

理解 GRPO 的组内相对学习、reward composition、reward hacking 风险，以及怎样得出诚实结论。

### 代码阅读顺序

1. `src/verifiable_posttraining/reward.py`
2. `tests/test_reward.py`
3. `src/verifiable_posttraining/grpo_training.py`
4. `tests/test_grpo_training.py`
5. `src/verifiable_posttraining/metrics.py`
6. `src/verifiable_posttraining/evaluation.py`
7. `src/verifiable_posttraining/native_tool_evaluation.py`
8. `docs/GPU_RUN_REPORT.md`

### Reward composition

本项目把 reward 拆成可审计组件：numeric outcome、numeric closeness、typed final、calculator trace、calculator result。

```text
R = w1 * outcome
  + w2 * closeness
  + w3 * format
  + w4 * tool_trace
  + w5 * tool_result
```

正确性应占主导。格式奖励只能帮助学协议，不能让“格式对、答案错”获得正确性奖励；malformed 或未经验证的 completion 不能拿 outcome reward。

若同一 group 全为 0 或全为 1，就没有相对信号。0.8B 早期 20-step run 仅 1/20 step 有非零 group reward variance，说明多数 step 几乎没有有效学习方向。closeness 可增加方差，但必须有界且权重小于最终正确性，否则模型会追求“接近”而非“正确”。

### GRPO 直觉

同一 prompt 采样 G 个 completion，简化组内优势为：

```text
A_i = (r_i - mean(r_group)) / (std(r_group) + epsilon)
```

高于组平均的输出获正优势，低于平均的获负优势。训练提高前者概率、降低后者概率，不需要单独训练 value model。若组内奖励完全相同，优势接近零，所以要记录 non-zero variance group 数。

TRL 实现还涉及重要性比率、裁剪、生成批次和截断 mask。你不必背全部内部代码，但要能解释 `num_generations`、temperature、reward weights、max completion length 和训练 prompt 来源。

### Smoke test 的证据边界

项目保存更新前的 trainable tensor，并检查训练后确实变化。这证明多响应生成、reward、反向传播、optimizer update 和 adapter 保存能运行；它不证明性能提升。参数变化只是工程验收。

### Reward hacking 与错误归因

常见问题：只学合法 JSON；输出多个数字钻 parser 漏洞；调用 calculator 却构造错误表达式；工具结果正确但 final 抄错；直接猜对却被误报为 tool-assisted。

calculator 错误应拆成：未调用、调用被拒、执行失败、表达式结果错误、工具结果正确但 final 错。只看 accuracy 无法判断应改数据、prompt、tool 还是 reward。

### Evaluation 指标与控制变量

评测保存 raw output、trajectory、verification、termination reason、协议错误和 latency，并分别报告 strict、outcome、tool-assisted、protocol error、rejected/failed calls、over-tool、平均调用数、按 kind/family 分解和 pass@k。

比较模型时固定 task IDs/顺序、prompt 版本、decoding/seed、verifier/容差、工具实现/预算和 checkpoint 规则。若修复 verifier 或 EOS bug，旧记录保留作审计，但不能与新口径直接混报。

### 本项目目前能诚实陈述的结果

- 4B search 证明明显 search gap：strict pass@1 14.3%，pass@8 43.7%。
- 4B starting-policy frozen validation 为 23/100 strict；frozen test 为 38/200 strict。它们是后续比较基线，不是 SFT 提升。
- 0.8B 已跑通 QLoRA、GRPO、原生工具调用和多套评测，出现过正向、持平和退化结果。
- corrected full80 -> native37 在内部工具任务上形成明显结构化调用能力，但 matched GSM8K calculator 持平，说明“会调用工具”不自动等于外部数学准确率。
- 13-step result-aware GRPO 改善了某个百分比任务的采样稳定性，但 GSM8K 轻微退化，只能称局部诊断，不能称广泛泛化提升。
- mixed replay step-20 在新 holdout 和 GSM8K 上只有弱且异质的正向变化，保留为消融候选，不夸大为稳定突破。

高质量项目允许负结果。价值在于预先规定假设、保存失败证据、发现 evaluator/selector bug、修复后重新界定结论，并定位下一瓶颈。

### 手敲练习

1. 给 rewards `[0, 0, 0.5, 1]`，手算均值、标准差和优势方向。
2. 设计三个 reward hacking 样例和检测测试。
3. 写 metrics aggregator，同时统计 strict、outcome、protocol、tool-assisted。
4. 为 SFT checkpoint A/B 写不查看 test 的选模规则。
5. 给“内部 25/25、外部 16/100”写一句不过度宣传的结论。

### 自测问题

1. GRPO 为什么需要同一 prompt 多次生成？
2. group reward variance 为零意味着什么？
3. format reward 为什么不能过大？
4. 参数变化为什么不等于 RL 有效？
5. strict、outcome、tool-assisted 各回答什么？
6. validation 选模后，test 应使用几次？
7. 负结果怎样仍构成有价值的项目？

### 完成标准

能从 prompt 到 reward 到参数更新讲清一轮 GRPO，并能指出实验比较中的泄漏和口径变化。

### 我的复述

> 待填写。

---

## 10. 把九章连成一个完整实验

1. 定义带隐藏答案、任务类型、工具权限和 family split 的 Task。
2. starting policy 按严格协议与安全环境交互，产生可审计 trajectory。
3. verifier 判断结果，metrics 分开记录 outcome、protocol 和 tool behavior。
4. 在 train tasks 上做 Best-of-N；有足够 search gap 才进入蒸馏。
5. 对成功候选做 train-only、回放一致性和 path alignment 筛选。
6. 转为多轮聊天数据，SFT 只监督 assistant token。
7. 用 QLoRA 降显存，记录实际样本、参数更新、checkpoint 和训练指标。
8. 用 validation 选 checkpoint，在 frozen test 上与同协议 starting policy 比较。
9. SFT 形成可用策略后，再用可验证、可分解 reward 做 GRPO。
10. GRPO 同样需要 validation/test，并报告方差、失败类别和跨分布结果。

### 一分钟项目介绍模板

> 我实现了一套可复现的 LLM post-training 流程，研究测试时 Best-of-N 找到的正确推理和工具轨迹能否被蒸馏到单次生成。系统包含安全 calculator/只读 SQL 环境、严格模型协议、数值 verifier、family-level 数据隔离、pass@k search、轨迹回放筛选、assistant-only QLoRA SFT、可验证奖励 GRPO 和统一评测。4B starting policy 在 300 个训练任务上表现出 14.3% 到 43.7% 的 strict pass@8 search gap，产生了 112 条路径对齐训练轨迹；0.8B 端到端实验验证了训练和工具流程，同时也说明工具格式能力与外部数学准确率并不等价。项目重点是可审计实验和真实错误分析，不把 loss 下降或局部结果冒充泛化提升。

使用这段话时必须随真实实验更新数字；未完成的 4B SFT/GRPO 不能说成已完成。

---

## 11. 最终自检清单

- [ ] 能画出 Task、Rollout、Trajectory、Verifier、SFT、GRPO 的关系。
- [ ] 能解释 calculator 为什么不用 `eval()`。
- [ ] 能手写数值归一化和容差比较。
- [ ] 能区分 outcome、strict、tool-assisted success。
- [ ] 能解释 family split 如何防泄漏。
- [ ] 能手算 pass@k，并解释 search gap 的边界。
- [ ] 能列出 trajectory 进入 SFT 前的四层检查。
- [ ] 能给 chat token 正确制作 assistant-only labels。
- [ ] 能解释 LoRA、4-bit、bf16、accumulation、checkpointing。
- [ ] 能讲清 GRPO 的组内优势和零方差问题。
- [ ] 能列举三种 reward hacking 及检测方法。
- [ ] 能解释 training loss、参数变化和 test 提升是三件事。
- [ ] 能设计 validation 选模与 frozen test 比较。
- [ ] 能诚实解释项目的正向、持平和负向结果。

---

## 12. 问答记录区

每学完一个问题，把结论用自己的语言写在这里。不要复制回答原文；压缩成 2–5 句话，并附对应文件或测试名。

### 01 Schema

> 待填写。

### 02 Calculator

> 待填写。

### 03 Verifier

> 待填写。

### 04 Environment / Rollout

> 待填写。

### 05 Dataset / Split

> 待填写。

### 06 Search

> 待填写。

### 07 SFT Data

> 待填写。

### 08 QLoRA SFT

> 待填写。

### 09 GRPO / Evaluation

> 待填写。
