# Phase 9E Record / book-aligned duration lifespan distribution rerun

**状态**: `Completed`  
**日期**: `2026-03-19`

---

## 1. 本轮问题

`在 GX10-GX12 整改已经改变 duration 参考面的前提下，按《专业投机原理》的书义把寿命轴收回到“长期趋势中的中级主要走势”，并用 quartile + average lifespan odds 重跑后，duration 轴还值不值得继续进入 Phase 9 runtime？`

---

## 2. 证据链

1. [`../17.8-phase-9e-duration-percentile-threshold-sweep-card-20260319.md`](../17.8-phase-9e-duration-percentile-threshold-sweep-card-20260319.md)
2. [`../../../docs/spec/v0.01-plus/evidence/phase9e_duration_lifespan_distribution_legacy_book_aligned_quartile_and_average_lifespan_odds_w20260105_20260224_t143518__phase9_duration_lifespan_distribution.json`](../../../docs/spec/v0.01-plus/evidence/phase9e_duration_lifespan_distribution_legacy_book_aligned_quartile_and_average_lifespan_odds_w20260105_20260224_t143518__phase9_duration_lifespan_distribution.json)
3. [`../17.9-phase-9f-frozen-combination-replay-card-20260319.md`](../17.9-phase-9f-frozen-combination-replay-card-20260319.md)

---

## 3. 本轮执行结果

### 3.1 执行窗口

1. 正式窗口：`2026-01-05` 到 `2026-02-24`
2. full-window paired trades：`13`
3. 实际 entry signal dates：`2026-01-09`、`2026-01-12`、`2026-01-29`、`2026-01-30`、`2026-02-03`、`2026-02-04`、`2026-02-05`、`2026-02-06`
4. 本轮 runner 已改为：
   `先回测，再仅按实际 entry signal dates 稀疏补 Gene snapshot`

### 3.2 Full-window 分布结果

1. `overall avg_pnl_pct = -0.5847%`
2. `overall win_rate = 46.15%`
3. `duration quartile counts = FIRST 0 / SECOND 0 / THIRD 0 / FOURTH 3 / UNSCALED 10`
4. `joint quartile counts = FIRST 1 / SECOND 1 / THIRD 1 / FOURTH 0 / UNSCALED 10`
5. `duration FOURTH_QUARTER avg_pnl_pct = -0.9745%`
6. `duration FOURTH_QUARTER win_rate = 33.33%`
7. `duration FOURTH_QUARTER avg_average_aged_prob = 0.6620`
8. `joint FOURTH_QUARTER trade_count = 0`

### 3.3 Split-window 结果

1. `front_half_window` 只有 `2` 笔 paired trades，且全部落在 `UNSCALED`
2. `back_half_window` 有 `11` 笔 paired trades，其中 `duration FOURTH_QUARTER = 3`
3. 因此当前 late-life quartile 的负向迹象存在，但样本仍偏薄，尤其 joint fourth-quarter 没有成交样本

---

## 4. 本轮正式结论

本轮 formal digest 已明确裁定：

`duration_should_return_to_sidecar_only_distribution_reading`

也就是：

1. 这轮 remediated quartile surface 不能 truthfully 支撑把 duration 继续作为 runtime guard
2. 当前 late-life quartile 负向迹象可以保留为 sidecar distribution reading
3. 历史 `p65 / p95` isolated rounds 只保留为 `legacy archive`
4. forward work 不再消费旧 tail-threshold 口径

---

## 5. 对下游的约束

1. `17.9 / Phase 9F` 不得继续把 `duration_percentile` 带进 frozen combination replay
2. `Phase 9C` 冻结的含 duration 组合仍保留为历史 frozen surface，但当前不具备 truthful replay 资格
3. 若后续仍想重开 `17.9`，必须先做新的 reruling，明确删去含 duration 组合或明确继续 defer
4. 当前 truthful runtime 继续保持：
   `legacy_bof_baseline + FIXED_NOTIONAL_CONTROL + FULL_EXIT_CONTROL + Gene sidecar only`

---

## 6. 一句话收口

`17.8` 已经把书义寿命分布真正跑出来了，但它给出的答案不是“找到一个新的 duration runtime 阈值”，而是“当前 duration 只能回到 sidecar-only，不能再拿旧 isolated winner 身份直接进入组合 replay”。`
