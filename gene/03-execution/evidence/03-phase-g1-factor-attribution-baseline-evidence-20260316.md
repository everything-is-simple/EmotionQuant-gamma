# G1 Evidence: 三子因子解释力基线主库读数

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. 证据来源

1. 配套 record：`records/04-phase-g1-factor-attribution-baseline-record-20260316.md`
2. 主库：`G:\EmotionQuant_data\emotionquant.duckdb`
3. 截至日：`2026-02-24`
4. 本文件只整理 record 中已固化的主库读数与排序证据

---

## 2. 基线写入规模

1. `l3_gene_factor_eval = 18` 行
2. `completed wave sample_size = 870,190`
3. 三个因子都具备 `ALL + 五档分箱`

---

## 3. ALL 行核心读数

1. `magnitude`
   - `monotonicity_score = -0.1426`
2. `duration`
   - `monotonicity_score = -0.0174`
3. `extreme_density`
   - `monotonicity_score = -0.0104`

---

## 4. 分箱差异证据

`magnitude` 的分箱差异最明显：

1. `P0_20 continuation rate = 19.85%`
2. `P80_100 continuation rate = 14.20%`
3. `P0_20 median forward return = -3.36%`
4. `P80_100 median forward return = -6.73%`

这说明已完成波段越大，后续 `10` 交易日越偏向衰竭而不是继续顺畅推进。

---

## 5. Evidence verdict

当前证据支持：

1. `magnitude` 是 `G1` 第一版最强子因子
2. `duration / extreme_density` 目前只可视为次级候选，不足以压过 `magnitude`
3. 第四战场当前更接近“极端后衰竭”读法，而不是“幅度越大越该追”
