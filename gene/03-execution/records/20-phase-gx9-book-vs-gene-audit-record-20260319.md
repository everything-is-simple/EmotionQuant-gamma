# GX9 Record: 《专业投机原理》对照 Gene 设计与实现审计

**状态**: `Completed`  
**日期**: `2026-03-19`

---

## 1. 这份记录回答什么

这份记录只回答四件事：

1. 书里关于 `个股寿命 / 趋势层级 / 转折确认 / 使用方式` 到底在说什么
2. 当前 Gene 的设计口径和实现口径，哪些地方对上了，哪些地方还没对上
3. 当前已经被 `Phase 9B` 证明过的三个要素，设计是否合理，实现是否偏移，使用是否顺手
4. 当前还没被证明的那些观点，哪些适合继续保留为 sidecar，哪些不该急着推进到 runtime

这份记录不回答：

1. 哪个组合已经赢下正式 replay
2. `17.8 / 17.9` 是否已经跑完
3. 当前主线是否应立刻改写

---

## 2. 审计范围

本轮审计同时核对了四层材料：

1. 书页原文
   - `G:\《股市浮沉二十载》\2011.专业投机原理\new-split`
   - 本轮重点直读页段：
     - split PDF `048-054`：次级折返、三层趋势、趋势定义
     - split PDF `073-080`：`1-2-3` 与 `2B`
     - split PDF `344-350`：平均寿命、宽度/时间分布、风险概念
     - split PDF `352-354`：三种趋势与市场四阶段
     - split PDF `428-432`：连续上涨/下跌日统计与“怎么用”
2. 第四战场设计与定义文档
   - [`gene/01-full-design/02-professional-speculation-principles-theory-annex-20260316.md`](../../01-full-design/02-professional-speculation-principles-theory-annex-20260316.md)
   - [`gene/02-implementation-spec/01-price-only-wave-ruler-spec-20260316.md`](../../02-implementation-spec/01-price-only-wave-ruler-spec-20260316.md)
   - [`docs/spec/common/governance/gene-foundational-definition-freeze-20260317.md`](../../../docs/spec/common/governance/gene-foundational-definition-freeze-20260317.md)
   - [`docs/spec/common/governance/gene-definition-gap-remediation-checklist-20260317.md`](../../../docs/spec/common/governance/gene-definition-gap-remediation-checklist-20260317.md)
3. 当前实现
   - [`src/selector/gene.py`](../../../src/selector/gene.py)
   - [`src/data/store.py`](../../../src/data/store.py)
4. 已有验证与治理结论
   - [`blueprint/03-execution/records/phase-9b-duration-percentile-validation-record-20260318.md`](../../../blueprint/03-execution/records/phase-9b-duration-percentile-validation-record-20260318.md)
   - [`blueprint/03-execution/records/phase-9b-reversal-state-validation-record-20260318.md`](../../../blueprint/03-execution/records/phase-9b-reversal-state-validation-record-20260318.md)
   - [`blueprint/03-execution/records/phase-9b-context-trend-direction-validation-record-20260319.md`](../../../blueprint/03-execution/records/phase-9b-context-trend-direction-validation-record-20260319.md)
   - [`blueprint/03-execution/records/phase-9b-wave-role-validation-record-20260318.md`](../../../blueprint/03-execution/records/phase-9b-wave-role-validation-record-20260318.md)
   - [`gene/03-execution/records/07-phase-g4-self-history-ruler-validation-record-20260316.md`](./07-phase-g4-self-history-ruler-validation-record-20260316.md)
   - [`gene/03-execution/records/08-phase-g5-market-industry-index-mirror-ruler-record-20260316.md`](./08-phase-g5-market-industry-index-mirror-ruler-record-20260316.md)
   - [`gene/03-execution/records/09-phase-g6-bof-pb-cpb-conditioning-record-20260316.md`](./09-phase-g6-bof-pb-cpb-conditioning-record-20260316.md)

---

## 3. 先给总判断

### 3.1 方向判断

