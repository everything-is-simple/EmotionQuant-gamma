# Phase P8 Partial-Exit Family Replay Record

**日期**: `2026-03-15`  
**阶段**: `Positioning / P8`  
**对象**: `第三战场第九张执行卡 formal readout`  
**状态**: `Closed`

---

## 1. 目标

本文用于把 `P8 / partial-exit family replay` 的正式长窗结论写死。
这张 record 只回答 5 件事：
1. 在同一 frozen baseline 下，首批 trailing partial-exit ratio family 各自交出了什么正式读数
2. 哪些 family 相对 `FULL_EXIT_CONTROL` 形成了 provisional retained readout
3. 哪些 family 只保留为 `watch_candidate`
4. `FULL_EXIT_CONTROL` 是否仍应继续作为 canonical control baseline
5. `P9 / positioning campaign closeout` 与 `PX2 / targeted mechanism follow-up` 应如何排队

---

## 2. Formal Evidence

本卡正式证据固定为：

1. `positioning/03-execution/evidence/positioning_p8_partial_exit_family_dtt_bof_control_no_irs_no_mss_partial_exit_family_w20230103_20260224_t162218__partial_exit_family_matrix.json`
2. `positioning/03-execution/evidence/positioning_p8_partial_exit_family_digest_dtt_bof_control_no_irs_no_mss_partial_exit_family_w20230103_20260224_t162247__partial_exit_family_digest.json`

窗口固定为：

`2023-01-03 -> 2026-02-24`

冻结前提固定为：

1. `entry baseline = legacy_bof_baseline / no IRS / no MSS`
2. `pipeline baseline = dtt / v0_01_dtt_pattern_only`
3. `entry family = BOF control only`
4. `sizing baseline = FIXED_NOTIONAL_CONTROL`
5. `canonical control baseline = FULL_EXIT_CONTROL`
6. `family shape = single trailing-stop partial-exit leg plus terminal liquidation leg`
7. `signal_date = T / execute_date = T+1 / fill = T+1 open`
8. `STOP_LOSS / FORCE_CLOSE = hard full exit`

---

## 3. Canonical Control Readout

`FULL_EXIT_CONTROL` 继续作为本轮正式对照尺子。
关键读数：

1. `trade_count = 275`
2. `EV = 0.01671`
3. `PF = 2.61626`
4. `MDD = 0.11832`
5. `net_pnl = 402,308.57`
6. `buy_filled_count = 275`
7. `trade_sequence_max_drawdown = 0.37203`

这说明 `P8` 当前要回答的不是“有没有任何 partial-exit 能把 pair 数堆高”，而是：

`在不显著破坏 entry participation、且不推翻 canonical control baseline 的前提下，哪类 partial-exit family 真正形成可保留的 operating-side 候选。`

---

## 4. 首批 Family 读数

### 4.1 Provisional Retained Queue

当前已形成 3 个 provisional retained candidate：

`TRAIL_SCALE_OUT_25_75`

1. `trade_count = 396`
2. `buy_fill_ratio_vs_control = 0.97818`
3. `partial_exit_pair_count = 239`
4. `EV = 0.04946`
5. `PF = 3.39562`
6. `MDD = 0.10255`
7. `net_pnl = 463,311.02`
8. `net_pnl_delta_vs_control = +61,002.45`
9. `trade_sequence_max_drawdown_delta_vs_control = +0.02459`

`TRAIL_SCALE_OUT_33_67`

1. `trade_count = 398`
2. `buy_fill_ratio_vs_control = 0.97818`
3. `partial_exit_pair_count = 243`
4. `EV = 0.04928`
5. `PF = 3.38726`
6. `MDD = 0.10488`
7. `net_pnl = 438,199.51`
8. `net_pnl_delta_vs_control = +35,890.94`
9. `trade_sequence_max_drawdown_delta_vs_control = +0.02339`

`TRAIL_SCALE_OUT_50_50`

1. `trade_count = 400`
2. `buy_fill_ratio_vs_control = 0.97455`
3. `partial_exit_pair_count = 248`
4. `EV = 0.04919`
5. `PF = 3.40966`
6. `MDD = 0.10912`
7. `net_pnl = 406,399.73`
8. `net_pnl_delta_vs_control = +4,091.16`
9. `trade_sequence_max_drawdown_delta_vs_control = +0.02186`

这 3 条 retained queue 的共同特征是：

