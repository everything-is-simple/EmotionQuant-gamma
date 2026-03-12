# Bob Volman 结构初筛：谁更像自带 Alpha 的 Volman 版 PAS 候选

**文档版本**：`Draft v0.01`  
**文档状态**：`Active`  
**创建日期**：`2026-03-12`  
**变更规则**：`允许继续补充筛选逻辑、证据需求与实验建议；不直接改写当前主线 PAS SoT。`

> **定位说明**：本文不是当前主线 `PAS` 的正式设计文，也不是 `Volman` 原书的逐章摘要。  
> 本文只做一件事：把 `Bob Volman` 书中常见结构先按“谁更像自带 alpha”做一次初筛，给后续是否要单开 `Volman PAS` 研究线提供起点。

> **当前主线说明**：当前正式 PAS 设计仍以 `blueprint/01-full-design/02-pas-trigger-registry-contract-annex-20260308.md` 与 `blueprint/01-full-design/06-pas-minimal-tradable-design-20260309.md` 为准。  
> 本文不改变当前主线 `BOF` baseline，也不直接宣布任何 `Volman` 结构升格为正式在线形态。

---

## 1. 为什么要单独做这份初筛

`docs/Strategy/PAS/volman-ytc-mapping.md` 已经完成了一件很重要的工作：

`把 Volman 的结构语言映射到 YTC / 当前 PAS 语义。`

但那份文档的重点是：

1. 映射关系
2. 结构解释
3. 历史适配草案

它还没有专门回答下面这个更直接的问题：

`如果先不管主线 taxonomy，只从 Volman 自身出发，哪几类结构更像“自带 alpha 的独立入场对象”，哪几类更像“质量增强器 / 触发细化器 / 复合确认器”。`

这正是本文的任务。

---

## 2. 什么叫“自带 alpha”

本文里的“自带 alpha”，不是说这个形态天然必赚，而是说它更接近下面这类对象：

1. 有独立的结构语义，而不是只给别的形态加分
2. 有相对清楚的行为链，而不是只是一根小 K 线
3. 有独立的失效点，可以定义入场为何失真
4. 可以在 `A 股日线 + T+1 Open` 下勉强改写成稳定实验对象
5. 不过度依赖盘中微结构，否则很难从 `Volman` 的超短线语境迁移到当前系统

如果一个结构更像：

1. `quality filter`
2. `timing refinement`
3. `context enhancer`
4. `composite confirmation`

那它就不应被优先归为“自带 alpha”的第一批候选。

---

## 3. Volman 七种结构的首轮筛选结果

| Volman结构 | 更像什么 | 自带alpha判断 | 初筛结论 |
|---|---|---|---|
| `RB` | 区间突破 / 假突破失败 | `强` | 第一优先候选 |
| `FB` | 趋势首次回撤后的顺势突破 | `强` | 第一优先候选 |
| `SB` | 第二次失败后的再突破 | `中等偏强` | 第二优先候选 |
| `IRB` | 区间内小箱体抢跑 / 杯柄细化 | `中等偏弱` | 更像触发细化器 |
| `DD` | 双十字测试 / hold signal | `弱` | 更像微观触发器 |
| `BB` | 箱体蓄压 | `弱` | 更像质量增强器 |
| `ARB` | 复合型高级突破 | `弱` | 更像后期复合研究对象 |

一句话先说结论：

`如果真的要从 Volman 单独开一条 PAS 研究线，第一批该研究的不是七个一起上，而是先盯 RB / FB / SB。`

---

## 4. 逐个结构的粗筛判断

### 4.1 RB：最像“自带 alpha”的第一候选

`RB` 里最有价值的不是“所有区间突破都做”，而是它清楚地区分了：

1. 真突破
2. 假突破
3. 捉弄式突破

这件事很关键，因为它天然带出一条完整行为链：

1. 区间边线被市场共同看到
2. 边线附近出现蓄力或直接冲击
3. 突破后有没有 follow-through
4. 如果没有，错误方向仓位会被迫退出

这就是标准的 `trapped traders + failed continuation` 逻辑。

因此 `RB` 的价值有两层：

1. 真突破一侧，它可以给出高质量 continuation 候选
2. 假突破一侧，它几乎天然就是 `BOF` 的 Volman 原型

如果只问“谁最像自带 alpha”，`RB fake breakout` 应该排第一梯队，原因是：

1. 结构语义完整
2. 失效定义清楚
3. A 股日线下容易被改写成“前高/平台/箱体假突破失败”
4. 当前系统已有 `BOF` 正向证据，至少说明这条结构链不是空想

但要注意：

`RB true breakout` 和 `RB fake breakout` 不应混在一个 detector 里。

如果未来真做 `Volman PAS`，更合理的做法是拆成两个研究对象：

1. `RB_FAKE`
2. `RB_TRUE`

其中真正先验更强的，其实是 `RB_FAKE`。

