# GX3 Record: trend-level context refactor
**状态**: `Active`  
**日期**: `2026-03-17`

---

## 1. 记录目的

这份 record 用来正式记录 `GX3 / trend-level context refactor` 第一阶段已经落下了什么，哪些问题还没有被本卡处理。

它只回答：

1. `trend_level + context proxy` 目前已经怎样进入 `gene.py`
2. schema 和单测已经补到了哪一步
3. 当前仍然保留了哪些定义缺口

---

## 2. 本阶段已完成的内容

### 2.1 `trend_level` 已正式进入落盘字段

当前第一阶段已经把 `trend_level` 正式写入：

1. `l3_gene_wave`
2. `l3_stock_gene`

并且显式写成：

`INTERMEDIATE`

这一步的意义不是宣称三层趋势已经做完，而是先承认“趋势有层级”，并把当前代码的真实口径诚实写出来。

### 2.2 `major_trend` 已被降格为 intermediate proxy

当前代码不再把单层 `major_trend` 伪装成无层级最终定义，而是正式承认为：

`INTERMEDIATE_MAJOR_TREND_PROXY`

### 2.3 context 相关字段已补齐

当前新增或正式落盘的上下文字段包括：

1. `context_trend_level`
2. `context_trend_direction_before`
3. `context_trend_direction_after`
4. `current_context_trend_level`
5. `current_context_trend_direction`
6. `wave_role_basis`
7. `current_wave_role_basis`

### 2.4 schema 与单测已同步

当前 schema 已升到：

`v11`

配套单测已覆盖新字段存在性和当前 proxy 语义。

---

## 3. 本阶段明确没有处理的内容

本卡第一阶段刻意没有碰以下问题：

1. `2B` 的层级化时间窗
2. `1-2-3` 的三条件 detector
3. `trendline` 对象化
4. `SHORT / LONG` 两个趋势层级的正式构造
5. `G4 / G5 / G6` 统计口径重跑

---

## 4. 本阶段结论

`GX3` 第一阶段的正式结论不是“第四战场趋势定义已完成”，而是：

1. 当前代码已经不再掩盖自己的层级缺口
2. `trend_level` 已从治理定义进入正式 schema 与实现
3. `mainstream / countertrend` 目前仍只是 `intermediate proxy`

一句话：

`这一步完成的是语义诚实化，不是最终语义完工。`

---

## 5. 后续直接承接项

`GX3` 之后最直接的后续项仍然固定为：

1. `trend_level + mainstream / countertrend` 深化
2. `2B window semantics refactor`
3. `1-2-3 three-condition refactor`

---

## 6. 当前阶段文档入口

1. 配套 card：[`../14-phase-gx3-trend-level-context-refactor-card-20260317.md`](../14-phase-gx3-trend-level-context-refactor-card-20260317.md)
2. 第一阶段 evidence：[`../evidence/14-phase-gx3-trend-level-context-refactor-evidence-20260317.md`](../evidence/14-phase-gx3-trend-level-context-refactor-evidence-20260317.md)
