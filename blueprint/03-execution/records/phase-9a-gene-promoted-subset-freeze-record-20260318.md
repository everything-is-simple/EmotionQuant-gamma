# Phase 9A Record: Gene promoted subset freeze

**状态**: `Completed`  
**日期**: `2026-03-18`

---

## 1. 本轮问题

`在 Phase 8 已经清掉活跃数据合同残留之后，第四战场哪一个 Gene 字段最适合先进入主线隔离验证，而且这个入口必须窄到不会把 Gene 口头升格成新的 runtime boss indicator？`

---

## 2. 本轮证据

本轮正式证据链如下：

1. [`../evidence/phase-9a-gene-promoted-subset-freeze-evidence-20260318.md`](../evidence/phase-9a-gene-promoted-subset-freeze-evidence-20260318.md)
2. [`../../../docs/spec/v0.01-plus/records/v0.01-plus-phase-8-data-contract-residual-audit-20260318.md`](../../../docs/spec/v0.01-plus/records/v0.01-plus-phase-8-data-contract-residual-audit-20260318.md)
3. [`../../../docs/spec/v0.01-plus/records/v0.01-plus-phase-6a-promoted-subset-freeze-20260317.md`](../../../docs/spec/v0.01-plus/records/v0.01-plus-phase-6a-promoted-subset-freeze-20260317.md)
4. [`../../../gene/03-execution/records/07-phase-g4-self-history-ruler-validation-record-20260316.md`](../../../gene/03-execution/records/07-phase-g4-self-history-ruler-validation-record-20260316.md)
5. [`../../../gene/03-execution/records/08-phase-g5-market-industry-index-mirror-ruler-record-20260316.md`](../../../gene/03-execution/records/08-phase-g5-market-industry-index-mirror-ruler-record-20260316.md)
6. [`../../../gene/03-execution/records/09-phase-g6-bof-pb-cpb-conditioning-record-20260316.md`](../../../gene/03-execution/records/09-phase-g6-bof-pb-cpb-conditioning-record-20260316.md)
7. [`../../../gene/03-execution/records/11-phase-g8-gene-campaign-closeout-record-20260316.md`](../../../gene/03-execution/records/11-phase-g8-gene-campaign-closeout-record-20260316.md)
8. [`../../../gene/03-execution/records/14-phase-gx3-trend-level-context-refactor-record-20260317.md`](../../../gene/03-execution/records/14-phase-gx3-trend-level-context-refactor-record-20260317.md)
9. [`../../../gene/03-execution/records/15-phase-gx4-mainstream-countertrend-semantics-record-20260318.md`](../../../gene/03-execution/records/15-phase-gx4-mainstream-countertrend-semantics-record-20260318.md)
10. [`../../../gene/03-execution/records/18-phase-gx7-post-refactor-g4-g5-g6-revalidation-record-20260318.md`](../../../gene/03-execution/records/18-phase-gx7-post-refactor-g4-g5-g6-revalidation-record-20260318.md)

---

## 3. 当前 validated baseline

本轮冻结使用的已验证基线保持不变：

`legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`

本轮改变了：

`没有任何 runtime 行为`

本轮冻结的是：

`第一张合法的 Gene 单变量主线验证入场券`

---

## 4. 正式裁决

### 4.1 本轮唯一打开的 runtime 候选

`Phase 9A` 正式打开的唯一 Gene runtime 候选字段是：

`duration_percentile`

它在下一轮被允许的唯一角色是：

`negative filter only`

### 4.2 本轮明确不打开的字段

本轮保持 `shadow-only` 的字段：

1. `current_wave_age_band`
2. `mirror_gene_rank`
3. `primary_ruler_rank`
4. `support_rise_ratio`
5. `conditioning` buckets

本轮保持 `pending candidate` 的字段：

1. `wave_role`
2. `reversal_state`
3. `context_trend_direction_before`
4. `GX8 / three-level trend hierarchy` 后续字段

本轮保持 `forbidden as default runtime gate` 的对象：

1. composite `gene_score`

### 4.3 本轮明确禁止的组合

`Phase 9A` 正式禁止以下做法：

1. `duration_percentile + current_wave_age_band`
2. `duration_percentile + wave_role`
3. 任意 `mirror` 字段与 `duration_percentile` 打包首轮入场
4. 任意 `conditioning` 字段与 `duration_percentile` 打包首轮入场
5. 直接把 `duration_percentile` 升格成 `sizing overlay`
6. 直接把 `duration_percentile` 升格成 `exit modulation`

---

## 5. 本轮为什么这样裁决

本轮裁决逻辑已经被证据链写清：

1. `duration_percentile` 已被 `G4 + GX7` 共同写定为当前最硬的 `PRIMARY_RULER`
2. 它当前更像 `过热 / 衰竭 / 历史极端` 尺，因此先开 `negative filter` 最诚实
3. `current_wave_age_band` 是 `duration` 主尺的分带读法，第一轮一起开会双重计分
4. `mirror` 层必须保留双榜与宽度解释，不适合抢第一轮单字段 gate
5. `conditioning` 是形态条件层，不适合抢第一轮通用单变量 gate
6. `wave_role / reversal_state / context_trend_direction_before` 仍属于结构语义字段，不该跳过单独验证直接抢第一轮
7. `gene_score` 当前仍然只能保留为 `KEEP_COMPOSITE`，不能偷变默认 runtime 硬门

---

## 6. Phase 9A 完成后，什么是真的

现在正式为真的事情只有这些：

1. `Phase 9A` 已完成第一轮 Gene promoted subset freeze
2. `Gene` 仍然没有进入主线默认 runtime
3. `duration_percentile` 获得了第一张正式主线验证入场券
4. 这张入场券当前只允许写成 `negative filter only`
5. 其余 Gene 字段仍然必须留在 `shadow-only / pending / forbidden` 之内

现在仍然不是真的事情：

1. `Gene` 已经完成 runtime promotion
2. `Phase 9B` 已经跑完
3. 多字段 Gene 组合已经被允许
4. Gene-driven sizing / exit modulation 已经被打开

---

## 7. 下一步

`Phase 9A` 完成后，下一张最自然也最合法的卡是：

`Phase 9B / isolated duration_percentile validation`

也就是正式验证：

`如果只把 duration_percentile 作为负向过滤器接进主线，结果到底会不会更好。`
