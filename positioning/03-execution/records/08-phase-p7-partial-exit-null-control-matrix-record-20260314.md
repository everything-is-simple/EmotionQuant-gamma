# Phase P7 Partial-Exit Null Control Matrix Record

**日期**: `2026-03-14`  
**阶段**: `Positioning / P7`  
**对象**: `第三战场第八张执行卡 formal readout`  
**状态**: `Closed`

---

## 1. 目标

本文用于把 `P7 / partial-exit null control matrix` 的正式长窗结论写死。

这张 record 只回答 5 件事：

1. `FULL_EXIT_CONTROL` 与 `NAIVE_TRAIL_SCALE_OUT_50_50_CONTROL` 在 operating control pair 下各自交出了什么正式读数
2. 在 floor sanity pair 下，naive scale-out 是否仍形成真实可比较的 control 差异
3. `P8` 应继续拿哪条 control baseline 作为正式尺子
4. `PX1 / cross-exit sensitivity` 当前是否具备打开条件
5. 下一张主干卡应如何切到 `P8 / partial-exit family replay`

---

## 2. Formal Evidence

本卡正式证据固定为：

1. `positioning/03-execution/evidence/positioning_p7_partial_exit_null_control_dtt_bof_control_no_irs_no_mss_partial_exit_w20230103_20260224_t100644__partial_exit_null_control_matrix.json`
2. `positioning/03-execution/evidence/positioning_p7_partial_exit_null_control_digest_dtt_bof_control_no_irs_no_mss_partial_exit_w20230103_20260224_t124711__partial_exit_null_control_digest.json`

窗口固定为：

`2023-01-03 -> 2026-02-24`

冻结前提固定为：

1. `entry baseline = legacy_bof_baseline / no IRS / no MSS`
2. `pipeline baseline = dtt / v0_01_dtt_pattern_only`
3. `signal_date = T / execute_date = T+1 / fill = T+1 open`
4. `STOP_LOSS / FORCE_CLOSE = hard full exit`
5. `operating control pair = FULL_EXIT_CONTROL vs NAIVE_TRAIL_SCALE_OUT_50_50_CONTROL on FIXED_NOTIONAL_CONTROL`
6. `floor sanity pair = FULL_EXIT_CONTROL vs NAIVE_TRAIL_SCALE_OUT_50_50_CONTROL on SINGLE_LOT_CONTROL`

---

## 3. Operating Control Pair Readout

`FIXED_NOTIONAL_CONTROL` 下，`NAIVE_TRAIL_SCALE_OUT_50_50_CONTROL` 相对 `FULL_EXIT_CONTROL` 交出了更强的 operating-side 读数。

### 3.1 `FULL_EXIT_CONTROL__FIXED_NOTIONAL_CONTROL`

1. `trade_count = 275`
2. `EV = 0.01671`
3. `PF = 2.61626`
4. `MDD = 0.11832`
5. `buy_filled_count = 275`
6. `paired_trade_count = 275`
7. `avg_hold_days = 23.64`

### 3.2 `NAIVE_TRAIL_SCALE_OUT_50_50_CONTROL__FIXED_NOTIONAL_CONTROL`

1. `trade_count = 400`
2. `EV = 0.04919`
3. `PF = 3.40966`
4. `MDD = 0.10912`
5. `buy_filled_count = 268`
6. `paired_trade_count = 400`
7. `partial_exit_pair_count = 248`
8. `avg_hold_days = 29.02`
9. `buy_fill_ratio_vs_full_exit = 0.97455`

Operating pair 的正式读数说明：

1. naive 50/50 scale-out 在 operating 环境下确实没有散掉参与一致性
2. 它把 `trade_count / EV / PF` 都明显拉高
3. 它同时把 `MDD` 略微压低
4. 因此如果只看 operating pair，naive scale-out 是一个成立的 retained control 候选

---

## 4. Floor Sanity Pair Readout

`SINGLE_LOT_CONTROL` 下，naive scale-out 没有形成真实 control 差异，而是退化回 full-exit degenerate case。

