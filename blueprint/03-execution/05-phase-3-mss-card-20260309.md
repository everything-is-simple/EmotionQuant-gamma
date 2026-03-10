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

### 2.1 执行级摘要（摘自 `08-mss-minimal-tradable-design`）

`Phase 3` 不重新发明算法正文，但执行时必须直接遵守下面 5 条冻结口径：

1. `phase_trend`
   - 正式值域：`UP / SIDEWAYS / DOWN`
   - 正常路径优先按 `8` 日趋势窗、`EMA(short=3, long=8)` 与 `slope_5d` 判定
   - 历史不足时允许进入 `cold start`，但必须把 `trend_quality = COLD_START` 写入真相源
2. `phase`
   - 正式值域：`EMERGENCE / FERMENTATION / ACCELERATION / DIVERGENCE / CLIMAX / DIFFUSION / RECESSION / UNKNOWN`
   - 高分市场优先允许直接落入 `CLIMAX`
   - `CLIMAX` 不等于风险开启，恰恰是 `RISK_OFF` 的关键来源之一
3. `phase_days`
   - 固定按交易日连续计数
   - `prev_phase == current_phase` 时递增，其余重置为 `1`
   - 不允许按自然日计数，也不允许因为缺一天历史就强行延续
4. `position_advice`
   - 只是解释层仓位区间，不直接替代正式倍率
   - 例如：`EMERGENCE=80%-100%`，`CLIMAX=20%-40%`，`RECESSION/UNKNOWN=0%-20%`
5. `risk_regime -> overlay`
   - 正式值域：`RISK_ON / RISK_NEUTRAL / RISK_OFF`
   - 映射冻结为：
     - `RISK_ON -> MSS_BULLISH_*`
     - `RISK_NEUTRAL -> MSS_NEUTRAL_*`
     - `RISK_OFF -> MSS_BEARISH_*`
   - 从本卡生效起，`Broker / Risk` 的长期正式消费面是 `risk_regime`，`MarketScore.signal` 只保留兼容语义

### 2.2 当前卡与上游正文的关系

1. `08-mss-minimal-tradable-design-20260309.md` 负责算法正文和状态机口径
2. 本卡只负责把这些口径翻译成：
   - 代码落点
   - 测试落点
   - evidence 落点
   - 出场条件
3. 若执行时发现 `08` 与本卡摘要不一致，以 `08` 为算法权威文件，本卡应先同步摘要后再开工

---

## 3. 任务

### 3.1 Task P3-A MSS Phase Layer

**代码落点**

1. `src/selector/mss.py`

**测试落点**

1. `tests/unit/selector/test_mss.py`

**至少覆盖**

1. `phase_trend = UP / SIDEWAYS / DOWN`
2. `cold start` 历史不足时的降级行为
3. `phase` 的 8 态映射，尤其是：
   - 高分直接落 `CLIMAX`
   - `DOWN + score>=60 -> DIFFUSION`
   - 判定失败 -> `UNKNOWN`

### 3.2 Task P3-B Position Advice Layer

**代码落点**

1. `src/selector/mss.py`

**测试落点**

1. `tests/unit/selector/test_mss.py`

**至少覆盖**

1. `phase -> position_advice` 的区间映射
2. `position_advice` 只落解释层，不直接进入正式倍率
3. `phase_days` 连续计数与重置逻辑

### 3.3 Task P3-C Risk Regime Integration

**代码落点**

1. `src/selector/mss.py`
2. `src/broker/risk.py`

**测试落点**

1. `tests/unit/broker/test_broker.py`

**执行约束**

1. `risk.py` 必须从“按 `signal` 选倍率”过渡到“按 `risk_regime` 选倍率”
2. `MarketScore.signal` 保留兼容字段，但不能继续充当长期正式消费面
3. 若 `risk_regime` 尚未正式落库，允许由 `phase + phase_trend + score` 现场解析
4. 不允许把 `risk_regime` 再重新等同为 `signal`

**至少覆盖**

1. `DISABLED / MISSING / NORMAL` 三条 overlay 路径
2. `CLIMAX -> RISK_OFF`
3. 高分但不进入 `RISK_ON`
4. `risk_regime` 改变后，`effective_max_positions / risk_per_trade / max_position_pct` 三者同步变化
5. `fallback` 路径不会伪装成真实状态变化

### 3.4 Task P3-D MSS Evidence

**脚本落点**

1. `scripts/backtest/run_v001_plus_mss_regime_sensitivity.py`

**证据落点**

1. `docs/spec/v0.01-plus/evidence/`
2. `docs/spec/v0.01-plus/records/`

**归属冻结**

1. `run_v001_plus_mss_regime_sensitivity.py` 的创建归属在 `Phase 3`
2. `Phase 4` 只消费该脚本和其 evidence，不再把脚本创建责任推迟到 Gate 阶段

---

## 4. 出场条件

- [ ] `phase / phase_trend / phase_days` 已落地
- [ ] `position_advice` 已落地
- [ ] `risk_regime` 已落地
- [ ] Broker 已稳定消费 `risk_regime`
- [ ] MSS 专项 evidence 已生成
- [ ] `MSS_BASELINE` 的校准适用窗口未被当前运行窗口越界，或已完成再评估 / 再标定
- [ ] `run_v001_plus_mss_regime_sensitivity.py` 已在 `Phase 3` 建立，不把脚本创建留到 `Phase 4`

---

## 5. 完成后必须回答的问题

1. 容量变化来自真实状态变化，还是 fallback 路径
2. `MarketScore.signal` 和 `risk_regime` 为什么不是一回事
3. 哪些天高分但必须降到 `RISK_OFF`
4. 哪些历史区间 `signal` 与 `risk_regime` 判断相反，相反时 Broker 的实际行为是什么
