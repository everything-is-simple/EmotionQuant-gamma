# Design Source Register

**状态**: `Active`  
**日期**: `2026-03-09`  
**对象**: `blueprint 当前主线设计来源登记`  
**定位**: `把“从哪来、保留什么、裁掉什么、落到哪”显式登记`  
**上游锚点**:

1. `blueprint/01-full-design/01-cross-version-object-mapping-matrix-20260308.md`
2. `blueprint/01-full-design/02-mainline-design-atom-gap-checklist-20260308.md`
3. `blueprint/01-full-design/03-selector-contract-supplement-20260308.md`
4. `blueprint/01-full-design/04-pas-trigger-bof-contract-supplement-20260308.md`
5. `blueprint/01-full-design/05-irs-lite-contract-supplement-20260308.md`
6. `blueprint/01-full-design/06-mss-lite-contract-supplement-20260308.md`
7. `blueprint/01-full-design/07-broker-risk-contract-supplement-20260308.md`
8. `G:\EmotionQuant\EmotionQuant-beta\docs\design\`
9. `G:\EmotionQuant\EmotionQuant-alpha\docs\design\`

---

## 1. 用途

本文不定义算法本体。

本文只做一件事：

`把 blueprint 当前主线各对象的设计来源、回收范围、裁剪边界和目标落点做成显式登记。`

这样做的目的只有两个：

1. 防止“明明是从旧文档回收来的，却在新文里看不出来源”
2. 防止“把旧语义整包带回当前主线，却没有留下裁剪记录”

---

## 2. 来源分类规则

后续统一使用下面 4 类来源标签：

| 标签 | 含义 | 当前用法 |
|---|---|---|
| `gamma-mainline` | 当前主线已确认的现行语义 | 作为最终落点和裁剪锚 |
| `beta-design` | 最优先回收的设计结构资产 | 提供 algorithm / data-models / information-flow / api |
| `alpha-review` | 经过多轮审视的成熟算法或治理回看 | 提供边界复核和验收口径回看 |
| `history-only` | 只保留历史对照，不进入当前正文 | `Frozen`、旧 `Integration`、旧前置 gate |

---

## 3. 当前对象来源登记

### 3.1 当前 5 个关键对象

| 对象 | blueprint 当前落点 | 主来源 | 主要回收内容 | 明确裁掉内容 | 当前状态 |
|---|---|---|---|---|---|
| `Selector` | `03-selector-contract-supplement-20260308.md` | `gamma-mainline` + `beta-design` | 候选入口、过滤分段、候选追溯、contract 原子 | `MSS gate`、`IRS filter`、旧 Integration 排序 | `contract 已冻结；主正文仍缺` |
| `PAS` | `04-pas-trigger-bof-contract-supplement-20260308.md`、`08-pas-minimal-tradable-design-20260309.md` | `gamma-mainline` + `beta-design` + `alpha-review` | `YTC` 五形态、quality/reference 表达、registry / detector / pipeline 分层 | `PAS-full` 机会等级、非 `YTC` 额外形态直接上线、旧集成耦合 | `contract 已冻结；算法正文已落地` |
| `IRS` | `05-irs-lite-contract-supplement-20260308.md`、`09-irs-minimal-tradable-design-20260309.md` | `gamma-mainline` + `beta-design` + `alpha-review` | 行业快照、后置增强、五层排序框架、industry -> signal 附着 | 前置行业硬过滤、事件主题层、旧配置建议强输出 | `contract 已冻结；算法正文已落地` |
| `MSS` | `06-mss-lite-contract-supplement-20260308.md`、`10-mss-minimal-tradable-design-20260309.md` | `gamma-mainline` + `beta-design` + `alpha-review` | 六因子、市场状态层、`risk_regime`、overlay 映射 | 前置 gate、写回 `final_score`、完整自适应周期模型 | `contract 已冻结；算法正文已落地` |
| `Broker / Risk` | `07-broker-risk-contract-supplement-20260308.md` | `gamma-mainline` + `beta-design` | `Signal / Order / Trade` 边界、执行时序、生命周期 trace、A 股约束 | 旧 `Integration -> Trading` 桥接包袱 | `contract 已冻结；主正文暂不扩` |

### 3.2 本轮新增主正文的角色

| 文件 | 角色 | 不是 |
|---|---|---|
| `08-pas-minimal-tradable-design-20260309.md` | 当前主线 `PAS` 五形态算法正文 | 不是第二份 contract supplement |
| `09-irs-minimal-tradable-design-20260309.md` | 当前主线 `IRS` 算法正文 | 不是第二份 implementation spec |
| `10-mss-minimal-tradable-design-20260309.md` | 当前主线 `MSS` 算法正文 | 不是第二份 execution 文 |

---

## 4. 按来源文件登记

### 4.1 PAS

| 来源文件 | 来源标签 | 回收了什么 | 没回收什么 | 目标落点 |
|---|---|---|---|---|
| `beta ... pas-algorithm.md` | `beta-design` | 因子边界、五形态体系表达、验收粒度 | `PAS-full` 完整机会等级在线化 | `08-pas-minimal-tradable-design-20260309.md` |
| `beta ... pas-data-models.md` | `beta-design` | 输入快照和结果对象表达方式 | 全量字段直接照搬 | `04-pas-trigger-bof-contract-supplement-20260308.md` |
| `beta ... pas-information-flow.md` | `beta-design` | `registry -> detector -> output` 分段结构 | 旧集成和 GUI 出口 | `08-pas-minimal-tradable-design-20260309.md` |
| `alpha ... pas-algorithm.md` | `alpha-review` | 单指标不得独立决策的边界复核 | 完整 `PAS-full` 机会层 | `08-pas-minimal-tradable-design-20260309.md` |

### 4.2 IRS

| 来源文件 | 来源标签 | 回收了什么 | 没回收什么 | 目标落点 |
|---|---|---|---|---|
| `beta ... irs-algorithm.md` | `beta-design` | 因子分层、行业排序表达、验收粒度 | 前置行业过滤、完整配置建议 | `09-irs-minimal-tradable-design-20260309.md` |
| `beta ... irs-data-models.md` | `beta-design` | 行业快照与结果对象表达方式 | 全量字段直接照搬 | `05-irs-lite-contract-supplement-20260308.md` |
| `beta ... irs-information-flow.md` | `beta-design` | 行业层到 signal 层的信息流结构 | 旧 Integration 出口 | `09-irs-minimal-tradable-design-20260309.md` |
| `alpha ... irs-algorithm.md` | `alpha-review` | 六因子历史边界、验收口径复核 | 完整行业配置建议语义 | `09-irs-minimal-tradable-design-20260309.md` |

### 4.3 MSS

| 来源文件 | 来源标签 | 回收了什么 | 没回收什么 | 目标落点 |
|---|---|---|---|---|
| `beta ... mss-algorithm.md` | `beta-design` | 六因子骨架、市场状态表达、验收粒度 | 前置 gate、完整自适应模型 | `10-mss-minimal-tradable-design-20260309.md` |
| `beta ... mss-data-models.md` | `beta-design` | 市场快照与 overlay 对象表达方式 | 全量字段直接照搬 | `06-mss-lite-contract-supplement-20260308.md` |
| `beta ... mss-information-flow.md` | `beta-design` | `snapshot -> score -> overlay -> consumer` 分段结构 | GUI / analysis 侧出口 | `10-mss-minimal-tradable-design-20260309.md` |
| `alpha ... mss-algorithm.md` | `alpha-review` | 状态层与仓位建议的边界复核 | 旧三三制集成语义 | `10-mss-minimal-tradable-design-20260309.md` |

---

## 5. 当前冻结结论

从本文生效起，统一冻结下面 4 条：

1. `gamma` 是唯一语义落点
2. `beta` 是设计结构的主来源
3. `alpha` 是边界复核和成熟表达的辅来源
4. 旧 `Integration`、旧 `MSS / IRS` 前置 gate 只保留为历史对照，不再进入当前正文

---

## 6. 下一步

基于本文，后续只应该做三件事：

1. 把“来源文件 / 回收内容 / 裁掉内容”继续补到 `08/09/10` 的对象级正文中
2. 把 `03/04/05/06/07` 明确收口为主正文的 contract annex，而不是并列 SoT
3. 再回写 `02-implementation-spec/` 和 `03-execution/`，消除任何“下游替上游做决定”的表述
