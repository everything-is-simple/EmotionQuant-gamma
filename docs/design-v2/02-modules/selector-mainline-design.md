# Selector 桥接稿（design-v2 -> blueprint）

**版本**: `v0.01-plus 桥接稿`  
**状态**: `Active`  
**封版日期**: `不适用（Active SoT）`  
**变更规则**: `本文仅保留 design-v2 阶段的兼容桥接说明；现行设计修订必须进入 blueprint/，本文只允许导航、勘误与桥接说明更新。`  
**上游文档**: `docs/design-migration-boundary.md`, `blueprint/01-full-design/03-selector-contract-supplement-20260308.md`  
**对应模块**: `src/selector/selector.py`, `src/config.py`

---

> 桥接说明：自 `2026-03-08` 起，本文已降级为 `docs/design-v2` 兼容桥接稿。文中出现的“当前主线”表述，仅用于解释 design-v2 收口阶段的整理结果，不再构成仓库现行设计权威。现行 `Selector` 正文以 `blueprint/01-full-design/03-selector-contract-supplement-20260308.md` 为准；当前实现与执行拆解见 `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`、`blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`。

## 1. 职责

当前主线中的 `Selector` 只负责三件事：

1. 基础过滤
2. `preselect_score`
3. `candidate_top_n`

它回答的问题是：

`今天哪些股票值得进入 BOF 扫描候选池。`

它不再承担历史 `v0.01 Frozen` 中的 `MSS gate` 和 `IRS filter` 漏斗职责。

---

## 2. 输入

`Selector` 当前主线读取：

1. `L1/L2` 的股票基础信息与日线快照
2. 配置项
   - `PRESELECT_SCORE_MODE`
   - `CANDIDATE_TOP_N`
   - 基础过滤阈值
3. 交易日上下文

当前主线不读取：

1. `l3_mss_daily`
2. `l3_irs_daily`
3. `PAS` 检测结果

---

## 3. 输出契约

`Selector` 输出正式候选契约：

- `list[StockCandidate]`

最小字段应至少可支撑下游 `Strategy`：

1. `code`
2. `trade_date`
3. `preselect_score`
4. `candidate_rank`
5. `candidate_reason` 或同等可追溯字段

输出语义固定为：

`候选准备结果`

而不是：

`交易优先级结论`

---

## 4. 不负责什么

当前主线中，`Selector` 不负责：

1. `MSS` 市场级停手或控仓位
2. `IRS` 行业硬过滤
3. `BOF` 形态触发
4. `final_score` 横截面排序
5. 最终下单数量和仓位分配

这些职责分别由：

1. `PAS-trigger / BOF`
2. `IRS-lite`
3. `Broker / Risk`

承担。

---

## 5. 决策规则 / 算法

当前主线固定链路为：

```text
全市场
-> 基础过滤
-> preselect_score
-> candidate_top_n
-> StockCandidate
```

执行规则：

1. 基础过滤先做可交易性与规模收缩。
2. `preselect_score` 只用于扫描优先级与规模控制。
3. `candidate_top_n` 只用于控制 `BOF` 计算规模。
4. `preselect_score` 不能被解释为最终交易评分。
5. `MSS / IRS` 不允许回流改写候选池。

当前主线保留的关键现实约束：

1. `PRESELECT_SCORE_MODE` 会改变候选覆盖，因此必须进入证据矩阵。
2. `CANDIDATE_TOP_N` 会改变后续触发样本，因此必须作为显式主线参数管理。

---

## 6. 失败模式与验证证据

主要失败模式：

1. 候选池过窄，直接误杀后续 `BOF` 样本。
2. `preselect_score_mode` 被错误当成“只影响算力”的参数。
3. `candidate_top_n` 过大或过小，导致运行成本或收益结构失真。
4. 候选输出缺少可追溯字段，后续无法解释样本去留。

当前验证证据：

1. `docs/spec/v0.01-plus/evidence/preselect_ablation_dtt_selector_preselect_matrix_w20260105_20260224_t200058__preselect_ablation.json`
2. `docs/spec/v0.01-plus/evidence/preselect_ablation_dtt_selector_preselect_matrix_w20250901_20260224_t_long__preselect_ablation.json`
3. `docs/spec/v0.01-plus/records/v0.01-plus-preselect-ablation-20260308.md`

验证结论当前只用于：

1. 约束主线默认参数
2. 说明初选不是“纯算力参数”

不直接替代 `Selector` 的稳定设计边界。
