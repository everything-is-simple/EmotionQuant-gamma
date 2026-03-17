# GX4 / mainstream-countertrend semantics refactor
**状态**: `Planned`  
**日期**: `2026-03-17`  
**类型**: `post-closeout targeted hypothesis`  
**直接目标文件**: [`../../src/selector/gene.py`](../../src/selector/gene.py)

---

## 1. 目标

这张卡只回答一个问题：

`在已经把 trend_level 与 context proxy 诚实落盘之后，能否继续把 mainstream / countertrend 从“单层 major_trend 近似”修到“相对于上一级趋势的正式结构状态”？`

---

## 2. 为什么现在开这张卡

[`../../docs/spec/common/governance/gene-foundational-definition-freeze-20260317.md`](../../docs/spec/common/governance/gene-foundational-definition-freeze-20260317.md) 与
[`../../docs/spec/common/governance/gene-definition-gap-remediation-checklist-20260317.md`](../../docs/spec/common/governance/gene-definition-gap-remediation-checklist-20260317.md)
已经正式冻结了以下判断：

1. `trend_level` 是第四战场的一等基础概念
2. `mainstream / countertrend` 不属于独立对象，而是 `wave` 相对于上一级趋势的结构状态
3. 当前 [`../../src/selector/gene.py`](../../src/selector/gene.py) 里这层语义仍然只是 `INTERMEDIATE_MAJOR_TREND_PROXY`

所以这张卡不是再争论定义，而是把定义继续往代码里推进一步。

---

## 3. 范围

本卡允许修改：

1. [`../../src/selector/gene.py`](../../src/selector/gene.py)
2. [`../../src/data/store.py`](../../src/data/store.py)
3. [`../../tests/unit/selector/test_gene.py`](../../tests/unit/selector/test_gene.py)
4. 第四战场相关执行卡与 record

本卡明确不做：

1. 不重写 `2B` 时间窗
2. 不重写 `1-2-3` detector
3. 不直接改 `G4 / G5 / G6` 统计逻辑
4. 不把 Gene 接成 runtime hard gate

---

## 4. 交付物

本卡完成时应至少交付：

1. `mainstream / countertrend` 的判定来源被明确写成“相对于哪一层趋势”
2. `wave_role_basis` 不再只停留在 `INTERMEDIATE_MAJOR_TREND_PROXY`
3. `snapshot` 层能明确回答当前 active wave 的角色判定来自哪一层 context
4. schema 与单测同步更新

---

## 5. 验收标准

1. [`../../src/selector/gene.py`](../../src/selector/gene.py) 不再把 `wave_role` 伪装成“无参照层”的最终语义
2. `l3_gene_wave` 与 `l3_stock_gene` 能写出角色判定的层级参照信息
3. [`../../tests/unit/selector/test_gene.py`](../../tests/unit/selector/test_gene.py) 覆盖新语义
4. `preflight` 通过

---

## 6. 当前判断

这张卡是 `GX3` 之后最窄、最该先做的结构语义补丁。

一句话：

`先把 mainstream / countertrend 说诚实，再去动 2B 和 1-2-3。`