1. `buy_fill_ratio_vs_control` 仍保持在可接受区间，没有明显打散 entry participation
2. `EV / PF / MDD` 都明显优于 `FULL_EXIT_CONTROL`
3. `trade_sequence_max_drawdown` 全都高于 control，说明 retained 只代表 operating-side 队列成立，不代表已经具备 control promotion 资格
4. 当前 provisional leader 明确是 `TRAIL_SCALE_OUT_25_75`

### 4.2 Watch Candidates

当前保留为 `watch_candidate` 的 family 是：

1. `TRAIL_SCALE_OUT_67_33`
2. `TRAIL_SCALE_OUT_75_25`

它们的共同形状是：

1. `EV / PF / MDD` 依然强于 control
2. `buy_fill_ratio_vs_control` 没有坏到直接出局
3. 但 `net_pnl` 已回落到 control 以下
4. 更高的一段卖出比例当前更像“把盈利提早锁死”，而不是更优的 retained mechanism

### 4.3 No-Go

当前首批 partial-exit family 没有对象被正式裁成 `no_go`。

---

## 5. 正式裁决

`P8` 的正式裁决固定为：

1. `diagnosis = provisional_retained_partial_exit_candidate_found`
2. `decision = write_p8_record_with_retained_queue`
3. `canonical_control_label = FULL_EXIT_CONTROL`
4. `provisional leader = TRAIL_SCALE_OUT_25_75`
5. `retained queue = TRAIL_SCALE_OUT_25_75 / TRAIL_SCALE_OUT_33_67 / TRAIL_SCALE_OUT_50_50`
6. `watch queue = TRAIL_SCALE_OUT_67_33 / TRAIL_SCALE_OUT_75_25`
7. `PX1 / cross-exit sensitivity` 继续保持 locked

这里必须同时写死一条边界：

`retained queue != formal control promotion`

也就是说：

`即使 partial-exit family 已经出现 retained queue，只要 canonical baseline 仍未被正式替换，P9 就只能先做 campaign closeout，而不是直接改写默认 control 语义。`

---

## 6. 已明确与未明确

当前已经明确的：

1. `FULL_EXIT_CONTROL` 继续保持 partial-exit lane 的 canonical control baseline
2. 首批 partial-exit family 已正式出现 retained queue
3. 当前最强 provisional leader 是 `TRAIL_SCALE_OUT_25_75`
4. `TRAIL_SCALE_OUT_33_67` 与 `TRAIL_SCALE_OUT_50_50` 仍保留推进资格，但都弱于 `TRAIL_SCALE_OUT_25_75`
5. 更高 first-leg 卖出比例当前会明显侵蚀 `net_pnl`

当前还未回答的：

1. retained queue 中是否存在值得单开 targeted mechanism hypothesis 的更窄机制读数
2. `trade_sequence_max_drawdown` 的额外代价是否还能继续压低
3. 第三战场收官后，哪些结论属于治理边界，哪些结论具备迁回主线的资格

---

## 7. 下一张卡

`P8` 完成后的 next main queue card 固定为：

`P9 / positioning campaign closeout`

后续卡的职责固定为：

1. `P9`：把第三战场的 frozen baseline、负面约束、retained queue 与迁移边界正式收官
2. `PX1`：当前继续锁住，不能因为 `P8` 出现 retained queue 就自动打开
3. `PX2`：只有在显式提出 targeted mechanism hypothesis 时才允许打开

---

## 8. 正式结论

当前 `P8 partial-exit family replay` 的正式结论固定为：

1. 首批 trailing partial-exit ratio family 已正式跑出 retained queue
2. `TRAIL_SCALE_OUT_25_75` 是当前最强 provisional leader
3. `TRAIL_SCALE_OUT_33_67 / TRAIL_SCALE_OUT_50_50` 保留为 retained queue 的后续成员
4. `TRAIL_SCALE_OUT_67_33 / TRAIL_SCALE_OUT_75_25` 只保留为 watch，不推进
5. `FULL_EXIT_CONTROL` 继续保持 canonical control baseline
6. 第三战场主队列正式切到 `P9 / positioning campaign closeout`

---

## 9. 一句话结论

`P8` 已把 partial-exit family 跑成“有 retained queue，但还不能改写 canonical control”的正式读数：当前最值得保留的是 `TRAIL_SCALE_OUT_25_75`，下一步应先收口第三战场，而不是提前打开新的机制卡。
