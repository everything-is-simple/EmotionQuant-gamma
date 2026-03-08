# 跨版本对象映射总表

**状态**: `Active`  
**日期**: `2026-03-08`  
**上游来源**:

1. `G:\EmotionQuant\EmotionQuant-beta\docs`
2. `G:\EmotionQuant\EmotionQuant-beta\Governance`
3. `G:\EmotionQuant\EmotionQuant-alpha\docs`
4. `G:\EmotionQuant\EmotionQuant-alpha\Governance`
5. `G:\EmotionQuant-gamma\docs`

---

## 1. 用途

本文是 `blueprint/` 新体系的第一张源表。

它只做一件事：

`把 alpha / beta / gamma 三版中与关键对象相关的设计入口、治理入口、当前入口拉平。`

它不直接写新版正文，也不直接写实现方案。

---

## 2. 路径归一化说明

本表统一使用文件系统中的真实路径。

说明：

1. 用户口述中的 `G:\EmotionQuant\EmotionQuant-beta\Governancev`，当前实际目录名为 `G:\EmotionQuant\EmotionQuant-beta\Governance`
2. `gamma` 当前唯一执行仓库仍是 `G:\EmotionQuant-gamma`
3. `alpha / beta` 现在只作为设计资产来源，不作为当前正文落点

---

## 3. 三版总体定位

| 版本 | 设计层特点 | 治理层特点 | 当前在 blueprint 中的角色 |
|---|---|---|---|
| `beta` | 三层设计骨架最完整：`core-algorithms / core-infrastructure / enhancements`，四件套表达成熟 | `Governance` 中保留大量可复用模板、资产登记、6A 轨迹 | 主设计资产来源 |
| `alpha` | 设计结构与 `beta` 基本同源，经过多轮回看 | `Governance` 归档、cards、records 更厚，历史轨迹更完整 | 主治理资产来源 |
| `gamma` | 当前代码仓库与当前主线语义所在地；已开始收口 `DTT` 与 `design-v2` | `docs/spec/` 已形成当前状态、evidence、roadmap 结构 | 唯一当前正文与实现落点 |

---

## 4. 对象映射矩阵

### 4.1 核心主线对象