### 4.1 `FULL_EXIT_CONTROL__SINGLE_LOT_CONTROL`

1. `trade_count = 275`
2. `EV = 0.00657`
3. `PF = 2.39157`
4. `MDD = 0.03519`
5. `buy_filled_count = 275`
6. `paired_trade_count = 275`
7. `avg_hold_days = 23.71`

### 4.2 `NAIVE_TRAIL_SCALE_OUT_50_50_CONTROL__SINGLE_LOT_CONTROL`

1. `trade_count = 275`
2. `EV = 0.00657`
3. `PF = 2.39157`
4. `MDD = 0.03519`
5. `buy_filled_count = 275`
6. `paired_trade_count = 275`
7. `partial_exit_pair_count = 0`
8. `avg_hold_days = 23.71`
9. `buy_fill_ratio_vs_full_exit = 1.00000`

这组正式读数说明：

1. naive 50/50 scale-out 在 floor line 下没有产生任何有效 partial-exit pair
2. 结合 `partial_exit_pair_count = 0` 与全组读数完全相同，当前应正式读成：
   `A 股一手约束下，single-lot floor 环境中的 naive 50/50 scale-out 退化成 full exit`
3. 因此它没有通过“两把尺子都成立”的 control baseline 门槛

---

## 5. 正式裁决

`P7` 的正式裁决固定为：

1. `diagnosis = full_exit_retained_control`
2. `decision = keep_full_exit_as_p8_control`
3. `canonical_control_label = FULL_EXIT_CONTROL`
4. `operating pair` 承认 naive scale-out 的局部改善
5. `floor pair` 正式判定 naive scale-out 退化为 degenerate case
6. `PX1 / cross-exit sensitivity` 继续保持锁住

这里必须同时写死一条边界：

`operating-side improvement != formal control promotion`

也就是说：

`只要 naive scale-out 还不能在 floor sanity line 下形成真实 control 差异，P8 就不能把它提升成正式 control baseline。`

---

## 6. 已明确与未明确

当前已经明确的：

1. `FULL_EXIT_CONTROL` 继续保持 P8 的 canonical control baseline
2. naive 50/50 scale-out 在 operating pair 下有改善，但改善不够稳健
3. floor line 已经给出强负面约束：
   `single-lot + A股一手约束` 下，naive 50/50 scale-out 当前会退化成 full exit
4. `PX1 / cross-exit sensitivity` 当前不具备打开条件

当前还未回答的：

1. 在 `FULL_EXIT_CONTROL` 作为 canonical baseline 的前提下，首批 partial-exit family 是否存在值得 retained 的 exit family
2. 是否存在不依赖 naive 50/50 control 的更强 partial-exit family 结构
3. 哪些 targeted mechanism hypothesis 值得在 `P8` 之后单独开条件卡

---

## 7. 下一张卡

`P7` 完成后的 next main queue card 固定为：

`P8 / partial-exit family replay`

`P8` 的职责固定为：

1. 在 `FULL_EXIT_CONTROL` 作为 canonical control baseline 的前提下展开首批 partial-exit family replay
2. 不再重审 `P7` control baseline
3. 未经 `P8` formal readout，不提前打开 `PX1 / cross-exit sensitivity`

---

## 8. 正式结论

当前 `P7 partial-exit null control matrix` 的正式结论固定为：

1. `FULL_EXIT_CONTROL` 继续保持 partial-exit lane 的 canonical control baseline
2. naive 50/50 trailing scale-out 只在 operating pair 下交出局部改善
3. 在 floor sanity pair 下，它没有形成真实可比较的 partial-exit control，而是退化成 full-exit degenerate case
4. 因此 `P8` 当前不得把 naive 50/50 scale-out 提升为 formal control baseline
5. 第三战场主队列正式切到 `P8 / partial-exit family replay`

---

## 9. 一句话结论

`P7` 已经把 partial-exit lane 的 control baseline 定下来了：naive 50/50 scale-out 有 operating-side 改善，但不够跨尺子稳健，所以 P8 继续以 `FULL_EXIT_CONTROL` 作为正式对照线。`