当前第四战场最正确的地方，不是某个 percentile 数值，而是你抓住了三条真正重要的轴：

1. `个股寿命`
2. `主要趋势`
3. `次级趋势 / 转折确认`

这三条轴和书的重心是一致的。

### 3.2 当前系统的真实位置

当前系统更准确的描述不是：

`已经把书里的寿命架构完整实现了`

而是：

`已经做出一把可运行的个股自历史波段尺，并且寿命轴已经在当前 runtime 验证里率先胜出；但它距离书里的“宽度 + 时间 + 风险赔率”寿命架构，仍有一段距离。`

### 3.3 对“设计合理性”和“使用便捷性”的总评

1. 设计方向：`对`
2. 设计收口：`比过去诚实，仍未到底`
3. 实现完成度：`够研究，不够终局`
4. 使用便捷性：`已证明三要素明显好于未证明层，但字段别名、压缩语义与层级命名仍有混淆`

---

## 4. 书里真正强调了什么

本轮直读书页后，可以把与当前系统最相关的原义收口成五条。

### 4.1 趋势必须承认层级并存

书里明确把趋势分成短期、中期、长期，并明确说三种趋势可以同时存在。  
这意味着：

1. `主趋势` 不是一句“涨”或“跌”
2. `次级趋势` 不是噪声
3. `主流 / 逆流` 必须相对于更高层趋势判断

### 4.2 趋势先是结构，不是指标

书里对上升趋势和下降趋势的定义，先是：

1. 更高高点 + 更高低点
2. 更低低点 + 更低高点

因此：

1. 趋势对象不能先从 `score` 开始
2. `percentile / band / gene_score` 只能建立在结构对象之后

### 4.3 寿命不是单阈值，而是“宽度 + 时间”的历史分布

书里关于“平均寿命”的真正重点不是一个 magic threshold，而是：

1. 把当前修正或趋势放回历史分布
2. 同时看 `宽度` 和 `时间`
3. 用它们去判断“继续”与“结束”的赔率结构
4. 趋势越老，未必立刻反转，但风险收益比会变差

这和“只看 age 是否超过某一档”不是一回事。

### 4.4 `1-2-3 / 2B` 是确认法，不是预测法

书里这两套东西都更像：

1. 结构破坏
2. 失败测试
3. 关键点位重新跌破/涨破

也就是说，它们更适合变成：

1. `确认标签`
2. `风险释放标签`
3. `退出准备标签`

而不是“神奇抄底器”。

### 4.5 短期连续日统计是战术层，不是本体层

书里后面关于连续上涨/下跌天数的统计，最后自己也讲得很克制：

1. 它帮助匹配时机
2. 它不单独告诉你方向
3. 它不替代一整套系统

所以这些东西更适合：

1. `conditioning`
2. `entry timing`
3. `pattern environment`

而不适合改写 `trend / wave / lifespan` 本体定义。

---

## 5. 个股寿命专项审计

### 5.1 设计是否合理

结论是：

`合理，而且应该继续作为 Gene refinement 的第一优先级`

原因很直接：

1. 书里“平均寿命 / 风险赔率”本来就是核心统计层
2. 你关心的低频、高胜率、高盈亏比，本质上也更像寿命筛选问题
3. 当前 `Phase 9B` 里最先胜出的也是寿命轴，而不是别的轴

### 5.2 当前设计和书义已经对上的地方

已经对上的地方有：

1. 系统承认寿命轴属于历史解释层，而不是趋势本体层
2. 系统把 `duration_percentile / band` 做成了正式输出，而不是口头概念
3. 系统已经把“当前波段在自历史里走得多老”做成可查询、可回测、可验证的日级 snapshot

### 5.3 当前实现和书义仍有三处关键偏差

#### 偏差 A：现在只做了“时间轴”，还没做成“宽度 + 时间”的赔率尺

当前代码里，`duration_percentile` 就是把当前 active wave 的年龄，和同方向历史 completed wave 的 `duration_trade_days` 做比较。  
这当然有用，但它仍然只是：

`time-only ruler`

而不是书里更完整的：

