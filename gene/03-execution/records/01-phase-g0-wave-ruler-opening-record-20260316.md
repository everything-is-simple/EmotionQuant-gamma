# G0 记录: 历史波段标尺脚手架已完成

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. 本轮落地内容

1. 第四战场 `gene/` 已正式开线
2. 个股历史波段对象层术语已冻结
3. DuckDB 已补 `l3_stock_gene / l3_gene_wave / l3_gene_event`
4. `build_l3()` 已接入 `compute_gene()`
5. 已补最小单元测试与 builder 回归测试

---

## 2. 主库验收结果

本次验收针对当前执行库：

`G:\EmotionQuant_data\emotionquant.duckdb`

主线回填运行：

1. 命令：`python main.py build --layers l3 --end 2026-02-24`
2. 运行元数据：`build_dtt_v0_01_dtt_pattern_plus_irs_score_n20260316_t015528`
3. 结果：`SUCCESS`
4. schema version：`v5`

主库落表结果：

1. `l3_stock_gene`: `4,030,427` 行，`2023-01-03 -> 2026-02-24`
2. `l3_gene_wave`: `871,174` 行，`2023-01-05 -> 2026-02-11`
3. `l3_gene_event`: `216,062` 行，`2023-01-04 -> 2026-02-11`

---

## 3. 当前实现口径

1. 价格来源固定为 `l2_stock_adj_daily`
2. `pivot` 采用第一版 `5-bar confirmation scaffold`
3. `wave` 以相邻反向 `pivot` 形成
4. `event` 以新高/新低刷新与 `2B` 失败检测形成
5. `snapshot` 输出自历史与横截面两套标尺

---

## 4. 当前限制

1. 这不是最终趋势定义正典
2. 这不是交易信号模块
3. 这还没有进入 `MSS / IRS` 融合
4. 这还没有扩展到指数/行业层

---

## 5. 结论

`G0` 已从“代码落地”推进到“主库迁移与回填完成”，可以正式结案。  
下一张卡应按顺序进入 `G1` 的真实读数验证；当前这一环也已在本轮同步完成。

---

## 6. 文档入口

1. 配套 card：[`../01-phase-g0-wave-ruler-opening-card-20260316.md`](../01-phase-g0-wave-ruler-opening-card-20260316.md)
2. 配套 evidence：[`../evidence/01-phase-g0-wave-ruler-opening-evidence-20260316.md`](../evidence/01-phase-g0-wave-ruler-opening-evidence-20260316.md)
