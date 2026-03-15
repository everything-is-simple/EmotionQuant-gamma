# Phase N3l Tachibana Pilot-Pack Unit-Regime Overlay Record

**日期**: `2026-03-15`  
**阶段**: `Normandy / N3l`  
**对象**: `Tachibana pilot-pack unit-regime overlay formal readout`  
**状态**: `Closed`

---

## 1. 目标

本文用于把 `N3l / Tachibana pilot-pack unit-regime overlay` 的正式裁决写死。  
这张 record 只回答 5 件事：

1. 当前 pilot-pack 的 operating unit regime 是否仍然只有 `FIXED_NOTIONAL_CONTROL`
2. `SINGLE_LOT_CONTROL` 是否仍然只应保留为 floor sanity regime
3. `TRAIL_SCALE_OUT_25_75` 在 `single_lot` 下是否仍然构成独立 proxy
4. `reduced_unit_scale` 当前是否已经成为 executable sizing
5. 下一张主队列卡应如何推进

---

## 2. Formal Evidence

本卡正式证据固定为：

1. `normandy/03-execution/evidence/tachibana_pilot_pack_unit_regime_overlay_20260315.md`
2. `normandy/03-execution/evidence/normandy_tachibana_pilot_pack_dtt_bof_control_no_irs_no_mss_tachibana_pilot_pack_w20230103_20260224_t035356__tachibana_pilot_pack_matrix.json`
3. `normandy/03-execution/evidence/normandy_tachibana_pilot_pack_dtt_bof_control_no_irs_no_mss_tachibana_pilot_pack_w20230103_20260224_t100049__tachibana_pilot_pack_matrix.json`
4. `normandy/03-execution/evidence/tachibana_pilot_pack_implementation_scaffold_20260315.md`
5. `normandy/03-execution/records/26-phase-n3i-tachibana-pilot-pack-implementation-scaffold-record-20260315.md`
6. `normandy/03-execution/records/28-phase-n3k-tachibana-pilot-pack-formal-cooldown-matrix-record-20260315.md`
7. `positioning/03-execution/records/09-phase-p8-partial-exit-family-replay-record-20260315.md`
8. `src/backtest/normandy_tachibana_pilot_pack.py`
9. `src/config.py`

窗口固定为：

`2023-01-03 -> 2026-02-24`

---

## 3. 正式裁决

`N3l` 的正式裁决固定为：

1. `FIXED_NOTIONAL_CONTROL` 继续是 Tachibana pilot-pack 当前唯一 operating unit regime
2. `SINGLE_LOT_CONTROL` 继续只保留为 floor sanity regime
3. `TRAIL_SCALE_OUT_25_75__SINGLE_LOT_CONTROL__CD0` 当前正式判定为：
   `degenerate_to_full_exit_floor_case`
4. `reduced_unit_scale` 当前正式判定为：
   `payload_governance_tag_only`
5. 下一张主队列卡固定切向：
   `N3m / Tachibana pilot-pack experimental-segment isolation`

---

## 4. 为什么 `FIXED_NOTIONAL_CONTROL` 仍然是唯一 operating regime

当前只有 `fixed_notional` 这条线，仍然保留 `control -> proxy` 的可解释执行差异：

1. `trade_count = 275 -> 396`
2. `buy_filled_count = 275 -> 269`
3. `partial_exit_pair_count = 0 -> 239`
4. `EV = 0.01671 -> 0.04946`
5. `PF = 2.61626 -> 3.39562`
6. `MDD = 0.11832 -> 0.10255`
7. `net_pnl = 402,308.57 -> 463,311.02`

这说明当前 pilot-pack 里真正还在工作的，不是抽象的 “unit regime family”，而是：

`fixed_notional operating baseline 上的 full-exit vs reduce-to-core proxy pair`

因此 `N3l` 完成后，不能把任何 floor-only 读数抬成第二条 operating lane。

---

## 5. 为什么 `SINGLE_LOT_CONTROL` 不能被提升为 operating alternative

`single_lot` 下的 floor control 与 floor proxy 当前完全重合：

1. `trade_count = 275 / 275`
2. `buy_filled_count = 275 / 275`
3. `partial_exit_pair_count = 0 / 0`
4. `EV = 0.00657 / 0.00657`
5. `PF = 2.39157 / 2.39157`
6. `MDD = 0.03519 / 0.03519`
7. `net_pnl = -21,421.86 / -21,421.86`

