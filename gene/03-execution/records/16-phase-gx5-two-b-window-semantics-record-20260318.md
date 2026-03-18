# GX5 Record: 2B window semantics refactor
**状态**: `Completed`  
**日期**: `2026-03-18`

---

## 1. 记录目的

这份 record 用来正式记录 `GX5 / 2B window semantics refactor` 把什么从旧 `3 bar` 近似推进成了层级相关语义，以及这一步刻意没有碰什么。

它只回答：

1. `2B` 的确认窗现在如何相对于 `trend_level` 定义
2. 这层语义是否已经落到 `event / wave / snapshot`
3. 这一步之后第四战场的定义尾账还剩哪些

---

## 2. 本阶段已完成的内容

### 2.1 `2B` 不再硬写成固定 `3 bar`

当前 [`../../../src/selector/gene.py`](../../../src/selector/gene.py) 已去掉旧的固定 `TWO_B_CONFIRMATION_BARS = 3` 口径，
改成显式的层级窗口 spec：

1. `SHORT -> 1 bar`
2. `INTERMEDIATE -> 3-5 bar`
3. `LONG -> 7-10 bar`

由于当前 detector 仍是机械扫描“最多几根 bar”，本阶段先采用区间上界：

1. `SHORT -> 1`
2. `INTERMEDIATE -> 5`
3. `LONG -> 10`

同时保留原始语义文案：

1. `SHORT_WITHIN_1_BAR`
2. `INTERMEDIATE_WITHIN_3_TO_5_BARS`
3. `LONG_WITHIN_7_TO_10_BARS`

### 2.2 当前 `INTERMEDIATE` 层已正式使用 `3-5 bar` 语义

第四战场当前 `trend_level` 仍只正式落到 `INTERMEDIATE`，
所以这一步的实质效果是：

`2B` 从旧 `3 bar` 近似推进到了 `INTERMEDIATE 3-5 bar` 语义，检测上界为 `5`

这比继续假装“3 bar 就是所有层级的永久真理”更诚实。

### 2.3 `2B` 窗口 spec 已落到三层落盘对象

当前新增并已写入的字段包括：

1. `l3_gene_event.confirmation_window_bars`
2. `l3_gene_event.confirmation_window_basis`
3. `l3_gene_wave.two_b_window_bars`
4. `l3_gene_wave.two_b_window_basis`
5. `l3_stock_gene.current_two_b_window_bars`
6. `l3_stock_gene.current_two_b_window_basis`

这意味着下游不再只能看到“有一个 2B 发生了”，
还可以看到“这次 2B 是按什么层级时间窗语义确认的”。

### 2.4 schema 与单测已同步

当前 schema 已升到：

`v13`

[`../../../tests/unit/selector/test_gene.py`](../../../tests/unit/selector/test_gene.py) 已同步验证：

1. `wave / snapshot` 的窗口字段存在且为 `5`
2. basis 文案为 `INTERMEDIATE_WITHIN_3_TO_5_BARS`
3. `2B_TOP / 2B_BOTTOM` 结构事件也会带上对应窗口 spec

---

## 3. 本阶段明确没有处理的内容

`GX5` 刻意没有处理：

1. `trend_level` 的三层并存实现
2. `1-2-3` 的三条件 detector
3. `trendline` 对象化
4. `G4 / G5 / G6` 的 post-refactor 重跑
5. 把 `2B` 直接升格成 runtime hard gate

---

## 4. 验证结果

本阶段验证已通过：

1. `python -m pytest tests/unit/selector/test_gene.py -q`
   - `4 passed`
2. `python -m py_compile src/selector/gene.py src/data/store.py tests/unit/selector/test_gene.py`
   - 通过

---

## 5. 本阶段结论

`GX5` 的正式结论不是“2B 语义已经最终完成”，而是：

1. `2B` 现在已经从固定 magic number 改成了层级相关确认窗
2. 当前 active 口径已诚实写成 `INTERMEDIATE 3-5 bar`
3. 第四战场下一步最该继续推进的，已经自然切到 `GX6 / 1-2-3 three-condition refactor`

一句话：

`GX5` 完成的是“2B 时间窗去绝对化”，不是“2B 整体定义终局版”。`

---

## 6. 文档入口

1. 配套 card：[`../16-phase-gx5-two-b-window-semantics-refactor-card-20260317.md`](../16-phase-gx5-two-b-window-semantics-refactor-card-20260317.md)
2. 配套 evidence：[`../evidence/16-phase-gx5-two-b-window-semantics-evidence-20260318.md`](../evidence/16-phase-gx5-two-b-window-semantics-evidence-20260318.md)
