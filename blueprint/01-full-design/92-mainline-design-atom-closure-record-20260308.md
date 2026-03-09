# 当前主线 5 个关键对象设计原子闭环记录

**状态**: `Active`  
**日期**: `2026-03-08`  
**范围**: `Selector / PAS Trigger / Registry / IRS-lite / MSS-lite / Broker / Risk`

---

## 1. 用途

本文只记录两件事：

1. `alpha / beta` 里哪些设计原子值得定向补回
2. 这些设计原子最终如何在 `gamma` 当前主线里闭环

它不是新版正文，也不是实现方案。

它是 `blueprint/01-full-design/` 的闭环附录，用来说明：

1. 本轮到底补回了什么
2. 本轮明确没有补回什么
3. 这些结论分别落到了哪一份正文
4. 下文中的“当前已具备”指闭环启动时的代码现实，不代表封版后的全部能力

---

## 2. 判断规则

本清单统一采用以下口径：

1. `gamma` 是当前唯一语义落点，缺口判断以 `gamma` 当前正文为准。
2. `beta` 四件套是主设计资产来源：`algorithm / api / data-models / information-flow`。
3. `alpha` 主要提供治理回看与历史复核，不单独定义新的当前语义。
4. 这里的“设计原子”主要指：
   - 输入契约
   - 输出契约
   - 数据模型
   - 分阶段信息流
   - fallback / stale / cold-start 语义
   - 时序、幂等键、追溯链
5. 旧 `Top-Down Integration`、`MSS / IRS` 前置 gate、`Validation-first` 主线语义，不在本轮回收范围内。

---

## 3. 当前批次边界

本轮 `blueprint` 第一批只收 5 个关键对象：

1. `Selector`
2. `PAS Trigger / Registry`
3. `IRS-lite`
4. `MSS-lite`
5. `Broker / Risk`

其余对象如 `Data Layer / Backtest / Report / Analysis` 先只保留入口与边界，不进入当前补原子批次。

---

## 4. 本轮闭环范围

本轮闭环前，当前 `gamma` 这 5 个对象普遍缺 5 类原子：

| 缺口类别 | 当前表现 | 为什么必须补 |
|---|---|---|
| 契约细度不足 | 只写了最小字段，没有把 required / optional / trace 字段拉平 | 后续实现会再次靠口头补语义 |
| 降级语义不足 | `fallback / stale / cold_start / baseline missing` 规则不完整 | 实现和验证会各自乱兜底 |
| 信息流分段不足 | 只给了主链路，没有给阶段边界与 stage artifact | 一到排障就重新发明流程 |
| 追溯链不足 | `sidecar / truth source / idempotency key` 还不够明确 | 很难解释排序、截断、容量变化来自哪里 |
| 时序与状态机不足 | 尤其在 `Broker / Risk` | 回测、纸交、重跑很容易口径漂移 |

---

## 5. 分对象闭环记录

### 5.1 Selector

**当前锚点**

- `docs/design-v2/02-modules/selector-design.md`

**可回收来源**

- `G:\EmotionQuant\EmotionQuant-beta\docs\system-overview.md`
- `G:\EmotionQuant\EmotionQuant-beta\docs\module-index.md`
- `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-algorithms\{mss,irs,pas}\*.md`
- `alpha` 同源设计与 cards/records 只作为回看佐证

**gamma 当前已具备**

- `Selector` 已被拉成独立对象
- 已明确只负责基础过滤、`preselect_score`、`candidate_top_n`
- 已明确不再承担 `MSS gate / IRS filter`

**已闭环的设计原子**

- 已闭环：`StockCandidate` 字段表，明确 required / optional / trace 字段
- 已闭环：基础过滤的阶段拆分：可交易性、样本卫生、规模控制、预排序
- 已闭环：`PRESELECT_SCORE_MODE` 的模式登记与不变量，不允许被实现层偷偷改义
- 已闭环：候选去留追溯字段：`candidate_reason / reject_reason / coverage_flag`
- 已闭环：缺失数据、新股、停牌、样本不足、stale 数据的降级规则
- 已闭环：`Selector sidecar` 与后续 `BOF` 样本覆盖审计的连接规则

**已冻结不回收的旧语义**

- 已闭环：`MSS` 前置 gate
- 已闭环：`IRS` 前置行业硬过滤
- 已闭环：旧 `Integration` 式最终排序职责

**已落地产物**

- `blueprint/01-full-design/01-selector-contract-annex-20260308.md`

### 5.2 PAS-trigger / BOF

**当前锚点**

- `docs/design-v2/02-modules/strategy-design.md`

**可回收来源**

- `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-algorithms\pas\pas-data-models.md`
- `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-algorithms\pas\pas-information-flow.md`
- `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-algorithms\pas\pas-api.md`

**gamma 当前已具备**

- 已把当前主线收窄到 `PAS-trigger`
- 已明确当前唯一在线形态是 `BOF`
- 已明确正式 `Signal` 与 sidecar 可分离

**已闭环的设计原子**

- 已闭环：从 `PasStockSnapshot` 裁出一份 `BOF-only` 输入快照契约
- 已闭环：正式 `Signal` 与 `bof_trace sidecar` 的字段边界
- 已闭环：历史窗口不足、量能字段缺失、stale 数据时的降级与拒绝规则
- 已闭环：`registry -> detector -> batch strategy` 的阶段信息流与责任边界
- 已闭环：`signal_id`、一股一日一形态唯一性、重跑幂等规则
- 已闭环：`reason_code / variant / selected / strength` 的追溯口径

**已冻结不回收的旧语义**

