# Phase 3 Card

**状态**: `Active`  
**日期**: `2026-03-09`  
**对象**: `P3 MSS 最小可交易风控层`  
**定位**: `当前主线第四张执行卡`  
**上游锚点**:

1. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
2. `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`
3. `blueprint/01-full-design/04-mss-lite-contract-annex-20260308.md`
4. `blueprint/01-full-design/08-mss-minimal-tradable-design-20260309.md`
5. `blueprint/01-full-design/09-mainline-system-operating-baseline-20260309.md`

---

## 1. 目标

把当前 `MSS-lite` 补到：

`最小可交易风控层`

---

## 2. 范围

当前 phase 只做：

1. `phase`
2. `phase_trend`
3. `phase_days`
4. `position_advice`
5. `risk_regime`

当前 phase 明确不做：

1. 不把 `MSS` 拉回 `Selector`
2. 不把 `MSS` 写回 `final_score`
3. 不追求完整自适应周期模型

---

## 3. 任务

### 3.1 Task P3-A MSS Phase Layer

**代码落点**

1. `src/selector/mss.py`

**测试落点**

1. `tests/unit/selector/test_mss.py`

### 3.2 Task P3-B Position Advice Layer

**代码落点**

1. `src/selector/mss.py`

**测试落点**

1. `tests/unit/selector/test_mss.py`

### 3.3 Task P3-C Risk Regime Integration

**代码落点**

1. `src/selector/mss.py`
2. `src/broker/risk.py`

**测试落点**

1. `tests/unit/broker/test_broker.py`

### 3.4 Task P3-D MSS Evidence

**脚本落点**

1. `scripts/backtest/run_v001_plus_mss_regime_sensitivity.py`

**证据落点**

1. `docs/spec/v0.01-plus/evidence/`
2. `docs/spec/v0.01-plus/records/`

---

## 4. 出场条件

- [ ] `phase / phase_trend / phase_days` 已落地
- [ ] `position_advice` 已落地
- [ ] `risk_regime` 已落地
- [ ] Broker 已稳定消费 `risk_regime`
- [ ] MSS 专项 evidence 已生成

---

## 5. 完成后必须回答的问题

1. 容量变化来自真实状态变化，还是 fallback 路径
2. `MarketScore.signal` 和 `risk_regime` 为什么不是一回事
3. 哪些天高分但必须降到 `RISK_OFF`
