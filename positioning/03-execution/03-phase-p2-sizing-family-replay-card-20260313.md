# Phase P2 Sizing Family Replay Card

**日期**: `2026-03-13`  
**阶段**: `Positioning / P2`  
**对象**: `第三战场第三张执行卡`  
**状态**: `Closed`

---

## 1. 目标

`P2` 只做一件事：

`在同一条 frozen baseline 下，把首批 sizing family 统一对照 FIXED_NOTIONAL_CONTROL，读出 retained-or-no-go 候选。`

这一步的职责不是优化 exit，也不是改 entry。

它只回答：

`在当前 frozen entry / exit 语义下，哪类 sizing family 真正在“买多少”这个问题上带来可保留的改善。`

这里同时写死一条：

`P2` 不把 `single-lot` 和 `fixed-notional` 扩成两套并行大矩阵。  
`FIXED_NOTIONAL_CONTROL` 负责正式主对照，`SINGLE_LOT_CONTROL` 只保留为 retained candidate 的 floor sanity line。

---

## 2. 本卡要回答的问题

`P2` 只回答下面 5 个问题：

1. `fixed-risk / fixed-capital / fixed-ratio / fixed-unit / williams-fixed-risk / fixed-percentage / fixed-volatility` 各自交出什么长窗读数
2. 它们相对 `FIXED_NOTIONAL_CONTROL` 的改善是收益改善、回撤改善，还是只是放大暴露
3. 哪些 family 只是在 current exit 下看起来有效，哪些更像稳健候选
4. 哪些 family 可以进入下一轮 retained-or-no-go
5. 哪些 family 应直接裁成 `watch` 或 `no-go`
6. 哪些 provisional retained candidate 在回到 `SINGLE_LOT_CONTROL` 的低暴露环境后仍然站得住

---

## 3. 冻结输入

本卡执行时，以下变量继续冻结，不允许漂移：

1. `pipeline baseline = dtt / v0_01_dtt_pattern_only`
2. `entry family = BOF control only`
3. `no IRS`
4. `no MSS`
5. `signal_date = T / execute_date = T+1 / fill = T+1 open`
6. `exit semantics = current Broker full-exit stop-loss + trailing-stop`
7. `canonical control baseline = FIXED_NOTIONAL_CONTROL`
8. `single-lot control = floor sanity line only`

这意味着：

1. `P2` 主矩阵只在 `FIXED_NOTIONAL_CONTROL` 环境下比较 sizing family
2. 不把 `single-lot` 扩成第二套完整 family matrix
3. 只有出现 provisional retained candidate 后，才允许补做 `single-lot sanity replay`

---

## 4. 候选清单

本卡允许进入正式 replay 的 sizing family 固定为：

1. `fixed-risk`
2. `fixed-capital`
3. `fixed-ratio`
4. `fixed-unit`
5. `williams-fixed-risk`
6. `fixed-percentage`
7. `fixed-volatility`

---

## 5. 当前不允许做的事

在 `P2` 完成前，当前明确不允许：

1. 把 `STOP_ONLY` 或新的 exit package 混进 sizing matrix
2. 把 `MSS / IRS` 重新接回仓位决定
3. 在首轮 family replay 完成前，就把所有 sizing family 扩成 `single-lot + fixed-notional` 双环境并行大矩阵
4. 提前打开 `partial-exit / scale-out lane`
5. 先做 retained candidate 的参数微扫，再补完整 family replay

---

## 6. 本卡交付物

本卡正式交付物固定为：

1. 一份 `sizing family matrix`
2. 一份 `sizing family digest`
3. 一张 `P2 formal record`
4. 如出现 provisional retained candidate，则补一份 `single-lot sanity replay note`

矩阵至少要覆盖：

1. `net_pnl`
2. `ev_per_trade`
3. `profit_factor`
4. `max_drawdown`
5. `trade_count`
6. `avg_position_size`
7. `exposure_utilization`
8. `cash / slot pressure diagnostics`
9. `ruin-sensitive path metrics`

---

## 7. 下一步出口

`P2` 完成后，下一步执行顺序固定为：

1. `P3 single-lot sanity replay`（仅对 provisional retained candidate 打开）
2. `P4 retained-or-no-go`
3. `cross-exit sensitivity`（仅在 retained sizing candidate 通过 single-lot sanity 后才允许打开）
4. `P10 partial-exit contract lane`

---

## 8. 一句话结论

`P2` 的职责是先在更接近真实运营的 fixed-notional 环境下筛出 sizing 候选，再用 single-lot 做 retained candidate 的下限复核。`
