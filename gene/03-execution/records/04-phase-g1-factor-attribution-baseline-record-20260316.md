# G1 记录: 三子因子解释力基线已完成

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. 本次实现内容

1. 为第四战场增加 `l3_gene_factor_eval` 研究表
2. 把 `G1` 最小基线口径接入 `compute_gene()`
3. 固定 `10` 个交易日 forward horizon
4. 固定 `SELF_HISTORY_PERCENTILE` 样本口径
5. 固定 `ALL + 五档分箱` 的解释力输出格式

---

## 2. 主库真实读数

本次读取对象：

`G:\EmotionQuant_data\emotionquant.duckdb`

截至：

`2026-02-24`

主库 `G1` 结果：

1. `l3_gene_factor_eval`: `18` 行
2. `completed wave` 样本量：`870,190`
3. 每个因子均具备 `ALL + 五档分箱`

`ALL` 行读数：

1. `magnitude`: `monotonicity_score = -0.1426`
2. `duration`: `monotonicity_score = -0.0174`
3. `extreme_density`: `monotonicity_score = -0.0104`

---

## 3. 第一版排序结论

### 3.1 最强因子

`magnitude` 明显最强，而且是反向解释力最强。

分箱读数表现为：

1. `P0_20` continuation rate = `19.85%`
2. `P80_100` continuation rate = `14.20%`
3. `P0_20` median forward return = `-3.36%`
4. `P80_100` median forward return = `-6.73%`

也就是说，已完成波段越大，后续 `10` 交易日继续顺畅推进的概率越低，衰竭倾向越强。

### 3.2 次级因子

`duration` 与 `extreme_density` 当前都远弱于 `magnitude`。

1. `duration` 有轻微负向单调性，但幅度很弱
2. `extreme_density` 的分箱差异存在，但稳定性不足
3. 当前没有足够证据把二三名彻底定死

---

## 4. 当前边界

这份记录证明的是：

1. `G1` 基线已能在主库稳定落表
2. 三子因子已能在真实样本上做第一版排序
3. `magnitude` 已可确认为当前核心子因子

这份记录暂时不声称：

1. `duration` 与 `extreme_density` 的最终次序已经定案
2. `gene_score` 已经完成重加权
3. `BOF / PB / CPB` 已经被条件层优化

---

## 5. 结论

`G1` 已经从“基线可写入”推进到“主库真实读数可解释”，可以正式结案。  
下一张卡应按顺序进入 `G2`：历史寿命分布与 `65 / 95` 校准。

---

## 6. 文档入口

1. 配套 card：[`../03-phase-g1-factor-attribution-baseline-card-20260316.md`](../03-phase-g1-factor-attribution-baseline-card-20260316.md)
2. 配套 evidence：[`../evidence/03-phase-g1-factor-attribution-baseline-evidence-20260316.md`](../evidence/03-phase-g1-factor-attribution-baseline-evidence-20260316.md)
