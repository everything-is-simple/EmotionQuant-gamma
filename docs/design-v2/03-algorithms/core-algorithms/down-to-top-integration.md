# Down-to-Top 主线替代设计（v0.01-plus）

**版本**: `v0.01-plus 主线替代版`  
**状态**: `Active`  
**封版日期**: `不适用（Active SoT）`  
**变更规则**: `作为 v0.01-plus 当前主开发线设计入口，允许在 Gate、证据与实现反馈下受控修订；涉及 v0.01 Frozen 历史口径时，以上游 baseline 为准。`  
**上游文档**: `docs/design-v2/01-system/system-baseline.md`, `docs/design-v2/02-modules/selector-design.md`, `docs/design-v2/02-modules/strategy-design.md`, `docs/design-v2/03-algorithms/core-algorithms/pas-algorithm.md`  
**治理入口**: `docs/spec/v0.01-plus/README.md`  
**创建日期**: `2026-03-07`  
**最后更新**: `2026-03-08`

---

## 1. 定位

本文是 `v0.01-plus` 当前主开发线的集成设计骨架。

它只负责定义当前主线的总装关系，不替代 5 份稳定设计文档：

1. `docs/design-v2/02-modules/selector-mainline-design.md`
2. `docs/design-v2/03-algorithms/core-algorithms/pas-algorithm.md`
3. `docs/design-v2/03-algorithms/core-algorithms/irs-algorithm.md`
4. `docs/design-v2/03-algorithms/core-algorithms/mss-algorithm.md`
5. `docs/design-v2/02-modules/broker-risk-mainline-design.md`

它不再复述旧版 top-down 漏斗，也不再把 `MSS / IRS / PAS` 混成一个总分系统。

本文只回答：

1. 当前主线的唯一链路是什么。
2. `Selector / PAS / IRS / MSS / Broker` 各自处于哪一段。
3. formal schema 与 sidecar 真相源如何共存。
4. 当前哪些地方已经落地，哪些地方仍需继续升级。

当前主线唯一口径：

`Selector 初选 -> BOF 触发 -> IRS 排序 -> MSS 控仓位 -> Broker 执行 -> Report`

---

## 2. 设计目标

### 2.1 解决的问题

`v0.01 Frozen` 的 top-down 链路存在三个主要问题：

1. `MSS/IRS` 前置过滤会提前误杀 BOF 触发样本。
2. 候选过滤、排序增强、执行风控混在一起，证据不可解释。
3. 当收益变化时，无法判断是删样本、换排序还是改仓位导致。

### 2.2 当前主线的改法

`v0.01-plus` 当前主线把三件事彻底拆开：

1. `Selector` 只负责基础过滤与规模控制。
2. `Strategy / PAS + IRS` 只负责触发和横截面排序。
3. `Broker / Risk + MSS` 只负责市场级风险预算与执行容量。

---

## 3. 子算法角色分工

### 3.1 Selector

职责：

- 基础过滤
- `preselect_score`
- `candidate_top_n`

不负责：

- `MSS gate`
- `IRS filter`
- 最终交易排序

### 3.2 PAS

职责：

- 在候选池上执行 `BOF` 检测
- 生成最小 formal `Signal`
- 提供 `bof_strength` 作为排序解释基础

不负责：

- 行业评分
- 市场风险控制
- 最终下单截断

### 3.3 IRS

职责：

- 在 BOF 触发后提供行业横截面增强分
- 参与 `final_score`
- 解释“同日谁更强”

当前限制：

- 当前仍是 `IRS-lite`
- 轮动状态、牛股基因、相对量能体系仍在后续升级范围内

### 3.4 MSS

职责：

- 读取市场级快照
- 生成 `score + signal`
- 在 `Broker / Risk` 层动态调节风险预算

不负责：

- 候选池删样本
- 排序层总分

### 3.5 Broker / Risk

职责：

- 读取排序结果
- 读取 `l3_mss_daily`
- 动态调整：
  - `max_positions`
  - `risk_per_trade_pct`
  - `max_position_pct`
- 决定最终可执行订单集合

---

## 4. 集成层分段结构

### 4.1 阶段 A：候选准备

```text
全市场
-> 硬过滤
-> preselect_score
-> candidate_top_n
```

输入：

- `L1/L2` 股票基础与行情

输出：

- `list[StockCandidate]`

### 4.2 阶段 B：形态触发

```text
list[StockCandidate]
-> 批量加载历史窗口
-> BOF detect
-> minimal formal Signal
```

输入：

- `StockCandidate`
- `l2_stock_adj_daily`

输出：

- formal `Signal`
- 运行时 `bof_strength`

### 4.3 阶段 C：排序增强

```text
Signal
-> attach IRS
-> final_score
-> final_rank
-> l3_signal_rank_exp
```

输入：

- `Signal`
- `l3_irs_daily`

输出：

