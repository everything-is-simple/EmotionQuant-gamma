# Partial-Exit Lane Opening Note

**日期**: `2026-03-14`  
**阶段**: `Positioning / P5 -> P6 handoff`  
**对象**: `partial-exit lane opening boundary`  
**状态**: `Active`

---

## 1. 目标

本文用于给 `P6 / partial-exit contract freeze` 写死开工前提。

它不讨论哪种 partial-exit family 更优。

它只回答：

`P6 开工时，哪些 baseline 固定继承，哪些 sizing 结论不得偷渡进来。`

---

## 2. P6 固定继承的前提

`P6` 开工时固定继承以下前提：

1. `entry baseline = legacy_bof_baseline`
2. `no IRS`
3. `no MSS`
4. `signal_date = T / execute_date = T+1 / fill = T+1 open`
5. `当前 full-exit stop-loss + trailing-stop` 仍作为兼容基线路径

同时，`sizing baseline` 固定继承 `P5 closeout baseline`：

1. `FIXED_NOTIONAL_CONTROL = operating control baseline`
2. `SINGLE_LOT_CONTROL = floor sanity baseline`

---

## 3. P6 明确不得继承的内容

`P6` 当前明确不得继承以下内容：

1. `WILLIAMS_FIXED_RISK / FIXED_RATIO` 的 residual watch 身份
2. `FIXED_RISK / FIXED_VOLATILITY / FIXED_CAPITAL / FIXED_PERCENTAGE` 的 watch 身份
3. `FIXED_UNIT` 的 no-go 之外任何重新解释
4. `PX1 / cross-exit sensitivity` 的前提
5. 任何“先假设某个 sizing candidate 已经成立，再去替它找 partial-exit 配套”的隐含问题设置

一句话说：

`partial-exit lane 不是 sizing lane 的补救包。`

---

## 4. P6 只允许回答什么

`P6` 当前只允许回答：

1. 部分减仓需要哪些 `Order / Trade / Position / Trace` 字段
2. Broker 状态机如何从“默认全平”扩成“允许部分减仓”
3. 回测引擎、报告和 trace 的兼容边界在哪里
4. 后续 `P7` control 组该如何定义
5. full-exit 历史路径如何保持兼容

`P6` 当前不允许回答：

1. 哪种 partial-exit family 最优
2. 哪个 sizing residual watch 与哪种 partial-exit 组合最强
3. 是否应该立刻打开 `PX1`

---

## 5. P7 / P8 的预埋边界

为了避免 `P6` 写完以后再次漂移，当前先把后两张卡的起跑线写死：

1. `P7` 必须先在 `FIXED_NOTIONAL_CONTROL` 上定义 operating null control
2. `P7` 必须保留 `SINGLE_LOT_CONTROL` 作为 floor sanity line
3. `P8` 只允许在 `P7` 正式定下 control baseline 之后展开 partial-exit family replay
4. 若未来 sizing lane 重开，必须作为新治理段并行处理，不能回写改造 `P6 ~ P8` 的问题定义

---

## 6. 一句话结论

`P6` 应该从“怎么表达分批卖、怎样保持兼容”开工，而不是从“替 sizing residual watch 找搭档”开工；当前 partial-exit lane 的 sizing baseline 只认 `FIXED_NOTIONAL_CONTROL + SINGLE_LOT_CONTROL` 这对 control。
