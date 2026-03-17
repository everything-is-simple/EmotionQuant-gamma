# 第三战场基础定义冻结稿

**状态**: `Active`  
**日期**: `2026-03-17`  
**适用范围**: `positioning / blueprint / normandy / gene / docs/spec/common`  
**文件定位**: `第三战场基础定义的正式冻结稿（第一版）`

---

## 1. 目的

这份文件不回答：

1. 哪个 sizing family 统计最优
2. `25/75` 是否该立刻升格
3. `Williams fixed risk` 最终能不能进默认运行

这份文件回答：

1. 第三战场到底在研究什么对象
2. `sizing / risk / tranche / partial-exit / full-exit / control` 这些词在系统里如何区分
3. 为什么第三战场必须先把“买多少”和“卖多少”拆开

---

## 2. 权威顺序

第三战场基础定义，统一按以下顺序服从：

1. B类系统与风险源  
   `2013.交易圣经`  
   `2014.Ernest P. Chan`
2. 第三战场实现规格  
   [`../../../../positioning/02-implementation-spec/01-positioning-baseline-and-sizing-spec-20260313.md`](../../../../positioning/02-implementation-spec/01-positioning-baseline-and-sizing-spec-20260313.md)  
   [`../../../../positioning/02-implementation-spec/02-partial-exit-contract-spec-20260314.md`](../../../../positioning/02-implementation-spec/02-partial-exit-contract-spec-20260314.md)
3. 第三战场正式 records 与 closeout
4. 当前 broker / engine / report 实现

---

## 3. 第三战场的正式问题域

第三战场正式回答的是：

1. `买多少`
2. `卖多少`
3. 在统一 entry baseline 下，哪些仓位与退出合同更能保护账户生存

第三战场正式不回答的是：

1. `买什么`
2. `何时买`
3. 新的 PAS / IRS / MSS 是否成立

---

## 4. 必须冻结的基础定义

## 4.1 Positioning

**系统冻结定义**

`positioning` 指的是围绕头寸规模、风险暴露、减仓路径和持仓生命周期控制而展开的独立问题域。

**结论**

第三战场研究的是执行资本控制，不是 alpha 发现。

---

## 4.2 Sizing

**系统冻结定义**

`sizing` 是决定首次建仓数量或风险预算分配方式的规则族。

当前正式 family 包括：

1. `single-lot control`
2. `fixed-notional control`
3. `fixed-risk`
4. `fixed-capital`
5. `fixed-ratio`
6. `fixed-unit`
7. `williams-fixed-risk`
8. `fixed-percentage`
9. `fixed-volatility`

**结论**

`sizing` 回答的是首次建仓规模，不自动包含卖出语义。

---

## 4.3 Control

**系统冻结定义**

`control` 是在统一 baseline 下用来对照和裁决的方法族运行口径。

例如：

1. `FIXED_NOTIONAL_CONTROL`
2. `FULL_EXIT_CONTROL`
3. `SINGLE_LOT_CONTROL` 作为 floor sanity

**结论**

control 是正式实验口径，不等同于任何单一本书公式。

---

## 4.4 Risk Unit

**系统冻结定义**

`risk unit` 指的是单笔交易允许承担的损失预算单位。

它可以通过不同 sizing family 被表达，但不能和“下多少股”简单画等号。

**结论**

风险单位是约束语言，不是某个具体仓位算法本身。

---

## 4.5 Operating Control 与 Floor Sanity

**系统冻结定义**

1. `operating control`：当前允许作为正式运行口径的控制组
2. `floor sanity`：用于校验候选方法是否连最低生存线都站不住的下限对照组

在第三战场当前正式口径里：

1. `FIXED_NOTIONAL_CONTROL` 是 operating control
2. `SINGLE_LOT_CONTROL` 是 floor sanity

**结论**

这两者都不是“最好”，而是治理上承担不同角色。

---

## 4.6 Full Exit

**系统冻结定义**

`full exit` 指一次性清空剩余仓位的退出语义。

在当前系统中，以下路径必须保持 full exit：

1. `STOP_LOSS`
2. `FORCE_CLOSE`

**结论**

full exit 是退出合同的一种，不是所有卖出动作的总称。

---

## 4.7 Partial Exit / Scale-Out

**系统冻结定义**

`partial exit` 或 `scale-out` 指一个 position 在生命周期中通过多腿 `SELL` 逐步减少仓位的退出合同。

它至少包含：

1. 多腿 sell order
2. leg-aware 身份
3. 剩余仓位跟踪
4. 报告与 trace 可回放

**结论**

partial exit 首先是合同与状态机问题，不先是参数优劣问题。

---

## 4.8 Tranche

**系统冻结定义**

`tranche` 指同一 position 内按计划拆出的头寸分段。

在第三战场里，它既可以服务建仓，也可以服务退出，但当前正式已实现重点在退出腿。

**结论**

tranche 是结构分段单位，不自动等于“分批买”或“分批卖”的某种特定战术。

---

## 4.9 Position Lifecycle

**系统冻结定义**

position 必须被视作有生命周期的对象，而不是只靠成交对碰出来的抽象结果。

最少应承认：

1. `OPEN`
2. `OPEN_REDUCED`
3. `PARTIAL_EXIT_PENDING`
4. `FULL_EXIT_PENDING`
5. `CLOSED`

**结论**

没有 position lifecycle，就没有正式 partial-exit 语义。

---

## 4.10 Williams Fixed Risk

**系统冻结定义**

`Williams fixed risk` 在第三战场里是 sizing family 的一个候选方法，不是风险语言本身，也不是默认系统 truth。

**结论**

凡是书里来的公式，到第三战场都先是 candidate method，不是直接系统宪法。

---

## 5. 第三战场的正式边界

第三战场正式冻结以下边界：

1. 不重开 `买什么 / 何时买`
2. 不让 `MSS / IRS` 重新进入仓位决策
3. 先做 sizing lane，再做 partial-exit lane
4. 未经正式治理，不把 retained candidate 直接写成默认 runtime

一句话：

`第三战场先把资本控制语言写干净，再谈哪条算法值得升格。`

---

## 6. 对其他战场的约束

### 6.1 对第一战场

第一战场只能接收经过第三战场正式裁决后的 control，不得跳过 replay 直接抄方法名。

### 6.2 对第二战场

第二战场负责 trigger truth，第三战场不得反向定义 trigger。

### 6.3 对第四战场

第四战场可以提供环境解释和 cohort 切片，但当前不得直接充当 sizing hard gate。

---

## 7. 第一版正式结论

第一版冻结结论如下：

1. 第三战场的本体是资本控制语言，不是新 alpha
2. `sizing` 和 `partial-exit` 必须分两条问题线处理
3. `control` 是正式实验口径，不等同于书上公式
4. `partial-exit` 首先是合同与状态机问题
5. `FIXED_NOTIONAL_CONTROL` 与 `SINGLE_LOT_CONTROL` 在当前治理里承担不同角色

一句话收口：

`第三战场要先像法律文本一样定义仓位与退出，再去比较方法优劣。`