这意味着当前必须写死两件事：

1. `TRAIL_SCALE_OUT_25_75` 在 `single_lot` 下没有生成独立 proxy 读数
2. `single_lot` 的职责只是 floor sanity，而不是 operating promotion

更重要的是，当前 floor line 相对 operating line 的净值差已经固定为：

1. `floor_control_net_pnl_delta_vs_operating_control = -423,730.43`
2. `floor_proxy_net_pnl_delta_vs_operating_proxy = -484,732.88`

因此 `single_lot` 不能被误写成 “drawdown 更小，所以 regime 更优”；  
它只是把 proxy 在 floor regime 下的退化事实明明白白地暴露了出来。

---

## 6. 为什么 `reduced_unit_scale` 仍然只能写成 tag

当前 `reduced_unit_scale` 仍然不能被写成 executable sizing，原因固定为：

1. `N3i` 已经正式写死 `E3 = tag/report glue only`
2. `src/config.py` 只暴露配置字段，没有新增 sizing 消费逻辑
3. `src/backtest/normandy_tachibana_pilot_pack.py` 只在 scenario、runtime config 透传与 matrix payload 输出中写出这些值
4. 当前没有新的 `Broker / RiskManager / Store schema / reporter pairing` 因为 `reduced_unit_scale` 而改变

因此当前更诚实的写法必须是：

`reduced_unit_scale` 现在承载的是 governance labeling，不是 executable sizing capability

---

## 7. 当前已经回答与仍未回答的

当前已经回答的：

1. pilot-pack 当前唯一 operating regime 仍然是 `FIXED_NOTIONAL_CONTROL`
2. `SINGLE_LOT_CONTROL` 当前只能保留为 floor sanity line
3. floor proxy 当前已经正式退化为 floor control
4. `reduced_unit_scale` 当前仍然只是 payload tag

当前仍未回答的：

1. `experimental_segment_policy` 如何写成正式隔离读法
2. 是否需要为 pilot-pack 补独立 `experimental sidecar digest`
3. 未来若真要开 `reduced-unit executable lane`，需要怎样的新证据链与新实现卡

---

## 8. 明确继续挡住的内容

`N3l` 完成后，以下内容继续明确挡住：

1. `R2 / probe_to_mother_promotion`
2. `R3 / discrete_same_side_add_ladder`
3. `R8 / lock_equivalent_reduce_and_readd`
4. `R9 / reverse_restart_as_new_position`
5. 任何持仓内 `add-on BUY`
6. 任何把 `reduced_unit_scale` 误写成“已经落地的 sizing 引擎”的说法
7. 任何把 `single_lot` 误写成第二条 operating lane 的说法

---

## 9. 下一张卡

`N3l` 完成后的 next main queue card 固定为：

`N3m / Tachibana pilot-pack experimental-segment isolation`

它只允许回答：

1. `experimental_segment_policy = isolate_from_canonical_aggregate` 如何在 matrix / digest / record 上写成正式隔离语义
2. 哪些 pilot 读数必须作为 `experimental sidecar`
3. 哪些 canonical aggregate 明确禁止并入 experimental 100% share

---

## 10. 正式结论

当前 `N3l Tachibana pilot-pack unit-regime overlay` 的正式结论固定为：

1. `FIXED_NOTIONAL_CONTROL` 继续是当前唯一 operating unit regime
2. `SINGLE_LOT_CONTROL` 继续只保留为 floor sanity regime
3. `TRAIL_SCALE_OUT_25_75` 在 `single_lot` 下已正式暴露为 `degenerate_to_full_exit_floor_case`
4. `reduced_unit_scale` 当前仍然只是 payload / governance tag
5. pilot-pack 下一步应进入 `experimental-segment isolation`，而不是偷开新的 sizing lane

---

## 11. 一句话结论

`N3l` 把 Tachibana pilot-pack 的 unit-regime 边界正式钉死了：当前只有 `FIXED_NOTIONAL_CONTROL` 还配叫 operating regime，`SINGLE_LOT_CONTROL` 只负责做 floor sanity，`TRAIL_SCALE_OUT_25_75` 在 floor 下已经退化，而 `reduced_unit_scale` 还只是治理标签，不是可执行 sizing。
