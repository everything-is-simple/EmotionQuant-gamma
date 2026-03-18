# G4 Evidence: 个股自历史标尺验证读数

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. 证据来源

1. 配套 record：`records/07-phase-g4-self-history-ruler-validation-record-20260316.md`
2. 主库：`G:\EmotionQuant_data\emotionquant.duckdb`
3. 截至日：`2026-02-24`
4. 本文件只整理 record 中已固化的 validation 读数

---

## 2. 写入规模

1. `_meta_schema_version = 8`
2. `compute_gene_validation()` 本轮真实写入：`4` 行
3. `sample_size = 3,974,334`

---

## 3. 核心 validation 读数

1. `duration_percentile`
   - `monotonicity_score = -0.011473`
   - `avg_daily_rank_corr = -0.015569`
   - `positive_daily_rank_corr_rate = 0.429719`
   - `decision_tag = PRIMARY_RULER`
2. `magnitude_percentile`
   - `monotonicity_score = -0.011651`
   - `avg_daily_rank_corr = -0.008349`
   - `positive_daily_rank_corr_rate = 0.465863`
   - `decision_tag = SUPPORTING_RULER`
3. `extreme_density_percentile`
   - `monotonicity_score = -0.003186`
   - `avg_daily_rank_corr = -0.010839`
   - `positive_daily_rank_corr_rate = 0.476573`
   - `decision_tag = SUPPORTING_RULER`
4. `gene_score`
   - `monotonicity_score = -0.014859`
   - `avg_daily_rank_corr = -0.016614`
   - `positive_daily_rank_corr_rate = 0.445783`
   - `decision_tag = KEEP_COMPOSITE`

---

## 4. top / bottom bucket 摘录

1. `duration_percentile`
   - `top_bucket_continuation_rate = 0.503520`
   - `bottom_bucket_continuation_rate = 0.503753`
   - `top_bucket_median_forward_return = 0.000000`
   - `bottom_bucket_median_forward_return = 0.088028`
2. `gene_score`
   - `top_bucket_continuation_rate = 0.502696`
   - `bottom_bucket_continuation_rate = 0.488544`
   - `top_bucket_median_forward_return = -0.158983`
   - `bottom_bucket_median_forward_return = -0.325733`

---

## 5. Evidence verdict

当前证据支持：

1. `duration_percentile` 是当前最硬的 `PRIMARY_RULER`
2. `gene_score` 仍可保留为 `KEEP_COMPOSITE`，但不能吹成强总尺
3. 第四战场当前更像“过热 / 衰竭 / 历史极端尺”，不是强 continuation 尺