### 4.2 FB：最像“自带 alpha”的顺势候选

`FB` 的核心不是普通回调，而是：

1. 先有突然爆发的趋势
2. 再有第一次、且相对有序的回撤
3. 最后在回撤末端做顺势恢复

这类结构本身就带有独立 alpha 候选的特征：

1. 它不是给别的形态加分，而是完整入场逻辑
2. 它有“首次回撤”这个非常重要的稀缺性条件
3. 它既有趋势背景，也有回撤深度边界
4. 它的失败点可以围绕回撤低点或破坏趋势延续来定义

为什么 `FB` 不像 `BB` 或 `DD` 那样只能做增强器：

因为 `FB` 自己已经具备：

1. 背景
2. 结构
3. 触发
4. 失效

它不是微观细节，而是完整 setup。

所以如果要从 Volman 里找一个最像独立顺势 alpha 的对象，`FB` 应该和 `RB_FAKE` 并列第一梯队。

它在现有映射里最接近：

1. `BPB`
2. 一部分高质量 `PB`

但如果未来真开 `Volman PAS`，我不建议直接把 `FB` 吞并进泛化 `PB`。  
`FB` 更适合单列，因为“首次回撤”本身就是 edge 的重要组成部分。

### 4.3 SB：有独立 alpha，但不适合当第一枪

`SB` 比 `FB` 更复杂，因为它依赖一段前情：

1. 第一次尝试失败
2. 价格再次回到 EMA 区域
3. 第二次被突破
4. 逆势方信心彻底崩掉

它当然有自己的 alpha 逻辑，而且这条逻辑并不弱：

1. 第一次失败制造怀疑
2. 第二次失败制造恐慌
3. 这比一次性突破更容易形成 forced exit

但 `SB` 的问题是：

1. 它依赖前序结构记忆
2. 它更容易与 `CPB / TST / M/W` 识别混线
3. 在日线系统里，结构跨度拉长后更容易引入噪音

所以我对 `SB` 的判断是：

1. 它不是纯增强器
2. 它确实是独立候选
3. 但它不适合作为第一批最小研究对象

也就是：

`SB` 值得研究，但顺序应在 `RB / FB` 之后。

### 4.4 IRB：更像 timing optimizer，而不是第一层 alpha

`IRB` 很吸引人，因为它有：

1. 区间内部小箱体
2. 杯柄
3. 抢跑边线突破
4. 真空效应

这些都很“交易员风格”。

但问题在于，`IRB` 的很多价值其实不是来自它独立成型，而是来自它能把别的 setup 做得更漂亮：

1. 它能细化 `FB`
2. 它能优化 `BPB`
3. 它能把 `PB` 的触发点做得更紧
4. 它能把“边线反弹”从模糊变成更可执行的 trigger

这意味着 `IRB` 更像：

1. `trigger refinement`
2. `quality booster`
3. `entry timing optimizer`

而不是第一层 standalone alpha。

我不否认 `IRB` 某些子型本身可能有 edge，尤其是：

1. `cup_handle`
2. `boundary IRB`

但就首轮粗筛而言，它更适合作为第二层增强模块，而不是第一批主 detector。

### 4.5 DD：有交易意义，但更像微观触发器

`DD` 的价值在于：

1. 它能刻画短暂平衡
2. 它能表达测试和 hold
3. 它常出现在支撑/阻力或 EMA 附近

但它的问题也很明显：

1. 单独看时，结构上下文太弱
2. 很依赖出现位置
3. 很容易沦为“看起来像信号，其实只是噪音”

因此 `DD` 更像：

1. `TST` 的微观触发器
2. `BB` 里的蓄压细节
3. `support/resistance` 测试中的辅助证据

它有解释价值，但不应优先被定义成 standalone alpha detector。

### 4.6 BB：更像 pressure meter，不像独立 alpha

`BB` 的核心价值是“蓄压”。

这类结构对交易非常重要，但它更像一种：

1. 结构质量评分
2. 突破前压力强弱刻画
3. 波动压缩度量

它当然可能出现在强 entry 前，但问题是：

`BB 自己并不自动告诉你，这次突破到底是 trend continuation、boundary reversal 还是 future fakeout。`

也就是说：

1. 它能告诉你“这里在积累力量”
2. 但不能单独告诉你“往哪边的 alpha 更值得先赌”

因此 `BB` 不该第一批独立化。

更合理的位置是：

1. 给 `RB / FB / IRB / TST` 加质量分
2. 作为 `compression / squeeze` sidecar

### 4.7 ARB：研究价值高，但不适合最先 formalize

`ARB` 的吸引力在于它很接近“成熟交易员真正看的整幅图”：

1. 假突破
2. 头肩
3. Higher Lows / Lower Highs
4. 多层结构综合判断

但它恰恰也因此最不适合第一批形式化：

