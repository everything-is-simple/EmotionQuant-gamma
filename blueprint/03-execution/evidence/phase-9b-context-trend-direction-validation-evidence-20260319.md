# Phase 9B Evidence / context_trend_direction_before isolated validation

**状态**: `Completed`  
**日期**: `2026-03-19`  
**对象**: `Phase 9B / isolated context_trend_direction_before validation`

---

## 1. 本轮问题

本轮只回答一个问题：

`如果只把 context_trend_direction_before 以 parent-context negative guard 身份接进当前 validated baseline，结果会不会比 baseline 更好？`

---

## 2. 被测规则

本轮正式规则只有一条：

`block when current_context_trend_direction == DOWN`

需要写诚实的是：

1. ledger 侧要验证的语义名是 `context_trend_direction_before`
2. runtime 真正消费的字段名是 `current_context_trend_direction`

这条规则的边界是：

1. 只测 `context_trend_direction_before`
2. 只允许 `parent-context negative guard`
3. 不改 entry backbone
4. 不改 sizing
5. 不偷带 `duration_percentile / wave_role / reversal_state / current_wave_age_band / mirror / conditioning / gene_score`

---

## 3. 真实回放入口

正式 runner：

1. [`../../../scripts/backtest/run_phase9_context_trend_direction_validation.py`](../../../scripts/backtest/run_phase9_context_trend_direction_validation.py)

正式 JSON evidence：

1. [`../../../docs/spec/v0.01-plus/evidence/phase9b_context_trend_direction_validation_legacy_context_direction_negative_guard_down_w20260105_20260224_t210823__phase9_context_trend_direction_validation.json`](../../../docs/spec/v0.01-plus/evidence/phase9b_context_trend_direction_validation_legacy_context_direction_negative_guard_down_w20260105_20260224_t210823__phase9_context_trend_direction_validation.json)

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

`PHASE9B_CONTEXT_DIRECTION_DOWN_NEGATIVE_GUARD`

1. `signals_count = 16`
2. `buy_filled_count = 10`
3. `trade_count = 10`
4. `expected_value = -0.0043857680`
5. `profit_factor = 0.8135666500`
6. `max_drawdown = 0.0144512924`
7. `reject_rate = 0.0476190476`
8. `missing_rate = 0.0000000000`

### 4.3 Candidate minus baseline

1. `expected_value delta = +0.0091613891`
2. `profit_factor delta = +0.0712458141`
3. `max_drawdown delta = -0.0054026669`
4. `buy_filled_count delta = -3`
5. `trade_count delta = -3`
6. `signal_count delta = 0`

这轮要诚实说明的一点是：

`candidate 没有把 EV 直接翻成正数，但它在 full-window 上仍然干净改善了 EV / PF / MDD / reject_rate。`

---

## 5. 它为什么不是 wave_role 的换名复跑

这轮 candidate 一共拦掉：

1. `6 / 16` 个 formal signals
2. 拦截占比 `37.5%`
3. 其中 `5 / 6` 在 baseline 里是真实 `BUY filled`
4. 占 baseline filled entries 的 `38.461538%`

更关键的是，被拦掉的 `6` 个信号内部组成是：

1. `MAINSTREAM = 4`
2. `COUNTERTREND = 2`

这意味着：

`如果它只是 wave_role 的换名复跑，就不该抓到这 4 个 MAINSTREAM。`

对照上一轮 `wave_role == COUNTERTREND`：

1. `wave_role` 拦掉的是 `12` 个信号
2. 其中 `11` 个是 baseline 真实 filled entry
3. 它更像“重压交易数量”
4. 而 `context_trend_direction == DOWN` 更像“只把父趋势向下的那一层风险单独切出来”

因此本轮 redundancy 结论应写成：

`context_trend_direction_before` 不是 `wave_role` 的改名复跑，而是一条更窄、更轻、且确实覆盖到部分 MAINSTREAM 信号的 parent-context 负向过滤规则。`

---

## 6. Split-window 读法

### 6.1 Front half

`2026-01-05` 至 `2026-01-23`

1. baseline `trade_count = 0`
2. candidate `trade_count = 0`
3. baseline `buy_filled_count = 2`
4. candidate `buy_filled_count = 2`
5. baseline `expected_value = 0.0000000000`
6. candidate `expected_value = 0.0000000000`

前半窗几乎没有产生差异。

### 6.2 Back half

`2026-01-26` 至 `2026-02-24`

1. baseline `trade_count = 11`
2. candidate `trade_count = 8`
3. baseline `buy_filled_count = 11`
4. candidate `buy_filled_count = 8`
5. baseline `expected_value = -0.0134463583`
6. candidate `expected_value = -0.0019568223`
7. baseline `profit_factor = 0.8484126907`
8. candidate `profit_factor = 0.9192244502`
9. baseline `max_drawdown = 0.0177045564`
10. candidate `max_drawdown = 0.0153999857`
11. baseline `reject_rate = 0.1111111111`
12. candidate `reject_rate = 0.0526315789`

真正支撑本轮 ruling 的主增益，来自后半窗：

`这条规则没有在前半窗制造假改善，而是在后半窗把 parent-context 向下的 entry 风险收窄了。`

---

## 7. 数据完整性观察

本轮有两条需要同时诚实记下：

1. `context_direction_filter_missing_direction_signal_count = 0`
2. full-window `missing_rate = 0`

但 candidate 也暴露出 `1` 条真实残留：

1. `NO_MARKET_DATA = 1`
2. 具体订单是：
   `EXIT_300308_2026-02-11_stop_loss`
3. 执行日是：
   `2026-02-12`

因此本轮数据质量判断应写成：

`parent-context 规则本身没有暴露字段缺失，但 candidate 运行路径里仍然保留 1 条旧有的 NO_MARKET_DATA 型 exit reject；这不足以推翻本轮 ruling，但不能省略。`

---

## 8. Evidence verdict

本轮 evidence 支持的正式结论是：

`promote_context_trend_direction_negative_guard`

因为这轮 isolated candidate：

1. 没有改动 formal `signals_count`
2. 真实拦掉了 `6` 个 signals，其中 `5` 个是 baseline filled entry
3. 明确抓到了 `4` 个 `MAINSTREAM`，证明它不是 `wave_role` 换名复跑
4. full-window `expected_value / profit_factor / max_drawdown / reject_rate` 相对 baseline 全部改善
5. 改善主要来自后半窗，而不是靠前半窗的偶然结果

一句话收口：

`这条 parent-context negative guard 不是把系统砍得很瘦才看起来变好，而是用比 wave_role 更轻的方式，真实切掉了父趋势向下的高风险 entry。`
