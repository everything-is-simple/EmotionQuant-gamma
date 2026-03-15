# Mainline System Operating Baseline

**状态**: `Active`  
**日期**: `2026-03-09`  
**对象**: `当前主线系统总纲`  
**定位**: `当前主线端到端运行路径与系统级印证基线`  
**上游锚点**:

1. `blueprint/01-full-design/01-selector-contract-annex-20260308.md`
2. `blueprint/01-full-design/02-pas-trigger-registry-contract-annex-20260308.md`
3. `blueprint/01-full-design/03-irs-lite-contract-annex-20260308.md`
4. `blueprint/01-full-design/04-mss-lite-contract-annex-20260308.md`
5. `blueprint/01-full-design/05-broker-risk-contract-annex-20260308.md`
6. `blueprint/01-full-design/06-pas-minimal-tradable-design-20260309.md`
7. `blueprint/01-full-design/07-irs-minimal-tradable-design-20260309.md`
8. `blueprint/01-full-design/08-mss-minimal-tradable-design-20260309.md`
9. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
10. `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`
11. `docs/spec/common/records/development-status.md`

---

## 1. 用途

本文不是模块正文，也不是实现任务单。

本文只冻结 4 件事：

1. 当前主线系统到底按什么端到端路径运行
2. 正常路径、降级路径、失败路径、回退路径分别是什么
3. 沙盘模拟最小场景矩阵应该覆盖什么
4. 哪些证据算系统设计被印证，哪些只算局部实现通过

一句话说：

`01-08` 负责把对象和算法写清楚，本文负责把“这些对象如何组成一个可印证的系统”写死。`

---

## 2. 当前冻结结论

从本文生效起，当前主线系统的端到端运行路径固定为：

```text
Selector
-> PAS
-> IRS
-> MSS
-> Broker
-> Backtest / Report
-> Gate
```

这里的关键点只有 6 条：

1. `Selector` 负责初选，不负责市场 gate、行业硬过滤和最终执行。
2. `PAS` 负责个股形态触发与形态解释层，不负责排序和仓位。
3. `IRS` 负责后置行业增强，不回到前置硬过滤。
4. `MSS` 负责市场级风险覆盖，不进入个股总分。
5. `Broker` 是唯一执行内核，回测与纸交同核，执行语义固定为 `T 日收盘生成 -> T+1 Open 成交`。
6. `Gate` 不是模块自证，而是系统级 `GO / NO-GO` 判定。

---

## 3. 系统职责边界

### 3.1 系统主链

| 环节 | 系统职责 | 正式输出 | 真相源 |
|---|---|---|---|
| `Selector` | 基础过滤、规模控制、候选初排 | `StockCandidate` | `selector_candidate_trace_exp` |
| `PAS` | 五形态检测、仲裁、formal `Signal` 生成 | `Signal` | `pas_trigger_trace_exp` |
| `IRS` | 行业层打分、唯一排名、signal attach | `IndustryScore` + signal attach | `l3_irs_daily + irs_industry_trace_exp` |
| `MSS` | 市场层打分、状态层、risk regime、overlay | `MarketScore` + overlay | `l3_mss_daily + mss_risk_overlay_trace_exp` |
| `Broker` | 风控评估、挂单、撮合、持仓、退出 | `Order / Trade` | `l4_orders + l4_trades + broker_order_lifecycle_trace_exp` |
| `Backtest / Report` | 统一时钟推进、归因、报告、环境切分 | 报告与 evidence | `scripts/backtest/* + docs/spec/*/evidence` |
| `Gate` | 统一判定是否切主线 | `GO / NO-GO` | `development-status.md` |

### 3.2 当前不属于系统主链的东西

下面这些内容可以存在，但不属于当前主线系统责任：

1. 旧 `Integration -> TradeSignal -> Trading` 桥接
2. `MSS` 前置 gate
3. `IRS` 前置硬过滤
4. GUI
5. 事件、主题、政策语义层
6. formal `Signal` 大迁移
7. 部分成交、拆单、分批执行状态机

---

## 4. 端到端运行路径

### 4.1 正常路径

```text
trade_date=T
Selector 生成 StockCandidate
-> PAS 在 T 日收盘后生成 BUY Signal
-> IRS 为 signal attach 行业增强分
-> MSS 为 Broker 提供风险覆盖
-> Broker 在 T+1 Open 撮合
-> 生成 Order / Trade
-> Backtest / Report 归因
-> Gate 汇总主线表现
```

### 4.2 正常路径的硬不变量

1. `signal_date=T`
2. `execute_date=T+1`
3. 成交价口径固定为 `T+1 open`
4. 模块间只传结果契约，不传内部中间特征
5. formal 契约保持最小稳定，解释信息优先进 trace / sidecar
6. 所有 trace / sidecar / artifact 都必须能通过 `run_id` 或 `signal_id` 回溯

### 4.3 系统运行图

```mermaid
flowchart LR
    A[Selector<br/>StockCandidate] --> B[PAS<br/>Signal]
    B --> C[IRS<br/>irs_score attach]
    C --> D[MSS<br/>risk_regime / overlay]
    D --> E[Broker<br/>Order / Trade]
    E --> F[Backtest / Report<br/>Attribution / Evidence]
    F --> G[Gate<br/>GO / NO-GO]