- `l3_signal_rank_exp`
- 入选 formal `Signal`

### 4.4 阶段 D：执行风控

```text
ranked signals
-> attach MSS risk overlay
-> capacity decision
-> Order / Trade
```

输入：

- 入选 formal `Signal`
- `l3_mss_daily`
- 当前账户状态

输出：

- `Order`
- `Trade`
- `RiskDecision`

---

## 5. 正式契约与 sidecar

### 5.1 formal schema

当前主线仍保持 `v0.01` 兼容 formal 契约：

- `l3_signals`
- `Order`
- `Trade`

目的：

- 控制切换面
- 不把链路替代和全量 schema 迁移绑死在一起

### 5.2 sidecar 真相源

当前排序解释与实验真相源统一写入：

- `_tmp_dtt_rank_stage`
- `l3_signal_rank_exp`

关键字段：

- `run_id`
- `signal_id`
- `variant`
- `bof_strength`
- `irs_score`
- `mss_score`
- `final_score`
- `final_rank`
- `selected`

### 5.3 当前原则

- formal schema 保兼容
- sidecar 保解释力
- 等主线稳定后，再决定是否升级正式 `Signal` 契约

---

## 6. 配置层语义

### 6.1 当前核心配置

```python
PIPELINE_MODE = "dtt"
DTT_VARIANT = "v0_01_dtt_bof_plus_irs_score"
MSS_RISK_OVERLAY_VARIANT = "v0_01_dtt_bof_plus_irs_mss_score"
PRESELECT_SCORE_MODE = "amount_plus_volume_ratio"
```

### 6.2 变体解释

| variant | 排序层 | 风控层 | 用途 |
|---|---|---|---|
| `legacy_bof_baseline` | BOF only | 固定 | 历史对照 |
| `v0_01_dtt_bof_only` | BOF only | 固定 | 触发保真 |
| `v0_01_dtt_bof_plus_irs_score` | BOF + IRS | 固定 | 当前排序主线 |
| `v0_01_dtt_bof_plus_irs_mss_score` | BOF + IRS | MSS overlay | 当前完整主线候选 |

---

## 7. 当前 companion docs 对照

| 领域 | 算法 | 数据模型 | 接口 | 信息流 |
|---|---|---|---|---|
| MSS | `mss-algorithm.md` | `mss-data-models.md` | `mss-api.md` | `mss-information-flow.md` |
| IRS | `irs-algorithm.md` | `irs-data-models.md` | `irs-api.md` | `irs-information-flow.md` |
| PAS | `pas-algorithm.md` | `pas-data-models.md` | `pas-api.md` | `pas-information-flow.md` |

本文不替代这些子文档，只负责定义它们如何被串起来。

---

## 8. 当前已知限制

### 8.1 IRS 仍然不完整

当前 `IRS` 只是 `IRS-lite`：

- 有后置排序能力
- 但没有完整的行业轮动状态层
- 没有行业内部结构层
- 没有牛股基因层
- 没有相对量能体系

### 8.2 PAS 仍是单形态

当前在线 detector 只有：

- `bof`

`BPB / TST / PB / CPB` 仍未接入。

### 8.3 MSS 仍需更长窗口证据

当前 `MSS` 已进入 `Broker / Risk`，但还需要更长窗口确认：

- 是否稳定改善 `MDD`
- 是否稳定改善收益结构
- 哪组倍率最合适

---

## 9. 当前证据关注点

当前主线应持续回答三个问题：

1. `BOF` 是否被前置环节误杀。
2. `IRS` 是否真正把更好的信号排到前面。
3. `MSS` 是否真正改善执行层风险暴露，而不是重新变相删样本。

因此当前证据矩阵要按三层拆开：

- 触发保真
- 排序增益
- 风险覆盖

---

## 10. 下一步演进骨架

### 10.1 算法层

1. `IRS-lite -> IRS-upgrade`
2. `BOF only -> BOF + BPB`
3. `MSS risk overlay -> calibrated overlay`

### 10.2 集成层

1. 保持 `Selector / PAS / IRS / MSS / Broker` 五段分层不回退
2. 保持 sidecar 真相源
3. 再决定是否升级 formal `Signal`

---

## 11. 权威结论

当前 `v0.01-plus` 的集成设计骨架只有一句话：

`Selector 负责谁进入计算，PAS 负责是否触发，IRS 负责同日谁更强，MSS 负责今天能开多大风险预算，Broker 负责真正下单。`

只要这句话不变，当前主线就不会再退回旧的一团混合逻辑。

---

## 12. 相关文档

- `mss-algorithm.md`
- `mss-data-models.md`
- `mss-api.md`
- `mss-information-flow.md`
- `irs-algorithm.md`
- `irs-data-models.md`
- `irs-api.md`
- `irs-information-flow.md`
- `pas-algorithm.md`
- `pas-data-models.md`
- `pas-api.md`
- `pas-information-flow.md`
