# 第二战场基础定义冻结稿

**状态**: `Active`  
**日期**: `2026-03-17`  
**适用范围**: `normandy / blueprint / positioning / gene / docs/spec/common`  
**文件定位**: `第二战场基础定义的正式冻结稿（第一版）`

---

## 1. 目的

这份文件不回答：

1. 哪个 `pattern family` 当前统计最好
2. 哪个 retained branch 值得立刻升格
3. 哪个执行改动该进默认 runtime

这份文件回答：

1. 第二战场到底在研究什么对象
2. 第二战场里哪些词是基础定义，哪些只是实验标签
3. `alpha / setup / trigger / provenance / quality / exit damage` 这些词在系统里到底是什么意思

一句话：

`第二战场先定义“买什么 / 为什么买”的语义骨架，再谈哪一支统计更强。`

---

## 2. 权威顺序

第二战场基础定义，统一按以下顺序服从：

1. A类概念源  
   `2020.(Au)LanceBeggs`  
   `2020.(Au)AL BROOKS`  
   `2021.Bob Volman`
2. 第二战场设计与实现规格  
   [`../../../../normandy/02-implementation-spec/01-alpha-provenance-and-exit-decomposition-spec-20260311.md`](../../../../normandy/02-implementation-spec/01-alpha-provenance-and-exit-decomposition-spec-20260311.md)  
   [`../../../../normandy/02-implementation-spec/09-bof-pinbar-broker-frozen-go-spec-20260312.md`](../../../../normandy/02-implementation-spec/09-bof-pinbar-broker-frozen-go-spec-20260312.md)
3. 第二战场正式 records 与 closeout
4. 当前代码与回测实现

---

## 3. 第二战场的正式问题域

第二战场正式回答的，是：

1. `PAS raw alpha` 到底来自哪类 entry shape
2. 同一类 entry 在相同 broker 语义下，哪些 quality branch 更纯
3. 当前收益伤害主要来自 entry 本身，还是来自 exit / execution

第二战场正式不回答的，是：

1. 默认 runtime 该不该立刻改写
2. 仓位该下多大
3. `Gene` 历史环境是否直接当成硬门

---

## 4. 必须冻结的基础定义

## 4.1 Alpha

**系统冻结定义**

`alpha` 在第二战场里，指的是某类 entry family 在统一执行基线下所携带的可重复方向性边际，不是单笔漂亮交易，也不是单一图形名字。

**结论**

`alpha` 是研究对象上的统计性质，不是一个 detector 名称。

---

## 4.2 Setup

**系统冻结定义**

`setup` 是交易背景与结构条件的组合描述，用来回答“这一类机会长什么样、为什么值得等待”。

它强调的是：

1. 背景
2. 结构
3. 支撑阻力 / 测试 / 接受 / 失败关系

**结论**

`setup` 不是最终下单动作；它是 trigger 的上游语义层。

---

## 4.3 Trigger

**系统冻结定义**

`trigger` 是在 setup 已存在前提下，具体触发入场的离散事件。

第二战场当前的正式 trigger family 包括：

1. `BOF`
2. `BPB`
3. `PB`
4. `TST`
5. `CPB`

**结论**

第二战场里，`BOF / BPB / PB / TST / CPB` 首先是 trigger family，不是对象，不是系统总定义。

---

## 4.4 Pattern Family

**系统冻结定义**

`pattern family` 是一组共享同类结构语法与触发逻辑的 trigger 集合。

例如：

1. `BOF family` 可以再分 quality branches
2. `YTC5_ANY` 只是“任意五形态”的实验集合口径，不是一个新的基础对象

**结论**

family 是实验分类单元，不得和基础价格对象混淆。

---

## 4.5 Raw Alpha Provenance

**系统冻结定义**

`raw alpha provenance` 指的是在尽量冻结执行语义、关闭额外前置过滤后，去追问收益边际原始来自哪类 entry family。

它要求：

1. 先冻结 broker
2. 先关闭 `MSS / IRS`
3. 再比较 entry family

**结论**

`provenance` 是来源证明过程，不是一个额外信号。

---

## 4.6 Quality Branch

**系统冻结定义**

`quality branch` 指的是在同一 trigger family 内，对更纯、更严格或更明确表达的子集切片。

例如 `BOF_CONTROL`、`BOF_KEYLEVEL_STRICT`、`BOF_PINBAR_EXPRESSION`、`BOF_KEYLEVEL_PINBAR`。

**结论**

quality branch 是 family 内部切片，不是新的独立 alpha 家族。

---

## 4.7 Exit Damage

**系统冻结定义**

`exit damage` 指的是当 entry family 基本成立时，收益被退出语义或执行路径截断、吞没或扭曲的那部分伤害。

它关注的是：

1. 是否卖坏
2. 伤害来自哪种退出机制
3. 伤害是普遍性的，还是少数极端值截断

**结论**

`exit damage` 是诊断问题域，不是卖出规则本身。

---

## 4.8 Broker-Frozen Comparison

**系统冻结定义**

第二战场当前所有 provenance 与 quality 判定，都必须尽量在同一 broker 语义下完成。

这条边界的作用是：

1. 不让 entry 结论和 exit 结论混在一起
2. 不让第二战场暗中偷改执行层

**结论**

`broker-frozen` 不是一个策略，而是一条研究纪律。

---

## 4.9 Candidate / Retained Branch / No-Go

**系统冻结定义**

1. `candidate`：有初步正读数，但未形成稳定结论
2. `retained branch`：允许保留观察或后续验证，但未升格
3. `no-go`：当前阶段正式裁掉，不再占主线队列

**结论**

这三者都是治理状态，不是交易信号。

---

## 5. 第二战场的正式边界

第二战场正式冻结以下边界：

1. 负责解释 `买什么 / 为什么打`
2. 不负责默认仓位法
3. 不负责默认 runtime promotion
4. 不允许把 `MSS / IRS / Gene` 偷写成前置硬门，再反过来冒充 raw alpha

一句话：

`第二战场先把 entry truth 读干净，再把结果交给第三战场和治理层。`

---

## 6. 对其他战场的约束

### 6.1 对第一战场

第一战场不能直接把第二战场里的 `candidate / retained branch` 写成默认参数。

### 6.2 对第三战场

第三战场消费的是第二战场已经冻结的 baseline 或 trigger family，不应反过来定义 trigger 语义。

### 6.3 对第四战场

第四战场提供环境与结构解释，但不得反过来抢占第二战场的 trigger 定义权。

---

## 7. 第一版正式结论

第一版冻结结论如下：

1. 第二战场的核心对象不是“股票”本身，而是 `entry family / quality branch / provenance question`
2. `setup` 是背景结构层，`trigger` 是离散入场层，二者不得混为一谈
3. `BOF / BPB / PB / TST / CPB` 首先是 trigger family
4. `raw alpha provenance` 与 `exit damage` 是第二战场两条正式主问题
5. `candidate / retained / no-go` 是治理状态，不是交易信号

一句话收口：

`第二战场的本体是 alpha 语义与伤害诊断，不是“多试几个图形看看哪个收益高”。`
