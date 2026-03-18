# Phase 9B Evidence / duration_percentile isolated validation

**状态**: `Completed`  
**日期**: `2026-03-18`  
**对象**: `Phase 9B / isolated duration_percentile validation`

---

## 1. 本轮问题

本轮只回答一个问题：

`如果只把 duration_percentile 以 negative filter only 身份接进当前 validated baseline，结果会不会比 baseline 更好？`

---

## 2. 被测规则

本轮唯一被测 runtime 规则是：

`block when current_wave_duration_percentile >= 95`

这条规则的来源是：

1. `Phase 9A` 已正式冻结 `duration_percentile = first runtime candidate`
2. `G2` 已把 `P95` 固定为 `duration` 历史位置标签的正式分布阈值
3. 本轮明确禁止偷带 `current_wave_age_band / wave_role / reversal_state / mirror / conditioning / gene_score`

所以这轮不是：

1. `age band` 过滤
2. `duration + age` 双变量过滤
3. Gene sizing / exit modulation

而只是：

`duration_percentile >= 95 -> block entry`

---

## 3. 真实回放入口

正式 runner：

1. [`../../../scripts/backtest/run_phase9_duration_percentile_validation.py`](../../../scripts/backtest/run_phase9_duration_percentile_validation.py)

正式 JSON evidence：

1. [`../../../docs/spec/v0.01-plus/evidence/phase9b_duration_percentile_validation_legacy_duration_percentile_negative_filter_p95_w20260105_20260224_t085921__phase9_duration_validation.json`](../../../docs/spec/v0.01-plus/evidence/phase9b_duration_percentile_validation_legacy_duration_percentile_negative_filter_p95_w20260105_20260224_t085921__phase9_duration_validation.json)

正式窗口：

1. `2026-01-05` 至 `2026-02-24`
2. `full_window + front_half_window + back_half_window`

固定 baseline：

`legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`

---

## 4. Full-window 结果

### 4.1 Baseline

`PHASE9B_BASELINE_CONTROL`

1. `signals_count = 16`
2. `buy_filled_count = 13`
3. `trade_count = 13`
4. `expected_value = -0.0135471571`
5. `profit_factor = 0.7423208359`
6. `max_drawdown = 0.0198539593`
7. `reject_rate = 0.1034482759`
8. `missing_rate = 0.0000000000`

### 4.2 Candidate

`PHASE9B_DURATION_P95_NEGATIVE_FILTER`

1. `signals_count = 16`
2. `buy_filled_count = 10`
3. `trade_count = 10`
4. `expected_value = -0.0130074713`
5. `profit_factor = 1.3346090740`
6. `max_drawdown = 0.0146233485`
7. `reject_rate = 0.0476190476`
8. `missing_rate = 0.0476190476`

### 4.3 Candidate minus baseline

1. `expected_value delta = +0.0005396858`
2. `profit_factor delta = +0.5922882381`
3. `max_drawdown delta = -0.0052306108`
4. `buy_filled_count delta = -3`
5. `trade_count delta = -3`
6. `signal_count delta = 0`

---

## 5. 规则到底拦掉了什么

本轮 `duration_percentile >= 95` 的真实过滤结果是：

1. `duration_filter_total_signal_count = 16`
2. `duration_filter_blocked_signal_count = 6`
3. `duration_filter_blocked_signal_share = 37.5%`
4. `duration_filter_missing_percentile_signal_count = 0`

更关键的是，这 `6` 个被拦信号不是假动作：

1. `blocked_signals_present_in_baseline_signal_count = 6`
2. `blocked_signals_with_baseline_buy_order_count = 6`
3. `blocked_signals_with_baseline_buy_fill_count = 6`
4. `blocked_signals_share_of_baseline_buy_fills = 46.153846%`

也就是说：

`这轮规则确实直接拿掉了 baseline 里原本真的会成交的 6 个 entry。`

被拦的 6 个信号是：

1. `300502 / 2026-01-12 / bof / duration_percentile = 100`
2. `002594 / 2026-01-28 / bof / duration_percentile = 100`
3. `600436 / 2026-01-29 / bof / duration_percentile = 100`
4. `600887 / 2026-01-29 / bof / duration_percentile = 100`
5. `601668 / 2026-01-29 / bof / duration_percentile = 100`
6. `000610 / 2026-02-04 / bof / duration_percentile = 100`

---

## 6. Split-window 读法

### 6.1 Front half

`2026-01-05` 至 `2026-01-23`

1. baseline `trade_count = 0`
2. candidate `trade_count = 0`
3. candidate `blocked_signal_count = 1 / 2 = 50%`

这说明前半窗只有很弱的 entry 差异，但没有形成可闭合交易，因此：

`front_half 不能单独支撑 promotion，也不能单独否定 promotion。`

### 6.2 Back half

`2026-01-26` 至 `2026-02-24`

1. baseline `trade_count = 11`
2. candidate `trade_count = 9`
3. candidate `blocked_signal_count = 5 / 14 = 35.714286%`
4. `expected_value: -0.0134463583 -> -0.0098480277`
5. `profit_factor: 0.8484126907 -> 1.3245854617`
6. `max_drawdown: 0.0177045564 -> 0.0145670622`

真正支撑本轮 ruling 的主要增益，来自后半窗。

---

## 7. 还剩什么残留风险

本轮不是没有残留问题。

需要明确写下来的有：

1. candidate `missing_rate` 从 `0` 升到 `0.0476190476`
2. full-window failure breakdown 从 baseline 的 `MAX_POSITIONS_REACHED = 3` 变成 candidate 的 `NO_MARKET_DATA = 1`
3. 这 `1` 个 `NO_MARKET_DATA` 来自 `EXIT_300308_2026-02-11_stop_loss`

这说明：

`duration_percentile` 过滤虽然改善了主结果，但同时改写了持仓路径，也把一个原本没暴露出来的 exit 数据缺口暴露了出来。`

这条残留不应被忽略，但它不足以推翻本轮 isolated ruling。

---

## 8. Evidence verdict

本轮 evidence 支持的结论是：

`duration_percentile >= 95` 作为单变量 `negative filter only`，在正式窗口内相对 validated baseline 取得了更好的 full-window 结果。`

因此本轮 evidence 支持：

`promote_duration_percentile_negative_filter`

但它支持的是：

`进入 Phase 9 包内的下一正式步骤`

而不是：

`Gene 已经整体进入默认 runtime`
