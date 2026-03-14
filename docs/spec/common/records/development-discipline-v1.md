# EmotionQuant 开发军规 v1

**状态**: `Active`
**日期**: `2026-03-14`
**对象**: `当前仓库跨线通用的开发纪律与执行军规`
**变更规则**: `允许按正式治理裁决受控修订；不得先于上游 SoT / card / record 擅自改写。`

---

## 1. 定位

本文不是新的设计正文，也不是新的 phase card。

本文只做一件事：

`把当前仓库已经被反复验证有效的开发纪律，编成一份统一可引用的执行军规。`

这里冻结的是：

1. 每张卡开工前必须怎样拆
2. 三目录必须怎样使用
3. 已论证 / 待论证必须怎样分治
4. 候选方案必须怎样设 baseline、怎样比较、怎样出场
5. 哪些开发习惯必须永久执行，不能靠记忆维持

---

## 2. 使用规则

1. 本文只收录当前已被仓库治理与执行实践证明有效的开发纪律，不替代 `blueprint/`、`normandy/`、`positioning/` 的设计正文。
2. 若与上游 `SoT / card / formal record` 冲突，以上游已裁决文件为准，随后必须同步修订本文。
3. 本文约束的是“怎么做开发”，不是“算法应该长什么样”。
4. 任何新卡开工前，都应先复核本文，再进入对应执行卡。

---

## 3. 经验教训

1. 不先拆卡就开工，任务会把目标、边界、代码、测试、证据混成一团。
   结果通常不是快，而是返工、补口径、补 evidence、补 record。

2. 三目录一旦混用，复现性会立刻下降。
   源码仓、正式数据库、临时实验副本只要互相污染，后续任何 matrix / replay / attribution 都会失去审计价值。

3. 不把“已论证”和“待论证”切开，就会发生候选方案偷渡。
   一旦 baseline 没冻结、候选没排队，团队就无法清楚回答“为什么它是默认”“为什么另一条只是候选”。

---

## 4. 开发军规

### 4.1 卡片拆解军规

1. 每张卡开工前，必须先做细分拆分。
2. 拆分内容至少必须包含：
   - 目标
   - 冻结输入
   - 代码落点
   - 测试落点
   - evidence / artifact 落点
   - done 标准
   - 下一张卡
3. 未完成拆分，不得直接进入实现。
4. 拆分文稿必须显式区分“本卡回答什么”和“本卡不回答什么”。
5. 拆分时必须先找现有真相源，不允许跳过仓库现状直接发明新结构。

### 4.2 三目录军规

1. `G:\EmotionQuant-gamma` 只放代码、文档、配置和必要脚本。
2. `G:\EmotionQuant_data` 只放正式数据库、日志和长期数据产物。
3. `G:\EmotionQuant-temp` 只放临时文件、working DB、实验缓存、回测副本和中间 artifact。
4. 禁止把临时 DuckDB、pytest 临时目录、实验输出写回仓库目录。
5. 禁止把源码、配置、长期 SoT 文档写进 data / temp 目录。

### 4.3 论证分治军规

1. 已论证结论必须冻结到 formal record，不再与待论证候选混写。
2. 待论证事项必须排成 hypothesis / watch / queued card，不得伪装成默认路径。
3. 已判 `NO-GO` 的路线，不得在原治理段内借局部参数微调复活。
4. 研究线结论若要升格，必须先形成正式 record，再迁回主线 SoT。
5. 任何讨论都必须先说明自己在回答：
   - 已论证结论
   - 待论证假设
   - 还是二者之间的迁移条件

### 4.4 Baseline-first 军规

1. 每一种假想，至少提出两条以上方案，再固定一条 baseline / control。
2. baseline 一旦冻结，其他方案只能拿它做对照，不能与其他候选横飞互比。
3. 未建立 baseline 的问题，不允许直接宣告“最优方案”。
4. 候选方案必须回答自己相对 baseline 的：
   - 参与一致性
   - trade set 变化
   - quantity 变化
   - pnl shape 变化
   - 风险指标变化
5. baseline 没被正式打赢前，默认路径不得切换。

### 4.5 变更范围军规

1. 一张卡只回答一个主问题，不并行偷解第二个问题。
2. 本卡非目标模块不改。
3. 若改动触发了 schema / contract / execution semantics 变化，必须显式进入 strict 模式。
4. 未经 formal card 打开，不允许提前实现下一张卡的能力。
5. 不允许用“顺手一起改”把候选实验扩成系统级重写。

### 4.6 证据链军规

1. 每个结论都必须有可回放 evidence，不能只留口头总结。
2. 每次论证至少落三类产物：
   - matrix / digest 或同级 evidence
   - formal record
   - development-status 同步
3. `run_id / signal_id / order_id / position_id` 这类身份层必须可追溯，不能靠人工猜。
4. 没有 artifact 路径的结论，视为未完成。
5. 没有 test 或未说明未跑原因的实现，视为未收口。

### 4.7 兼容与退化军规

1. 新能力必须先保留旧 baseline 的 degenerate case。
2. 新语义上线前，必须写清楚哪些旧路径保持 hard compatibility。
3. 无法满足 A 股一手约束、执行约束或契约约束时，必须定义退化路径，不能留隐式行为。
4. 所有“默认不变”的部分都要显式写出来，不能只写“新增什么”。

### 4.8 状态同步军规

1. 任何卡完成一轮实现后，必须同步 `development-status.md`。
2. 若无新增债务，也要明确结论是 `debts=无变化`。
3. 若无新增可复用资产，也要明确结论是 `assets=无变化`。
4. 未完成 A6 同步，不得开始下一张卡。
5. 当前 active card 必须唯一，不允许多张主队列卡并行处于 active。

---

## 5. 当前固定执行口径

当前仓库从现在起固定执行以下口径：

1. 先拆卡，后实现。
2. 先分已论证 / 待论证，后讨论方案。
3. 先定 baseline，后比较候选。
4. 先保三目录纪律，后谈复现性。
5. 先补 evidence / record / status，后宣告完成。

---

## 6. 上游依据

1. `docs/spec/common/records/development-status.md`
2. `docs/spec/common/records/system-constitution-v1.md`
3. `docs/workflow/6A-WORKFLOW.md`
4. `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`
5. `positioning/README.md`
6. `positioning/03-execution/07-phase-p6-partial-exit-contract-freeze-card-20260314.md`
7. `positioning/03-execution/records/07-phase-p6-partial-exit-contract-freeze-record-20260314.md`

---

## 7. 一句话军规

`先拆、先分、先定尺子、再实现、再举证、再收口。`
