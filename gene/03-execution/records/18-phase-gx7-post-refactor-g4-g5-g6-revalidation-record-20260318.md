# GX7 记录: 定义整改后的 G4 / G5 / G6 重审已完成

**状态**: `Completed`  
**日期**: `2026-03-18`

---

## 1. 本次重审范围

本次 `GX7` 只回答一个问题：

`在 GX4 / GX5 / GX6 已经把 mainstream-countertrend、2B window、1-2-3 three-condition 语义修正之后，G4 / G5 / G6 原来的正式统计结论是否仍然站得住。`

本次重审直接重跑对象：

1. `compute_gene(2026-02-24, 2026-02-24)`
2. `compute_gene_validation(2026-02-24)`
3. `compute_gene_mirror(2026-02-24)`
4. `compute_gene_conditioning(2026-02-24)`

主库对象：

`G:\EmotionQuant_data\emotionquant.duckdb`

---

## 2. 主库真实读数

### 2.1 重跑规模

1. `compute_gene_rows = 2,205,324`
2. `compute_gene_validation_rows = 4`
3. `compute_gene_mirror_rows = 32`
4. `compute_gene_conditioning_rows = 108`
5. `_meta_schema_version = 14`

### 2.2 G4 validation 读数

`sample_size = 3,974,334`

1. `duration_percentile`
   - `monotonicity_score = -0.012453`
   - `avg_daily_rank_corr = -0.015062`
   - `positive_daily_rank_corr_rate = 0.429719`
   - `decision_tag = PRIMARY_RULER`
2. `magnitude_percentile`
   - `monotonicity_score = -0.011385`
   - `avg_daily_rank_corr = -0.008421`
   - `positive_daily_rank_corr_rate = 0.464525`
   - `decision_tag = SUPPORTING_RULER`
3. `extreme_density_percentile`
   - `monotonicity_score = -0.005215`
   - `avg_daily_rank_corr = -0.012073`
   - `positive_daily_rank_corr_rate = 0.469880`
   - `decision_tag = SUPPORTING_RULER`
4. `gene_score`
   - `monotonicity_score = -0.015948`
   - `avg_daily_rank_corr = -0.016733`
   - `positive_daily_rank_corr_rate = 0.447122`
   - `decision_tag = KEEP_COMPOSITE`

### 2.3 G5 mirror 读数

市场层：

1. `entity_code = 000001.SH`
2. `current_wave_direction = DOWN`
3. `gene_score = 66.666667`
4. `primary_ruler_metric = duration_percentile`
5. `primary_ruler_value = 100.0`
6. `mirror_gene_rank = 1`
7. `primary_ruler_rank = 1`
8. `support_rise_ratio = 0.731823`
9. `support_strong_ratio = 0.065035`
10. `support_new_high_ratio = 0.066496`
11. `composite_decision_tag = KEEP_COMPOSITE`

行业层 `mirror_gene_rank` 前十：

1. `石油石化 / DOWN / gene_score = 77.777778 / mirror_gene_rank = 1 / primary_ruler_rank = 10`
2. `传媒 / DOWN / gene_score = 70.175439 / mirror_gene_rank = 2 / primary_ruler_rank = 23`
3. `食品饮料 / DOWN / gene_score = 68.000000 / mirror_gene_rank = 3 / primary_ruler_rank = 5`
4. `商贸零售 / DOWN / gene_score = 66.666667 / mirror_gene_rank = 4 / primary_ruler_rank = 6`
5. `机械设备 / DOWN / gene_score = 64.814815 / mirror_gene_rank = 5 / primary_ruler_rank = 1`

行业层 `primary_ruler_rank` 前十：

1. `机械设备 / DOWN / duration_percentile = 100.0 / primary_ruler_rank = 1 / mirror_gene_rank = 5`
2. `公用事业 / DOWN / duration_percentile = 94.736842 / primary_ruler_rank = 2 / mirror_gene_rank = 8`
3. `电子 / DOWN / duration_percentile = 88.0 / primary_ruler_rank = 3 / mirror_gene_rank = 11`
4. `美容护理 / DOWN / duration_percentile = 81.818182 / primary_ruler_rank = 4 / mirror_gene_rank = 12`
5. `银行 / DOWN / duration_percentile = 81.818182 / primary_ruler_rank = 4 / mirror_gene_rank = 12`

### 2.4 G6 conditioning 读数

pattern baseline：

