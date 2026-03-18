# G5 Evidence: 市场与行业镜像层主库读数

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. 证据来源

1. 配套 record：`records/08-phase-g5-market-industry-index-mirror-ruler-record-20260316.md`
2. 主库：`G:\EmotionQuant_data\emotionquant.duckdb`
3. 截至日：`2026-02-24`
4. 本文件只整理 record 中已固化的镜像层读数

---

## 2. 写入规模

1. `_meta_schema_version = 9`
2. `compute_gene_mirror()` 本轮真实写入：`32` 行
3. `MARKET = 1` 行
4. `INDUSTRY = 31` 行

---

## 3. 市场层镜像读数

1. `entity_code = 000001.SH`
2. `current_wave_direction = DOWN`
3. `gene_score = 65.517241`
4. `primary_ruler_metric = duration_percentile`
5. `primary_ruler_value = 100.0`
6. `mirror_gene_rank = 1`
7. `support_rise_ratio = 0.731823`
8. `support_strong_ratio = 0.065035`
9. `support_new_high_ratio = 0.066496`
10. `composite_decision_tag = KEEP_COMPOSITE`

---

## 4. 行业层双榜分离证据

`composite rank` 前列：

1. `石油石化 / DOWN / gene_score = 77.192982`
2. `传媒 / DOWN / gene_score = 73.684211`
3. `商贸零售 / DOWN / gene_score = 66.666667`

`primary_ruler_rank` 前列：

1. `机械设备 / duration_percentile = 100.000000`
2. `公用事业 / duration_percentile = 94.736842`
3. `电子 / duration_percentile = 88.000000`

---

## 5. 辅助确认字段证据

1. `support_rise_ratio`：`MARKET / INDUSTRY` 均已稳定可读
2. `support_strong_ratio / support_new_high_ratio`：当前仅 `MARKET` 稳定可读
3. `support_amount_vs_ma20 / support_return_20d / support_follow_through`：当前仍为 `NULL`

---

## 6. Evidence verdict

当前证据支持：

1. `G5` 已形成市场层与行业层正式镜像入口
2. `mirror_gene_rank` 与 `primary_ruler_rank` 必须并存，不能偷并成单榜
3. 第一版稳定辅助确认是宽度比率，而不是旧 `MSS / IRS` 语义包
