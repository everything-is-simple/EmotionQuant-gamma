# Phase 9B Record / reversal_state isolated validation

**状态**: `Completed`  
**日期**: `2026-03-18`

---

## 1. 本轮问题

`如果只把 reversal_state 以 exit-preparation only 身份接进当前主线，而其余全部固定在 validated baseline，结果会不会更好？`

---

## 2. 证据链

本轮正式证据链如下：

1. [`../evidence/phase-9b-reversal-state-validation-evidence-20260318.md`](../evidence/phase-9b-reversal-state-validation-evidence-20260318.md)
2. [`../../../docs/spec/v0.01-plus/evidence/phase9b_reversal_state_validation_legacy_reversal_state_exit_prep_confirmed_turn_down_w20260105_20260224_t160310__phase9_reversal_validation.json`](../../../docs/spec/v0.01-plus/evidence/phase9b_reversal_state_validation_legacy_reversal_state_exit_prep_confirmed_turn_down_w20260105_20260224_t160310__phase9_reversal_validation.json)
3. [`./phase-9a-gene-promoted-subset-freeze-record-20260318.md`](./phase-9a-gene-promoted-subset-freeze-record-20260318.md)
4. [`./phase-9b-duration-percentile-validation-record-20260318.md`](./phase-9b-duration-percentile-validation-record-20260318.md)
5. [`./phase-9b-wave-role-validation-record-20260318.md`](./phase-9b-wave-role-validation-record-20260318.md)
6. [`../../../docs/spec/v0.01-plus/records/v0.01-plus-phase-8-data-contract-residual-audit-20260318.md`](../../../docs/spec/v0.01-plus/records/v0.01-plus-phase-8-data-contract-residual-audit-20260318.md)

---

## 3. 当前 fixed baseline

本轮固定不动的 baseline 仍然是：

`legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`

本轮唯一改动的是：

`add reversal_state == CONFIRMED_TURN_DOWN exit-preparation semantics`

---

## 4. 正式裁决

### 4.1 本轮 ruling

`Phase 9B` 的正式 ruling 是：

`promote_reversal_state_exit_preparation`

### 4.2 用人话解释这张卡

这张卡的结论，不是“Gene 已经整体进主线了”。

更准确的人话是：

1. `reversal_state` 这轮不是拿来挡 entry，而是拿来对已有持仓做更早的防守准备
2. 这条规则在正式窗口里一共触发了 `9` 次真实 `T+1 SELL`
3. 它没有把系统切瘦，反而让主线多拿到了 `1` 笔真实 entry 和 `1` 笔闭合 trade
4. full-window `expected_value` 从 `-0.0135471571` 翻到 `+0.0054696770`
5. `profit_factor / max_drawdown / reject_rate` 也一起改善

所以它真正说明的是：

`reversal_state` 已经从 sidecar 结构读数，走到了“可以作为窄 exit-preparation 规则进入主线 runtime”的位置。`

### 4.3 为什么这轮能通过

本轮通过，关键不是口头理解，而是 runtime 事实：

1. `signals_count` 保持 `16` 不变
2. candidate 真实创建并成交了 `9` 笔 `GENE_REVERSAL_PREP` exits
3. baseline `buy_filled_count = 13`，candidate `buy_filled_count = 14`
4. baseline `trade_count = 13`，candidate `trade_count = 14`
5. baseline `reject_rate = 0.1034482759`，candidate `reject_rate = 0.0666666667`

也就是说：

`这条规则不是通过“少做交易”赢的，而是通过更早风险释放，让后续主线路径更顺。`

---

## 5. 本轮没有声称什么

本轮裁决**没有**声称：

1. `Gene` 已经整体进入默认 runtime
2. `Phase 9` 整包已经完成
3. `duration_percentile + reversal_state` 现在可以自动打包做组合
4. `reversal_state` 现在可以直接扩成 sizing overlay
5. `17.6 / Phase 9C` 现在自动打开

本轮只声称：

`reversal_state == CONFIRMED_TURN_DOWN` 这条窄 exit-preparation 规则，已经通过了 truthful isolated runtime validation。`

---

## 6. 本轮残留观察

这轮结果是正向的，但仍有一条残留需要留下：

1. `reversal_exit_missing_state_position_day_count = 3`
2. 这 `3` 个缺口集中在 `2026-02-12`

需要强调的是：

1. full-window `missing_rate` 仍然是 `0`
2. 没有新的 `NO_MARKET_DATA`
3. 没有 `GENE_REVERSAL_PREP` exit reject
4. 没有 `GENE_REVERSAL_PREP` exit expire

因此当前最诚实的判断是：

`这是一条应继续跟踪的 state completeness 残留，但它没有形成本轮 runtime failure。`

---

## 7. 现在什么是真的

现在正式为真的事情有：

1. `Phase 9A` 已完成 promoted subset freeze
2. `Phase 9B / duration_percentile` 已完成并胜出
3. `Phase 9B / wave_role` 已完成，但 ruling 是 `retain_sidecar_only`
4. `Phase 9B / reversal_state` 现在也已完成并胜出
5. 当前包内已经有 `2` 个 isolated winner：
   `duration_percentile` 和 `reversal_state`

现在仍然不是真的事情有：

1. `Gene default runtime promotion completed`
2. `Phase 9 package closeout completed`
3. `Phase 9C combination candidate is now open`
4. `17.5 / context_trend_direction_before` 已自动变成 active

---

## 8. 下一步

本轮完成后，当前最诚实的下一步不是口头跳组合，而是先承认门槛状态已经变化：

1. `17.5 / context_trend_direction_before` 的第一道门槛 `17.4 completed` 已满足
2. 但它仍受 `GX8 completed or non-blocking + redundancy note` 双门槛约束，所以继续保持 `Planned`
3. `17.6 / Phase 9C combination candidate` 的“至少两个 isolated winner”门槛现在已满足
4. 但它仍受 `GX8 completed or non-blocking` 与 `explicit combination freeze` 约束，所以也继续保持 `Planned`
5. 因此当前真实状态不是“下一张卡自动跳出来了”，而是：
   `Phase 9 package remains Active, but the next truthful move now depends on clearing the remaining gate rather than pretending the gate no longer exists.`

一句话收口：

`我们已经从“只有 duration_percentile 一张 isolated winner 票”，走到了“duration_percentile + reversal_state 两张 isolated winner 都已成立”；但第四战场离 package closeout 仍然差 GX8 与组合冻结这两道门。`
