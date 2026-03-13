# Phase P3 Single-Lot Sanity Replay Record

**日期**: `2026-03-14`  
**阶段**: `Positioning / P3`  
**对象**: `第三战场第四张执行卡 formal readout`  
**状态**: `Closed`

---

## 1. 目标

本文用于把 `P3 / single-lot sanity replay` 的正式长窗结论写死。

这张 record 只回答 5 件事：

1. `WILLIAMS_FIXED_RISK / FIXED_RATIO` 拉回 `SINGLE_LOT_CONTROL` 环境后分别交出了什么正式读数
2. 它们是否还能被诚实地读成 `sanity_survivor`
3. 哪些对象只能保留为 `sanity_watch`
4. 当前是否仍存在可继续升格的 retained sizing candidate
5. 下一张卡应如何切换到 `no retained candidate case`

---

## 2. Formal Evidence

本卡正式证据固定为：

1. `positioning/03-execution/evidence/positioning_p3_single_lot_sanity_dtt_bof_control_no_irs_no_mss_w20230103_20260224_formal__single_lot_sanity_matrix.json`
2. `positioning/03-execution/evidence/positioning_p3_single_lot_sanity_digest_dtt_bof_control_no_irs_no_mss_w20230103_20260224_formal__single_lot_sanity_digest.json`

窗口固定为：

`2023-01-03 -> 2026-02-24`

冻结前提固定为：

1. `pipeline baseline = dtt / v0_01_dtt_pattern_only`
2. `entry family = BOF control only`
3. `no IRS`
4. `no MSS`
5. `signal_date = T / execute_date = T+1 / fill = T+1 open`
6. `exit semantics = current Broker full-exit stop-loss + trailing-stop`
7. `control baseline = SINGLE_LOT_CONTROL`
8. `只允许 replay P2 的两个 provisional retained candidate`

---

## 3. Floor Control Readout

`SINGLE_LOT_CONTROL` 继续作为本卡的正式 floor sanity 尺子。

关键读数：

1. `trade_count = 277`
2. `EV = 0.00598`
3. `PF = 2.38860`
4. `MDD = 0.03530`
5. `net_pnl = -21,654.98`
6. `cash_pressure_reject_rate = 0.00000`
7. `trade_sequence_max_drawdown = 0.04662`
8. `risk_adjusted_ev = 0.16946`

这说明：

`P3` 当前要回答的不是“谁在 fixed-notional 环境下更像样”，而是  
`候选 sizing family 一旦被拉回 low-deployment floor 环境，是否仍能保住足够干净的改善形状。`

---

## 4. Candidate Readout

### 4.1 `WILLIAMS_FIXED_RISK`

1. `verdict = sanity_watch`
2. `trade_count = 274`
3. `trade_count_ratio_vs_control = 0.98917`
4. `EV = 0.01801`
5. `PF = 2.72958`
6. `MDD = 0.03482`
7. `trade_sequence_max_drawdown = 0.14064`
8. `cash_pressure_reject_rate = 0.01453`

### 4.2 `FIXED_RATIO`

1. `verdict = sanity_watch`
2. `trade_count = 274`
3. `trade_count_ratio_vs_control = 0.98917`
4. `EV = 0.01801`
5. `PF = 2.72959`
6. `MDD = 0.04239`
7. `trade_sequence_max_drawdown = 0.15665`
8. `cash_pressure_reject_rate = 0.01453`

这两条候选在 `single-lot` floor 环境下呈现出的共同形状是：

1. `trade_count` 基本没散
2. `EV / PF` 仍高于 floor control
3. 但都重新引入了正向 `cash_pressure_delta`
4. `trade_sequence_max_drawdown` 都显著高于 floor control
5. `FIXED_RATIO` 的 `MDD` 也重新高于 floor control
6. 当前证据不足以把它们诚实地升级为 `sanity_survivor`

也就是说：

`它们在 fixed-notional 环境下的漂亮读数，无法直接被翻译成“single-lot floor 环境下依旧成立的 clean sizing edge”。`

---

## 5. 正式裁决

`P3` 的正式裁决固定为：

1. `diagnosis = no_candidate_survives_single_lot_sanity`
2. `decision = write_p3_record_and_prepare_p4_no_retained_case`
3. `survivors = []`
4. `WILLIAMS_FIXED_RISK` 与 `FIXED_RATIO` 均降级为 `sanity_watch`
5. `PX1 / cross-exit sensitivity` 继续保持锁住

这里必须同时写死一条边界：

`sanity_watch != retained sizing candidate`

当前最关键的正式结论不是：

`这两个 candidate 在 floor 环境下完全失败`

而是：

`它们都没有通过“single-lot sanity survivor”这道门，因此当前不能再把任何对象写成 retained sizing candidate。`

---

## 6. 已明确与未明确

当前已经明确的：

1. `P2` 的两条 provisional retained candidate 都没有通过 `single-lot sanity`
2. 当前不存在 `sanity_survivor`
3. `WILLIAMS_FIXED_RISK / FIXED_RATIO` 最多只配保留为 residual watch
4. `PX1 / cross-exit sensitivity` 当前不具备打开条件

当前还未回答的：

1. `P4` 应如何把这轮结果正式裁成 `no retained candidate case`
2. sizing lane 在没有 retained candidate 的前提下应如何收口和迁移边界
3. 是否存在值得未来重开的全新 sizing hypothesis，而不是继续为现有候选做救火式解释

---

## 7. 下一张卡

`P3` 完成后的 next main queue card 固定为：

`P4 / sizing retained-or-no-go`

但这里的执行口径已经固定为：

1. `P4` 必须按 `no retained candidate case` 收口
2. `WILLIAMS_FIXED_RISK / FIXED_RATIO` 只允许被裁成 residual watch 或 no-go
3. `PX1 / cross-exit sensitivity` 当前不允许提前打开

---

## 8. 正式结论

当前 `P3 single-lot sanity replay` 的正式结论固定为：

1. `WILLIAMS_FIXED_RISK / FIXED_RATIO` 都没有通过 `single-lot sanity survivor` 门槛
2. 它们在 floor 环境下仍保留一定改善，但改善形状不够干净
3. 当前不能再把任何对象写成 retained sizing candidate
4. 因此第三战场必须转入 `P4 no retained candidate case`

---

## 9. 一句话结论

`P3` 已经把 P2 的两个 provisional retained candidate 拉回 floor 环境审过一轮：两条都没能活成 survivor，所以第三战场当前没有 retained sizing candidate。`
