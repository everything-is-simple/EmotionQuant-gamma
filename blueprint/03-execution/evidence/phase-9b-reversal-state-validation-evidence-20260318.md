# Phase 9B Evidence / reversal_state isolated validation

**状态**: `Completed`  
**日期**: `2026-03-18`  
**对象**: `Phase 9B / isolated reversal_state validation`

---

## 1. 本轮问题

本轮只回答一个问题：

`如果只把 reversal_state 以 exit-preparation only 身份接进当前 validated baseline，结果会不会比 baseline 更好？`

---

## 2. 被测规则

本轮正式规则只有一条：

`schedule T+1 SELL when reversal_state == CONFIRMED_TURN_DOWN`

这条规则的边界是：

1. 只测 `reversal_state`
2. 只允许 `exit-preparation only`
3. 不改 entry backbone
4. 不改 sizing
5. 不偷带 `duration_percentile / wave_role / current_wave_age_band / context_trend_direction_before / mirror / conditioning / gene_score`

---

## 3. 真实回放入口

正式 runner：

1. [`../../../scripts/backtest/run_phase9_reversal_state_validation.py`](../../../scripts/backtest/run_phase9_reversal_state_validation.py)

正式 JSON evidence：

1. [`../../../docs/spec/v0.01-plus/evidence/phase9b_reversal_state_validation_legacy_reversal_state_exit_prep_confirmed_turn_down_w20260105_20260224_t160310__phase9_reversal_validation.json`](../../../docs/spec/v0.01-plus/evidence/phase9b_reversal_state_validation_legacy_reversal_state_exit_prep_confirmed_turn_down_w20260105_20260224_t160310__phase9_reversal_validation.json)

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

`PHASE9B_REVERSAL_CONFIRMED_TURN_DOWN_EXIT_PREP`

1. `signals_count = 16`
2. `buy_filled_count = 14`
3. `trade_count = 14`
4. `expected_value = 0.0054696770`
5. `profit_factor = 0.9509735734`
6. `max_drawdown = 0.0137531180`
7. `reject_rate = 0.0666666667`
8. `missing_rate = 0.0000000000`

### 4.3 Candidate minus baseline

1. `expected_value delta = +0.0190168341`
2. `profit_factor delta = +0.2086527375`
3. `max_drawdown delta = -0.0061008413`
4. `buy_filled_count delta = +1`
5. `trade_count delta = +1`
6. `signal_count delta = 0`

---

## 5. 这条规则到底有没有碰到真实 runtime

答案是：碰到了，而且碰得很实。

本轮 candidate 的真实 exit-preparation 触发结果是：

1. `reversal_exit_total_position_day_count = 87`
2. `reversal_exit_matched_state_position_day_count = 9`
3. `reversal_exit_created_count = 9`
4. `reversal_exit_filled_count = 9`
5. `reversal_exit_trade_count = 9`
6. `reversal_exit_reject_count = 0`
7. `reversal_exit_expire_count = 0`
8. `reversal_exit_created_share_of_positions = 10.34482759%`

这说明：

`本轮不是“信号没变所以规则没碰到主线”，而是“formal signals 数量不变，但已有持仓被 9 次真实 defensive exit 改写了路径”。`

更关键的是，这 9 次 exit-preparation 没有把系统压扁，反而让主线结果更好：

1. `buy_filled_count: 13 -> 14`
2. `trade_count: 13 -> 14`
3. `reject_rate: 0.1034482759 -> 0.0666666667`

也就是说：

`reversal_state` 不是拿掉 entry，而是通过更早释放风险和仓位，反过来让后续主线多拿到 1 笔真实成交。`

本轮被真实创建并成交的 `9` 笔 defensive exits 是：

1. `002475 / 2026-01-19 / GENE_REVERSAL_PREP`
2. `601818 / 2026-01-30 / GENE_REVERSAL_PREP`
3. `601668 / 2026-02-09 / GENE_REVERSAL_PREP`
4. `002547 / 2026-02-09 / GENE_REVERSAL_PREP`
5. `002384 / 2026-02-09 / GENE_REVERSAL_PREP`
6. `600887 / 2026-02-10 / GENE_REVERSAL_PREP`
7. `600436 / 2026-02-10 / GENE_REVERSAL_PREP`
8. `002517 / 2026-02-10 / GENE_REVERSAL_PREP`
9. `002227 / 2026-02-13 / GENE_REVERSAL_PREP`

---

## 6. Split-window 读法

### 6.1 Front half

`2026-01-05` 至 `2026-01-23`

1. baseline `trade_count = 0`
2. candidate `trade_count = 1`
3. baseline `buy_filled_count = 2`
4. candidate `buy_filled_count = 2`
5. candidate `reversal_exit_created_count = 1`
6. candidate `expected_value = 0.0472084783`

前半窗真正发生的是：

`reversal_state` 在不减少 entry 的前提下，先做出 1 次真实 defensive exit，并让窗口内首次形成正向闭合 trade。`

### 6.2 Back half

`2026-01-26` 至 `2026-02-24`

1. baseline `trade_count = 11`
2. candidate `trade_count = 12`
3. baseline `buy_filled_count = 11`
4. candidate `buy_filled_count = 12`
5. baseline `expected_value = -0.0134463583`
6. candidate `expected_value = 0.0013439698`
7. baseline `profit_factor = 0.8484126907`
8. candidate `profit_factor = 1.0564363251`
9. baseline `max_drawdown = 0.0177045564`
10. candidate `max_drawdown = 0.0148177182`
11. candidate `reversal_exit_created_count = 8`

真正支撑本轮 ruling 的主增益，来自后半窗：

`8` 次真实 defensive exit 把后半窗从负 EV 推到了正 EV，同时还降低了回撤。`

---

## 7. 数据完整性观察

本轮没有暴露出上一轮 `duration_percentile` 那种 `NO_MARKET_DATA` 型残留。

需要诚实记下来的只有两点：

1. full-window `missing_rate` 继续保持 `0`
2. `reversal_exit_missing_state_position_day_count = 3`，全部集中在 `2026-02-12`

但这 `3` 个 position-day 缺的是当日 `reversal_state` 读数，不是成交数据缺口，也没有形成：

1. exit reject
2. exit expire
3. `NO_MARKET_DATA`

因此本轮数据质量判断应写成：

`存在轻微 state completeness 残留，但没有形成足以推翻本轮 ruling 的 runtime failure。`

---

## 8. Evidence verdict

本轮 evidence 支持的正式结论是：

`promote_reversal_state_exit_preparation`

因为这轮 isolated candidate：

1. 没有改动 formal `signals_count`
2. 真实创建并成交了 `9` 笔 defensive exits
3. 让 `buy_filled_count / trade_count` 都比 baseline 多 `1`
4. 让 full-window `expected_value` 从负数转成正数
5. 同时改善了 `profit_factor / max_drawdown / reject_rate`

一句话收口：

`这不是一条“看起来聪明”的 sidecar 规则，而是一条已经在主线 runtime 上做出真实防守动作、并且干净赢下 baseline 的窄 exit-preparation 规则。`
