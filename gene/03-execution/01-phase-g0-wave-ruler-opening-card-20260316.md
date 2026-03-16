# G0 开场卡: 历史波段标尺脚手架

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. 目标

在仓库内正式开辟第四战场，并落下第一版可运行脚手架。

---

## 2. 本卡范围

1. 新建 `gene/` 研究线入口
2. 冻结第四战场术语
3. 补 `DuckDB` 三张正式表合同
4. 把 `src/selector/gene.py` 接进 `build_l3()`
5. 为价格波段标尺补最小单元测试

---

## 3. 输出物

1. `gene/README.md`
2. `01-stock-historical-trend-ruler-charter-20260316.md`
3. `01-price-only-wave-ruler-spec-20260316.md`
4. `l3_stock_gene / l3_gene_wave / l3_gene_event`
5. `tests/unit/selector/test_gene.py`

---

## 4. 完成标准

1. `Store` 能创建并迁移 `Gene` 表结构
2. `build_l3()` 能独立推进 `Gene` 窗口
3. `compute_gene()` 能回写三张表
4. 测试能证明快照、波段账本和事件账本都落库
5. 主库完成一次真实迁移与回填

---

## 5. 结案结论

本卡已完成。  
`2026-03-16` 已通过主线入口将 `Gene` 跑入当前执行库 `G:\EmotionQuant_data\emotionquant.duckdb`，主库已具备：

1. `l3_stock_gene`
2. `l3_gene_wave`
3. `l3_gene_event`
4. schema version `v5`

---

## 6. 明确不做

1. 不把 `gene` 接进实时选股过滤
2. 不在本卡里改造 `MSS / IRS`
3. 不在本卡里引入指数与行业版标尺