```

---

## 5. 四类系统路径

### 5.1 正常路径

正常路径满足下面条件：

1. `Selector` 正常产出候选
2. `PAS` 至少有一个 pattern 触发并生成 formal `Signal`
3. `IRS` 行业层与 signal attach 能完成，哪怕部分因子走 `FILL`
4. `MSS` 能产出有效 overlay 或有明确兼容路径
5. `Broker` 能进入 `PENDING -> FILLED`
6. 报告链能把成交归因回候选、形态、行业、市场和执行

### 5.2 降级路径

降级路径允许系统继续运行，但必须显式记录原因。

当前主线允许的系统级降级包括：

1. `IRS` 某层因子 `FILL=50.0`
2. `IRS` signal attach 层 `FILL=50.0`
3. `MSS` 因子层 `FILL`
4. `MSS` 状态层 `FILL`
5. overlay 走 `DISABLED / MISSING / NORMAL` 兼容路径
6. `PAS` 某个 pattern 未启用，但 registry 仍可运行

系统级降级的硬约束：

1. 降级必须可追溯
2. 降级不能伪装成正常路径
3. 降级后若继续生成交易，报告里必须能区分“正常贡献”和“降级贡献”

### 5.3 失败路径

失败路径指系统必须中断当前节点，不能把错误静默吞掉。

当前主线最小失败面包括：

1. `Selector` 没有候选或候选契约不成立
2. `PAS` 输入窗口不足且不满足最低历史要求
3. `Broker` 风控拒绝
4. `Broker` 撮合拒绝
5. `Broker` 执行前二次现金检查失败
6. 无下一交易日
7. 缺关键市场数据导致无法撮合
8. formal 契约与 sidecar 真相源不一致

失败路径的硬约束：

1. 必须有明确失败原因
2. 必须落到 trace / order lifecycle / evidence
3. 不能靠“默认值硬跑过去”伪造系统稳定

### 5.4 回退路径

回退路径不是局部 fallback，而是主线级 rollback。

当前主线只允许一种正式回退路径：

1. 回退到 `legacy_bof_baseline`

触发场景包括：

1. `P4` 后系统级证据结论仍是 `NO-GO`
2. 新主线收益结构不可解释
3. 新主线只能靠参数偶然改善
4. 任一核心模块升级后破坏 `T+1 Open`、幂等、全链追溯或报告真实性

回退路径的硬约束：

1. `legacy_bof_baseline` 必须始终可重跑
2. 回退不是删代码，而是恢复默认运行路径
3. 回退条件必须写入 `development-status.md`

---

## 6. 系统级最小场景矩阵

### 6.1 目的

沙盘模拟不是为了证明某个模块“看起来合理”，而是为了验证系统在典型路径下能否稳定运行并保留真实归因。

### 6.2 最小矩阵

当前系统级最小场景矩阵固定为 8 类：

| 场景 | 目的 | 最低关注点 |
|---|---|---|
| `S1 正常触发日` | 验证标准主链闭环 | `candidate -> signal -> order -> trade` |
| `S2 多形态竞争日` | 验证 `PAS` 仲裁 | `selected_pattern` 与 registry summary |
| `S3 行业排序改写日` | 验证 `IRS` 真正影响执行结果 | `rank_diff_days / execution_diff_days` |
| `S4 市场风险缩放日` | 验证 `MSS -> overlay -> quantity` | `risk_regime -> overlay -> quantity` |
| `S5 风控拒绝日` | 验证 Broker 失败语义 | `REJECTED reason` |
| `S6 撮合拒绝日` | 验证停牌 / 涨跌停 / 无价数据 | `Matcher` 拒绝原因 |
| `S7 降级运行日` | 验证 `FILL / MISSING / DISABLED` 路径 | 降级原因与交易后果 |
| `S8 回退判定日` | 验证主线 `GO / NO-GO` 与 rollback | `legacy` 对照仍成立 |

### 6.3 场景覆盖要求

这 8 类场景至少要覆盖下面 4 个系统问题：

1. 主链是否通
2. 降级是否真可控
3. 失败是否真可解释
4. 回退是否真可执行

---

## 7. 证据分级

### 7.1 算“印证设计”的证据

下面这些证据，才算系统设计被印证：

1. 端到端矩阵可在同一数据快照下稳定重跑
2. `run_id + signal_id + order_id + trade_id` 能串起全链
3. 正常路径、降级路径、失败路径、回退路径都已有真实样本或明确演示
4. trade attribution、windowed sensitivity、rank decomposition、regime sensitivity 能共同解释收益变化
5. `GO / NO-GO` 能明确写回状态文档，且有回退条件

### 7.2 只算“局部实现通过”的证据

下面这些只能说明局部模块通过，不能单独证明系统设计成立：

1. 单个模块单测通过
2. 单个公式输出看起来合理
3. 单个 json evidence 存在
4. 单个场景收益改善
5. 某个 sidecar 已经落表

### 7.3 系统级证据最小包

当前主线最小系统证据包固定为：

1. `matrix replay`
2. `idempotency`
3. `trade attribution`
4. `windowed sensitivity`
5. `rank decomposition`
6. `regime sensitivity`
7. `GO / NO-GO + rollback condition`

---

## 8. 当前与 Phase 4 的关系

本文不是 `Phase 4` 的替代品。

本文冻结的是：

1. `Phase 4` 到底要证明什么
2. 什么叫系统级闭环

当前 `Phase 4` 必须对齐本文完成：

1. 不是只重跑收益矩阵
2. 不是只证明 `PAS / IRS / MSS` 各自能跑
3. 而是必须证明这三者接入后，系统路径仍然可解释、可回放、可回退

---

## 9. 当前必须显式承认的现实

截至 `2026-03-09`，当前现实是：

1. 新设计已经足够承担系统级责任
2. 模块正文、实现方案、执行拆解三层关系已经成立
3. 但系统级印证还没有最终闭环
4. 当前缺的不是更多模块细节，而是一轮按本文口径出清的 `Phase 4` 证据

---

## 10. 当前实现映射与对齐要求

### 10.1 当前已落地

当前已经与本文一致的部分：

1. 主链方向已固定为 `Selector -> PAS -> IRS -> MSS -> Broker`
2. `legacy_bof_baseline` 已被明确保留为回退路径
3. `P4` 已被定义为全链回归与 `GO / NO-GO`
4. `Broker / Risk` 已明确有稳定时序、拒绝语义和生命周期追溯
5. `PAS / IRS / MSS` 三份正文都已写明失败模式与验证证据

### 10.2 当前必须对齐

从本文件生效起，后续实现与治理必须补齐：

1. 一份按本文场景矩阵组织的系统级 records / evidence
2. 一轮按本文四类路径出清的 `Phase 4` 证据
3. 一次把系统级 `GO / NO-GO` 与 rollback condition 写回状态文档的动作

### 10.3 当前不允许的回退

实现层不允许：

1. 再把系统总路径打散回模块散文
2. 用局部 evidence 冒充系统级闭环
3. 在没有 rollback condition 的情况下宣布切主线
4. 为了过 Gate 临时改默认参数掩盖系统路径问题

### 10.4 Phase 5A / Normandy absorption boundary

`Phase 5A` 生效后，主线对第二战场的吸收边界固定为：

1. 正式默认运行路径继续保持 `legacy_bof_baseline`；`BOF_CONTROL` 只保留为 Normandy 研究线 baseline 名称，不迁成主线默认标签。
2. `baseline diagnosis lane` 与 `promotion lane` 的分离升格为主线治理约束：允许先围绕稳定 baseline 做 exit diagnosis，但不允许因此提前打开 promotion lane。
3. `N2 / N2A` 产出的正式结论只支持“trailing-stop 存在局部 fat-tail truncation 风险”，不支持全局取消或重写主线 trailing-stop 语义。
4. `N1.11 / N1.12` 产出的质量分支结论只迁负面约束：在没有新的长窗稳定性 record 之前，不得把任何 `BOF` quality branch 升格为新主位。
5. `Tachibana pilot-pack` 只允许以 `existing BOF stack + thin runner + optional hook scaffold` 的形式进入主线叙述；主线当前只承认 `R4 + R5 + R6 + R7 + R10` 的 executable boundary。
6. `TRAIL_SCALE_OUT_25_75` 在主线里只能叫 `reduce_to_core engineering proxy`；`pilot-pack != full Tachibana system` 继续作为正式负面约束。
7. `CD5 / CD10`、`single_lot floor`、`noncanonical side references`、`reduced_unit_scale` 继续隔离在研究线 sidecar，不进入主线默认 aggregate。
8. `Phase 5A` 只吸收 Normandy 边界，不在这里重写 `FIXED_NOTIONAL_CONTROL / SINGLE_LOT_CONTROL / FULL_EXIT_CONTROL`；这些 control baseline 的主线吸收留给 `Phase 5B`。
9. `R2 / R3 / R8 / R9` 与所有仍受 `ALREADY_HOLDING` 阻塞的机制段继续冻结；若未来要继续，只能新开 explicit migration package 或 targeted mechanism hypothesis。

### 10.5 Phase 5B / Positioning absorption boundary

`Phase 5B` 生效后，主线对第三战场的吸收边界固定为：

1. 主线默认运行路径继续保持 `legacy_bof_baseline`；`Positioning` 结论只迁治理边界，不直接改写默认 sizing / exit 参数。
2. `FIXED_NOTIONAL_CONTROL` 进入主线的正式身份是 `current operating control baseline`，不是新的默认仓位公式。
3. `SINGLE_LOT_CONTROL` 进入主线的正式身份是 `floor sanity baseline`，不是第二 operating lane。
4. `FULL_EXIT_CONTROL` 进入主线的正式身份是 `partial-exit canonical control baseline`；在没有新 formal record 前，不得把 retained queue 误写成 canonical replacement。
5. `TRAIL_SCALE_OUT_25_75` 当前在主线里只能保留为 `partial-exit provisional leader`；若在 Tachibana 语境下被引用，也继续只能叫 `reduce_to_core engineering proxy`。
6. `TRAIL_SCALE_OUT_33_67 / TRAIL_SCALE_OUT_50_50` 继续只保留为 retained queue；`TRAIL_SCALE_OUT_67_33 / TRAIL_SCALE_OUT_75_25` 继续只保留为 watch queue。
7. `WILLIAMS_FIXED_RISK / FIXED_RATIO`、`FIXED_RISK / FIXED_VOLATILITY / FIXED_CAPITAL / FIXED_PERCENTAGE`、`FIXED_UNIT` 继续只保留为 sizing lane residual-watch / watch / no-go 身份，不迁为主线默认 sizing。
8. `partial-exit lane` 不能替 `sizing lane` 擦屁股；主线不允许把 sizing residual watch 偷渡成 partial-exit baseline。
9. `PX1` 继续保持 `locked`，`PX2` 继续保持 `conditional_only`；二者都不能因为 retained queue 已存在就自动打开。
10. `Phase 5B` 只吸收 Positioning 边界，不在这里提升任何 retained / watch 对象；统一的禁止误用层补丁留给 `Phase 5C`。

---

## 11. 冻结结语

从现在起，`blueprint` 不再只是“模块设计已经补齐”。

它还必须承担一条更重的责任：

`证明这些模块已经组成一个可运行、可解释、可降级、可失败、可回退、可被 Gate 判定的系统。`
