# 第四战场定义差距整改清单

**状态**: `Active`  
**日期**: `2026-03-17`  
**适用范围**: `src/selector/gene.py / gene / docs/spec/common`  
**文件定位**: `第四战场从“定义冻结”走向“代码语义整改”的执行清单`

---

## 1. 目的

这份清单不重写第四战场定义。  
定义已经在 [`gene-foundational-definition-freeze-20260317.md`](./gene-foundational-definition-freeze-20260317.md) 冻结。

这份清单只回答：

1. 当前 [`gene.py`](../../../../src/selector/gene.py) 和冻结定义差在哪里
2. 这些差距应按什么顺序整改
3. 每一项整改大致会影响哪些函数、哪些字段、哪些下游结论

---

## 2. 整改总原则

1. 先补定义对象，再修统计层
2. 先修 `trend_level / structure semantics`，再修 `band / score / conditioning`
3. 不允许为了保住既有统计读数，反向篡改冻结定义
4. 每一项整改都必须说明对 `G4 / G5 / G6` 的影响范围

---

## 3. 差距总表

## 3.1 Gap A: 缺正式 `trend_level`

**冻结定义**

第四战场必须承认趋势层级。

**当前实现**

[`gene.py`](../../../../src/selector/gene.py) 只有单层 `major_trend` 语义。

**整改目标**

1. 引入正式 `trend_level` 术语与枚举
2. 允许 `wave / event / snapshot` 挂接趋势层级
3. 明确当前第一版若只实现中期层，也要在 schema 和命名上留下层级位置

**直接影响区域**

1. `trend` 相关常量区
2. `_assign_wave_trend_context()`
3. `wave / event / snapshot` 输出字段

**风险**

会影响 `MAINSTREAM / COUNTERTREND` 定义、`2B` 时间窗解释、`mirror` 与 `conditioning` 的标签语义。

**优先级**

`P0`

---

## 3.2 Gap B: `MAINSTREAM / COUNTERTREND` 仍是单层近似

**冻结定义**

主流/逆流必须相对于更高一层趋势判定。

**当前实现**

当前仅按单层 `major_trend` 与 `wave.direction` 比较。

**整改目标**

1. 明确“相对于哪一层趋势”的判定来源
2. 避免把局部噪声、正常回调与真正逆流混成一类
3. 在落库层保留“判定基准层级”

**直接影响区域**

1. `_assign_wave_trend_context()`
2. snapshot 中的 reversal/watch 语义
3. `conditioning` 中对 `MAINSTREAM / COUNTERTREND` 的使用

**优先级**

`P0`

---

## 3.3 Gap C: `2B` 时间窗固定为 `3` bar

**冻结定义**

`2B` 是层级相关的失败极值事件；时间窗不能永远固定。

**当前实现**

`TWO_B_CONFIRMATION_BARS = 3`

**整改目标**

1. 把 `2B` 时间窗从固定常量改成“层级相关口径”
2. 第一版即使只支持中期层，也要把语义从“固定真理”改成“中期默认值”
3. 为短期/长期预留扩展位置

**直接影响区域**

1. 常量区
2. 极值候选与失败确认逻辑
3. `2B_TOP / 2B_BOTTOM` 事件生成

**优先级**

`P1`

---

## 3.4 Gap D: `1-2-3` 被压成三段波近似

**冻结定义**

`1-2-3` 是三条件确认法：

1. `trendline_break`
2. `failed_extreme_test`
3. `prior_pivot_breach`

**当前实现**

主要用 `wave_a / wave_b / wave_c` 的 A-B-C 波段结构近似。

**整改目标**

1. 把 `123_STEP1 / STEP2 / STEP3` 从“结果标签”改回“条件标签”
2. 让三条件可被独立记录、组合确认
3. 明确 detector 里哪些是结构前置，哪些是真正确认

**直接影响区域**

1. `_apply_structure_labels()`
2. `turn_confirm_type`
3. `event` 层记录
4. snapshot 的 reversal_state 优先级

**风险**

会重写当前 `G3 / G4 / G6` 里一部分结构统计口径。

**优先级**

`P1`

---

## 3.5 Gap E: `self-history ruler` 的转译标签还不够硬

**冻结定义**

`self-history ruler` 是系统转译定义，不是原书原义。

**当前实现**

代码已经按这个定义运行，但文档与字段语义容易被误读成“书里原本就是这样”。

**整改目标**

1. 在代码注释和相关 spec 里强化“系统转译”标签
2. 在需要的字段说明中区分 `book notion` 与 `system ruler`
3. 避免后续把 `gene_score / band` 当成原书直接术语

**直接影响区域**

1. [`gene.py`](../../../../src/selector/gene.py) 注释
2. `G1 / G2 / G4` 相关 spec 与 record

**优先级**

`P1`

---

## 3.6 Gap F: 统计层已经快于定义层

**冻结定义**

定义层必须先于 `mirror / conditioning / score / band`。

**当前实现**

`G4 / G5 / G6` 已经形成完整统计层，但底下的 `trend_level / 1-2-3 / 2B` 语义还未完全纠正。

**整改目标**

1. 后续若继续开发第四战场，不再先开新统计卡
2. 先完成语义整改，再决定是否重跑 `validation / mirror / conditioning`

**优先级**

`P0`

---

## 4. 建议执行顺序

### 4.1 第一组：定义对象补齐

1. `trend_level`
2. `mainstream / countertrend`

### 4.2 第二组：结构确认修正

1. `2B` 时间窗层级化
2. `1-2-3` 三条件化

### 4.3 第三组：统计层校准

1. 重新审视 `snapshot / validation`
2. 重新审视 `mirror`
3. 重新审视 `conditioning`

---

## 5. 对执行卡的要求

如果后续真的开始整改代码，应至少拆成以下子卡：

1. `trend-level-and-context-refactor`
2. `two-b-window-semantics-refactor`
3. `123-three-condition-refactor`
4. `post-refactor-g4-g5-g6-revalidation`

不建议把这四件事混成一张大卡直接硬改。

---

## 6. 当前正式结论

当前第四战场不是“方向错了”，而是“骨架已成，但定义层仍有四处关键缺口”：

1. `trend_level`
2. `mainstream / countertrend`
3. `2B` 时间窗
4. `1-2-3` 语义

一句话收口：

`第四战场下一步最该做的，不是新分位、新镜像、新条件矩阵，而是把 gene.py 从“可运行研究骨架”修成“定义学站得住的语义实现”。`
