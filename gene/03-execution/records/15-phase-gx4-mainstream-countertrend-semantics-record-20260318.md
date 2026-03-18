# GX4 Record: mainstream-countertrend semantics refactor
**状态**: `Completed`  
**日期**: `2026-03-18`

---

## 1. 记录目的

这份 record 用来正式记录 `GX4 / mainstream-countertrend semantics refactor` 已经把什么定义债落到了代码里，以及这一步明确没有处理什么。

它只回答：

1. `mainstream / countertrend` 现在相对于哪一层语义判定
2. `wave ledger` 与 `snapshot` 是否已经共享同一条角色判定口径
3. 这一步做完后，第四战场还剩哪些定义尾账

---

## 2. 本阶段已完成的内容

### 2.1 `wave_role` 不再跟着本 wave 自己翻转后洗白

当前 [`../../../src/selector/gene.py`](../../../src/selector/gene.py) 已改成：

`wave_role` 先相对于 `context_trend_direction_before` 判定，
再单独更新 `trend_direction_after / context_trend_direction_after`。

这一步的意义是：

当某个反向 wave 自己把 `trend_direction_after` 翻转时，
它不会再因为“翻完之后方向一样”而被回写成 `MAINSTREAM`。

也就是说：

`wave_role` 现在回答的是“它相对于进入本 wave 之前已确认的父趋势，属于主流还是逆流”，
而不是“它最后把趋势翻成什么方向”。

### 2.2 `wave_role_basis` 已从旧 proxy 文案更新

当前正式落盘值已经从：

`INTERMEDIATE_MAJOR_TREND_PROXY`

更新为：

`INTERMEDIATE_PARENT_CONTEXT_DIRECTION`

这不是宣称三层 `trend_level` 已经完成，而是把当前真实语义写诚实：

当前 `MAINSTREAM / COUNTERTREND` 仍然只建立在 `INTERMEDIATE` 层，
但它已经明确是“相对于父趋势参照方向”判定，不再是假装成无参照层的最终答案。

### 2.3 `snapshot` 与 `wave ledger` 已共用同一条判定规则

`current_wave_role` 与 `current_wave_role_basis` 现在和 `l3_gene_wave.wave_role` 共享同一条父趋势参照逻辑。

这意味着：

1. `completed wave` 的结构角色
2. `active wave` 的当日快照角色

不再各写各的近似口径。

### 2.4 单测已覆盖新语义

[`../../../tests/unit/selector/test_gene.py`](../../../tests/unit/selector/test_gene.py) 已同步到新口径：

1. 断言 `wave_role_basis / current_wave_role_basis = INTERMEDIATE_PARENT_CONTEXT_DIRECTION`
2. 断言样本里同时出现 `MAINSTREAM` 与 `COUNTERTREND`

---

## 3. 本阶段明确没有处理的内容

`GX4` 刻意没有处理以下问题：

1. `trend_level` 的三层并存
2. `2B` 的层级时间窗
3. `1-2-3` 的三条件 detector
4. `trendline` 对象化
5. `G4 / G5 / G6` 的 post-refactor 重跑

---

## 4. 验证结果

本阶段验证已通过：

1. `python -m pytest tests/unit/selector/test_gene.py -q`
   - `4 passed`
2. `python -m py_compile src/selector/gene.py tests/unit/selector/test_gene.py`
   - 通过

---

## 5. 本阶段结论

`GX4` 的正式结论不是“第四战场的主流/逆流定义已经彻底完成”，而是：

1. `mainstream / countertrend` 已经从“单层 major_trend proxy”推进到“相对于父趋势参照方向”的诚实语义
2. `wave` 与 `snapshot` 两层的角色判定口径已经统一
3. 第四战场接下来最该继续推进的，已经自然切到 `GX5 / 2B window semantics`

一句话：

`GX4` 完成的是“角色判定去伪装”，不是“第四战场定义债全部还清”。`

---

## 6. 文档入口

1. 配套 card：[`../15-phase-gx4-mainstream-countertrend-semantics-card-20260317.md`](../15-phase-gx4-mainstream-countertrend-semantics-card-20260317.md)
2. 配套 evidence：[`../evidence/15-phase-gx4-mainstream-countertrend-semantics-evidence-20260318.md`](../evidence/15-phase-gx4-mainstream-countertrend-semantics-evidence-20260318.md)
