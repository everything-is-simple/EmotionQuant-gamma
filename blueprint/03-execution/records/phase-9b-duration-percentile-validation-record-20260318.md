# Phase 9B Record / duration_percentile isolated validation

**状态**: `Completed`  
**日期**: `2026-03-18`

---

## 1. 本轮问题

`如果只把 duration_percentile 作为 negative filter 接进当前主线，而其余全部固定在 validated baseline，结果会不会更好？`

---

## 2. 证据链

本轮正式证据链如下：

1. [`../evidence/phase-9b-duration-percentile-validation-evidence-20260318.md`](../evidence/phase-9b-duration-percentile-validation-evidence-20260318.md)
2. [`../../../docs/spec/v0.01-plus/evidence/phase9b_duration_percentile_validation_legacy_duration_percentile_negative_filter_p95_w20260105_20260224_t085921__phase9_duration_validation.json`](../../../docs/spec/v0.01-plus/evidence/phase9b_duration_percentile_validation_legacy_duration_percentile_negative_filter_p95_w20260105_20260224_t085921__phase9_duration_validation.json)
3. [`../../../docs/spec/v0.01-plus/evidence/phase9b_duration_percentile_validation_legacy_duration_percentile_negative_filter_p65_w20260105_20260224_t100421__phase9_duration_validation.json`](../../../docs/spec/v0.01-plus/evidence/phase9b_duration_percentile_validation_legacy_duration_percentile_negative_filter_p65_w20260105_20260224_t100421__phase9_duration_validation.json)
4. [`./phase-9a-gene-promoted-subset-freeze-record-20260318.md`](./phase-9a-gene-promoted-subset-freeze-record-20260318.md)
5. [`../../../docs/spec/v0.01-plus/records/v0.01-plus-phase-8-data-contract-residual-audit-20260318.md`](../../../docs/spec/v0.01-plus/records/v0.01-plus-phase-8-data-contract-residual-audit-20260318.md)
6. [`../../../gene/03-execution/records/05-phase-g2-percentile-band-calibration-record-20260316.md`](../../../gene/03-execution/records/05-phase-g2-percentile-band-calibration-record-20260316.md)

---

## 3. 当前 fixed baseline

本轮固定不动的 baseline 仍然是：

`legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`

本轮唯一改动的是：

`add duration_percentile >= 95 negative-filter semantics`

---

## 4. 正式裁决

### 4.1 本轮 ruling

`Phase 9B` 的正式 ruling 是：

`promote_duration_percentile_negative_filter`

### 4.2 用人话解释这张卡

这张卡的结论，不是“Gene 已经进主线了”。

更准确的人话是：

1. `duration_percentile >= 95` 这把刀，确实砍掉了一批 baseline 里原本会真实成交的 late-life entry
2. 它没有把系统砍废，主线还在跑，`13` 笔交易变成 `10` 笔
3. 在这把细刀之下，full-window 的 `expected_value / profit_factor / max_drawdown / reject_rate` 都比 baseline 更好

所以它真正说明的是：

`duration_percentile` 已经从“只拿到入场券”，走到了“赢下第一轮主线单变量验证”。`

### 4.3 为什么是 `95`，不是 `65`

补跑的 `65` 对照，账面指标确实更好看，但它的代价也更重：

1. `95` 只拦 `6 / 16 = 37.5%` formal signals，保留 `10` 笔成交
2. `65` 直接拦 `13 / 16 = 81.25%` formal signals，只剩 `3` 笔成交
3. `95` 拿掉的是 baseline 中 `46.15%` 的真实 `BUY filled`
4. `65` 拿掉的是 baseline 中 `84.62%` 的真实 `BUY filled`

也就是说：

1. `95` 还是保守过滤，像一把细刀
2. `65` 已经更像“重度交易压缩”
3. `65` 的改善，很大程度来自“把大多数交易不做了”，而不是更诚实地证明“这是更合适的正式主线阈值”

因此本轮结论是：

1. `65` 作为 sensitivity reference 保留
2. 它不改写本轮 formal ruling
3. `Phase 9B` 当前正式留下的阈值仍然是 `95`

---

## 5. 本轮没有声称什么

本轮裁决**没有**声称：

1. `Gene` 已经整体进入默认 runtime
2. `Phase 9` 整包已经完成
3. `current_wave_age_band / wave_role / reversal_state / mirror / conditioning / gene_score` 现在可以一起进
4. `duration_percentile` 已经可以直接升格成 sizing / exit modulation

本轮只声称：

`duration_percentile` 已经通过了第一轮单变量、negative-filter-only、主线 isolated validation。`

---

## 6. 本轮残留风险

本轮仍需明确保留两个残留观察：

1. candidate `missing_rate = 0.0476190476`，baseline 为 `0`
2. candidate 暴露出 `EXIT_300308_2026-02-11_stop_loss -> NO_MARKET_DATA` 这一条 exit 数据缺口

所以本轮不是“从此没有问题”，而是：

`在真实改善成立的前提下，保留一条应继续跟踪的数据侧残留。`

---

## 7. 现在什么是真的

现在正式为真的事情有：

1. `Phase 9A` 已完成 promoted subset freeze
2. `Phase 9B` 已完成 `duration_percentile` isolated validation
3. 第一张 Gene runtime 单变量胜出项现在是 `duration_percentile`
4. 它当前唯一被验证通过的角色仍然是 `negative filter only`

现在仍然不是真的事情有：

1. `Gene default runtime promotion completed`
2. `Phase 9 package closeout completed`
3. `combination candidate is now open`

---

## 8. 下一步

本轮完成后，当前最诚实的下一步是：

1. `Phase 9` 包继续保持 `Active`
2. `duration_percentile >= 95` 保留为当前已过 isolated round 的正式阈值
3. `65` 只保留为 sensitivity reference，不升格成新的 formal threshold
4. 下一张卡进入新的单变量字段，而不是偷开组合或继续放宽 duration 阈值

当前最自然的下一张卡是：

`Phase 9B / isolated wave_role validation`

理由是：

1. `wave_role` 在 `Phase 9A` 中是 `pending candidate`，不是 `shadow-only`
2. 它是结构语义字段，和 `duration` 不是同一把尺的重复读法
3. 包级卡已经把它列为下一批合法的 isolated round 候选之一
4. 先开 `wave_role`，比直接去做组合、或继续把 `duration` 这把刀开得更宽，更符合当前单变量纪律

一句话收口：

`我们已经证明 95 这把 duration 刀是有用的，但现在不该把刀开得更宽，而该换下一把合法的单变量刀。`
