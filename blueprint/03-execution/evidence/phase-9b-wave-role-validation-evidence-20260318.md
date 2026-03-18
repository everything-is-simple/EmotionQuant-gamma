# Phase 9B Evidence / wave_role isolated validation

**状态**: `Completed`  
**日期**: `2026-03-18`  
**对象**: `Phase 9B / isolated wave_role validation`

---

## 1. 本轮问题

本轮只回答一个问题：

`如果只把 wave_role 以 negative filter only 身份接进当前 validated baseline，结果会不会比 baseline 更好？`

---

## 2. 被测规则

本轮正式规则只有一条：

`block when current_wave_role == COUNTERTREND`

这条规则的边界是：

1. 只测 `wave_role`
2. 只允许 `negative filter only`
3. 禁止偷带 `duration_percentile / current_wave_age_band / reversal_state / mirror / conditioning / gene_score`
4. 不允许改成 `sizing overlay` 或 `exit modulation`

---

## 3. 真实回放入口

正式 runner：

1. [`../../../scripts/backtest/run_phase9_wave_role_validation.py`](../../../scripts/backtest/run_phase9_wave_role_validation.py)

正式 JSON evidence：

1. [`../../../docs/spec/v0.01-plus/evidence/phase9b_wave_role_validation_legacy_wave_role_negative_filter_countertrend_w20260105_20260224_t151651__phase9_wave_role_validation.json`](../../../docs/spec/v0.01-plus/evidence/phase9b_wave_role_validation_legacy_wave_role_negative_filter_countertrend_w20260105_20260224_t151651__phase9_wave_role_validation.json)

正式窗口：

1. `2026-01-05` 至 `2026-02-24`
2. `full_window + front_half_window + back_half_window`

固定 baseline：

`legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`

---

## 4. Full-window 结果

### 4.1 Baseline

`PHASE9B_BASELINE_CONTROL`

1. `signals_count = 15`
2. `buy_filled_count = 13`
3. `trade_count = 13`
4. `expected_value = -0.0058474335`
5. `profit_factor = 0.8669414787`
6. `max_drawdown = 0.0163806236`
7. `reject_rate = 0.0714285714`
8. `missing_rate = 0.0000000000`

### 4.2 Candidate

`PHASE9B_WAVE_ROLE_COUNTERTREND_NEGATIVE_FILTER`

1. `signals_count = 15`
2. `buy_filled_count = 3`
3. `trade_count = 3`
4. `expected_value = -0.0115219631`
5. `profit_factor = 0.9035810907`
6. `max_drawdown = 0.0008524064`
7. `reject_rate = 0.0000000000`
8. `missing_rate = 0.0000000000`

### 4.3 Candidate minus baseline

1. `expected_value delta = -0.0056745295`
2. `profit_factor delta = +0.0366396120`
3. `max_drawdown delta = -0.0155282172`
4. `buy_filled_count delta = -10`
5. `trade_count delta = -10`
6. `signal_count delta = 0`

---

## 5. 这条规则到底拦掉了什么

`wave_role == COUNTERTREND` 的真实过滤结果是：

1. `blocked_signal_count = 12`
2. `blocked_signal_share = 80%`
3. `blocked_signals_present_in_baseline_signal_count = 12`
4. `blocked_signals_with_baseline_buy_order_count = 12`
5. `blocked_signals_with_baseline_buy_fill_count = 11`
6. `blocked_signals_with_baseline_buy_reject_count = 1`
7. `blocked_signals_share_of_baseline_buy_fills = 84.615385%`

也就是说：

`这条规则不是没有碰到 runtime，而是碰得太重，直接拿掉了 baseline 里大部分真实 entry。`

被拦信号样本包括：

1. `002475 / 2026-01-09 / bof / COUNTERTREND`
2. `300502 / 2026-01-12 / bof / COUNTERTREND`
3. `600887 / 2026-01-29 / bof / COUNTERTREND`
4. `300308 / 2026-02-04 / bof / COUNTERTREND`
5. `002384 / 2026-02-05 / bof / COUNTERTREND`

---

## 6. Split-window 读法

### 6.1 Front half

`2026-01-05` 至 `2026-01-23`

1. baseline `trade_count = 0`
2. candidate `trade_count = 0`
3. baseline `buy_filled_count = 2`
4. candidate `buy_filled_count = 0`

前半窗没有形成可闭合交易，因此不构成本轮 ruling 的主支撑。

### 6.2 Back half

`2026-01-26` 至 `2026-02-24`

1. baseline `trade_count = 11`
2. candidate `trade_count = 3`
3. baseline `buy_filled_count = 11`
4. candidate `buy_filled_count = 3`
5. baseline `expected_value = -0.0043466850`
6. candidate `expected_value = -0.0115219631`
7. baseline `profit_factor = 0.9745077451`
8. candidate `profit_factor = 0.9035810907`

真正的 ruling 主要来自后半窗：

`COUNTERTREND` 过滤确实压低了回撤，但也把太多真实交易机会一起压掉了。

---

## 7. 本轮没有暴露数据残缺，暴露的是“过度压缩”

本轮没有出现 `missing_rate` 上升，也没有新增 `NO_MARKET_DATA` 一类的数据缺口。

本轮失败的原因更直接：

1. 不是 trace gap
2. 不是数据缺口
3. 而是 `wave_role == COUNTERTREND` 作为默认 isolated negative filter 太重

它带来了：

1. 更低回撤
2. 略高 `profit_factor`
3. 但更差的 `expected_value`
4. 以及从 `13` 笔 baseline 成交直接压到 `3` 笔成交

---

## 8. Evidence verdict

本轮 evidence 支持的结论是：

`wave_role == COUNTERTREND` 虽然能真实改写 runtime，但它没有相对 validated baseline 取得干净的 full-window 改善。`

因此本轮 evidence 支持：

`retain_sidecar_only`

而不支持：

`promote_wave_role_negative_filter`