| 对象 | beta 设计来源 | beta 治理来源 | alpha 设计来源 | alpha 治理来源 | gamma 当前来源 | 归类判断 | blueprint 动作 |
|---|---|---|---|---|---|---|---|
| `Selector` | 无独立模块文；需从 `docs/system-overview.md`、`docs/module-index.md`、`docs/design/core-algorithms/{mss,irs,pas}/` 反提炼 | `Governance/archive/archive-capability-v8-20260223/CP-02-mss.md`、`CP-03-irs.md`、`CP-04-pas.md` | 同 beta，无独立 Selector 正文 | `Governance/cards/R2-mss-cards.md`、`R3-irs-pas-cards.md` | `docs/design-v2/02-modules/selector-mainline-design.md`、`selector-design.md`、`down-to-top-integration.md` | `Selector` 作为独立对象是 `gamma` 明确化后的产物；`alpha / beta` 只能提供设计原子，不能直接复用正文 | 以 `gamma` 当前主线为骨架，回收 `alpha / beta` 中关于样本收缩、入口排序、漏斗分段的设计原子 |
| `PAS-trigger / BOF` | `docs/design/core-algorithms/pas/pas-algorithm.md`、`pas-api.md`、`pas-data-models.md`、`pas-information-flow.md` | `Governance/archive/archive-capability-v8-20260223/CP-04-pas.md`、`record/reusable-assets.md` | 同 beta 四件套 | `Governance/cards/R3-irs-pas-cards.md`、`record/reusable-assets.md` | `docs/design-v2/03-algorithms/core-algorithms/pas-algorithm.md`、`strategy-design.md`、`docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-03-pas-upgrade.md` | `alpha / beta` 的 PAS 设计深度高，但属于 `PAS-full` 或更宽语义；`gamma` 当前只落 `PAS-trigger / BOF` | 复用 `alpha / beta` 的 detector 骨架、数据模型、信息流表达；丢弃超出当前主线的多形态在线语义 |
| `IRS-lite` | `docs/design/core-algorithms/irs/irs-algorithm.md`、`irs-api.md`、`irs-data-models.md`、`irs-information-flow.md` | `Governance/archive/archive-capability-v8-20260223/CP-03-irs.md`、`record/reusable-assets.md` | 同 beta 四件套 | `Governance/cards/R3-irs-pas-cards.md`、`record/reusable-assets.md` | `docs/design-v2/03-algorithms/core-algorithms/irs-algorithm.md`、`selector-design.md`、`down-to-top-integration.md`、`docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-02-irs-upgrade.md` | `alpha / beta` 的 IRS 四件套是高价值设计资产；但前置过滤语义已过时 | 复用行业口径、评分结构、data-models 与 info-flow；明确舍弃 `Top-N` 前置行业硬过滤 |
| `MSS-lite` | `docs/design/core-algorithms/mss/mss-algorithm.md`、`mss-api.md`、`mss-data-models.md`、`mss-information-flow.md` | `Governance/archive/archive-capability-v8-20260223/CP-02-mss.md`、`record/reusable-assets.md` | 同 beta 四件套 | `Governance/cards/R2-mss-cards.md`、`record/reusable-assets.md` | `docs/design-v2/03-algorithms/core-algorithms/mss-algorithm.md`、`broker-design.md`、`down-to-top-integration.md`、`docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-04-mss-upgrade.md` | `alpha / beta` 的 MSS 算法骨架很成熟；但前置 gate 语义在当前主线已降级 | 复用六因子、接口契约和信息流表达；明确改写消费位置为 `Broker / Risk` 风险覆盖 |
| `Broker / Risk` | 无独立 Broker 文；对应 `docs/design/core-infrastructure/trading/trading-algorithm.md`、`trading-api.md`、`trading-data-models.md`、`trading-information-flow.md` | `Governance/archive/archive-capability-v8-20260223/CP-07-trading.md` | 同 beta Trading 四件套 | `Governance/cards/R6-trading-cards.md` | `docs/design-v2/02-modules/broker-risk-mainline-design.md`、`broker-design.md`、`docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-01-selector-strategy.md` | `Broker / Risk` 在 `gamma` 中已被当前主线显式化；`alpha / beta` 对应对象名称更接近 `Trading` | 以 `Trading -> Broker / Risk` 做语义映射，复用执行模型、订单契约、信息流表达，不复用旧集成依赖 |

### 4.2 基础设施对象

| 对象 | beta 设计来源 | beta 治理来源 | alpha 设计来源 | alpha 治理来源 | gamma 当前来源 | 归类判断 | blueprint 动作 |
|---|---|---|---|---|---|---|---|
| `Data Layer` | `docs/design/core-infrastructure/data-layer/` 四件套 | `Governance/archive/archive-capability-v8-20260223/CP-01-data-layer.md` | 同 beta 四件套 | `Governance/cards/R1-data-layer-cards.md` | `docs/design-v2/02-modules/data-layer-design.md`、`docs/spec/v0.01/roadmap/v0.01-mvp-spec-01-data-layer.md`、`docs/spec/v0.01/records/v0.01-week1-data-layer-gap-audit-20260306.md` | `alpha / beta` 的 Data Layer 表达最完整；`gamma` 当前更偏执行收口 | 作为后续 `blueprint` 第二批收口对象，高优先回收 beta 四件套 |
| `Backtest` | `docs/design/core-infrastructure/backtest/` 四件套 + `backtest-engine-selection.md` + `backtest-test-cases.md` | `Governance/archive/archive-capability-v8-20260223/CP-06-backtest.md` | 同 beta | `Governance/cards/R5-backtest-cards.md` | `docs/design-v2/02-modules/backtest-report-design.md`、`docs/spec/v0.01/roadmap/v0.01-mvp-spec-05-backtest-report.md` | `alpha / beta` 的 Backtest 设计深度高；`gamma` 当前正文尚未拆细 | 后续单独收成 `Backtest Full Design`，先不进当前 5 个主线对象 |
| `Report / Analysis` | `docs/design/core-infrastructure/analysis/` 四件套 | `Governance/archive/archive-capability-v8-20260223/CP-09-analysis.md` | 同 beta | `Governance/cards/R7-analysis-cards.md` | `docs/design-v2/02-modules/backtest-report-design.md`、`docs/spec/v0.04/roadmap/`、`docs/spec/v0.01-mvp-spec-05-backtest-report.md`（间接） | `alpha / beta` 的 Analysis 更接近完整报告层；`gamma` 当前仍混在 backtest-report 里 | 后续拆成独立对象，先作为第二批整理对象 |