`width + time joint odds ruler`

对应位置：

1. [`src/selector/gene.py`](../../../src/selector/gene.py)
2. [`gene/02-implementation-spec/01-price-only-wave-ruler-spec-20260316.md`](../../02-implementation-spec/01-price-only-wave-ruler-spec-20260316.md)

#### 偏差 B：当前自历史窗口固定为 `260` 个交易日，历史深度明显偏浅

当前入口固定：

`GENE_LOOKBACK_TRADE_DAYS = 260`

这意味着当前所谓“自历史”，更接近：

`近一年自历史`

而不是：

`这只股票尽可能长的可用历史`

这对寿命轴尤其敏感，因为书里的寿命判断强调的是历史分布稳定性，而不是只看最近一小段样本。

#### 偏差 C：当前没有显式表达“相对前一主要波段的折返宽度”

书里谈次级折返时，时间和幅度始终一起出现，而且幅度明确是相对于前一主要波段。  
当前 Gene 有 `magnitude_pct`，但没有把：

`当前修正幅度 / 前一主要波段幅度`

做成正式寿命赔率的一部分。

因此当前系统更像：

`当前波段自己有多老`

还不像：

`当前折返对前一主要波段已经吃掉了多少，并且已经拖了多久`

### 5.4 当前“使用便捷性”如何

当前寿命轴的使用便捷性，分成两半。

好的一半：

1. `l3_stock_gene` 直接有 `current_wave_duration_percentile`
2. 同时给出 `p65 / p95 / band`
3. 已经有独立的 isolated validation runner
4. 17.8 已经重写成书义寿命分布 follow-up

不好的另一半：

1. `current_wave_duration_band` 和 `current_wave_age_band` 在实现上是同一个东西，容易让使用者误以为是两把尺
2. 当前阈值语义还是“单刀切”，不够接近书里的赔率/拐点/斜率读法
3. 260 日 lookback 让使用者容易高估“自历史”的代表性

### 5.5 寿命轴最终判断

一句话收口：

`寿命轴方向完全对，但当前实现仍是“简化版年龄尺”，还不是书义中的“寿命赔率架构”；它值得继续深做，而且就该先深做它。`

---

## 6. 三个已证明要素审计

## 6.1 `duration_percentile`

### 设计合理性

`高`

这是当前最符合书义、也最符合你目标的一条轴。

### 实现偏差

主要偏差就是上一节那三条：

1. 只做了时间维
2. lookback 偏短
3. 没和前一主要波段折返宽度联立

### 使用便捷性

`中高`

优点：

1. snapshot 直接暴露
2. isolated validation 已跑
3. 17.8 sweep 已经开卡

缺点：

1. `age_band` 和 `duration_band` 重复
2. 还没形成正式曲线汇总，而不是单点阈值争论

### 审计结论

`继续保留为第一主轴，并优先完成 17.8；但不要把 age_band 当成独立第四个观点。`

## 6.2 `context_trend_direction_before`

### 设计合理性

`中高`

书里明确要求先分清你是在什么趋势层级下做决策，所以“父趋势方向”作为负向 guard 是合理的。

### 实现偏差

当前真正 runtime 用的是：

`current_context_trend_direction`

而不是文档名里的：

`context_trend_direction_before`

而且当前 canonical snapshot 里的：

`current_context_trend_level`

仍写成 `INTERMEDIATE`，与 wave ledger 中 `INTERMEDIATE` 波段对应 `LONG` parent context 的口径并不完全一致。  
也就是说，当前这一层是：

`parent-direction proxy`

不是完整、统一、无歧义的层级上下文实现。

### 使用便捷性

`中`

优点：

1. 读取简单
2. isolated validation 已经完成
3. 规则形态也很清楚：
   `block when current_context_trend_direction == DOWN`

缺点：

1. 字段名和治理文案不完全统一
2. canonical row 与 hierarchy row 的层级解释还不够顺手

### 审计结论

`可以继续保留为窄 negative guard，但它当前仍是 proxy，不应被误读为“主趋势模型已经完成”。`

