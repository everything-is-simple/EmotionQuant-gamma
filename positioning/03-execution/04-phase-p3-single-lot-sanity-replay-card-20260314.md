# Phase P3 Single-Lot Sanity Replay Card

**日期**: `2026-03-14`  
**阶段**: `Positioning / P3`  
**对象**: `第三战场第四张执行卡`  
**状态**: `Active`

---

## 1. 目标

`P3` 只做一件事：

`把 P2 的 provisional retained candidate 拉回 SINGLE_LOT_CONTROL 环境，回答它们到底是真 sizing edge，还是只是更低暴露下的更好形状。`

这一步不是重新打开全 family matrix。

它只服务一个治理问题：

`WILLIAMS_FIXED_RISK / FIXED_RATIO 是否值得继续进入 retained-or-no-go。`

---

## 2. 本卡要回答的问题

`P3` 只回答下面 5 个问题：

1. `WILLIAMS_FIXED_RISK` 回到 `single-lot` 环境后还能否维持风险调整改善
2. `FIXED_RATIO` 回到 `single-lot` 环境后还能否维持风险调整改善
3. 它们相对 `SINGLE_LOT_CONTROL` 的 `trade_count / EV / PF / MDD / path metrics` 是改善、持平，还是退化
4. 哪一条 candidate 可以继续进入 retained-or-no-go
5. 哪一条 candidate 应被降级为 `watch` 或直接 `no_go`

---

## 3. 冻结输入

本卡执行时，以下变量继续冻结，不允许漂移：

1. `pipeline baseline = dtt / v0_01_dtt_pattern_only`
2. `entry family = BOF control only`
3. `no IRS`
4. `no MSS`
5. `signal_date = T / execute_date = T+1 / fill = T+1 open`
6. `exit semantics = current Broker full-exit stop-loss + trailing-stop`
7. `control baseline = SINGLE_LOT_CONTROL`

本卡唯一允许进入 replay 的 candidate 固定为：

1. `WILLIAMS_FIXED_RISK`
2. `FIXED_RATIO`

---

## 4. 当前不允许做的事

在 `P3` 完成前，当前明确不允许：

1. 重新把所有 sizing family 拉回双环境大矩阵
2. 在 sanity replay 前直接宣布默认仓位升级
3. 提前打开 `cross-exit sensitivity`
4. 把新的 exit 机制混入 replay
5. 提前打开 `partial-exit / scale-out lane`

---

## 5. 本卡交付物

本卡正式交付物固定为：

1. 一份 `single-lot sanity replay matrix`
2. 一份 `single-lot sanity replay digest`
3. 一张 `P3 formal record`

矩阵至少要覆盖：

1. `trade_count`
2. `expected_value`
3. `profit_factor`
4. `max_drawdown`
5. `trade_sequence_max_drawdown`
6. `net_pnl`
7. `cash / slot pressure diagnostics`

---

## 6. 下一步出口

`P3` 完成后，下一步执行顺序固定为：

1. `P4 retained-or-no-go`
2. `cross-exit sensitivity`（仅在 retained sizing candidate 明确存在后才允许打开）
3. `P10 partial-exit contract lane`

---

## 7. 一句话结论

`P3` 的职责是把 P2 的 provisional retained candidate 拉回 low-exposure floor 环境，检查它们是不是只在 fixed-notional 环境下看起来成立。`
