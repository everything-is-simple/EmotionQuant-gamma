# GX6 Record: 1-2-3 three-condition refactor
**状态**: `Completed`  
**日期**: `2026-03-18`

---

## 1. 记录目的

这份 record 用来正式记录 `GX6 / 1-2-3 three-condition refactor` 已把什么从旧“三段波近似标签”推进成了三条件确认语法，以及这一步明确没有处理什么。

它只回答：

1. `123_STEP1 / STEP2 / STEP3` 现在分别对应什么条件
2. `turn_confirm_type` 是否已经建立在三条件齐备之上
3. 这一步之后第四战场还剩哪些定义尾账

---

## 2. 本阶段已完成的内容

### 2.1 `123_STEP1 / STEP2 / STEP3` 已显式映射到三条件

当前 [`../../../src/selector/gene.py`](../../../src/selector/gene.py) 已把旧的 `123_STEP1 / STEP2 / STEP3`
从单纯结果标签推进成了带条件语义的结构事件：

1. `123_STEP1 -> trendline_break`
2. `123_STEP2 -> failed_extreme_test`
3. `123_STEP3 -> prior_pivot_breach`

这一步的意义是：

下游不再只能看见“有三个 step 发生了”，
还可以审计每一个 step 到底是在扮演哪条确认条件。

### 2.2 `turn_confirm_type` 现在建立在三条件齐备之上

当前 detector 仍然通过三段相邻 completed wave 来近似承载 `1-2-3`，
但代码已经不再把这件事表述成“任意 A-B-C 三段图形”。

当前正式口径是：

1. 第一段反向波提供 `trendline_break`
2. 第二段回测需要满足 `failed_extreme_test`
3. 第三段必须满足 `prior_pivot_breach`

只有三条件齐备，才会写出：

1. `CONFIRMED_TURN_UP`
2. `CONFIRMED_TURN_DOWN`

### 2.3 条件字段已落到 `wave / event`

当前新增并已写入的字段包括：

1. `l3_gene_wave.turn_step1_condition`
2. `l3_gene_wave.turn_step2_condition`
3. `l3_gene_wave.turn_step3_condition`
4. `l3_gene_event.structure_condition`

这意味着：

`1-2-3` 现在不再只存在“最后结论”，而是能回溯到每一步条件。

### 2.4 schema 与单测已同步

当前 schema 已升到：

`v14`

[`../../../tests/unit/selector/test_gene.py`](../../../tests/unit/selector/test_gene.py) 已同步验证：

1. `turn_step1/2/3_condition` 的值分别正确
2. `123_STEP1 / STEP2 / STEP3` 结构事件带有对应 `structure_condition`
3. `CONFIRMED_TURN_UP / DOWN` 仍能正常产出

---

## 3. 本阶段明确没有处理的内容

`GX6` 刻意没有处理：

1. `trendline` 对象化
2. 三条件先后顺序的所有变体
3. `G4 / G5 / G6` 的 post-refactor 重跑
4. 把 `1-2-3` 直接升格成交易触发器

---

## 4. 验证结果

本阶段验证已通过：

1. `python -m pytest tests/unit/selector/test_gene.py -q`
   - `4 passed`
2. `python -m py_compile src/selector/gene.py src/data/store.py tests/unit/selector/test_gene.py`
   - 通过

---

## 5. 本阶段结论

`GX6` 的正式结论不是“1-2-3 语义已经完全终局化”，而是：

1. `1-2-3` 已经从“结果标签”推进成“可审计的三条件确认语法”
2. 当前 detector 仍是 completed wave 近似承载，不是假装 trendline 对象已经完整存在
3. 第四战场下一步最该继续推进的，已经自然切到 `GX7 / post-refactor G4-G5-G6 revalidation`

一句话：

`GX6` 完成的是“1-2-3 条件拆账”，不是“趋势线理论的全对象化终局版”。`
