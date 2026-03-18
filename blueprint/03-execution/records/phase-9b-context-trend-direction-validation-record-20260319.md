# Phase 9B Record / context_trend_direction_before isolated validation

**状态**: `Completed`  
**日期**: `2026-03-19`

---

## 1. 本轮问题

`如果只把 context_trend_direction_before 以 parent-context negative guard 身份接进当前主线，而其余全部固定在 validated baseline，结果会不会更好？`

---

## 2. 证据链

本轮正式证据链如下：

1. [`../evidence/phase-9b-context-trend-direction-validation-evidence-20260319.md`](../evidence/phase-9b-context-trend-direction-validation-evidence-20260319.md)
2. [`./phase-9b-context-trend-direction-readiness-note-20260319.md`](./phase-9b-context-trend-direction-readiness-note-20260319.md)
3. [`../../../docs/spec/v0.01-plus/evidence/phase9b_context_trend_direction_validation_legacy_context_direction_negative_guard_down_w20260105_20260224_t210823__phase9_context_trend_direction_validation.json`](../../../docs/spec/v0.01-plus/evidence/phase9b_context_trend_direction_validation_legacy_context_direction_negative_guard_down_w20260105_20260224_t210823__phase9_context_trend_direction_validation.json)
4. [`./phase-9a-gene-promoted-subset-freeze-record-20260318.md`](./phase-9a-gene-promoted-subset-freeze-record-20260318.md)
5. [`./phase-9b-duration-percentile-validation-record-20260318.md`](./phase-9b-duration-percentile-validation-record-20260318.md)
6. [`./phase-9b-wave-role-validation-record-20260318.md`](./phase-9b-wave-role-validation-record-20260318.md)
7. [`./phase-9b-reversal-state-validation-record-20260318.md`](./phase-9b-reversal-state-validation-record-20260318.md)
8. [`../../../docs/spec/v0.01-plus/records/v0.01-plus-phase-8-data-contract-residual-audit-20260318.md`](../../../docs/spec/v0.01-plus/records/v0.01-plus-phase-8-data-contract-residual-audit-20260318.md)
9. [`../../../docs/spec/v0.01-plus/records/v0.01-plus-phase-9b-context-trend-direction-readiness-20260319.md`](../../../docs/spec/v0.01-plus/records/v0.01-plus-phase-9b-context-trend-direction-readiness-20260319.md)

---

## 3. 当前 fixed baseline

本轮固定不动的 baseline 仍然是：

`legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`

本轮唯一改动的是：

`add context_trend_direction_before parent-context negative guard semantics`

但 runtime 入口名必须写诚实：

`block when current_context_trend_direction == DOWN`

---

## 4. 正式裁决

### 4.1 本轮 ruling

`Phase 9B` 的正式 ruling 是：

`promote_context_trend_direction_negative_guard`

### 4.2 用人话解释这张卡

这张卡的结论，不是“父趋势字段已经能单独决定买不买”。

更准确的人话是：

1. 它现在只赢下了一条很窄的负向过滤语义
2. 这条语义的真实意思是：
   `父趋势方向向下时，当前 entry 不值得进主线`
3. 它没有像 `wave_role` 那样把交易压得很狠
4. 它拦掉的是 `6 / 16` 个 signals，其中 `5` 个是 baseline 的真实 filled entry
5. full-window `expected_value` 虽然仍是负数，但已经从 `-0.0135471571` 收窄到 `-0.0043857680`
6. `profit_factor / max_drawdown / reject_rate` 也一起改善

所以它真正说明的是：

`context_trend_direction_before` 已经从父趋势参考 sidecar，走到了“可作为窄 parent-context negative guard 进入下一层包内判断”的位置。`

### 4.3 为什么这轮能通过

本轮通过，关键有三点：

1. 它不是没碰到 runtime
2. 它不是 `wave_role` 的换名复跑
3. 它在 full-window 上确实比 baseline 更好

对应事实是：

1. `signals_count` 保持 `16` 不变
2. candidate 真正拦掉了 `6` 个 signals
3. 其中 `5` 个是 baseline 里的真实 `BUY filled`
4. 被拦对象里有 `4` 个 `MAINSTREAM`、`2` 个 `COUNTERTREND`
5. baseline `expected_value = -0.0135471571`
6. candidate `expected_value = -0.0043857680`
7. baseline `profit_factor = 0.7423208359`
8. candidate `profit_factor = 0.8135666500`
9. baseline `max_drawdown = 0.0198539593`
10. candidate `max_drawdown = 0.0144512924`

也就是说：

`这条规则不是靠“多拦一点总会更好”的粗暴方式过关，而是用比 wave_role 更轻的 parent-context 切法，做出了更干净的改善。`

---

## 5. 本轮没有声称什么

本轮裁决**没有**声称：

1. `Gene` 已经整体进入默认 runtime
2. `Phase 9` 整包已经完成
3. `duration_percentile + reversal_state + context_trend_direction_before` 现在可以自动做组合
4. `17.6 / Phase 9C` 现在自动打开
5. `context_trend_direction_before` 现在可以直接扩成 default hard gate 或 sizing overlay

本轮只声称：

`context_trend_direction_before` 已通过 truthful isolated runtime validation，并赢下了 narrow parent-context negative guard 这一条角色。`

---

## 6. 本轮残留观察

这轮结果是正向的，但仍有一条残留需要留下：

1. candidate 暴露了 `1` 条 `NO_MARKET_DATA`
2. 具体订单是：
   `EXIT_300308_2026-02-11_stop_loss`
3. 执行日是：
   `2026-02-12`

需要同时强调的是：

1. `context_direction_filter_missing_direction_signal_count = 0`
2. full-window `missing_rate = 0`
3. 这不是 parent-context 字段缺失

因此当前最诚实的判断是：

`本轮仍有一条旧的 market-data 残留需要继续跟踪，但它没有形成足以推翻本轮 ruling 的 parent-context runtime failure。`

---

## 7. 现在什么是真的

现在正式为真的事情有：

1. `Phase 9A` 已完成 promoted subset freeze
2. `Phase 9B / duration_percentile` 已完成并胜出
3. `Phase 9B / wave_role` 已完成，但 ruling 是 `retain_sidecar_only`
4. `Phase 9B / reversal_state` 已完成并胜出
5. `Phase 9B / context_trend_direction_before` 现在也已完成并胜出
6. 当前包内已经有 `3` 个 isolated winner：
   `duration_percentile`、`reversal_state`、`context_trend_direction_before`

现在仍然不是真的事情有：

1. `Gene default runtime promotion completed`
2. `Phase 9 package closeout completed`
3. `Phase 9C combination candidate is now open`
4. `GX8` 已经对组合 scope 正式 non-blocking

---

## 8. 下一步

本轮完成后，当前最诚实的下一步不是口头跳组合，而是先承认剩余门槛是什么：

1. `17.6 / Phase 9C combination candidate` 已不再受 winner-count 阻塞
2. 但 `GX8` 当前只被裁定为：
   `non-blocking for isolated proxy validation only`
3. 组合对象本身也还没有被写成 explicit combination freeze
4. 因此 `17.6` 仍不能自动切成 `Active`
5. `Phase 9` 主包继续保持 `Active`

一句话收口：

`我们已经从“父趋势方向只是 sidecar 参考”，走到了“父趋势方向已赢下 isolated parent-context negative guard 这一轮”；但第四战场离组合与包级 closeout 之间，仍然隔着 GX8 scope 与 formal combination freeze 这两道门。`
