# Phase 9C Record / formal combination freeze

**状态**: `Completed`  
**日期**: `2026-03-19`

---

## 1. 本轮问题

`在 Phase 9B 已经留下 3 个 truthful isolated winners、且 GX8 已完成之后，Phase 9C 这一步到底先留下什么最小合法组合面，以及组合 replay 是否应该在本卡内直接打开？`

---

## 2. 证据链

本轮正式证据链如下：

1. [`../17.6-phase-9c-formal-combination-freeze-card-20260318.md`](../17.6-phase-9c-formal-combination-freeze-card-20260318.md)
2. [`./phase-9b-duration-percentile-validation-record-20260318.md`](./phase-9b-duration-percentile-validation-record-20260318.md)
3. [`./phase-9b-wave-role-validation-record-20260318.md`](./phase-9b-wave-role-validation-record-20260318.md)
4. [`./phase-9b-reversal-state-validation-record-20260318.md`](./phase-9b-reversal-state-validation-record-20260318.md)
5. [`./phase-9b-context-trend-direction-validation-record-20260319.md`](./phase-9b-context-trend-direction-validation-record-20260319.md)
6. [`../../../gene/03-execution/records/19-phase-gx8-three-level-trend-hierarchy-record-20260319.md`](../../../gene/03-execution/records/19-phase-gx8-three-level-trend-hierarchy-record-20260319.md)
7. [`../17-phase-9-gene-mainline-integration-package-card-20260318.md`](../17-phase-9-gene-mainline-integration-package-card-20260318.md)

---

## 3. 本轮正式结论

### 3.1 本轮冻结的唯一合法组合面

`Phase 9C` 当前只允许使用下面 `3` 个已赢下 isolated round 的字段：

1. `duration_percentile`
2. `reversal_state`
3. `context_trend_direction_before`

当前只允许冻结下面 `4` 个组合：

1. `duration_percentile + reversal_state`
2. `duration_percentile + context_trend_direction_before`
3. `reversal_state + context_trend_direction_before`
4. `duration_percentile + reversal_state + context_trend_direction_before`

### 3.2 本轮正式 ruling

`Phase 9C` 的正式 ruling 仍是：

`no combination replay opened`

### 3.3 本轮直接留下的事实

本轮正式留下的事实只有这些：

1. `Phase 9C` 不存在 formal combination winner
2. 后续任何组合 replay 都只能发生在这 `4` 个冻结组合里
3. `Phase 9C` 只完成了 freeze，没有完成 replay

---

## 4. 为什么本轮不开 combination replay

当前最诚实的原因是：

1. 仓库中不存在任何 formal combination replay evidence
2. `17.6` 的职责是 `freeze + decision`，不是在没有 replay 产物时口头假装 replay 已获准
3. `duration_percentile` 的阈值面本身还没有做完 `p65 ~ p95, step 5` sweep
4. 因此当前若要做组合 replay，也应在 freeze 之后另开更小、更明确的 follow-up，而不是在本卡里边冻边补

因此本轮真正的结论不是：

`组合没有价值`

而是：

`组合 replay 尚未在本卡内 truthfully opened。`

---

## 5. 本轮没有声称什么

本轮裁决**没有**声称：

1. `Gene` 已整体完成 runtime promotion
2. 任一组合已证明优于 isolated winners
3. 未来永远不得新开更小的组合 follow-up
4. `Phase 9` 整包已经 closeout

---

## 6. 现在什么是真的

现在正式为真的事情有：

1. `Phase 9A` 已完成 promoted subset freeze
2. `Phase 9B / duration_percentile` 已完成并胜出
3. `Phase 9B / wave_role` 已完成，但 ruling 是 `retain_sidecar_only`
4. `Phase 9B / reversal_state` 已完成并胜出
5. `Phase 9B / context_trend_direction_before` 已完成并胜出
6. `Phase 9C` 已完成 formal combination freeze，并以 `no combination replay opened` 收口
7. `Phase 9C` 只冻结了 `4` 个组合，没有任何 formal combination winner

现在仍然不是真的事情有：

1. `Phase 9C formal combination winner exists`
2. `Gene default runtime promotion completed`
3. `Phase 9 package closeout completed`

---

## 7. Post-Remediation Note

`2026-03-19` 的 `17.8 / Phase 9E` 已经完成 book-aligned quartile rerun，并正式裁定：

1. `duration_should_return_to_sidecar_only_distribution_reading`
2. 历史 `p65 / p95` round 只保留为 `legacy archive`
3. 含 `duration_percentile` 的 frozen combos 继续保留为历史冻结事实，但当前不具备 truthful replay 资格
4. `reversal_state + context_trend_direction_before` 是当前唯一没有被 `17.8` 直接否决的历史冻结组合，但是否打开，必须在本 record 之外另做 reruling

---

## 8. 下游含义

`17.6` 完成之后，当前 truthful downstream 不再是“直接默认 package promotion 可以成立”。

当前更准确的下游顺序是：

1. `17.7 / Phase 9D` 必须先对现有证据做包级判断
2. 若现有证据不足，它只能选择：
   `defer and open a smaller follow-up package`
3. `17.8 / book-aligned duration lifespan distribution rerun` 现已完成，并把 duration 裁回 `sidecar only`
4. 因此当前 truthful downstream 不再是“直接打开旧定义的 17.9”，而是：
   - 先做新的 reruling
   - 再决定是否只在无 duration 的 frozen combo 上重开 replay

一句话收口：

`Phase 9C` 现在已经把组合面冻结清楚了，并正式裁定本卡内部不开 combination replay；这张卡的价值不在于替 package closeout 预支结论，而在于把后续所有组合 replay 严格锁进一个可治理、可追责的最小 surface。`
