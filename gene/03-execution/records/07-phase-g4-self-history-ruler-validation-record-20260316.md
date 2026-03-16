# G4 记录: 个股自历史标尺验证已完成

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. 本次实现内容

1. 将 `Store` schema 正式升级到 `v8`
2. 新增 `l3_gene_validation_eval` 作为第四战场验证汇总表
3. 新增 `compute_gene_validation(store, calc_date)`，对以下四个读数做统一验证：
   - `gene_score`
   - `current_wave_magnitude_percentile`
   - `current_wave_duration_percentile`
   - `current_wave_extreme_density_percentile`
4. 将 `compute_gene()` 正式接上 `G4 validation`，使 `l3_stock_gene` 产出后自动写入验证层
5. 为 `G5 / G6 / G7` 预留正式决策标签：
   - `PRIMARY_RULER`
   - `SUPPORTING_RULER`
   - `WEAK_COMPONENT`
   - `KEEP_COMPOSITE`
   - `SUMMARY_ONLY`
   - `DOWNGRADE_COMPONENT_PANEL`

---

## 2. 主库真实读数

本次读取对象：

`G:\EmotionQuant_data\emotionquant.duckdb`

截至：

`2026-02-24`

主库 `G4` 结果：

1. `_meta_schema_version = 8`
2. `compute_gene_validation()` 本轮真实写入：`4` 行
3. `l3_gene_validation_eval.sample_size`：`3,974,334`

`l3_gene_validation_eval` 正式读数：

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

`top / bottom bucket` 读数摘要：

1. `duration_percentile`
   - `top_bucket_continuation_rate = 0.503520`
   - `bottom_bucket_continuation_rate = 0.503753`
   - `top_bucket_median_forward_return = 0.000000`
   - `bottom_bucket_median_forward_return = 0.088028`
2. `magnitude_percentile`
   - `top_bucket_continuation_rate = 0.504694`
   - `bottom_bucket_continuation_rate = 0.503888`
   - `top_bucket_median_forward_return = -0.269784`
   - `bottom_bucket_median_forward_return = 0.000000`
3. `extreme_density_percentile`
   - `top_bucket_continuation_rate = 0.504249`
   - `bottom_bucket_continuation_rate = 0.524228`
   - `top_bucket_median_forward_return = 0.000000`
   - `bottom_bucket_median_forward_return = 0.140771`
4. `gene_score`
   - `top_bucket_continuation_rate = 0.502696`
   - `bottom_bucket_continuation_rate = 0.488544`
   - `top_bucket_median_forward_return = -0.158983`
   - `bottom_bucket_median_forward_return = -0.325733`

---

## 3. 第一版 G4 结论

### 3.1 当前三子因子里，`duration_percentile` 是最硬的主尺

按本轮 `strength_score = |monotonicity| + |avg_daily_rank_corr|` 口径，
`duration_percentile` 是三子因子里当前最硬的 `PRIMARY_RULER`。

这说明若只保留一个最直接的个股自历史读数，当前应优先看：

`当前这段波是否已经在该股自历史里走得过久`

而不是只看波幅大小。

### 3.2 `gene_score` 当前还能保留，但不能吹成强总尺

`gene_score` 当前没有弱到需要立即降级为 `SUMMARY_ONLY` 或 `DOWNGRADE_COMPONENT_PANEL`。
按当前规则，它仍可保留为 `KEEP_COMPOSITE`。

但这不等于它已经成为强解释力总尺。
本轮主库读数里，四个指标的：

1. 单调性绝对值都不高
2. 日度 rank-corr 绝对值也偏弱
3. top / bottom continuation rate 大多只在 `0.50` 左右

因此 `gene_score` 当前更适合作为“汇总视图”，不宜被误读为高置信度单指标决策尺。

### 3.3 第四战场当前更像“过热/衰竭尺”，不是强 continuation 尺

本轮四个指标的 `monotonicity_score` 与 `avg_daily_rank_corr` 都偏负。
这说明高分位/高总分并没有表现出更强的顺势 continuation，
反而更接近“走得越极端，后续越容易转弱或回吐”的弱负相关口径。

因此当前第四战场的正式对外读法应收口为：

1. 它能回答“当前波段在该股自历史里有多极端”
2. 它暂时不能回答“越高分位就越应该顺势追”
3. 它更适合作为过热、衰竭、历史极端度的背景尺

### 3.4 当前还不需要抢开 `GX1`

`G4` 这轮主库结果虽然表明解释力偏弱，但没有证明当前检测器已出现阻塞级一致性故障。

因此当前不打开 `GX1 / targeted detector rewrite`。
主线仍按顺序进入 `G5 / market-industry-index mirror ruler`。

---

## 4. 当前边界

这份记录证明的是：

1. `G4` 已能把第四战场正式扩到自历史验证层
2. 当前已能对 `gene_score` 与三子因子给出正式 `decision_tag`
3. 第四战场当前已有足够依据，把主读数收口为“个股自历史极端/过热/衰竭尺”

这份记录暂时不声称：

1. `G5` 的指数、行业、大盘镜像尺已经完成
2. `G6` 的 `BOF / PB / CPB` 条件层已经完成回灌
3. 当前第四战场已足以单独改写实时交易或直接退役 `MSS / IRS`

---

## 5. 结论

`G4` 已完成。  
第四战场主线当前已从 `G0 / G1 / G2 / G3` 正式推进到 `G4` 结案，下一张卡应按顺序进入 `G5 / market-industry-index mirror ruler`。
