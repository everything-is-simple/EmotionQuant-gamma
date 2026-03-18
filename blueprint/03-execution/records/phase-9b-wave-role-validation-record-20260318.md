# Phase 9B Record / wave_role isolated validation

**状态**: `Completed`  
**日期**: `2026-03-18`

---

## 1. 本轮问题

`如果只把 wave_role 作为 negative filter 接进当前主线，而其余全部固定在 validated baseline，结果会不会更好？`

---

## 2. 证据链

本轮正式证据链如下：

1. [`../evidence/phase-9b-wave-role-validation-evidence-20260318.md`](../evidence/phase-9b-wave-role-validation-evidence-20260318.md)
2. [`../../../docs/spec/v0.01-plus/evidence/phase9b_wave_role_validation_legacy_wave_role_negative_filter_countertrend_w20260105_20260224_t151651__phase9_wave_role_validation.json`](../../../docs/spec/v0.01-plus/evidence/phase9b_wave_role_validation_legacy_wave_role_negative_filter_countertrend_w20260105_20260224_t151651__phase9_wave_role_validation.json)
3. [`./phase-9a-gene-promoted-subset-freeze-record-20260318.md`](./phase-9a-gene-promoted-subset-freeze-record-20260318.md)
4. [`./phase-9b-duration-percentile-validation-record-20260318.md`](./phase-9b-duration-percentile-validation-record-20260318.md)
5. [`../../../gene/03-execution/records/15-phase-gx4-mainstream-countertrend-semantics-record-20260318.md`](../../../gene/03-execution/records/15-phase-gx4-mainstream-countertrend-semantics-record-20260318.md)
6. [`../../../docs/spec/v0.01-plus/records/v0.01-plus-phase-8-data-contract-residual-audit-20260318.md`](../../../docs/spec/v0.01-plus/records/v0.01-plus-phase-8-data-contract-residual-audit-20260318.md)

---

## 3. 当前 fixed baseline

本轮固定不动的 baseline 仍然是：

`legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`

本轮唯一改动的是：

`add wave_role == COUNTERTREND negative-filter semantics`

---

## 4. 正式裁决

### 4.1 本轮 ruling

`Phase 9B` 这一轮 `wave_role` isolated validation 的正式 ruling 是：

`retain_sidecar_only`

### 4.2 用人话解释这张卡

这张卡的结论不是：

`wave_role 没价值`

而是：

1. `wave_role == COUNTERTREND` 这条规则确实碰到了真实 runtime
2. 它不是假过滤，因为它真实拦掉了 `12 / 15` 个 formal signals
3. 被拦掉的信号里，有 `11` 个本来会在 baseline 中真实 `BUY filled`
4. 它确实把回撤压得很低
5. 但它也把交易压得太狠，full-window `expected_value` 反而更差

更准确的人话是：

`这条 wave_role 过滤不是没用，而是太重，重到不足以作为当前主线的默认单变量负向过滤。`

### 4.3 为什么这轮没有通过

本轮失败的关键不是数据问题，而是行为问题：

1. baseline `trade_count = 13`
2. candidate `trade_count = 3`
3. baseline `buy_filled_count = 13`
4. candidate `buy_filled_count = 3`
5. baseline `expected_value = -0.0058474335`
6. candidate `expected_value = -0.0115219631`

也就是说：

1. `profit_factor` 有小幅改善
2. `max_drawdown` 有明显改善
3. 但这是建立在“把大多数真实交易机会都不做了”的基础上
4. 对当前主线包来说，这不构成一个干净的 isolated win

---

## 5. 本轮没有声称什么

本轮裁决**没有**声称：

1. `wave_role` 永远不能进入 runtime
2. `Gene` 已经整体进入默认 runtime
3. `Phase 9` 整包已经完成
4. `duration_percentile + wave_role` 现在可以组合
5. `wave_role` 现在可以直接转成 sizing / exit modulation

本轮只声称：

`wave_role == COUNTERTREND` 作为当前这轮单变量、negative-filter-only、isolated runtime rule，没有赢下 baseline。`

---

## 6. 现在什么是真的

现在正式为真的事情有：

1. `Phase 9A` 已完成 promoted subset freeze
2. `Phase 9B / duration_percentile` 已完成并胜出
3. `Phase 9B / wave_role` 已完成，但 formal ruling 是 `retain_sidecar_only`
4. `duration_percentile` 仍然是当前唯一通过 isolated runtime round 的 Gene 字段
5. `wave_role` 当前仍应保留在 `sidecar / structure readout` 位置

现在仍然不是真的事情有：

1. `Gene default runtime promotion completed`
2. `Phase 9 package closeout completed`
3. `combination candidate is now open`

---

## 7. 下一步

本轮完成后，当前最诚实的下一步是：

1. `Phase 9` 包继续保持 `Active`
2. `duration_percentile >= 95` 保留为当前已过 isolated round 的正式 winner
3. `wave_role` 明确保留为 `retain_sidecar_only`
4. 若要继续扩 `Gene`，必须新开下一张单变量卡，不能因为这轮失败就偷开组合

一句话收口：

`我们已经证明 wave_role 这把刀会切到真实 runtime，但现在这把刀太重，不适合直接升格成默认主线负向过滤。`
