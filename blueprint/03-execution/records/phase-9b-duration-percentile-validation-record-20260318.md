# Phase 9B Record / duration_percentile isolated validation

**状态**: `Completed`  
**日期**: `2026-03-18`

---

## 1. 本轮问题

`如果只把 duration_percentile 作为 negative filter 接入当前主线，而其余全部固定在 validated baseline，结果会不会更好？`

---

## 2. 证据链

本轮正式证据链如下：

1. [`../evidence/phase-9b-duration-percentile-validation-evidence-20260318.md`](../evidence/phase-9b-duration-percentile-validation-evidence-20260318.md)
2. [`../../../docs/spec/v0.01-plus/evidence/phase9b_duration_percentile_validation_legacy_duration_percentile_negative_filter_p95_w20260105_20260224_t085921__phase9_duration_validation.json`](../../../docs/spec/v0.01-plus/evidence/phase9b_duration_percentile_validation_legacy_duration_percentile_negative_filter_p95_w20260105_20260224_t085921__phase9_duration_validation.json)
3. [`./phase-9a-gene-promoted-subset-freeze-record-20260318.md`](./phase-9a-gene-promoted-subset-freeze-record-20260318.md)
4. [`../../../docs/spec/v0.01-plus/records/v0.01-plus-phase-8-data-contract-residual-audit-20260318.md`](../../../docs/spec/v0.01-plus/records/v0.01-plus-phase-8-data-contract-residual-audit-20260318.md)
5. [`../../../gene/03-execution/records/05-phase-g2-percentile-band-calibration-record-20260316.md`](../../../gene/03-execution/records/05-phase-g2-percentile-band-calibration-record-20260316.md)

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

### 4.2 为什么这样裁决

因为在正式窗口 `2026-01-05 ~ 2026-02-24` 内：

1. `signals_count` 没变，仍然是 `16`
2. candidate 真实拦掉了 `6` 个信号，占全部 formal signals 的 `37.5%`
3. 这 `6` 个被拦信号在 baseline 中全部都是真实 `BUY filled` entry
4. candidate 相对 baseline 的 `expected_value / profit_factor / max_drawdown / reject_rate` 都是改善

关键差值是：

1. `expected_value: -0.0135471571 -> -0.0130074713`
2. `profit_factor: 0.7423208359 -> 1.3346090740`
3. `max_drawdown: 0.0198539593 -> 0.0146233485`
4. `reject_rate: 0.1034482759 -> 0.0476190476`

因此：

`duration_percentile` 这张入场券已经不只是“可测”，而是已经完成了第一轮 isolated runtime win。`

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

`在真实改善成立的前提下，仍保留一条应继续跟踪的数据侧残留。`

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
2. `duration_percentile` 作为已过 isolated round 的 candidate，进入后续包内判断
3. 若要继续扩 Gene，必须继续遵守单变量纪律，不能偷开组合
4. `Phase 9` 的包级 promotion closeout 仍受 `GX8 completed or formally non-blocking` 这一 gate 约束

一句话收口：

`我们已经从“duration_percentile 只拿到入场券”，走到了“duration_percentile 已经完成第一轮主线单变量验证并赢下这一轮”。`
