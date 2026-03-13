# Phase P0 Baseline Freeze Card

**日期**: `2026-03-13`  
**阶段**: `Positioning / P0`  
**对象**: `第三战场第一张执行卡`  
**状态**: `Active`

---

## 1. 目标

`P0` 只做一件事：

`把第三战场后续所有 sizing 实验所依赖的 baseline、对照组和禁止混问边界正式冻结。`

如果这一步不先做，后面的 sizing 对照都会混进：

1. entry 变化
2. exit 变化
3. `MSS / IRS` 影响
4. execution 语义漂移

---

## 2. 本卡要回答的问题

`Positioning` 当前首先要回答的是：

`后续所有“买多少 / 卖多少”实验，到底是基于哪一条固定交易骨架在比。`

所以本卡只回答下面 4 个问题：

1. 当前固定 entry baseline 是什么
2. 当前固定 exit baseline 是什么
3. 当前 control sizing 是什么
4. 后续哪些变量暂时不许动

---

## 3. 冻结对象

本卡完成后，第三战场必须冻结：

1. `pipeline baseline = legacy_bof_baseline`
2. `no IRS`
3. `no MSS`
4. `signal_date = T / execute_date = T+1 / fill = T+1 open`
5. `exit semantics = current Broker full-exit stop-loss + trailing-stop`
6. `buy-side sizing denominator = current Broker risk budget / max position cap semantics`

当前 control 组固定为两条：

1. `single-lot control`
2. `fixed-notional control`

---

## 4. 首批候选注册表

本卡完成后，后续允许进入 replay 的 sizing family 固定为：

1. `fixed-risk`
2. `fixed-capital`
3. `fixed-ratio`
4. `fixed-unit`
5. `williams-fixed-risk`
6. `fixed-percentage`
7. `fixed-volatility`

它们当前都还不是 retained candidate。

它们只是：

`被允许进入 Positioning 第三战场正式对照矩阵的首批仓位方法。`

---

## 5. 本卡交付物

本卡的正式交付物固定为：

1. 一份 baseline freeze record
2. 一份 control sizing manifest
3. 一张后续 execution queue

后续执行顺序固定为：

1. `P1 null control matrix`
2. `P2~P8 sizing family replay`
3. `P9 retained-or-no-go`
4. `P10 partial-exit contract lane`（仅在前面完成后才允许打开）

---

## 6. 验收标准

本卡通过的条件固定为：

1. 已写出 baseline freeze formal record
2. 已把 `control / candidate / forbidden variables` 写死
3. 已明确下一张执行卡是 `P1 null control matrix`
4. 已同步共享治理入口，确保仓库不再把研究线误写成只有 `Normandy`

---

## 7. 当前不允许做的事

在 `P0` 完成前，当前明确不允许：

1. 直接跑 `fixed-risk / fixed-ratio / fixed-volatility` 长窗矩阵
2. 先做参数微扫，再补 baseline freeze
3. 把 `partial-exit` 偷渡进 sizing replay
4. 把 `MSS / IRS` 重新接回仓位决定

---

## 8. 一句话结论

`P0` 的职责不是找最优仓位，而是先把“后面到底在比什么”冻结下来。`