### 4.3 已明确不直接承接的旧对象

| 旧对象 | 主要来源 | 原因 | 处理方式 |
|---|---|---|---|
| `Integration` 作为独立总分层 | `alpha / beta docs/design/core-algorithms/integration/` | 当前主线已从 `Top-Down` 切换到 `DTT`，不再把 `MSS / IRS / PAS` 混成统一总分系统 | 只回收信息流表达、契约表达，不直接承接旧集成语义 |
| `Validation` 作为当前主线前置核心对象 | `alpha / beta docs/design/core-algorithms/validation/` | 当前 `v0.01-plus` 主线不以 Validation 为第一优先对象 | 暂列为后续对象，不进入当前第一批 blueprint 正文 |
| `GUI / Enhancements` | `alpha / beta core-infrastructure/gui/`、`enhancements/` | 当前不在主线收口优先级前列 | 保留为后续层，不进入当前第一轮正文 |

---

## 5. 标签归类规则

后续整理时，统一使用这 5 类标签：

| 标签 | 含义 | 本轮典型对象 |
|---|---|---|
| `历史基线` | 冻结历史口径、用于对照与回退 | `gamma system-baseline.md`、`selector-design.md` |
| `可复用设计资产` | 可提炼设计原子与表达结构 | `alpha / beta` 的四件套文档 |
| `已过时实现口径` | 设计结构可参考，但执行语义不再承接 | `Top-Down Integration`、`MSS/IRS 前置 gate` |
| `当前主线入口` | 当前 `gamma` 真正承载主线语义的文档 | `selector-mainline-design.md`、`pas/irs/mss-algorithm.md` |
| `证据 / 状态 / 治理` | 只记录实现推进与证据，不承担正文设计 | `development-status.md`、`v0.01-plus/evidence/`、`records/` |

---

## 6. 当前结论

### 6.1 可以直接确定的事

1. `beta` 是当前最强的设计资产来源，尤其在四件套结构上最完整。
2. `alpha` 是当前最强的治理资产来源，尤其在 `records / cards / reusable-assets` 的沉淀上更厚。
3. `gamma` 是唯一当前语义与当前代码落点，但其历史口径与当前口径曾经混写。
4. `Selector` 和 `Broker / Risk` 作为独立对象，是 `gamma` 才被明确拉出来的。

### 6.2 不能直接复制的事

1. 不能把 `alpha / beta` 的 `Integration` 总分语义直接搬进 `blueprint`。
2. 不能把 `MSS / IRS` 的旧前置 gate 语义直接搬进当前主线。
3. 不能把 `Governance` 中的 roadmap / cards 当当前设计正文。

---

## 7. 下一步输入

基于这张总表，下一步应继续做两件事：

1. 为 5 个关键对象分别补“设计原子缺口清单”
2. 从这 5 份稳定设计中裁出唯一 `Implementation Spec`
