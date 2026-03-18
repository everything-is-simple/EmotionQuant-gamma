# Phase 9A Evidence / Gene promoted subset freeze

**状态**: `Completed`  
**日期**: `2026-03-18`  
**对象**: `Phase 9A / Gene promoted subset freeze`

---

## 1. 本轮要回答什么

本轮 `Phase 9A` 只回答一个问题：

`在 Phase 8 已经清掉活跃数据合同残留之后，第四战场里最小、最诚实、最适合先进入主线隔离验证的 Gene 单变量到底是哪一个？`

---

## 2. 本轮证据链

### 2.1 数据地基已经够干净，可以开隔离验证

来自 [`../../../docs/spec/v0.01-plus/records/v0.01-plus-phase-8-data-contract-residual-audit-20260318.md`](../../../docs/spec/v0.01-plus/records/v0.01-plus-phase-8-data-contract-residual-audit-20260318.md) 的正式结论是：

1. `Phase 7` 没有留下隐藏的 runtime split-brain
2. 活跃数据合同继续以 `industry_member / l1_industry_member` 与本地 `up_limit / down_limit` 推导为准
3. 当前系统已经 `truthful enough for isolated runtime experiments`

这说明 `Phase 9A` 可以打开，但必须继续遵守“单变量、隔离、不可偷带”的纪律。

### 2.2 当前 validated baseline 没有变

来自：

1. [`../../../docs/spec/v0.01-plus/records/v0.01-plus-phase-6a-promoted-subset-freeze-20260317.md`](../../../docs/spec/v0.01-plus/records/v0.01-plus-phase-6a-promoted-subset-freeze-20260317.md)
2. [`../../../docs/reference/operations/current-mainline-operating-runbook-20260317.md`](../../../docs/reference/operations/current-mainline-operating-runbook-20260317.md)

当前主线已验证基线仍然是：

`legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`

因此 `Phase 9A` 做的不是“把 Gene 口头升格进 runtime”，而是为下一轮隔离验证冻出唯一合法入口。

### 2.3 `duration_percentile` 已经被 G4 和 GX7 共同写成最硬主尺

来自：

1. [`../../../gene/03-execution/records/07-phase-g4-self-history-ruler-validation-record-20260316.md`](../../../gene/03-execution/records/07-phase-g4-self-history-ruler-validation-record-20260316.md)
2. [`../../../gene/03-execution/records/18-phase-gx7-post-refactor-g4-g5-g6-revalidation-record-20260318.md`](../../../gene/03-execution/records/18-phase-gx7-post-refactor-g4-g5-g6-revalidation-record-20260318.md)

`GX7` 重审后的正式读数仍然是：

1. `duration_percentile`
   - `monotonicity_score = -0.012453`
   - `avg_daily_rank_corr = -0.015062`
   - `positive_daily_rank_corr_rate = 0.429719`
   - `decision_tag = PRIMARY_RULER`
2. `magnitude_percentile`
   - `decision_tag = SUPPORTING_RULER`
3. `extreme_density_percentile`
   - `decision_tag = SUPPORTING_RULER`
4. `gene_score`
   - `decision_tag = KEEP_COMPOSITE`

这条证据链已经足够支持：

`duration_percentile` 是当前 Gene 面里最适合先被单独拿出来做 runtime 隔离验证的字段。

### 2.4 `duration_percentile` 当前更像“过热/衰竭尺”，因此先开 negative filter 比先开 sizing/exit 更诚实

来自 `G4` 与 `GX7` 的共同结论：

1. 当前 Gene 个股主尺整体更像 `历史极端 / 过热 / 衰竭` 读数
2. 它不是已经被证明的强 `continuation` 尺
3. 因此第一轮最诚实的 runtime 角色不是：
   - `sizing overlay`
   - `exit modulation`
   - `full hard gate`
4. 而是：
   - `negative filter only`

也就是说，`Phase 9A` 冻的是“先验证它能不能拦掉不该做的票”，不是“先假设它会带来更积极的交易强化”。

### 2.5 `current_wave_age_band` 不能和 `duration_percentile` 一起开

来自 [`../../../src/selector/gene.py`](../../../src/selector/gene.py) 当前正式实现：

1. `current_wave_age_band` 由 `age_trade_days` 对 `duration_thresholds` 做分带得到
2. 它和 `current_wave_duration_band` 当前使用同一套 `duration_thresholds`
3. 它本质上是 `duration` 这条主尺的分带读法，不是独立一条新主尺

因此本轮如果同时开：

1. `duration_percentile`
2. `current_wave_age_band`

就会形成同一原始观测的重复计分和重复验证，不符合当前单变量纪律。

### 2.6 `mirror` 相关字段不适合做第一轮主线候选

来自：

1. [`../../../gene/03-execution/records/08-phase-g5-market-industry-index-mirror-ruler-record-20260316.md`](../../../gene/03-execution/records/08-phase-g5-market-industry-index-mirror-ruler-record-20260316.md)
2. [`../../../gene/03-execution/records/18-phase-gx7-post-refactor-g4-g5-g6-revalidation-record-20260318.md`](../../../gene/03-execution/records/18-phase-gx7-post-refactor-g4-g5-g6-revalidation-record-20260318.md)

`G5 / GX7` 已经正式写定：

1. `mirror_gene_rank` 和 `primary_ruler_rank` 必须双榜并存
2. 二者不能偷并成单榜
3. `support_rise_ratio` 这类宽度比率更像环境解释层，不是单一硬 gate

