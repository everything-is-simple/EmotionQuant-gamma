# Phase P2 Sizing Family Replay Record

**日期**: `2026-03-14`  
**阶段**: `Positioning / P2`  
**对象**: `第三战场第三张执行卡 formal readout`  
**状态**: `Closed`

---

## 1. 目标

本文用于把 `P2 / sizing family replay` 的正式长窗结论写死。

这张 record 只回答 5 件事：

1. 首批 `sizing family` 在同一 frozen baseline 下各自交出了什么长窗读数
2. 哪些 family 相对 `FIXED_NOTIONAL_CONTROL` 交出 provisional retained readout
3. 哪些 family 只是 `watch_candidate`
4. 哪些 family 已可直接裁成 `no_go`
5. 下一张卡应该继续回答什么，而不是提前宣布默认仓位公式

---

## 2. Formal Evidence

本卡正式证据固定为：

1. `positioning/03-execution/evidence/positioning_p2_sizing_family_dtt_bof_control_no_irs_no_mss_w20230103_20260224_formal__sizing_family_matrix.json`
2. `positioning/03-execution/evidence/positioning_p2_sizing_family_digest_dtt_bof_control_no_irs_no_mss_w20230103_20260224_formal__sizing_family_digest.json`

窗口固定为：

`2023-01-03 -> 2026-02-24`

冻结前提固定为：

1. `pipeline baseline = dtt / v0_01_dtt_pattern_only`
2. `entry family = BOF control only`
3. `no IRS`
4. `no MSS`
5. `signal_date = T / execute_date = T+1 / fill = T+1 open`
6. `exit semantics = current Broker full-exit stop-loss + trailing-stop`
7. `canonical control baseline = FIXED_NOTIONAL_CONTROL`
8. `single-lot control = floor sanity line only`

同时写死一条：

`本轮 formal evidence 只承认修正后的 trade-equity path metrics 口径。`

---

## 3. Canonical Control Readout

`FIXED_NOTIONAL_CONTROL` 继续作为本轮正式主对照尺子。

关键读数：

1. `trade_count = 277`
2. `EV = 0.01609`
3. `PF = 2.61207`
4. `MDD = 0.12229`
5. `net_pnl = 388,254.93`
6. `cash_pressure_reject_rate = 0.00291`
7. `trade_sequence_max_drawdown = 0.37292`

这说明：

`P2` 当前要找的不是“赚得最多的低暴露公式”，而是  
`在接近真实 fixed-notional 运营环境下，哪类 sizing family 能在不显著恶化压力和路径风险的前提下交出更好的风险调整读数。`

---

## 4. 首批 Family 读数

### 4.1 Provisional Retained Candidates

当前有两条 provisional retained candidate：

`WILLIAMS_FIXED_RISK`

1. `trade_count = 274`
2. `trade_count_ratio_vs_control = 0.98917`
3. `EV = 0.01801`
4. `PF = 2.72958`
5. `MDD = 0.03482`
6. `cash_pressure_reject_rate = 0.01453`
7. `trade_sequence_max_drawdown = 0.14064`
8. `avg_position_size = 31,885.70`

`FIXED_RATIO`

1. `trade_count = 274`
2. `trade_count_ratio_vs_control = 0.98917`
3. `EV = 0.01801`
4. `PF = 2.72959`
5. `MDD = 0.04239`
6. `cash_pressure_reject_rate = 0.01453`
7. `trade_sequence_max_drawdown = 0.15665`
8. `avg_position_size = 34,978.54`

这两条候选的共同特征是：

1. `trade_count` 基本没散
2. `EV / PF` 都高于 control
3. `MDD / trade_sequence_max_drawdown` 都显著低于 control
4. 但 `avg_position_size` 明显小于 control 的 `80,607.77`
5. `net_pnl` 也都显著低于 control

也就是说：

`它们当前更像“更保守、更平顺的 sizing family”，而不是已经证明自己是更优默认仓位。`

### 4.2 Watch Candidates

当前保留为 `watch_candidate` 的 family 是：

1. `FIXED_RISK`
2. `FIXED_VOLATILITY`
3. `FIXED_CAPITAL`
4. `FIXED_PERCENTAGE`

这些对象的共同形状是：

1. 风险路径通常好于 control
2. `EV / PF` 只有轻微改善或与 control 基本持平
3. `net_pnl` 仍明显低于 control
4. 当前证据不足以推进到 retained gate

### 4.3 No-Go

当前已可正式裁成 `no_go` 的 family 是：

`FIXED_UNIT`

关键读数：

1. `EV = 0.01517`
2. `PF = 2.54139`
3. `MDD = 0.22128`
4. `cash_pressure_reject_rate = 0.02035`
5. `net_pnl_delta_vs_control = -477,048.35`

它既没有交出更好的收益效率，也显著恶化了风险路径，不保留后续升格空间。

---

## 5. 正式裁决

`P2` 的正式裁决固定为：

1. `diagnosis = provisional_retained_sizing_candidate_found`
2. `decision = advance_retained_candidate_to_single_lot_sanity_replay`
3. `WILLIAMS_FIXED_RISK` 与 `FIXED_RATIO` 正式进入 provisional retained 队列
4. `FIXED_RISK / FIXED_VOLATILITY / FIXED_CAPITAL / FIXED_PERCENTAGE` 保留为 watch
5. `FIXED_UNIT` 正式 `no_go`

但这里必须同时写死一条边界：

`provisional retained != 默认仓位已确定`

当前最关键的未决问题不是：

`谁的 EV / PF 更高`

而是：

`WILLIAMS_FIXED_RISK / FIXED_RATIO 的改善，到底是真正的 sizing edge，还是主要来自显著降低了 capital deployment。`

---

## 6. 已明确与未明确

当前已经明确的：

1. `P2` 已经产出 provisional retained sizing candidate
2. `WILLIAMS_FIXED_RISK` 当前是更干净的 provisional leader
3. `FIXED_RATIO` 也保持推进资格
4. `FIXED_UNIT` 已经可以退出主队列

当前还未回答的：

1. 这两个 provisional retained candidate 在 `single-lot` 低暴露环境下是否仍然成立
2. 它们的优势是否只是 fixed-notional 环境下的保守降杠杆结果
3. 谁能真正通过 retained-or-no-go 的下一道门

---

## 7. 下一张卡

`P2` 完成后的 next main queue card 固定为：

`P3 / single-lot sanity replay`

当前只允许把下面两条对象带入下一张卡：

1. `WILLIAMS_FIXED_RISK`
2. `FIXED_RATIO`

`single-lot sanity replay` 的职责固定为：

1. 回到 `SINGLE_LOT_CONTROL` 环境复核这两条 provisional retained candidate
2. 判断它们是否仍然保持优于 floor control 的风险调整改善
3. 判断它们是否只是因为 fixed-notional 环境下暴露下降而显得更好

---

## 8. 正式结论

当前 `P2 sizing family replay` 的正式结论固定为：

1. 首批 sizing family 里已经出现 provisional retained candidate
2. 当前 provisional leader 是 `WILLIAMS_FIXED_RISK`
3. `FIXED_RATIO` 也保持推进资格
4. 这两条候选都呈现出“更低暴露、更低路径风险、更高 EV/PF、但更低 net_pnl”的共同形状
5. 因此 `P2` 当前不能宣布默认仓位升级，只能推进到 `single-lot sanity replay`

---

## 9. 一句话结论

`P2` 已经把首批 sizing family 跑成了“有候选，但还不能升格”的正式读数：WILLIAMS_FIXED_RISK 与 FIXED_RATIO 可以继续，但必须先过 single-lot sanity replay。`