1. 过于复合
2. 主观解释空间大
3. 很难先做成稳定 detector
4. 容易把多个本来该拆开的 edge 混在一起

所以 `ARB` 更像：

1. 后期研究对象
2. composite confirmation layer
3. 结构 bias 分析层

它应该晚于 `RB / FB / SB`，甚至晚于 `IRB`。

---

## 5. 初步分层：谁先研究，谁先别碰

### 5.1 第一梯队：最像 standalone alpha

1. `RB_FAKE`
2. `FB`

这两个对象的共同特点是：

1. 结构完整
2. 交易心理清楚
3. 失效边界清楚
4. 可直接转写为 detector

如果只能从 Volman 里挑两个先做，这两个最值。

### 5.2 第二梯队：有 alpha，但要晚一点

1. `SB`
2. `RB_TRUE`

原因不是它们没价值，而是：

1. 更依赖上下文
2. 更容易和别的 continuation / breakout 语义重叠
3. 更需要先把第一梯队做清楚，才知道增量 edge 来自哪里

### 5.3 第三梯队：更像增强层

1. `IRB`
2. `DD`
3. `BB`

这三类更适合作为：

1. trigger refinement
2. structure quality
3. pressure / hold / boundary sidecar

### 5.4 第四梯队：后期复合研究

1. `ARB`

它不是不重要，而是太重要、也太复合。  
先用它做 detector，几乎必然把问题做糊。

---

## 6. 如果要做“Volman 版 PAS”，建议怎么起步

我建议不要一开始就做“Volman 七结构全家桶”，而是拆成三层：

### 6.1 第一层：独立 detector

1. `RB_FAKE`
2. `FB`
3. `SB`

这是要直接拿去问：

`谁真的在创造 raw alpha。`

### 6.2 第二层：quality / timing sidecar

1. `BB_pressure`
2. `IRB_handle`
3. `DD_hold`

这层不回答“有没有 entry”，只回答：

`这次 entry 的质量是不是更高。`

### 6.3 第三层：composite structure layer

1. `ARB_bias`

这层先别做 trigger，只做解释、分桶和后验归因。

---

## 7. 与当前 PAS 的关系

把这份初筛放回当前仓库语境，可以得到一个很重要的关系图：

| Volman对象 | 更接近当前什么 | 当前判断 |
|---|---|---|
| `RB_FAKE` | `BOF` | 已被当前系统部分验证 |
| `FB` | `BPB` / 高质量 `PB` | 值得单独研究 |
| `SB` | `CPB` / `TST` 的复杂版本 | 值得后续研究 |
| `IRB` | `BPB / PB` 的 timing 细化 | 更适合作为 sidecar |
| `DD` | `TST` 的微观触发 | 更适合作为 sidecar |
| `BB` | 全部形态的压力增强 | 更适合作为 sidecar |
| `ARB` | `CPB` 的高级复合结构 | 适合后期研究 |

这张表的含义不是：

`Volman 已经被当前 PAS 完整覆盖。`

而是：

`Volman 真正独特的价值，很可能不在于重新发明一套完全不同的 taxonomy，而在于把 continuation / failure / pressure / handle / composite bias 这几层拆得比当前仓库更细。`

---

## 8. 当前最值得先验证的三件事

如果下一步要把这份初筛转成真正的实验卡，我建议顺序是：

1. 单独做 `RB_FAKE`
   - 问题：它是否比当前 `BOF` 更接近原始 Volman edge
2. 单独做 `FB`
   - 问题：`首次回撤` 是否真的自带独立 alpha，而不只是 `PB/BPB` 的一个子集
3. 再做 `SB`
   - 问题：第二次失败的 forced exit 是否足以支撑独立 detector

但有一条边界要明确写死：

`如果真的开第一张 Volman PAS 实验卡，候选集可以收窄，但不能因为实现复杂就把 SB 从第一批研究对象里删掉。`

在这之前，不建议直接做：

1. `IRB standalone`
2. `BB standalone`
3. `ARB standalone`

因为大概率会把“增强器”和“主形态”混在一起。

---

## 9. 本文的粗结论

如果只做首轮筛选，`Volman` 书里最像“自带 alpha”的不是七个对象平均分布，而是明显集中在：

1. `RB_FAKE`
2. `FB`
3. `SB`

其中：

1. `RB_FAKE` 最像 reversal alpha
2. `FB` 最像 trend-continuation alpha
3. `SB` 最像 second-chance continuation alpha

而 `IRB / DD / BB / ARB` 更合理的首轮定位分别是：

1. `IRB` = timing refinement
2. `DD` = micro trigger
3. `BB` = pressure / quality enhancer
4. `ARB` = composite structure research object

所以，如果要真的补一条“Volman 版 PAS”研究线，最合理的起点不是：

`把七种结构都 detector 化。`

而是：

`先把 RB_FAKE / FB / SB 当作三类候选 alpha object，其余结构先降级为 sidecar 或后期复合层。`