1. `bof = 15107 / hit_rate = 0.582776 / avg_forward_return_pct = 3.369605`
2. `bpb = 62 / hit_rate = 0.403226 / avg_forward_return_pct = -1.569684`
3. `cpb = 16814 / hit_rate = 0.458071 / avg_forward_return_pct = 0.933428`
4. `pb = 19713 / hit_rate = 0.443870 / avg_forward_return_pct = 0.337060`
5. `tst = 23332 / hit_rate = 0.487999 / avg_forward_return_pct = 0.800565`

代表性 `BETTER` 条件：

1. `bof / streak_bucket = UP_1 / payoff_delta = +1.311795`
2. `bof / current_wave_direction = DOWN / payoff_delta = +0.327793`
3. `pb / current_wave_age_band = NORMAL / payoff_delta = +0.659794`
4. `pb / current_wave_direction = DOWN / payoff_delta = +0.553605`
5. `cpb / streak_bucket = UP_4P / payoff_delta = +0.627361`
6. `cpb / current_wave_age_band = UNSCALED / payoff_delta = +0.207320`
7. `tst / current_wave_magnitude_band = EXTREME / payoff_delta = +2.064805`
8. `tst / current_wave_magnitude_band = STRONG / payoff_delta = +1.513617`
9. `tst / streak_bucket = UP_2_3 / payoff_delta = +0.392585`

代表性 `WORSE` 条件：

1. `bof / current_wave_direction = UP / payoff_delta = -5.168286`
2. `bof / streak_bucket = DOWN_1 / payoff_delta = -4.086828`
3. `cpb / current_wave_magnitude_band = EXTREME / payoff_delta = -1.498231`
4. `cpb / current_wave_age_band = EXTREME / payoff_delta = -0.959705`
5. `cpb / latest_two_b_confirm_type = 2B_TOP / payoff_delta = -0.508318`
6. `pb / current_wave_direction = UP / payoff_delta = -0.117853`
7. `tst / streak_bucket = DOWN_2_3 / payoff_delta = -1.028775`

---

## 3. 重审结论

### 3.1 G4 结论保留

`duration_percentile = PRIMARY_RULER` 仍然成立。  
`magnitude_percentile / extreme_density_percentile = SUPPORTING_RULER` 仍然成立。  
`gene_score = KEEP_COMPOSITE` 仍然成立。

这说明定义整改后，第四战场最核心的 `self-history ruler` 结论没有翻车，仍然更像：

`历史极端 / 过热 / 衰竭尺`

而不是强 `continuation` 尺。

### 3.2 G5 结论保留

市场与行业镜像层仍然成立。  
同时保留 `mirror_gene_rank` 和 `primary_ruler_rank` 两张榜，仍然是必须的，不可偷并。

定义整改后行业排序有数值漂移，但没有出现“两个榜已经收敛成同一件事”的证据。  
所以 `G5` 的治理口径保持不变：

`镜像层成立，但单榜不成立。`

### 3.3 G6 结论保留

五形态条件层仍然成立，而且结构语义修正后并没有推翻旧结论。

当前仍然可以保留的主结论是：

1. `BOF` baseline 仍最强
2. `BOF / DOWN + UP_1` 仍是最值得打的组合之一
3. `PB` 仍然更偏向 `DOWN` 与 `NORMAL age`
4. `CPB` 仍然更偏向 `NONE / UNSCALED / UP_4P`
5. `TST` 仍然更像强波段中的支撑测试

`BPB` 样本仍然稀疏，所以继续维持 `sparse watch readout`，不升格。

### 3.4 这次重审没有触发新的 runtime promotion

`GX7` 只是重审定义整改后的统计层与治理层结论。  
本次没有证据支持：

1. 把 `Gene` 升成 runtime hard gate
2. 直接改写第二战场 trigger
3. 直接改写第三战场 sizing / exit
4. 重开 `MSS / IRS` 退役结论

---

## 4. 对 G4 / G5 / G6 旧结论的处理

1. `G4`
   - 处理：`保留`
   - 说明：主尺、辅助尺、复合尺的治理标签均未翻转
2. `G5`
   - 处理：`保留`
   - 说明：双榜并存仍有必要，市场/行业镜像未失效
3. `G6`
   - 处理：`保留并微修订`
   - 说明：数值有小幅漂移，但 pattern 环境结论不变

---

## 5. 结论

`GX7` 已完成。  
`GX4 / GX5 / GX6` 的定义整改并没有推翻第四战场原有的 `G4 / G5 / G6` 治理结论。

因此，第四战场 post-closeout targeted chain 目前已完成：

1. `GX3`
2. `GX4`
3. `GX5`
4. `GX6`
5. `GX7`

当前剩余口径应收成：

`Gene 已从“能跑的研究引擎”明显向“定义站得住的语义引擎”推进了一大步；统计层结论仍成立，但运行层身份仍保持 sidecar。`
