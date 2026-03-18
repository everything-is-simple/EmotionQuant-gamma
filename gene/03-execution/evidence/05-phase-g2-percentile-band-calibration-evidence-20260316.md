# G2 Evidence: 历史寿命分布与 65/95 校准主库读数

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. 证据来源

1. 配套 record：`records/05-phase-g2-percentile-band-calibration-record-20260316.md`
2. 主库：`G:\EmotionQuant_data\emotionquant.duckdb`
3. 截至日：`2026-02-24`
4. 本文件只整理 record 中已固化的分布带与阈值读数

---

## 2. 写入规模

1. `_meta_schema_version = 6`
2. `compute_gene()` 本轮真实写入：`1,854,141` 行
3. `l3_gene_distribution_eval = 10,948` 行
4. 覆盖 `5,474` 只股票
5. 每只股票固定输出 `magnitude_pct` 与 `duration_trade_days` 两条正式读数

---

## 3. 当日 band 分布

`2026-02-24` 当前波段分布：

1. `magnitude band`
   - `NORMAL = 4,574`
   - `STRONG = 731`
   - `EXTREME = 158`
   - `UNSCALED = 11`
2. `wave_age_band`
   - `STRONG = 3,154`
   - `NORMAL = 1,939`
   - `EXTREME = 370`
   - `UNSCALED = 11`

---

## 4. 自历史阈值中位数

1. `magnitude_pct`
   - `median P65 = 10.25%`
   - `median P95 = 21.50%`
2. `duration_trade_days`
   - `median P65 = 5.0`
   - `median P95 = 9.6`

---

## 5. 分布带解释力摘录

1. `magnitude`
   - `NORMAL continuation rate = 17.16%`
   - `STRONG continuation rate = 14.49%`
   - `EXTREME continuation rate = 14.70%`
   - `NORMAL median forward return = -4.35%`
   - `EXTREME median forward return = -7.47%`
2. `duration`
   - `NORMAL continuation rate = 15.15%`
   - `STRONG continuation rate = 16.12%`
   - `EXTREME continuation rate = 17.02%`

---

## 6. Evidence verdict

当前证据支持：

1. `P65 / P95` 已能稳定落库并形成正式 band 标签
2. `wave_age_band` 已具备主库真实分布，不再只是概念字段
3. `65 / 95` 当前应被解释为历史位置标签，而不是直接交易参数
4. `magnitude` 的 band 解释力仍明显强于 `duration`
