# G5 卡: 指数/行业/大盘镜像尺

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. 目标

把个股历史尺的对象语言镜像到指数、行业和大盘，形成市场层的历史趋势排序表。

---

## 2. 本卡范围

1. 复用 `G4` 已验证过的对象语言
2. 用指数数据做市场层历史尺
3. 用行业数据做板块层历史尺
4. 明确哪些辅助确认工具值得进入镜像层

---

## 3. 输入

1. `G4` 已冻结的个股历史尺口径
2. 指数与行业时间序列
3. 《专业投机原理》后半部的宽度、均线、相对强弱辅助材料

---

## 4. 输出

1. 市场层历史趋势排序表
2. 行业层历史趋势排序表
3. 镜像层字段合同或研究表
4. 对 `MSS / IRS` 的镜像改造边界说明

---

## 5. 完成标准

1. 不依赖旧 `MSS / IRS` 参数体系也能输出市场层历史尺
2. 个股对象语言在指数和行业上能基本成立
3. 辅助确认层仍是辅助，不篡位成核心定义
4. 产物能作为 `G7` 决策输入

---

## 6. 明确不做

1. 不直接复活旧 `MSS / IRS` 逻辑
2. 不把宽度、均线、成交量抬成第一层对象
3. 不在本卡讨论具体执行信号

---

## 7. 结案结论

本卡已完成。  
当前第四战场已经把 `G5` 所需的镜像层正式落到 `l3_gene_mirror`：

1. 市场层：
   - 使用 `l1_index_daily`
   - 当前主库第一版以 `000001.SH` 为市场镜像对象
   - 保留 `rise_ratio / strong_ratio / new_high_ratio` 作为辅助确认
2. 行业层：
   - 使用 `l2_industry_daily`
   - 以 `pct_chg` 复合出 `synthetic close-only` 价格对象
   - 当前先保留 `rise_ratio` 为稳定辅助字段
3. 镜像表固定同时暴露：
   - `mirror_gene_rank`
   - `primary_ruler_rank`
   - `composite_decision_tag`
   - `price_source_kind`

截至 `2026-02-24` 的主库真实读数表明：

1. `G4` 的 `duration_percentile = PRIMARY_RULER` 已正式镜像到市场层与行业层
2. 行业 `composite rank` 与 `primary_ruler rank` 明显不完全相同，不能偷简化成单榜
3. 当前可稳定进入镜像层的辅助确认工具，是市场/行业宽度比率而不是旧 `MSS / IRS` 语义包
4. `amount_vs_ma20 / return_20d / follow_through` 字段当前先保留为预留列，不提升为第一版稳定主辅助集

下一张主线卡应按顺序进入 `G6 / BOF-PB-CPB conditioning readout`。

---

## 8. 文档入口

1. 配套 record：[`records/08-phase-g5-market-industry-index-mirror-ruler-record-20260316.md`](records/08-phase-g5-market-industry-index-mirror-ruler-record-20260316.md)
2. 配套 evidence：[`evidence/08-phase-g5-market-industry-index-mirror-ruler-evidence-20260316.md`](evidence/08-phase-g5-market-industry-index-mirror-ruler-evidence-20260316.md)
