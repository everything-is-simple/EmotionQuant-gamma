# GX6 / 1-2-3 three-condition refactor
**状态**: `Planned`  
**日期**: `2026-03-17`  
**类型**: `post-closeout targeted hypothesis`  
**直接目标文件**: [`../../src/selector/gene.py`](../../src/selector/gene.py)

---

## 1. 目标

这张卡只回答一个问题：

`在 trend_level、mainstream/countertrend、2B 语义逐步落稳之后，能否把 1-2-3 从“三段波近似标签”修成“三条件确认语法”？`

---

## 2. 为什么现在开这张卡

[`../../docs/spec/common/governance/gene-foundational-definition-freeze-20260317.md`](../../docs/spec/common/governance/gene-foundational-definition-freeze-20260317.md) 已经正式冻结：

1. `1-2-3` 不是任意三段波
2. `1-2-3` 应被理解为趋势改变的三条件确认法
3. 三个条件分别是：
   - `trendline_break`
   - `failed_extreme_test`
   - `prior_pivot_breach`

[`../../docs/spec/common/governance/gene-definition-gap-remediation-checklist-20260317.md`](../../docs/spec/common/governance/gene-definition-gap-remediation-checklist-20260317.md) 也已经把这项整改列为 `P1`。

所以这张卡的任务不是发明新结构，而是把当前 `123_STEP1 / STEP2 / STEP3` 从结果标签改回条件标签。

---

## 3. 范围

本卡允许修改：

1. [`../../src/selector/gene.py`](../../src/selector/gene.py)
2. [`../../src/data/store.py`](../../src/data/store.py)
3. [`../../tests/unit/selector/test_gene.py`](../../tests/unit/selector/test_gene.py)
4. 第四战场相关执行卡与 record

本卡明确不做：

1. 不重写 `pivot` 机械确认法
2. 不直接改 `G4 / G5 / G6` 统计逻辑
3. 不把 `1-2-3` 直接升格成交易触发器
4. 不把 Gene 接成 runtime hard gate

---

## 4. 交付物

本卡完成时应至少交付：

1. `123_STEP1 / STEP2 / STEP3` 被明确映射到三条件语义
2. `turn_confirm_type` 不再只依赖三段波近似
3. 必要时在落盘层补出三条件的独立记录字段
4. schema 与单测同步更新

---

## 5. 验收标准

1. [`../../src/selector/gene.py`](../../src/selector/gene.py) 不再把 `1-2-3` 伪装成“任意 A-B-C 波段结构”
2. `1-2-3` 的三个条件能够被独立追溯与审计
3. [`../../tests/unit/selector/test_gene.py`](../../tests/unit/selector/test_gene.py) 覆盖新语义
4. `preflight` 通过

---

## 6. 当前判断

`1-2-3` 在第四战场里属于第二层“转折确认语法”，不是第一层本体定义，也不是第三层交易触发语法。

一句话：

`先把 1-2-3 还原成三条件确认法，再决定它如何服务结构层、条件层和后续重验证。`