## 6.3 `reversal_state`

### 设计合理性

`中高`

如果把它理解成：

`把 1-2-3 / 2B / countertrend watch 压成一个运行时可消费的防守语义`

那么它是合理的，而且更像书里的“确认法服务防守”。

### 实现偏差

当前 `reversal_state` 不是单一书义对象，而是压缩字段。  
它在代码里的优先级是：

1. `confirmed turn`
2. `active 2B watch`
3. `countertrend watch`
4. `none`

这意味着它很好用，但并不纯。

真正已经赢下 isolated validation 的，也不是整个 `reversal_state`，而只是：

`reversal_state == CONFIRMED_TURN_DOWN`

这一条极窄子语义。

### 使用便捷性

`高，但诊断透明度一般`

优点：

1. 下游只要看一个字段
2. exit-preparation 规则非常容易挂进去

缺点：

1. 同一字段混了多种来源
2. 一旦行为不好，诊断要回看 `latest_confirmed_turn_type / latest_two_b_confirm_type / current_wave_role`

### 审计结论

`当前保留“CONFIRMED_TURN_DOWN exit-preparation only”是合理的；但不要把整个 reversal_state 一口气扩成更宽的 runtime 语义。`

---

## 7. 未证明要素审计

## 7.1 `wave_role`

### 设计合理性

`概念对`

书里本来就要求区分主流和逆流。

### 当前实现偏差

当前实现仍然太粗：

1. 它是二元标签
2. 它依赖 parent-context proxy
3. 它还不能稳定区分“重要逆流”和“更小级别噪声”

这也是它 isolated round 太重、拦太狠的根本原因。

### 使用便捷性

`中`

它好查，但不好放心用。  
字段很容易拿来做 gate，但当前语义还不够细。

### 审计结论

`保留 sidecar / structure readout 是对的；现在不该强行升格。`

## 7.2 `current_wave_age_band`

### 设计合理性

`作为展示别名可以，作为独立观点不合理`

### 当前实现偏差

在当前代码里：

1. `current_wave_age_band`
2. `current_wave_duration_band`

本质上是同一个 `_distribution_band(age_trade_days, duration_thresholds)` 结果。  
也就是说，它不是独立新信息，而是 `duration` 的 band 视图。

### 使用便捷性

`展示方便，研究容易误导`

对于报表面板，它直观。  
对于研究和组合 freeze，它会制造“这是不是第四个变量”的假象。

### 审计结论

`当前应把它明确收口成 duration 的展示别名，不应再把它当独立 runtime 候选。`

## 7.3 `mirror`

### 设计合理性

`作为 sidecar context 合理`

书里后半段确实强调宽度、相对强弱、辅助确认，但它们本来就更像背景尺，不是个股本体层。

### 当前实现偏差

当前 `G5` 的问题不在于方向错，而在于还不够硬：

1. 行业层使用 `synthetic close-only`
2. 多个 support 字段仍为 `NULL`
3. composite rank 和 primary-ruler rank 必须并存，说明结构仍不够收敛

### 使用便捷性

`中低`

它已经有正式表，但现在更适合研究读取，不适合直接挂主线。  
使用者要同时理解：

1. 市场层与行业层不是同质输入
2. 哪些 support 指标是真的稳定，哪些只是预留列

### 审计结论

`继续保留为 context sidecar 是合理的；在正式稳定供数和明确消费位点之前，不该推进 runtime。`

## 7.4 `conditioning`

### 设计合理性

`方向对`

这层和书里“短期连续日统计 + 环境配对”的精神是相符的。

### 当前实现偏差

当前 `G6` 不是用真实 runtime fills，而是用价格重构出来的 pattern trigger 样本做条件层统计。  
这很适合研究，但和真实主线运行之间仍隔着一层。

### 使用便捷性

`研究便捷，中线接入不便`

优点：

1. 表结构清楚
2. 输出的是相对 baseline 的 `BETTER / WORSE / MIXED`

缺点：

1. 现在还不是“直接可接主线”的消费形态
2. 使用者需要理解它只是解释层，不是 gate

