# 四战场对象-指标-信号边界表

**状态**: `Active`  
**日期**: `2026-03-17`  
**适用范围**: `blueprint / normandy / positioning / gene / docs/spec/common`  
**文件定位**: `四战场共同服从的分类边界冻结稿（第一版）`

---

## 1. 目的

这份文件回答的是：

1. 哪些东西是对象
2. 哪些东西只是对象上的状态
3. 哪些东西是事件
4. 哪些东西只是指标
5. 哪些东西才可以被叫做信号

它的作用，是把四战场里最容易混掉的几类词拆开，避免系统把：

- 对象当指标
- 指标当信号
- 信号当定义
- 历史解释层当 runtime 决策层

本文件与术语总表的分工是：

1. [`four-battlefields-unified-terminology-glossary-20260317.md`](./four-battlefields-unified-terminology-glossary-20260317.md) 回答“这个词在系统里是什么意思”
2. 本文件回答“这个词在系统里属于哪一层”

---

## 2. 权威入口

- `../../../design-v2/01-system/system-baseline.md`
- `../records/development-status.md`
- `./four-battlefields-unified-terminology-glossary-20260317.md`

---

## 3. 总原则

### 3.1 分类顺序

统一按以下顺序判断：

1. 先问它是不是一个可独立追踪的真实单位
2. 再问它是不是这个单位当前所处的条件
3. 再问它是不是某个时间点发生的离散动作
4. 再问它是不是数值化测量结果
5. 最后才问它是不是系统给出的可执行输出

也就是：

`对象 -> 状态 -> 事件 -> 指标 -> 信号`

### 3.2 不允许的偷换

以下偷换一律不允许：

1. 不把分数、百分位、rank 叫做对象。
2. 不把“是否值得打”的判断偷写成“历史定义”。
3. 不把某类观察层标签偷升格成 runtime 硬门。
4. 不把来源理论词直接拿来替代系统内部分类。

### 3.3 当前系统特别强调的一条

`Gene` 当前只能提供历史解释和语境分层，所以：

1. `gene_score` 是指标
2. `magnitude_band / age_band / mirror_rank` 是状态或指标
3. 它们都不是默认 runtime 信号

---

## 4. 五类正式分类

## 4.1 对象

**定义**：系统承认其独立存在、能被单独追踪、能拥有属性与历史的单位。

**判定问题**：

1. 它能否拥有自己的生命周期
2. 它能否被唯一标识
3. 它能否独立积累状态、事件、指标

**典型例子**：

- 股票
- 行业
- 市场
- pivot
- wave
- trade
- portfolio

## 4.2 状态

**定义**：对象在某一时刻或某一阶段所处的枚举条件。

**判定问题**：

1. 它是不是附着在某个对象上
2. 它是不是在描述“当前处于什么条件”
3. 它是不是通常可枚举

**典型例子**：

- `UP / DOWN`
- `active / completed`
- `mainstream / countertrend`
- `NORMAL / STRONG / EXTREME`

## 4.3 事件

**定义**：在某个时间点发生、会改变对象状态或触发后续判断的离散发生。

**判定问题**：

1. 它是否强调“发生了”
2. 它是否带有时间戳或确认点
3. 它是否会改变后续状态或判断路径

**典型例子**：

- 突破
- 失败测试
- 确认拐点
- 入场
- 止损
- 退出

## 4.4 指标

**定义**：对对象某种属性的数值化测量结果。

**判定问题**：

1. 它是不是数值、比例、排名、分位、计数
2. 它是不是在测量，而不是在决定
3. 它是不是通常可以被比较、排序或聚合

**典型例子**：

- 收益率
- PF
- MDD
- percentile
- rank
- support ratio

## 4.5 信号

**定义**：系统基于对象、状态、事件、指标之后，输出的决策结论或执行结论。

**判定问题**：

1. 它是否回答“做不做”
2. 它是否会驱动入场、拒单、减仓、退出、观察
3. 它是否属于 runtime 或治理输出

**典型例子**：

- 可买
- 拒单
- 减仓
- 全平
- 进入观察

---

## 5. 第一战场边界表

### 5.1 对象

- 主线设计包
- migration package
- promoted subset
- execution phase
- run artifact

### 5.2 状态

- `active / completed / archived`
- `default / candidate / retained`
- `trace_complete / boundary_passed`

### 5.3 事件

- phase closeout
- gate decision
- promotion decision
- replay completion

### 5.4 指标

- trade_count
- EV
- PF
- MDD
- coverage
- idempotency result

### 5.5 信号

- `go / no-go`
- `promote / retain / retire`
- `default runtime unchanged / changed`

### 5.6 常见误分类

1. `PF / EV / MDD` 不是信号，只是指标。
2. `phase_6_candidate_validated` 不是对象，它是治理状态或治理结论。
3. `migration package` 是对象，不是一次事件。

---

## 6. 第二战场边界表

### 6.1 对象

- setup family
- trigger family
- trade provenance record
- rejection case
- attribution cohort

