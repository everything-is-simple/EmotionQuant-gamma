# GX16 Record / 平均寿命赔率面接入

**状态**: `Completed`  
**日期**: `2026-03-19`

---

## 1. 本轮回答的问题

`图 26-1 与 341 ~ 350 页的平均寿命框架，能否变成 Gene 里的正式数据合同，而不是只停留在理论附录。`

---

## 2. 书义落点

本轮把书里的算式收口成中性对象：

1. `remaining_prob`
2. `aged_prob`
3. `remaining_vs_aged_odds`
4. `aged_vs_remaining_odds`

其中：

1. 对 `MAINSTREAM` 波段，`aged_prob` 更接近主趋势段进入高龄区的风险
2. 对 `COUNTERTREND` 波段，`aged_prob` 更接近修正段接近尾声、主趋势恢复的概率

---

## 3. 代码落点

本轮实际改动：

1. [`../../../src/selector/gene.py`](../../../src/selector/gene.py)
2. [`../../../src/data/store.py`](../../../src/data/store.py)
3. [`../../../tests/unit/selector/test_gene.py`](../../../tests/unit/selector/test_gene.py)

核心结果：

1. `Store` schema version `18 -> 19`
2. `l3_stock_gene` 新增平均寿命赔率字段
3. `l3_gene_wave` 新增平均寿命赔率字段
4. `l3_gene_distribution_eval` 新增 metric-level remaining/aged 与 average odds 字段

---

## 4. 验证

本轮验证为：

1. `python -m py_compile src/selector/gene.py src/data/store.py tests/unit/selector/test_gene.py`
2. `python -m pytest tests/unit/selector/test_gene.py -q`

结果：

1. `py_compile` 通过
2. `5 passed`

---

## 5. 下游影响

这轮完成后，`GX13` 与 `17.8` 的 truthful rerun surface 又向前推进了一步：

1. 不再只有 quartile band
2. 还多了 average lifespan / odds 这一层风险老化读数

因此后续重跑应继续消费：

1. quartile distribution
2. joint lifespan percentile
3. average lifespan odds
