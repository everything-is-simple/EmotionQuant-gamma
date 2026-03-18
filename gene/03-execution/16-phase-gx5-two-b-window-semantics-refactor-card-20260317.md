# GX5 / 2B window semantics refactor
**状态**: `Completed`  
**日期**: `2026-03-17`  
**类型**: `post-closeout targeted hypothesis`  
**直接目标文件**: [`../../src/selector/gene.py`](../../src/selector/gene.py)

---

## 1. 目标

这张卡只回答一个问题：

`在 trend_level 与 context 语义逐步落稳之后，能否把 2B 从“固定 3 bar 的失败极值近似”修成“层级相关的失败极值确认语法”？`

---

## 2. 为什么现在开这张卡

[`../../docs/spec/common/governance/gene-foundational-definition-freeze-20260317.md`](../../docs/spec/common/governance/gene-foundational-definition-freeze-20260317.md) 已经正式冻结：

1. `2B` 不是神奇预测器，而是失败性新高/新低事件
2. `2B` 的确认时间窗与趋势层级相关
3. 当前 [`../../src/selector/gene.py`](../../src/selector/gene.py) 里的 `TWO_B_CONFIRMATION_BARS = 3` 只能算中期近似

[`../../docs/spec/common/governance/gene-definition-gap-remediation-checklist-20260317.md`](../../docs/spec/common/governance/gene-definition-gap-remediation-checklist-20260317.md) 也已经把这项整改列为 `P1`。

所以这张卡的任务不是重新发明 `2B`，而是把当前固定窗口语义改成诚实的层级语义。

---

## 3. 范围

本卡允许修改：

1. [`../../src/selector/gene.py`](../../src/selector/gene.py)
2. [`../../src/data/store.py`](../../src/data/store.py)
3. [`../../tests/unit/selector/test_gene.py`](../../tests/unit/selector/test_gene.py)
4. 第四战场相关执行卡与 record

本卡明确不做：

1. 不重写 `1-2-3` detector
2. 不直接改 `G4 / G5 / G6` 统计逻辑
3. 不把 `2B` 直接升格成 runtime hard gate
4. 不把 `2B` 偷写成交易触发器定义

---

## 4. 交付物

本卡完成时应至少交付：

1. `2B` 确认时间窗不再只表现为固定常量
2. `2B` 的判定来源能明确回答“相对于哪一层趋势”
3. 必要时在落盘层补出 `2B` 时间窗或确认基础说明字段
4. schema 与单测同步更新

---

## 5. 验收标准

1. [`../../src/selector/gene.py`](../../src/selector/gene.py) 不再把 `3 bar` 伪装成所有层级的永久真理
2. `2B_TOP / 2B_BOTTOM` 的事件生成逻辑可以追溯到层级相关语义
3. [`../../tests/unit/selector/test_gene.py`](../../tests/unit/selector/test_gene.py) 覆盖新语义
4. `preflight` 通过

---

## 6. 当前判断

`2B` 在第四战场里属于第二层“转折确认语法”，不是第一层本体定义，也不是第三层交易触发语法。

一句话：

`先让 2B 的确认窗口服从趋势层级，再谈它在结构层和条件层里怎样被使用。`

---

## 7. 完成结果

`GX5` 已完成本卡原定目标：

1. `2B` 检测不再硬写成固定 `3 bar`
2. 当前 `INTERMEDIATE` 层正式改成 `3-5 bar` 语义，检测时显式采用上界 `5`
3. `2B` 时间窗 spec 已落到 `event / wave / snapshot` 三层
4. schema 与单测已同步到新口径

配套 record：
[`records/16-phase-gx5-two-b-window-semantics-record-20260318.md`](records/16-phase-gx5-two-b-window-semantics-record-20260318.md)

配套 evidence：
[`evidence/16-phase-gx5-two-b-window-semantics-evidence-20260318.md`](evidence/16-phase-gx5-two-b-window-semantics-evidence-20260318.md)
