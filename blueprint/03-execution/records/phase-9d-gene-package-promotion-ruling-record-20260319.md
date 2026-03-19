# Phase 9D Record / Gene package promotion ruling

**状态**: `Completed`  
**日期**: `2026-03-19`

---

## 1. 本轮问题

`在 Phase 9A / 9B / 9C 都已经正式收口之后，第四战场到底该留下什么包级结论：promote、retain，还是 defer？`

---

## 2. 证据链

本轮正式证据链如下：

1. [`../17.7-phase-9d-gene-package-promotion-ruling-card-20260318.md`](../17.7-phase-9d-gene-package-promotion-ruling-card-20260318.md)
2. [`./phase-9a-gene-promoted-subset-freeze-record-20260318.md`](./phase-9a-gene-promoted-subset-freeze-record-20260318.md)
3. [`./phase-9b-duration-percentile-validation-record-20260318.md`](./phase-9b-duration-percentile-validation-record-20260318.md)
4. [`./phase-9b-wave-role-validation-record-20260318.md`](./phase-9b-wave-role-validation-record-20260318.md)
5. [`./phase-9b-reversal-state-validation-record-20260318.md`](./phase-9b-reversal-state-validation-record-20260318.md)
6. [`./phase-9b-context-trend-direction-validation-record-20260319.md`](./phase-9b-context-trend-direction-validation-record-20260319.md)
7. [`./phase-9c-formal-combination-freeze-record-20260319.md`](./phase-9c-formal-combination-freeze-record-20260319.md)
8. [`./phase-9-gene-promotion-flowchart-20260319.md`](./phase-9-gene-promotion-flowchart-20260319.md)
9. [`../17.8-phase-9e-duration-percentile-threshold-sweep-card-20260319.md`](../17.8-phase-9e-duration-percentile-threshold-sweep-card-20260319.md)
10. [`../17.9-phase-9f-frozen-combination-replay-card-20260319.md`](../17.9-phase-9f-frozen-combination-replay-card-20260319.md)

---

## 3. 正式裁决

`Phase 9D` 的正式 package ruling 现改为：

`defer and open a smaller follow-up package`

这次不是口头 defer，而是带着明确补证范围的 formal defer。

---

## 4. 为什么不是 promotion

当前最硬的证据缺口有两条：

1. `Phase 9C` 冻结的 `4` 个组合还没有任何 formal combination replay evidence
2. `duration_percentile` 目前只留下了：
   - `p95` formal round
   - `p65` sensitivity reference

因此当前并没有完成：

1. `p65 ~ p95, step 5` 的阈值扫描
2. turning-point / slope-change 判断
3. frozen-combination replay

在这三件事都没补完之前，包级 promotion 不诚实。

---

## 5. 为什么也不是 retain

当前也不能直接把包级结论写成：

`retain Gene as sidecar only`

因为：

1. `duration_percentile`
2. `reversal_state`
3. `context_trend_direction_before`

这 `3` 个字段都已经赢过 isolated round。

如果现在直接 `retain`，等于跳过了仍然值得做的精细化研究：

1. `duration_percentile` 阈值曲线
2. `Phase 9C` 冻结组合 replay

---

## 6. 当前真正为真的 runtime 边界

截至 `2026-03-19`，当前真正为真的 runtime 边界是：

`legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`

当前没有任何 Gene 字段被 package-promote 进 default runtime。

---

## 7. `Phase 9C` 的正式答案

本轮必须继续保留这条治理事实：

`Phase 9C has no formal combination winner`

但它现在的治理含义是：

1. `17.6` 只完成 freeze
2. 组合 replay 仍待后续更小 card 补完
3. 包级 closeout 不能提前假装 replay 已做完

---

## 8. 本轮打开的 follow-up

本轮 defer 后，必须立刻打开下面两张更小 card：

1. [`17.8-phase-9e-duration-percentile-threshold-sweep-card-20260319.md`](../17.8-phase-9e-duration-percentile-threshold-sweep-card-20260319.md)
2. [`17.9-phase-9f-frozen-combination-replay-card-20260319.md`](../17.9-phase-9f-frozen-combination-replay-card-20260319.md)

它们的作用是：

1. `17.8` 先把寿命轴做细
2. `17.9` 再把冻结组合面补回测

---

## 9. Rollback Target

当前正式 rollback target 保持为：

`legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`

因为这本来就是当前 truthful runtime。

---

## 10. 现在什么是真的

现在正式为真的事情有：

1. `Phase 9` 仍然 active
2. 当前 package output = `defer and open a smaller follow-up package`
3. `duration_percentile`、`reversal_state`、`context_trend_direction_before` 继续保留为 validated isolated winners
4. `Phase 9C` 只留下 frozen combination surface，没有留下 formal combination winner
5. 当前主线仍是：
   `legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`
6. `Phase 10` 当前仍被 `Phase 9` 阻塞

现在仍然不是真的事情有：

1. `full Gene runtime surface promoted`
2. `reversal_state package promotion completed`
3. `Phase 9 package closeout completed`

---

## 11. 下一步

当前真实下一步是：

1. 先做 `17.8 / duration sweep`
2. 再做 `17.9 / frozen combination replay`
3. 等 follow-up evidence 补齐后，再回到 package-level ruling

一句话收口：

`Phase 9D` 这次没有留下“哪个 Gene 字段已经进 runtime”的答案；它留下的是真正更重要的治理答案：当前还不能假装知道 package closeout，必须先把寿命轴和冻结组合面补证完。`
