# SB Refinement Or No-Go Spec

**状态**: `Active`  
**日期**: `2026-03-12`  
**对象**: `Normandy / N1.10 SB refinement or no-go`

---

## 1. 定位

`N1.10` 是 `N1.5` 之后对 `SB` 的正式处置卡。

它要回答的不是：

`SB 在理论上像不像 continuation alpha。`

这个问题在 `N1.5` 已经回答过一半了。

`N1.10` 当前只回答：

`当前 full SB detector 还有没有继续 refinement 的主队列资格，还是已经足够明确地进入 no-go。`

---

## 2. 当前已知前提

截至 `2026-03-12`，下面这些结论已经固定：

1. `BOF` 继续是 `PAS raw alpha baseline`
2. `FB family` 已完成 refinement 与 stability follow-up，但当前只保留 `FB_BOUNDARY` 为 watch candidate
3. `N1.5` 已经证明 `SB` 的问题不在独立性，而在 detector 还没有收缩成正向 edge
4. `SB` 当前长窗读数固定为：
   - `trade_count = 648`
   - `EV = -0.01455`
   - `MDD = 0.64103`
   - `overlap_rate_vs_bof_control = 0.0`

因此 `N1.10` 的职责不是直接把 `SB` 升格，而是先把它读完。

---

## 3. 当前要回答的问题

`N1.10` 固定只回答四个问题：

1. `SB` 当前负向读数是时间上局部事故，还是跨年持续存在
2. `SB` 当前 detector 是否明显过宽，导致 selected entries 与真实成交严重脱节
3. 是否存在值得保留的窄 watch branch
4. 正式裁决应是 `refinement continue` 还是 `no-go`

---

## 4. 当前实验允许做什么

当前实验固定允许：

1. 继承 `N1.5` 的 `volman_alpha_matrix`
2. 读取同一 working DB 的 lifecycle pairing
3. 用 `buy-fill sequence -> exit sequence` 重建 `SB` 的 paired trades
4. 输出一份正式 `sb_refinement_report`
5. 固定 `SB` 当前去留与 `Normandy` 主队列下一张卡

当前实验固定不允许：

1. 在本卡直接修改 `SB detector` 进入运行链
2. 重开 `FB` family 问题
3. 把 `RB_FAKE / PB / TST / CPB` 拉回本卡
4. 在本卡顺手打开 `N2`

---

## 5. 当前证据对象

`N1.10` 当前默认消费：

1. `volman_alpha_matrix`
2. `N1.5 second-alpha record`

本卡新增正式 evidence：

3. `sb_refinement_report`

---

## 6. 出场条件

`N1.10` 只有在以下条件之一满足时才允许出场：

1. 已明确 `SB` 仍值得继续占用主队列做 refinement
2. 已明确 `SB` 当前 full detector 路线进入 `no-go`，并写明是否保留窄 watch branch

---

## 7. 当前一句话方案

`围绕 SB 做 formal refinement / no-go readout：先证明它到底是 detector 太宽，还是对象本身当前不成立，再把 full route 与窄 watch branch 的去留写死。`
