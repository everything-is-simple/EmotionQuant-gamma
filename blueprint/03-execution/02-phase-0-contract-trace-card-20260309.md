# Phase 0 Card

**状态**: `Completed`  
**日期**: `2026-03-10`  
**对象**: `P0 契约与 Trace 收口`  
**定位**: `当前主线第一张执行卡`  
**上游锚点**:

1. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
2. `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`
3. `blueprint/01-full-design/01-selector-contract-annex-20260308.md`
4. `blueprint/01-full-design/02-pas-trigger-registry-contract-annex-20260308.md`
5. `blueprint/01-full-design/03-irs-lite-contract-annex-20260308.md`
6. `blueprint/01-full-design/04-mss-lite-contract-annex-20260308.md`
7. `blueprint/01-full-design/05-broker-risk-contract-annex-20260308.md`
8. `blueprint/01-full-design/09-mainline-system-operating-baseline-20260309.md`

---

## 1. 目标

这一 phase 只做一件事：

`先把 5 个关键对象的正式契约落点和真相源补齐。`

它的价值不是提升收益，而是让后面的收益变化可以被系统级解释。

截至 `2026-03-10`，本卡代码、测试和 docs gate 已全部收口，允许进入后续 phase。

---

## 2. 范围

当前 phase 只覆盖：

1. `Selector trace`
2. `PAS trigger / registry trace`
3. `IRS trace`
4. `MSS trace`
5. `Broker lifecycle trace`

当前 phase 明确不做：

1. 不升级 `PAS / IRS / MSS` 算法
2. 不改默认参数
3. 不跑主线收益矩阵

---

## 3. 任务

### 3.1 Task P0-A Selector Trace

**代码落点**

1. `src/selector/selector.py`
2. `src/contracts.py`
3. `src/data/store.py`

**测试落点**

1. `tests/unit/selector/test_selector_strategy.py`

**产物**

1. `selector_candidate_trace_exp`

**检查项**

- [x] `StockCandidate.score == preselect_score`
- [x] 正式候选不再混入 `reject_reason`
- [x] `candidate_top_n` 截断可解释

### 3.2 Task P0-B PAS Trigger / Registry Trace

**代码落点**

1. `src/strategy/strategy.py`
2. `src/strategy/registry.py`
3. `src/contracts.py`
4. `src/data/store.py`

**测试落点**

1. `tests/unit/strategy/test_ranker.py`
2. `tests/unit/strategy/` 下新增 PAS 相关单测

**产物**

1. `pas_trigger_trace_exp`

**检查项**

- [x] `l3_signals` 只保留 formal 最小字段
- [x] trigger reason 与 rank sidecar 不混写
- [x] `signal_id` 幂等稳定

### 3.3 Task P0-C IRS Trace

**代码落点**

1. `src/selector/irs.py`
2. `src/strategy/ranker.py`
3. `src/data/store.py`

**测试落点**

1. `tests/unit/strategy/test_ranker.py`
2. `tests/unit/selector/` 下新增 IRS 相关单测

**产物**

1. `irs_industry_trace_exp`

**检查项**

- [x] `l3_irs_daily.score` 与 signal 层 `irs_score` 明确分离
- [x] 未知行业与缺匹配行业统一 `FILL=50.0`
- [x] 每日行业层 `SKIP / FILL` 可追溯

### 3.4 Task P0-D MSS Trace

**代码落点**

1. `src/selector/mss.py`
2. `src/broker/risk.py`
3. `src/strategy/ranker.py`
4. `src/data/store.py`

**测试落点**

1. `tests/unit/selector/test_mss.py`
2. `tests/unit/broker/test_broker.py`

**产物**

1. `mss_risk_overlay_trace_exp`

**检查项**

- [x] `mss_score` 只作为 sidecar 解释位
- [x] 执行容量变化可追到 `MssRiskOverlay`
- [x] `DISABLED / MISSING / NORMAL` 可区分

### 3.5 Task P0-E Broker Lifecycle Trace

**代码落点**

1. `src/broker/broker.py`
2. `src/broker/risk.py`
3. `src/broker/matcher.py`
4. `src/data/store.py`

**测试落点**

1. `tests/unit/broker/test_broker.py`
2. `tests/integration/backtest/test_backtest_engine.py`

**产物**

1. `broker_order_lifecycle_trace_exp`

**检查项**

- [x] 风控拒绝、撮合拒绝、执行拒绝、过期四类原因可区分
- [x] `signal_id -> order_id -> trade_id` 可完整追踪
- [x] `origin` 能区分 `UPSTREAM_SIGNAL / EXIT_* / FORCE_CLOSE`

---

## 4. 出场条件

- [x] 5 个对象各自都有 trace 真相源
- [x] 关键拒绝语义已有单测
- [x] `run_id + signal_id` 可以串起全链
- [x] docs gate 通过
- [x] 不改当前默认参数

---

## 5. 完成后允许进入什么

只有本卡出场后，才允许进入：

1. `Phase 1 / PAS`
2. `Phase 2 / IRS`
3. `Phase 3 / MSS`

原因：

`没有真相源，后面的系统证据都不可信。`
