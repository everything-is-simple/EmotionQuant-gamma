# G5 记录: 指数/行业/大盘镜像尺已完成

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. 本次实现内容

1. 将 `Store` schema 正式升级到 `v9`
2. 新增 `l3_gene_mirror` 作为第四战场镜像层正式表
3. 新增 `compute_gene_mirror(store, calc_date)`，把 `G4` 已冻结的对象语言镜像到：
   - 市场层 `MARKET`
   - 行业层 `INDUSTRY`
4. 第一版镜像口径正式固定为：
   - 市场层使用 `l1_index_daily` 的原生 OHLC
   - 行业层使用 `l2_industry_daily.pct_chg` 复合出的 `synthetic close-only` 价格对象
5. 将 `G4` 验证结论同步带入镜像层：
   - `primary_ruler_metric`
   - `primary_ruler_value`
   - `primary_ruler_rank`
   - `composite_decision_tag`
6. 将以下辅助确认字段纳入镜像层，但明确不升格为第一层对象：
   - `support_rise_ratio`
   - `support_strong_ratio`
   - `support_new_high_ratio`
   - `support_amount_vs_ma20`
   - `support_return_5d / support_return_20d`
   - `support_follow_through`

---

## 2. 主库真实读数

本次读取对象：

`G:\EmotionQuant_data\emotionquant.duckdb`

截至：

`2026-02-24`

主库 `G5` 结果：

1. `_meta_schema_version = 9`
2. `compute_gene_mirror()` 本轮真实写入：`32` 行
3. 其中：
   - `MARKET`: `1` 行
   - `INDUSTRY`: `31` 行

市场层镜像读数：

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

行业层 `composite rank` 前十：

1. `石油石化` / `DOWN` / `gene_score = 77.192982`
2. `传媒` / `DOWN` / `gene_score = 73.684211`
3. `商贸零售` / `DOWN` / `gene_score = 66.666667`
4. `食品饮料` / `DOWN` / `gene_score = 66.666667`
5. `煤炭` / `UP` / `gene_score = 65.217391`
6. `机械设备` / `DOWN` / `gene_score = 64.814815`
7. `钢铁` / `UP` / `gene_score = 63.333333`
8. `公用事业` / `DOWN` / `gene_score = 61.403509`
9. `基础化工` / `UP` / `gene_score = 61.111111`
10. `医药生物` / `DOWN` / `gene_score = 60.000000`

行业层 `primary_ruler_rank` 前十：

1. `机械设备` / `duration_percentile = 100.000000`
2. `公用事业` / `duration_percentile = 94.736842`
3. `电子` / `duration_percentile = 88.000000`
4. `美容护理` / `duration_percentile = 81.818182`
5. `银行` / `duration_percentile = 81.818182`
6. `食品饮料` / `duration_percentile = 80.769231`
7. `钢铁` / `duration_percentile = 80.000000`
8. `交通运输` / `duration_percentile = 79.166667`
9. `商贸零售` / `duration_percentile = 79.166667`
10. `汽车` / `duration_percentile = 77.272727`

辅助确认字段当前主库可用性：

1. `support_rise_ratio`：`MARKET / INDUSTRY` 当前均有正式读数
2. `support_strong_ratio / support_new_high_ratio`：当前仅 `MARKET` 稳定可用
3. `support_amount_vs_ma20 / support_return_20d / support_follow_through`：当前主库仍为 `NULL`，只保留为预留列

---

## 3. 第一版 G5 结论

### 3.1 市场层与行业层已经有了正式镜像表，但镜像口径必须分两种价格源

第一版 `G5` 不是强行假装市场层和行业层都拥有同样的数据质量。

当前正式口径是：

1. 市场层：`l1_index_daily` 原生 OHLC
2. 行业层：`l2_industry_daily.pct_chg` 复合出的 `synthetic close-only`

这意味着 `G5` 已经完成“对象语言镜像”，但也明确保留了数据源分层，不伪装成同质输入。

### 3.2 因为 `G4` 主尺是 `duration`，所以 `G5` 不能只给一张混合榜

当前 `G4` 已正式写定 `duration_percentile = PRIMARY_RULER`。
因此 `G5` 第一版必须同时保留两套排序：

1. `mirror_gene_rank`
2. `primary_ruler_rank`

主库结果已经表明这两张榜不完全相同。  
例如：

1. `石油石化` 是当前 `composite rank` 第一
2. `机械设备` 则是当前 `duration primary-ruler rank` 第一

这说明镜像层如果只保留一张排序表，会把“总尺”和“主尺”混在一起，导致后续 `G7` 决策失真。

### 3.3 第一版真正稳定进入镜像层的辅助确认，是宽度比率，不是旧语义包

截至 `2026-02-24` 的主库现状里：

1. `support_rise_ratio` 已在市场层与行业层稳定可读
2. 市场层的 `support_strong_ratio / support_new_high_ratio` 也已稳定可读
3. `support_amount_vs_ma20 / support_return_20d / support_follow_through` 当前仍未形成稳定供数

因此第一版 `G5` 的正式结论是：

1. 宽度比率可以进入镜像层做辅助确认
2. 旧 `MSS / IRS` 语义包仍然不能直接借尸还魂
3. 当前为空的辅助字段只能保留为预留列，不能冒充稳定判读输入

### 3.4 当前还不需要抢开 `GX2`

`G5` 已经把镜像层正式落到：

`l3_gene_mirror`

当前没有出现必须集中迁移旧表、旧脚本或旧文档入口的阻塞级重构压力。  
因此 `GX2 / targeted migration package` 继续保持关闭。

---

## 4. 当前边界

这份记录证明的是：

1. `G5` 已能把第四战场对象语言正式镜像到市场层和行业层
2. 当前镜像层已经能同时输出 `composite rank` 与 `primary_ruler rank`
3. 第一版稳定辅助确认集已收口到宽度比率，而不是旧 `MSS / IRS` 语义包

这份记录暂时不声称：

1. 当前镜像层已经足以直接替代旧 `MSS / IRS`
2. `G6` 的 `BOF / PB / CPB` 条件层已经完成回灌
3. 当前所有行业辅助字段已经全部具备正式稳定供数

---

## 5. 结论

`G5` 已完成。  
第四战场主线当前已从 `G0 / G1 / G2 / G3 / G4` 正式推进到 `G5` 结案，下一张卡应按顺序进入 `G6 / BOF-PB-CPB conditioning readout`。

---

## 6. 文档入口

1. 配套 card：[`../08-phase-g5-market-industry-index-mirror-ruler-card-20260316.md`](../08-phase-g5-market-industry-index-mirror-ruler-card-20260316.md)
2. 配套 evidence：[`../evidence/08-phase-g5-market-industry-index-mirror-ruler-evidence-20260316.md`](../evidence/08-phase-g5-market-industry-index-mirror-ruler-evidence-20260316.md)