- 已闭环：`PAS-full` 的 `S/A/B/C/D` 完整机会体系
- 已闭环：`BPB / TST / PB / CPB` 多形态在线并行
- 已闭环：旧 PAS 与行业池、集成总分的强耦合

**已落地产物**

- `blueprint/01-full-design/02-pas-trigger-registry-contract-annex-20260308.md`

### 5.3 IRS-lite

**当前锚点**

- `docs/design-v2/02-modules/selector-design.md`

**可回收来源**

- `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-algorithms\irs\irs-data-models.md`
- `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-algorithms\irs\irs-information-flow.md`
- `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-algorithms\irs\irs-api.md`

**gamma 当前已具备**

- 已明确 `IRS` 只进入排序层，不做前置过滤
- 已收敛为两因子 `IRS-lite`
- 已明确 `未知行业 -> 50` 的主线 fallback

**已闭环的设计原子**

- 已闭环：从 `IrsIndustrySnapshot` 裁出当前 `IRS-lite` 输入字段表
- 已闭环：`IndustryScore` 的 required / optional / trace 字段表
- 已闭环：`sample_days / quality_flag / stale_days / min_industries` 的有效性规则
- 已闭环：行业映射版本、未知行业、缺行业、退市成分的处理规则
- 已闭环：`industry -> stock -> signal` 的附着路径与 sidecar 真相源
- 已闭环：两因子 raw 值、归一化、fallback 50 的落库与追溯口径

**已冻结不回收的旧语义**

- 已闭环：行业 `Top-N` 前置硬过滤
- 已闭环：把 `allocation_advice / rotation_mode` 作为当前主线强制输出
- 已闭环：完整六因子 `IRS-full` 直接覆盖当前 `IRS-lite`

**已落地产物**

- `blueprint/01-full-design/03-irs-lite-contract-annex-20260308.md`

### 5.4 MSS-lite

**当前锚点**

- `docs/design-v2/02-modules/broker-design.md`

**可回收来源**

- `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-algorithms\mss\mss-data-models.md`
- `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-algorithms\mss\mss-information-flow.md`
- `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-algorithms\mss\mss-api.md`

**gamma 当前已具备**

- 已明确 `MSS` 只给 `Broker / Risk` 提供风险覆盖
- 已保留六因子主骨架
- 已明确 `score / signal` 不进入个股横截面总分

**已闭环的设计原子**

- 已闭环：从 `MssMarketSnapshot` 裁出当前主线输入快照契约
- 已闭环：`MarketScore` 的字段表，以及 `score -> signal -> risk overlay` 映射字段
- 已闭环：baseline 缺失、stale、冷启动、观测缺列时的降级规则
- 已闭环：六因子 raw 值、归一化快照、解释字段的落库口径
- 已闭环：`BULLISH / NEUTRAL / BEARISH` 到 `max_positions / risk_per_trade_pct / max_position_pct` 的固定映射矩阵
- 已闭环：给执行归因用的 `risk_overlay_trace` 字段与 artifact 口径

**已冻结不回收的旧语义**

- 已闭环：`Selector` 前置 gate
- 已闭环：进入 `final_score`
- 已闭环：把完整 `cycle / trend / position_advice` 重新做成当前主线硬依赖

**已落地产物**

- `blueprint/01-full-design/04-mss-lite-contract-annex-20260308.md`

### 5.5 Broker / Risk

**当前锚点**

- `docs/design-v2/02-modules/broker-design.md`

**可回收来源**

- `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-infrastructure\trading\trading-data-models.md`
- `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-infrastructure\trading\trading-information-flow.md`
- `G:\EmotionQuant\EmotionQuant-beta\docs\design\core-infrastructure\trading\trading-api.md`

**gamma 当前已具备**

- 已明确 `Broker / Risk` 只消费正式 `Signal`
- 已明确 `MSS-lite` 只在执行层覆盖容量
- 已明确执行语义固定为 `T+1 Open`

**已闭环的设计原子**

- 已闭环：`Signal / Order / Trade / Position` 的字段表与枚举口径
- 已闭环：`signal_id / order_id / trade_id / run_id` 的幂等键与重跑规则
- 已闭环：`T 日收盘生成 -> T+1 盘前挂单 -> T+1 Open 成交` 的正式时序
- 已闭环：A 股约束：手数、涨跌停、T+1、费用、滑点、拒单原因
- 已闭环：账户状态、风险覆盖、容量截断、成交回写的责任顺序
- 已闭环：回测与纸交共用 Broker 内核时，哪些状态必须完全同口径

**已冻结不回收的旧语义**

- 已闭环：旧 `Integration -> TradeSignal` 的整套桥接包袱
- 已闭环：`MSS` 重新上移为信号构建前置 gate
- 已闭环：把 Report / GUI 依赖写回执行主链

**已落地产物**

- `blueprint/01-full-design/05-broker-risk-contract-annex-20260308.md`

---

## 6. 当前结论

这 5 个对象里，本轮真正补的不是主线方向，而是“可长期冻结的细原子”。

也就是说：

1. 大方向已经比 `alpha / beta` 更清楚
2. 契约、降级、追溯、时序四类原子已在本轮被拉平
3. 本文对应的缺口已经闭环，不再作为 live checklist 使用

---

## 7. 使用边界

`Full Design` 第一批 contract annex 与算法正文都已经落地。

本文从现在起只承担 4 个用途：

1. 作为“为什么会有 `01-08` 这套结构”的闭环记录
2. 解释哪些旧语义被明确挡在当前主线之外
3. 供来源审计或历史回看时参考
4. 不再作为 live checklist，也不参与当前主线排序
