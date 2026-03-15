# Tachibana Pilot-Pack Unit-Regime Overlay

**文档版本**: `v0.01`  
**文档状态**: `Active`  
**日期**: `2026-03-15`  
**适用范围**: `Normandy / Tachibana pilot-pack unit-regime overlay formal readout`

---

## 1. 目标

`N3k` 已经把 `cooldown family` 在正式窗口下跑成 formal readout。  
`N3l` 当前要回答的不是“还要不要再开新的 sizing lane”，而是：

`当前 pilot-pack 的 unit regime overlay，到底哪一条还是 operating regime，哪一条只配保留为 floor sanity line。`

因此本文只回答 4 件事：

1. `FIXED_NOTIONAL_CONTROL` 是否继续是当前唯一 operating unit regime
2. `SINGLE_LOT_CONTROL` 是否只应保留为 floor sanity regime
3. `TRAIL_SCALE_OUT_25_75` 在 `single_lot` 下是否仍然给出独立 proxy readout
4. `reduced_unit_scale` 当前到底是不是 executable sizing，还是仅为 payload / governance tag

---

## 2. Formal Inputs

本文正式输入固定为：

1. `normandy/03-execution/evidence/tachibana_pilot_pack_formal_cooldown_matrix_20260315.md`
2. `normandy/03-execution/evidence/normandy_tachibana_pilot_pack_dtt_bof_control_no_irs_no_mss_tachibana_pilot_pack_w20230103_20260224_t035356__tachibana_pilot_pack_matrix.json`
3. `normandy/03-execution/evidence/normandy_tachibana_pilot_pack_dtt_bof_control_no_irs_no_mss_tachibana_pilot_pack_w20230103_20260224_t100049__tachibana_pilot_pack_matrix.json`
4. `normandy/03-execution/evidence/tachibana_pilot_pack_implementation_scaffold_20260315.md`
5. `normandy/03-execution/records/26-phase-n3i-tachibana-pilot-pack-implementation-scaffold-record-20260315.md`
6. `positioning/03-execution/records/09-phase-p8-partial-exit-family-replay-record-20260315.md`
7. `src/backtest/normandy_tachibana_pilot_pack.py`
8. `src/config.py`

---

## 3. Formal Window And Frozen Premises

窗口固定为：

`2023-01-03 -> 2026-02-24`

冻结前提固定为：

1. `entry baseline = legacy_bof_baseline / no IRS / no MSS`
2. `pipeline baseline = dtt / v0_01_dtt_pattern_only`
3. `entry family = BOF control only`
4. `operating sizing baseline = FIXED_NOTIONAL_CONTROL`
5. `floor sizing baseline = SINGLE_LOT_CONTROL`
6. `control baseline = FULL_EXIT_CONTROL`
7. `proxy baseline = TRAIL_SCALE_OUT_25_75`
8. `same-side add-on BUY` 继续禁止
9. `probe -> mother promotion` 继续禁止
10. `reduce -> re-add` 继续禁止
11. `reduced_unit_scale` 不允许在 `N3l` 被偷写成新的 sizing formula

---

## 4. Formal Unit-Regime Matrix

| 场景 | unit regime | trade_count | buy_filled_count | partial_exit_pair_count | EV | PF | MDD | net_pnl |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `FULL_EXIT_CONTROL__FIXED_NOTIONAL_CONTROL__CD0` | `fixed_notional_control` | 275 | 275 | 0 | `0.01671` | `2.61626` | `0.11832` | `402,308.57` |
| `TRAIL_SCALE_OUT_25_75__FIXED_NOTIONAL_CONTROL__CD0` | `fixed_notional_control` | 396 | 269 | 239 | `0.04946` | `3.39562` | `0.10255` | `463,311.02` |
| `FULL_EXIT_CONTROL__SINGLE_LOT_CONTROL__CD0` | `single_lot_control` | 275 | 275 | 0 | `0.00657` | `2.39157` | `0.03519` | `-21,421.86` |
| `TRAIL_SCALE_OUT_25_75__SINGLE_LOT_CONTROL__CD0` | `single_lot_control` | 275 | 275 | 0 | `0.00657` | `2.39157` | `0.03519` | `-21,421.86` |

---

## 5. Key Readouts