### 6.2 状态

- setup 成立 / 未成立
- trigger armed / fired
- accepted / rejected
- clean / damaged

### 6.3 事件

- breakout
- failed test
- pullback acceptance
- trigger fire
- rejection
- entry

### 6.4 指标

- setup win rate
- trigger EV
- attribution decomposition
- opportunity count
- rejection rate

### 6.5 信号

- `allow entry`
- `reject entry`
- `watch only`

### 6.6 常见误分类

1. `BOF / PB / BPB / TST / CPB` 首先是 trigger family，不是对象本体。
2. 某个 trigger 的 `EV` 不是 alpha 本身，它只是 alpha 的统计读数。
3. provenance 是可追溯记录对象，不是单纯指标。

---

## 7. 第三战场边界表

### 7.1 对象

- position
- tranche
- exit leg
- risk budget
- sizing method

### 7.2 状态

- test-size / full-size
- in-position / flat
- partial-exit active
- trail active

### 7.3 事件

- add position
- partial exit
- stop move
- full exit

### 7.4 指标

- notional
- risk per trade
- position utilization
- average holding days
- exit distribution

### 7.5 信号

- `open small`
- `open full`
- `trim`
- `full exit`
- `do not size up`

### 7.6 常见误分类

1. `FIXED_NOTIONAL_CONTROL` 和 `Williams fixed risk` 是仓位法对象，不是信号。
2. `25/75` 是执行结构，不是 alpha。
3. `partial exit outperforms` 是统计结论，不是默认 runtime 信号。

---

## 8. 第四战场边界表

### 8.1 对象

- 价格对象：股票 / 行业 / 市场
- pivot
- wave
- structure record
- mirror record
- conditioning cohort

### 8.2 状态

- `UP / DOWN`
- `active / completed`
- `mainstream / countertrend`
- `NORMAL / STRONG / EXTREME`
- `2B_TOP / 2B_BOTTOM`
- `123_STEP1 / STEP2 / STEP3`

### 8.3 事件

- confirmed pivot
- failed extreme test
- turn confirmation
- 2B confirmation
- prior pivot breach

### 8.4 指标

- wave magnitude
- wave duration
- extreme density
- percentile
- band
- gene_score
- mirror rank
- support ratio

### 8.5 信号

当前冻结边界下，第四战场默认不直接产出 runtime 信号。

它当前只允许产出：

1. 历史解释输出
2. 观察层标签
3. attribution / dashboard / mirror readout

如果未来要升格为硬门，必须另开治理流程。

### 8.6 常见误分类

1. `trend` 是结构状态，不是指标。
2. `wave` 是对象，不是指标。
3. `1-2-3 / 2B` 首先是结构状态和确认事件，不是自动交易信号。
4. `gene_score` 是指标，不是默认信号。
5. `conditioning readout` 是条件层解释，不是默认过滤器。

---

## 9. 跨战场最容易混掉的词

### 9.1 BOF

当前系统内应理解为：

1. 第二战场的 trigger family
2. 第一战场默认运行路径所采用的入场触发语义

不应理解为：

1. 一个对象
2. 一个仓位法
3. 第四战场基础定义

### 9.2 Alpha

当前系统内应理解为：

1. 第二战场对某类 setup / trigger 的可重复收益能力判断

不应理解为：

1. 单笔赚钱结果
2. 某个分数本身
3. 某种仓位法

### 9.3 Gene

当前系统内应理解为：

1. 第四战场的价格对象历史语境层
2. 当前默认运行中的 `sidecar / attribution layer`

不应理解为：

1. 当前默认 runtime 信号源
2. 新的统一排序器
3. 可直接替代第二战场的 trigger 语言

### 9.4 IRS / MSS

当前系统内应理解为：

1. 历史主线吸收遗产
2. 今日系统中的语义参考边界

不应理解为：

1. 当前默认 runtime 仍在启用的排序/控仓层

---

## 10. 运行层特别边界

截至本文件版本，以下边界正式成立：

1. 默认 runtime 决策主要来自第一战场冻结链路。
2. 第二战场可以提供 trigger 与 entry allow/reject 语义。
3. 第三战场可以提供 sizing / exit 决策语义。
4. 第四战场默认只提供 sidecar / attribution / mirror / conditioning readout。

一句话：

`第四战场解释，第二战场触发，第三战场执行，第一战场治理。`

---

## 11. 当前冻结结论

1. 对象、状态、事件、指标、信号必须严格分层。
2. 所有跨战场文档和代码命名，若使用这些词，必须优先服从本表。
3. 若某个研究对象想从“指标/观察层”升格为“默认 runtime 信号”，必须显式经过治理。
4. 当前最容易被误升格的是第四战场的历史分位、band、mirror、conditioning 结果，必须持续防止偷升格。

---

## 12. 待续文件

本文件之后，下一份必须继续补齐的是：

1. `gene-foundational-definition-freeze-20260317.md`

只有把第四战场基础定义冻结稿写完，四战场的“概念骨架”才算真正闭环。