### 审计结论

`conditioning 现在最合适的位置仍然是解释层；若未来要接 runtime，必须先经过真实主线 trace 回灌，而不是只靠价格重构样本。`

## 7.5 `gene_score`

### 设计合理性

`作为汇总视图可以，作为决策主尺不合理`

### 当前实现偏差

当前 `gene_score` 只是三个 percentile 的等权均值。  
G4 自己也已经诚实地把它裁成：

`KEEP_COMPOSITE`

而不是 `PRIMARY_RULER`。

### 使用便捷性

`最高，也最危险`

因为一个数最好用，所以最容易被误用。  
但它恰恰不该被拿来抢掉寿命轴和趋势轴的主地位。

### 审计结论

`继续保留 panel / summary only 的阅读位置，不应进入当前 freeze surface。`

---

## 8. 跨要素共性问题

### 8.1 当前统计层仍然快于定义层

虽然 `GX3-GX8` 已经做了大量修正，但当前真实状态仍然是：

1. `duration / mirror / conditioning / validation` 已经跑得很快
2. `trend_level / mainstream-countertrend / 1-2-3 / 2B` 的最终语义仍未完全站稳

这也是为什么当前最诚实的口径仍然应当是：

`Gene refinement first`

### 8.2 canonical snapshot 的层级语义还不够干净

当前系统已经能输出 `short / intermediate / long` hierarchy fields。  
但同时 canonical row 里仍保留一套更旧、更方便、但不够纯的字段。  
这会带来两个问题：

1. 用起来方便
2. 但越方便，越容易把 proxy 当 final semantics

### 8.3 当前运行面里最容易误导人的字段就是“重复字段”和“压缩字段”

具体就是：

1. `current_wave_age_band` vs `current_wave_duration_band`
2. `reversal_state` vs 其底层 confirm/watch 来源
3. `context_trend_direction_before` 文档名 vs `current_context_trend_direction` runtime 名

这些问题不会立刻把结果做坏，但会让后续研究和组合 freeze 容易偷带歧义。

---

## 9. 当前建议顺序

按本轮审计，最合理的后续顺序仍然是：

1. 先完成 [`blueprint/03-execution/17.8-phase-9e-duration-percentile-threshold-sweep-card-20260319.md`](../../../blueprint/03-execution/17.8-phase-9e-duration-percentile-threshold-sweep-card-20260319.md)
2. 明确把 `current_wave_age_band` 收口成 duration 展示别名，不再把它当独立变量候选
3. 在 sweep 之后进入 [`blueprint/03-execution/17.9-phase-9f-frozen-combination-replay-card-20260319.md`](../../../blueprint/03-execution/17.9-phase-9f-frozen-combination-replay-card-20260319.md)
4. 若寿命轴继续胜出，下一步不该只是继续玩单点 percentile，而该补：
   - 更长历史窗口
   - 宽度 + 时间联立
   - 相对前一主要波段折返宽度
5. `wave_role / mirror / conditioning / gene_score` 继续按当前治理口径留在 sidecar 或解释层，先不抢主线
6. `context` 与 `reversal` 两条已证明轴，只保留当前已经被证据证明的窄角色，不扩面

---

## 10. 最终结论

一句话版本：

`你现在把 Gene 的主轴放在“个股寿命 + 主趋势 + 次级趋势”上，这个方向是对的；当前最大的问题不是选错了轴，而是寿命轴还只做成了简化年龄尺，主趋势轴还是 proxy，次级趋势轴仍带压缩语义，所以现在最该做的是继续把 Gene 做细，而不是把未证明层硬推入 runtime。`

再收口成更短的话：

1. `duration_percentile`：值得继续深做，是当前第一主轴
2. `context_trend_direction_before`：可保留为窄负向 guard，但还只是 proxy
3. `reversal_state`：可保留为窄 exit-preparation，但不要把整包压缩语义误当终局
4. `wave_role / age_band / mirror / conditioning / gene_score`：当前都不该抢进 freeze 之外的位置
