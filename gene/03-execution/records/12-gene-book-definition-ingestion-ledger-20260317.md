# Gene Book Definition Ingestion Ledger
**状态**: `Active`  
**日期**: `2026-03-17`

---

## 1. 目的

这份账本只回答三件事：

1. 按书的顺序，第四战场当前已经把哪些基本概念正式落盘
2. 哪些概念只是先落了一个可运行外壳，但语义还没有按书站稳
3. 后续 targeted hypothesis 应该按什么顺序继续修正

这份账本不回答：

1. 某个 percentile 或 band 现在统计上是否最有用
2. 某个交易触发器是否应该立刻升格进默认 runtime
3. `G4 / G5 / G6` 当前读数孰优孰劣

---

## 2. 书本顺序

当前统一按以下顺序吸收原始概念：

1. `39-42` 页：趋势层级、次级折返、幅度与期限
2. `73-75` 页：`1-2-3`
3. `77-82` 页：`2B`
4. `159-166` 页：平均寿命、幅度/期限分布、风险检查表

这意味着第四战场的吸收顺序必须是：

`趋势定义 -> 转折确认 -> 波段统计 -> 历史寿命解释`

而不能倒过来从 `band / percentile / score` 去反推定义。

---

## 3. 三档台账

## 3.1 已经正式落盘的概念

### `pivot`

- 书中角色：结构确认点
- 当前状态：`已落盘`
- 当前实现：[`src/selector/gene.py`](../../../src/selector/gene.py)
- 说明：
  当前系统已正式把 `pivot` 作为基础结构对象使用，用于切分 `wave`、识别极值刷新与失败测试。

### `wave`

- 书中角色：后续幅度、期限、主流/逆流、结构标签的承载对象
- 当前状态：`已落盘`
- 当前实现：
  [`src/selector/gene.py`](../../../src/selector/gene.py)  
  [`src/data/store.py`](../../../src/data/store.py)
- 说明：
  `wave` 已经正式落到 `l3_gene_wave`，是第四战场当前最扎实的基础对象。

### `trend direction proxy`

- 书中角色：趋势本体的一部分，但不是全部
- 当前状态：`已落盘，但仅为 proxy`
- 当前实现：`trend_direction_before / trend_direction_after`
- 说明：
  当前已经能表达方向上下文，但还不是完整书义中的分层趋势。

### `trend_level`

- 书中角色：三层趋势并存
- 当前状态：`已落盘，但仅 INTERMEDIATE`
- 当前实现：
  [`src/selector/gene.py`](../../../src/selector/gene.py)  
  [`src/data/store.py`](../../../src/data/store.py)
- 说明：
  `GX3` 第一阶段已经把 `trend_level` 正式写入 schema 与 snapshot，但当前只是诚实地写成 `INTERMEDIATE`，还没有完成三层并存。

### `context`

- 当前状态：`已落盘`
- 当前实现：
  `context_trend_level`  
  `context_trend_direction_before`  
  `context_trend_direction_after`  
  `current_context_trend_level`  
  `current_context_trend_direction`  
  `wave_role_basis`
- 说明：
  当前系统已经不再假装上下文是“无层级最终定义”，而是正式承认它是 `intermediate proxy`。

### `mainstream / countertrend` 标签

- 当前状态：`已落盘，但仍属 proxy`
- 当前实现：`wave_role / current_wave_role`
- 说明：
  标签已经正式存在，但还只是相对于单层 context proxy 的近似判定。

### `2B` 结果标签

- 当前状态：`已落盘`
- 当前实现：`2B_TOP / 2B_BOTTOM`
- 说明：
  失败性极值事件标签已经进入 `wave / event / snapshot`。

### `1-2-3` 结果标签

- 当前状态：`已落盘`
- 当前实现：`123_STEP1 / 123_STEP2 / 123_STEP3 / turn_confirm_type`
- 说明：
  结构标签已经存在，但当前 detector 仍是工程近似。

### `historical lifespan translation layer`

- 当前状态：`已落盘`
- 当前实现：
  `magnitude_percentile / duration_percentile / extreme_density_percentile`  
  `band / zscore / self-history comparison`
- 说明：
  幅度、期限、极值密度的自历史分布解释层已经完整存在。

### `self-history ruler`

- 当前状态：`已落盘`
- 当前实现：
  `snapshot / validation / mirror / conditioning`
- 说明：
  这是系统正式承认的转译定义，不再假装等同于原书原义。

---

## 3.2 已经落了壳，但还没按书落透的概念

### `三层趋势并存`

- 当前状态：`半落盘`
- 缺口：
  现在只有 `trend_level=INTERMEDIATE`，还没有 `SHORT / INTERMEDIATE / LONG` 同时并存的正式结构。

### `mainstream / countertrend`

- 当前状态：`半落盘`
- 缺口：
  现在还不是“相对于更高层趋势”的正式定义，只是相对于单层 `major_trend proxy`。

### `2B`

- 当前状态：`半落盘`
- 缺口：
  事件标签已存在，但时间窗仍是固定口径，没有按层级展开。

### `1-2-3`

- 当前状态：`半落盘`
- 缺口：
  标签已存在，但 detector 仍是三段波近似，不是书里的三条件确认法。

### `趋势`

- 当前状态：`半落盘`
- 缺口：
  现在有方向、有上下文，但“更高高点/更高低点、趋势线破坏、结构转折”还没有完全对象化。

---

## 3.3 还没真正落盘、必须继续补的概念

1. `SHORT / INTERMEDIATE / LONG` 三层趋势并存
2. `mainstream / countertrend` 的上级参照层
3. `2B` 的层级化时间窗
4. `1-2-3` 的三条件对象化：
   - `trendline_break`
   - `failed_extreme_test`
   - `prior_pivot_breach`
5. `次级折返` 与 `更小级别噪声` 的区分
6. `trendline` 本身作为正式结构对象
7. `历史剩余寿命 / 风险检查表` 的对象化表达

---

## 4. 关于 `1-2-3 / 2B` 的正式分层

当前正式判断如下：

1. `1-2-3 / 2B` 不属于第四战场第一层“本体基础定义”
2. 第一本体层应该是：
   - `trend_level`
   - `trend`
   - `pivot`
   - `wave`
   - `reference extreme`
   - `trendline`
3. `1-2-3 / 2B` 应归入第二层：
   - `趋势改变 / 趋势失效 / 结构转折` 的确认语法
4. `BOF / BPB / PB / TST / CPB` 再归入第三层：
   - 交易触发语法

一句话：

`1-2-3 / 2B` 不是最底层本体，但也不是可有可无的多余概念；它们是把“趋势改变”机械化、可审计化的确认工具。`

---

## 5. 后续整改顺序

当前正式建议顺序固定为：

1. 先完成 `trend_level + mainstream / countertrend`
2. 再做 `2B window semantics`
3. 再做 `1-2-3 three-condition refactor`
4. 最后才允许重跑 `G4 / G5 / G6`

---

## 6. 当前结论

第四战场当前已经最扎实落盘的是：

`pivot / wave / self-history ruler`

当前半落盘的是：

`trend_level / mainstream-countertrend / 2B / 1-2-3`

当前后续 targeted hypothesis 最该补的，是：

`真正的三层趋势、层级化 2B、三条件化 1-2-3、次级折返语义`
