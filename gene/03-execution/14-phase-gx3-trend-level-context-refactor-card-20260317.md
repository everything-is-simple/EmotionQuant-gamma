# GX3 / trend-level context refactor

**状态**: `Active`  
**日期**: `2026-03-17`  
**类型**: `post-closeout targeted hypothesis`  
**直接目标文件**: [`../../src/selector/gene.py`](../../src/selector/gene.py)

---

## 1. 目标

这张卡只回答一个问题：

`在不提前重写 2B / 1-2-3 语义的前提下，能否先把第四战场的 trend_level 与 context 语义正式落到 gene.py，并把当前单层 major_trend 口径降格为诚实的 intermediate proxy。`

---

## 2. 为什么现在开这张卡

[`../../docs/spec/common/governance/gene-foundational-definition-freeze-20260317.md`](../../docs/spec/common/governance/gene-foundational-definition-freeze-20260317.md) 已经正式冻结：

1. `trend_level` 是第四战场不可缺失的基础定义
2. `mainstream / countertrend` 必须相对于更高层趋势理解
3. 当前 [`../../src/selector/gene.py`](../../src/selector/gene.py) 仍然只有单层 `major_trend` 近似

所以这张卡不再讨论“定义是否需要”，而是先把最小诚实实现落下。

---

## 3. 范围

本卡允许修改：

1. [`../../src/selector/gene.py`](../../src/selector/gene.py)
2. [`../../src/data/store.py`](../../src/data/store.py)
3. [`../../tests/unit/selector/test_gene.py`](../../tests/unit/selector/test_gene.py)
4. 当前卡片与第四战场入口索引

本卡明确不做：

1. 不重写 `2B` 层级时间窗
2. 不重写 `1-2-3` 三条件 detector
3. 不新开 `G4 / G5 / G6` 统计口径
4. 不把 Gene 直接接成 runtime hard gate

---

## 4. 交付物

本卡完成时应至少交付：

1. `trend_level` 正式进入 Gene 落库字段
2. `wave_role` 的判定依据被明确写成 `intermediate proxy`
3. snapshot 层能明确回答当前 context 来自哪一层趋势
4. schema 与单测同步更新

---

## 5. 验收标准

1. [`../../src/selector/gene.py`](../../src/selector/gene.py) 不再把当前 context 语义伪装成“无层级最终定义”
2. `l3_gene_wave` 与 `l3_stock_gene` 能写出 `trend_level / context proxy` 相关字段
3. [`../../tests/unit/selector/test_gene.py`](../../tests/unit/selector/test_gene.py) 覆盖新字段
4. `preflight` 通过

---

## 6. 当前判断

这张卡是第四战场 closeout 之后的第一张 targeted hypothesis。  
它不是重开 `G0 ~ G8` 主线，也不是 `GX1 detector rewrite` 的替代品。

一句话：

`先把 trend_level 和 context 语义说诚实，再谈后续 detector 深修。`

---

## 7. 当前阶段文档入口

1. 配套 record：[`records/14-phase-gx3-trend-level-context-refactor-record-20260317.md`](records/14-phase-gx3-trend-level-context-refactor-record-20260317.md)
2. 第一阶段 evidence：[`evidence/14-phase-gx3-trend-level-context-refactor-evidence-20260317.md`](evidence/14-phase-gx3-trend-level-context-refactor-evidence-20260317.md)
