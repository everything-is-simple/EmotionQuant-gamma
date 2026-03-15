# Tachibana Pilot-Pack Formal Cooldown Matrix

**文档版本**: `v0.01`  
**文档状态**: `Active`  
**日期**: `2026-03-15`  
**适用范围**: `Normandy / Tachibana pilot-pack cooldown family formal readout`

---

## 1. 目标

`N3j` 已经把 pilot-pack runner、`signal_filter hook` 与 short-window smoke 接通。
`N3k` 当前要回答的不是“hook 能不能工作”，而是：

`CD0 / CD2 / CD5 / CD10` 在正式窗口下，到底有没有打出可解释的 cooldown 差异。`

因此本文只回答 4 件事：

1. 当前 cooldown family 在正式窗口里的实际读数
2. 哪些 cooldown 仍然只是 `no-op overlay`
3. 哪个 cooldown 当前形成了 provisional leader
4. 这些差异是否同时出现在 `control + proxy` 两条线上

---

## 2. Formal Inputs

本文正式输入固定为：

1. `normandy/03-execution/records/27-phase-n3j-tachibana-pilot-pack-runner-implementation-record-20260315.md`
2. `normandy/03-execution/evidence/normandy_tachibana_pilot_pack_dtt_bof_control_no_irs_no_mss_tachibana_pilot_pack_w20230103_20260224_t035356__tachibana_pilot_pack_matrix.json`
3. `normandy/03-execution/evidence/normandy_tachibana_pilot_pack_digest_dtt_bof_control_no_irs_no_mss_tachibana_pilot_pack_w20230103_20260224_t063327__tachibana_pilot_pack_digest.json`
4. `positioning/03-execution/records/09-phase-p8-partial-exit-family-replay-record-20260315.md`

---

## 3. Formal Window And Frozen Premises

窗口固定为：

`2023-01-03 -> 2026-02-24`

冻结前提固定为：

1. `entry baseline = legacy_bof_baseline / no IRS / no MSS`
2. `pipeline baseline = dtt / v0_01_dtt_pattern_only`
3. `entry family = BOF control only`
4. `sizing baseline = FIXED_NOTIONAL_CONTROL`
5. `control baseline = FULL_EXIT_CONTROL`
6. `proxy baseline = TRAIL_SCALE_OUT_25_75`
7. `same-side add-on BUY` 继续禁止
8. `probe -> mother promotion` 继续禁止
9. `reduce -> re-add` 继续禁止

---

## 4. Formal Cooldown Matrix

| 场景 | blocked signals | blocked share | trade_count | buy_filled_count | EV | PF | MDD | net_pnl |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `FULL_EXIT_CONTROL__FIXED_NOTIONAL_CONTROL__CD0` | 0 | `0.0000` | 275 | 275 | `0.01671` | `2.61626` | `0.11832` | `402,308.57` |
| `TRAIL_SCALE_OUT_25_75__FIXED_NOTIONAL_CONTROL__CD0` | 0 | `0.0000` | 396 | 269 | `0.04946` | `3.39562` | `0.10255` | `463,311.02` |
| `FULL_EXIT_CONTROL__FIXED_NOTIONAL_CONTROL__CD2` | 0 | `0.0000` | 275 | 275 | `0.01671` | `2.61626` | `0.11832` | `402,308.57` |
| `TRAIL_SCALE_OUT_25_75__FIXED_NOTIONAL_CONTROL__CD2` | 0 | `0.0000` | 396 | 269 | `0.04946` | `3.39562` | `0.10255` | `463,311.02` |
| `FULL_EXIT_CONTROL__FIXED_NOTIONAL_CONTROL__CD5` | 2 | `0.00585` | 273 | 273 | `0.01882` | `2.72390` | `0.09197` | `447,984.84` |
| `TRAIL_SCALE_OUT_25_75__FIXED_NOTIONAL_CONTROL__CD5` | 2 | `0.00585` | 396 | 267 | `0.05128` | `3.54307` | `0.08560` | `529,109.21` |
| `FULL_EXIT_CONTROL__FIXED_NOTIONAL_CONTROL__CD10` | 5 | `0.01462` | 272 | 272 | `0.01923` | `2.68760` | `0.08740` | `458,627.29` |
| `TRAIL_SCALE_OUT_25_75__FIXED_NOTIONAL_CONTROL__CD10` | 5 | `0.01462` | 395 | 265 | `0.05157` | `3.54499` | `0.08538` | `542,511.40` |

---

## 5. Key Readouts

### 5.1 `CD2` 仍然是 no-op overlay

`CD2` 在 `control` 与 `proxy` 两条线都没有打出任何非零阻挡：

1. `cooldown_blocked_signal_count = 0`
2. `cooldown_blocked_signal_share = 0.0000`
3. 全部关键读数与 `CD0` 完全一致

因此当前正式固定：

`CD2 = operational no-op overlay`

### 5.2 `CD5` 是第一条真正生效的 cooldown

`CD5` 当前第一次打出非零阻挡：

1. `blocked signals = 2`
2. `blocked share = 0.00585`

同时两条线都出现同方向改善：

`control / CD5 vs CD0`

1. `trade_count_delta = -2`
2. `EV_delta = +0.00211`
3. `PF_delta = +0.10764`
4. `MDD_delta = -0.02636`
5. `net_pnl_delta = +45,676.27`

`proxy / CD5 vs CD0`

1. `buy_filled_delta = -2`
2. `EV_delta = +0.00183`
3. `PF_delta = +0.14745`
4. `MDD_delta = -0.01695`
5. `net_pnl_delta = +65,798.19`

因此当前正式固定：

`CD5 = first effective cooldown, not pseudo-difference`

### 5.3 `CD10` 是当前 provisional cooldown leader

`CD10` 当前给出本轮最强 cooldown 读数：

1. `blocked signals = 5`
2. `blocked share = 0.01462`

并且 `control` 与 `proxy` 都继续朝同一方向推进：

`control / CD10 vs CD0`

1. `trade_count_delta = -3`
2. `EV_delta = +0.00252`
3. `PF_delta = +0.07134`
4. `MDD_delta = -0.03092`
5. `net_pnl_delta = +56,318.72`

`proxy / CD10 vs CD0`

1. `trade_count_delta = -1`
2. `buy_filled_delta = -4`
3. `EV_delta = +0.00211`
4. `PF_delta = +0.14937`
5. `MDD_delta = -0.01717`
6. `net_pnl_delta = +79,200.38`

同时它仍保持：

1. `control buy_fill_ratio_vs_canonical = 0.98909`
2. `proxy buy_fill_ratio_vs_canonical = 0.96364`

因此当前正式固定：

`CD10 = provisional cooldown leader on both control and proxy lines`

---

## 6. What This Does And Does Not Prove

当前已经证明的：

1. cooldown family 在正式窗口下已出现非零阻挡证据
2. 这种差异同时出现在 `control + proxy` 两条线上
3. `CD5` 与 `CD10` 当前都不是伪实验
4. `CD10` 是当前 pilot-pack cooldown provisional leader

当前仍然没有证明的：

1. 完整立花系统已经可验证
2. `R2 / R3 / R8 / R9` 已经可打开
3. `ALREADY_HOLDING` 的持仓内再开仓限制已经解除
4. `CD10` 已经具备升格为主线默认语义的资格

---

## 7. 一句话结论

`N3k` 已把 cooldown family 从“hook 已接通”推进到“长窗已打出非零证据”：`CD2` 仍是 no-op，`CD5` 是第一条生效 cooldown，而 `CD10` 当前成为 control/proxy 双线一致的 provisional cooldown leader。`
