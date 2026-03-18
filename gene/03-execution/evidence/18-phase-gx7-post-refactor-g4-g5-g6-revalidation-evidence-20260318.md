# GX7 Evidence / post-refactor G4-G5-G6 revalidation

**日期**: `2026-03-18`  
**主库**: `G:\EmotionQuant_data\emotionquant.duckdb`  
**重审窗口**: `2026-02-24`

---

## 1. 重跑命令口径

本次 `GX7` 使用同一主库按以下顺序重跑：

1. `compute_gene(store, 2026-02-24, 2026-02-24)`
2. `compute_gene_validation(store, 2026-02-24)`
3. `compute_gene_mirror(store, 2026-02-24)`
4. `compute_gene_conditioning(store, 2026-02-24)`

---

## 2. 写入规模

1. `compute_gene_rows = 2,205,324`
2. `compute_gene_validation_rows = 4`
3. `compute_gene_mirror_rows = 32`
4. `compute_gene_conditioning_rows = 108`
5. `_meta_schema_version = 14`

---

## 3. G4 证据摘录

1. `duration_percentile / PRIMARY_RULER`
   - `monotonicity_score = -0.012453`
   - `avg_daily_rank_corr = -0.015062`
2. `magnitude_percentile / SUPPORTING_RULER`
   - `monotonicity_score = -0.011385`
   - `avg_daily_rank_corr = -0.008421`
3. `extreme_density_percentile / SUPPORTING_RULER`
   - `monotonicity_score = -0.005215`
   - `avg_daily_rank_corr = -0.012073`
4. `gene_score / KEEP_COMPOSITE`
   - `monotonicity_score = -0.015948`
   - `avg_daily_rank_corr = -0.016733`

---

## 4. G5 证据摘录

市场层：

1. `000001.SH / DOWN / gene_score = 66.666667`
2. `primary_ruler_metric = duration_percentile`
3. `primary_ruler_value = 100.0`
4. `mirror_gene_rank = 1`
5. `primary_ruler_rank = 1`

行业层仍可观察到双榜分离：

1. `石油石化 = mirror_gene_rank 1 / primary_ruler_rank 10`
2. `机械设备 = primary_ruler_rank 1 / mirror_gene_rank 5`
3. `公用事业 = primary_ruler_rank 2 / mirror_gene_rank 8`

---

## 5. G6 证据摘录

baseline：

1. `bof = 15107 / avg_forward_return_pct = 3.369605`
2. `bpb = 62 / avg_forward_return_pct = -1.569684`
3. `cpb = 16814 / avg_forward_return_pct = 0.933428`
4. `pb = 19713 / avg_forward_return_pct = 0.337060`
5. `tst = 23332 / avg_forward_return_pct = 0.800565`

代表性 better：

1. `bof / UP_1 / payoff_delta = +1.311795`
2. `pb / NORMAL age / payoff_delta = +0.659794`
3. `cpb / UP_4P / payoff_delta = +0.627361`
4. `tst / EXTREME magnitude / payoff_delta = +2.064805`

代表性 worse：

1. `bof / current_wave_direction = UP / payoff_delta = -5.168286`
2. `cpb / EXTREME magnitude / payoff_delta = -1.498231`
3. `tst / DOWN_2_3 / payoff_delta = -1.028775`

---

## 6. Evidence verdict

`GX4 / GX5 / GX6` 的语义整改没有推翻 `G4 / G5 / G6` 的治理结论。  
本次 evidence 支持：

1. `G4 = keep`
2. `G5 = keep`
3. `G6 = keep_with_minor_numeric_drift`