### 5.1 `FIXED_NOTIONAL_CONTROL` 继续是唯一 operating regime

当前只有 `fixed_notional` 这条线仍然保留了可解释的 `control / proxy` 差异：

1. `trade_count_delta = +121`
2. `buy_filled_count_delta = -6`
3. `partial_exit_pair_count = 239`
4. `EV_delta = +0.03275`
5. `PF_delta = +0.77936`
6. `MDD_delta = -0.01577`
7. `net_pnl_delta = +61,002.45`

这说明当前 `reduce_to_core proxy` 的正式运行语境，仍然只能写在：

`FIXED_NOTIONAL_CONTROL`

而不是任何 floor-only regime。

### 5.2 `SINGLE_LOT_CONTROL` 只能保留为 floor sanity line

`single_lot` 下的 floor control 与 floor proxy 当前给出完全相同的读数：

1. `trade_count = 275 vs 275`
2. `buy_filled_count = 275 vs 275`
3. `partial_exit_pair_count = 0 vs 0`
4. `EV = 0.00657 vs 0.00657`
5. `PF = 2.39157 vs 2.39157`
6. `MDD = 0.03519 vs 0.03519`
7. `net_pnl = -21,421.86 vs -21,421.86`

因此当前必须正式写死：

`TRAIL_SCALE_OUT_25_75 under SINGLE_LOT_CONTROL = degenerate-to-full-exit floor case`

也就是说，`single_lot` 不是第二条 operating lane，而只是当前 pilot-pack 的 floor sanity anchor。

### 5.3 floor line 不能反写 operating verdict

虽然 `single_lot` 的 `MDD` 更低，但它不能被解释成“更优 operating regime”，原因固定为：

1. 它没有打出任何独立 `proxy` 读数
2. 它没有打出任何 `partial_exit_pair_count`
3. 它的 `net_pnl` 已经落到 `-21,421.86`
4. 相对 operating control，`net_pnl_delta = -423,730.43`
5. 相对 operating proxy，`net_pnl_delta = -484,732.88`

因此 `single_lot` 的职责仍然只能是：

`证明这条 partial-exit proxy 没有在 floor regime 下伪装出第二套独立赢家。`

### 5.4 `reduced_unit_scale` 当前仍然只是 payload / governance tag

`N3i` 已经把这条边界写死：`E3` 先只落到 `scenario + matrix/digest payload`。  
当前代码引用点也继续支持这个裁定：

1. `src/config.py` 只新增了 `tachibana_unit_regime_tag` 与 `tachibana_reduced_unit_scale`
2. `src/backtest/normandy_tachibana_pilot_pack.py` 只在 scenario builder、runtime config 透传、matrix payload 输出里写出这些字段
3. 当前没有新的 `Broker / RiskManager / Store schema / sizing formula` 消费 `reduced_unit_scale`
4. 当前正式长窗读数里，operating line 与 floor line 都只是把它写成 `1.0` 的标签值

因此当前必须正式写死：

`reduced_unit_scale = governance tag only, not executable sizing regime`

---

## 6. What This Does And Does Not Prove

当前已经证明的：

1. `FIXED_NOTIONAL_CONTROL` 继续是当前唯一诚实 operating regime
2. `SINGLE_LOT_CONTROL` 继续只配保留为 floor sanity regime
3. `TRAIL_SCALE_OUT_25_75` 只有在 `fixed_notional` 下才给出独立 proxy readout
4. `reduced_unit_scale` 当前仍然只是 payload 层治理标签

当前仍然没有证明的：

1. 已经存在可执行的 `reduced-unit sizing lane`
2. `single_lot + cooldown family` 值得继续扩跑
3. `unit regime overlay` 已经足以改写 `N3k` 的 cooldown leader 裁定
4. `R2 / R3 / R8 / R9` 可以被偷带回 pilot-pack

---

## 7. 一句话结论

`N3l` 把 Tachibana pilot-pack 的 unit-regime overlay 正式收窄成一句话：`FIXED_NOTIONAL_CONTROL` 继续是唯一 operating regime，`SINGLE_LOT_CONTROL` 只保留为 floor sanity line，而 `reduced_unit_scale` 当前仍然只是 payload / governance tag，不是新的 sizing 执行能力。