因此 `mirror_gene_rank / primary_ruler_rank / support_rise_ratio` 当前都不适合拿来当第一轮单字段 runtime 候选。

### 2.7 `conditioning` 不适合做第一轮主线候选

来自：

1. [`../../../gene/03-execution/records/09-phase-g6-bof-pb-cpb-conditioning-record-20260316.md`](../../../gene/03-execution/records/09-phase-g6-bof-pb-cpb-conditioning-record-20260316.md)
2. [`../../../gene/03-execution/records/18-phase-gx7-post-refactor-g4-g5-g6-revalidation-record-20260318.md`](../../../gene/03-execution/records/18-phase-gx7-post-refactor-g4-g5-g6-revalidation-record-20260318.md)

`G6` 写清楚的是：

1. `conditioning` 是 pattern-conditioned 环境解释层
2. 它的更优/更差读数依赖具体触发器、方向、年龄带、幅度带和 streak bucket
3. 它不是一个天然的、与 `BOF` 入口解耦的通用单字段 gate

因此 `conditioning` 不能作为 `Phase 9A` 第一张主线候选入场券。

### 2.8 `wave_role / reversal_state / context_trend_direction_before` 现在还不适合抢第一轮

来自：

1. [`../../../gene/03-execution/records/14-phase-gx3-trend-level-context-refactor-record-20260317.md`](../../../gene/03-execution/records/14-phase-gx3-trend-level-context-refactor-record-20260317.md)
2. [`../../../gene/03-execution/records/15-phase-gx4-mainstream-countertrend-semantics-record-20260318.md`](../../../gene/03-execution/records/15-phase-gx4-mainstream-countertrend-semantics-record-20260318.md)
3. [`../../../gene/03-execution/19-phase-gx8-three-level-trend-hierarchy-card-20260318.md`](../../../gene/03-execution/19-phase-gx8-three-level-trend-hierarchy-card-20260318.md)
4. [`../../../src/selector/gene.py`](../../../src/selector/gene.py)

当前正式状态是：

1. `context_trend_direction_before` 是父趋势参照字段
2. `wave_role` 刚被修正为相对于父趋势方向判定的结构角色
3. `reversal_state` 是给下游消费的压缩语义，不是独立统计主尺
4. `GX8 / three-level trend hierarchy` 仍然是单独待推进的 targeted hypothesis

因此这些字段当前更适合留在 `pending candidate`，而不是抢第一轮最窄 runtime 候选。

### 2.9 `gene_score` 不能在这一轮偷变成默认硬 gate

来自：

1. [`../../../gene/03-execution/records/07-phase-g4-self-history-ruler-validation-record-20260316.md`](../../../gene/03-execution/records/07-phase-g4-self-history-ruler-validation-record-20260316.md)
2. [`../../../gene/03-execution/records/11-phase-g8-gene-campaign-closeout-record-20260316.md`](../../../gene/03-execution/records/11-phase-g8-gene-campaign-closeout-record-20260316.md)

`gene_score` 当前正式标签仍然是：

`KEEP_COMPOSITE`

这意味着它还可以作为汇总视图保留，但不诚实的做法是：

1. 把它直接升格成默认硬 filter
2. 把它包装成比 `duration_percentile` 更适合先入 runtime 的候选

---

## 3. 本轮证据支持的冻结矩阵

| Gene 字段 | Phase 9A 位置 | 证据理由 |
|---|---|---|
| `duration_percentile` | `single-variable candidate` | `G4 + GX7` 共同写定 `PRIMARY_RULER`；最适合先做 `negative filter only` |
| `current_wave_age_band` | `shadow-only` | `duration` 主尺的分带读法；本轮一起开会 double-count |
| `mirror_gene_rank` | `shadow-only` | `G5` 写定双榜不可偷并；不是第一轮单字段 gate |
| `primary_ruler_rank` | `shadow-only` | 同上；镜像层仍属环境/对照层 |
| `support_rise_ratio` | `shadow-only` | 宽度解释层，不是最小单字段 runtime 候选 |
| `conditioning` buckets | `shadow-only` | `G6` 是形态条件层，不是通用第一候选 |
| `gene_score` | `forbidden as default hard gate` | 当前只够 `KEEP_COMPOSITE`，不能偷变默认硬 gate |
| `wave_role` | `pending candidate` | `GX4` 刚修语义；结构字段不应抢第一轮 |
| `reversal_state` | `pending candidate` | 下游压缩语义，尚未单独验证成主尺 |
| `context_trend_direction_before` | `pending candidate` | 父趋势参照字段，不是最小 first runtime candidate |
| `GX8` 新字段 | `pending candidate` | `three-level trend hierarchy` 尚未作为第一战场正式吸收 |

---

## 4. Evidence verdict

本轮证据只支持一个结论：

`Phase 9A 只能先给 duration_percentile 一张单变量主线验证入场券。`

而且这张入场券当前只允许写成：

`negative filter only`

本轮证据**不支持**：

1. `duration_percentile + current_wave_age_band` 打包进入
2. `duration_percentile + wave_role` 打包进入
3. 任意 `mirror` 字段直接升格为第一轮 runtime gate
4. 任意 `conditioning` 字段直接升格为第一轮 runtime gate
5. `gene_score` 直接升格为默认硬 filter
6. 直接跳过 `Phase 9B` 去做组合验证
