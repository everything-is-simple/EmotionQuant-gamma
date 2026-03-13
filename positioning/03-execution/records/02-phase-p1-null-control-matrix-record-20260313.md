# Phase P1 Null Control Matrix Record

**日期**: `2026-03-13`  
**阶段**: `Positioning / P1`  
**对象**: `第三战场第二张执行卡 formal readout`  
**状态**: `Closed`

---

## 1. 目标

本文用于把 `P1 / null control matrix` 的正式长窗结论写死。

这张 record 只回答五件事：

1. `single-lot control` 和 `fixed-notional control` 在同一 frozen baseline 下各自交出了什么结果
2. 两条 control 的交易参与一致性是否足够高
3. 它们的收益差异主要来自哪里
4. 后续 `P2~P8` 应该拿哪条 control 当正式对照尺子
5. 当前哪些结论已经明确，哪些路留到下一张卡

---

## 2. Formal Evidence

本卡正式证据固定为：

1. `positioning/03-execution/evidence/positioning_p1_null_control_dtt_bof_control_no_irs_no_mss_w20230103_20260224_t043316__null_control_matrix.json`
2. `positioning/03-execution/evidence/positioning_p1_null_control_digest_dtt_bof_control_no_irs_no_mss_w20230103_20260224_t052647__null_control_digest.json`

窗口固定为：

`2023-01-03 -> 2026-02-24`

冻结前提固定为：

1. `pipeline baseline = dtt / v0_01_dtt_pattern_only`
2. `entry family = BOF control only`
3. `no IRS`
4. `no MSS`
5. `signal_date = T / execute_date = T+1 / fill = T+1 open`
6. `exit semantics = current Broker full-exit stop-loss + trailing-stop`

---

## 3. Single-Lot vs Fixed-Notional

### 3.1 交易参与一致性

`single-lot` 与 `fixed-notional` 的交易参与差异有限，足以继续承担后续 sizing replay 的对照职责。

关键读数：

1. `SINGLE_LOT_CONTROL trade_count = 277`
2. `FIXED_NOTIONAL_CONTROL trade_count = 272`
3. `trade_count_ratio = 0.98195`
4. `filled_count_ratio = 0.98195`

这说明：

`fixed-notional` 并没有因为仓位更大而把交易集合打散到失去对照意义。`

### 3.2 暴露尺度与压力形状

`fixed-notional` 真正改变的，不是 entry family，而是资金暴露尺度。

关键读数：

1. `single-lot avg_entry_notional = 4,859.45`
2. `fixed-notional avg_entry_notional = 86,033.06`
3. `avg_notional_scale_ratio = 17.7043`
4. 两条 control 的 `exposure_rate` 都是 `0.95641`

同时，`fixed-notional` 也显式暴露了资金压力：

1. `single-lot cash_pressure_reject_rate = 0.0`
2. `fixed-notional cash_pressure_reject_rate = 0.13953`
3. `single-lot max_position_reject_count = 64`
4. `fixed-notional max_position_reject_count = 20`

也就是说：

`single-lot` 更像最低噪声 floor control；  
`fixed-notional` 更像真实 sizing family 后续会面对的资金约束环境。`

### 3.3 收益与回撤形状

两条 control 都有正读数，但它们承担的是不同角色。

`SINGLE_LOT_CONTROL`

1. `EV = 0.00598`
2. `PF = 2.38860`
3. `MDD = 0.03530`

`FIXED_NOTIONAL_CONTROL`

1. `EV = 0.01068`
2. `PF = 2.39870`
3. `MDD = 0.12068`

当前不能把这组结果误读成：

`fixed-notional = 最优仓位`

它真正说明的是：

`fixed-notional` 在保持交易参与基本一致的同时，把后续 sizing family 需要面对的真实资金暴露与现金压力提前暴露出来了。`

---

## 4. 正式裁决

`P1` 的正式裁决固定为：

1. `FIXED_NOTIONAL_CONTROL = retained canonical control baseline`
2. `SINGLE_LOT_CONTROL = retained floor control, but not canonical`
3. 当前不允许把 `fixed-notional` 直接翻译成“主线默认仓位已经确定”
4. 后续 `P2~P8 sizing family replay` 统一以 `FIXED_NOTIONAL_CONTROL` 为主对照尺子
5. `single-lot` 保留为最低噪声 sanity line，用于防止后续 sizing family 只是在高暴露下放大结果

一句话收口：

`single-lot` 有用，但它更适合做下限参照；  
`fixed-notional` 更适合做第三战场后续正式 replay 的 canonical control baseline。`

---

## 5. 已明确与未明确

当前已经明确的：

1. `single-lot` 不是后续 `P2~P8` 的正式主对照尺子
2. `fixed-notional` 是后续 sizing family replay 的正式 canonical control baseline
3. 第三战场当前仍然只研究 `买多少`
4. `partial-exit / scale-out lane` 继续后置

当前还未回答的：

1. `fixed-risk / fixed-capital / fixed-ratio / fixed-unit / williams-fixed-risk / fixed-percentage / fixed-volatility` 谁更强
2. 是否存在能够正式 retained 的 sizing family
3. retained sizing candidate 是否会对当前 frozen exit semantics 过度敏感

---

## 6. Exit Dependency Note

`P1` 同时正式写下一条边界：

`本轮 sizing 结论只对当前 frozen full-exit semantics 成立。`

因此后续治理顺序固定为：

1. 先完成 `P2~P8 sizing family replay`
2. 若出现 retained sizing candidate，再做 `cross-exit sensitivity` 复核
3. 在 retained sizing candidate 出现之前，不提前把 `STOP_ONLY` 或新的 exit mechanism 混入 `P1` 重新定义问题

---

## 7. 下一张卡

`P1` 完成后的 next main queue card 固定为：

`P2 / sizing family replay`

当前允许进入正式 replay 的路固定为：

1. `fixed-risk`
2. `fixed-capital`
3. `fixed-ratio`
4. `fixed-unit`
5. `williams-fixed-risk`
6. `fixed-percentage`
7. `fixed-volatility`

---

## 8. 正式结论

当前 `P1 null control matrix` 的正式结论固定为：

1. `single-lot` 与 `fixed-notional` 的交易参与一致性足够高，可以继续承担正式 control 职责
2. `single-lot` 更适合作为最低噪声 floor control
3. `fixed-notional` 在暴露尺度、现金压力和后续可比性上更适合作为 `P2~P8` 的 canonical control baseline
4. `P1` 没有宣布默认仓位公式，只是把后续仓位实验到底拿什么当尺子正式定下来
5. 第三战场下一张正式执行卡固定为 `P2 / sizing family replay`

---

## 9. 一句话结论

`P1` 已经把第三战场后续仓位实验的正式尺子定下来：single-lot 留作地板参照，fixed-notional 升格为 canonical control baseline。`
