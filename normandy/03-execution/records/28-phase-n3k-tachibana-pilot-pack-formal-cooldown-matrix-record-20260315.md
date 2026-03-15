# Phase N3k Tachibana Pilot-Pack Formal Cooldown Matrix Record

**日期**: `2026-03-15`  
**阶段**: `Normandy / N3k`  
**对象**: `Tachibana pilot-pack formal cooldown matrix readout`  
**状态**: `Closed`

---

## 1. 目标

本文用于把 `N3k / Tachibana pilot-pack formal cooldown matrix` 的正式裁决写死。

这张 record 只回答 5 件事：

1. cooldown family 在正式窗口下是否已经产生非零证据
2. 哪个 cooldown 当前只是 no-op overlay
3. 哪个 cooldown 当前形成了 provisional leader
4. 这个结论是否同时出现在 `control + proxy` 两条线上
5. 下一张主队列卡应如何推进

---

## 2. Formal Evidence

本卡正式证据固定为：

1. `normandy/03-execution/evidence/tachibana_pilot_pack_formal_cooldown_matrix_20260315.md`
2. `normandy/03-execution/evidence/normandy_tachibana_pilot_pack_dtt_bof_control_no_irs_no_mss_tachibana_pilot_pack_w20230103_20260224_t035356__tachibana_pilot_pack_matrix.json`
3. `normandy/03-execution/evidence/normandy_tachibana_pilot_pack_digest_dtt_bof_control_no_irs_no_mss_tachibana_pilot_pack_w20230103_20260224_t063327__tachibana_pilot_pack_digest.json`
4. `normandy/03-execution/records/27-phase-n3j-tachibana-pilot-pack-runner-implementation-record-20260315.md`
5. `positioning/03-execution/records/09-phase-p8-partial-exit-family-replay-record-20260315.md`

窗口固定为：

`2023-01-03 -> 2026-02-24`

---

## 3. 正式裁决

`N3k` 的正式裁决固定为：

1. cooldown family 已在正式窗口下打出非零阻挡证据
2. `CD2` 当前正式判定为：
   `no-op overlay`
3. `CD5` 当前正式判定为：
   `first effective cooldown`
4. `CD10` 当前正式判定为：
   `provisional cooldown leader`
5. 当前这个 leader 结论同时出现在：
   `FULL_EXIT_CONTROL + TRAIL_SCALE_OUT_25_75`

---

## 4. 为什么 `CD2` 不能再被当成有效候选

`CD2` 当前必须被明确降格，原因固定为：

1. `cooldown_blocked_signal_count = 0`
2. `cooldown_blocked_signal_share = 0.0000`
3. `trade_count / EV / PF / MDD / net_pnl` 与 `CD0` 完全一致

因此当前必须写死：

`CD2` 不是“很轻但有效的 cooldown”，而是当前正式窗口里的无差异 overlay。`

---

## 5. 为什么 `CD5` 已经足以证明 cooldown 不是伪实验

`CD5` 当前第一次同时满足两件事：

1. 读数上已经出现非零阻挡
2. 改善方向同时出现在 `control + proxy` 两条线上

关键读数固定为：

1. `blocked signals = 2`
2. `blocked share = 0.00585`
3. `control net_pnl_delta_vs_CD0 = +45,676.27`
4. `proxy net_pnl_delta_vs_CD0 = +65,798.19`
5. `control MDD_delta_vs_CD0 = -0.02636`
6. `proxy MDD_delta_vs_CD0 = -0.01695`

因此当前必须写死：

`CD5` 已经证明 cooldown family 不是只会生成伪差异的 report ornament。`

---

## 6. 为什么 `CD10` 当前成为 provisional leader

`CD10` 当前成为 provisional leader，原因固定为：

1. 它打出本轮最高的 `blocked_signal_count = 5`
2. 它打出本轮最高的 `blocked_signal_share = 0.01462`
3. `control` 线继续改善：
   `EV +0.00252 / MDD -0.03092 / net_pnl +56,318.72`
4. `proxy` 线继续改善：
   `EV +0.00211 / MDD -0.01717 / net_pnl +79,200.38`
5. `proxy buy_fill_ratio_vs_canonical` 仍维持在 `0.96364`

因此当前正式写死：

`CD10` 是当前 pilot-pack cooldown family 的 provisional leader，而不是仅仅“阻挡最多的 setting”。`

---

## 7. 当前已经回答与仍未回答的

当前已经回答的：

1. cooldown family 已在正式窗口打出非零证据
2. `CD2` 当前没有实际作用
3. `CD5` 是第一条真正生效的 cooldown
4. `CD10` 是 control/proxy 双线一致的 provisional leader

当前仍未回答的：

1. `CD10` 是否值得迁回更高层治理基线
2. `unit_regime` 是否会改变当前 cooldown leader 的排序
3. `experimental segment isolation` 是否需要在 cooldown family 结果里补独立切片

---

## 8. 明确继续挡住的内容

`N3k` 完成后，以下内容仍然继续明确挡住：

1. `R2 / probe_to_mother_promotion`
2. `R3 / discrete_same_side_add_ladder`
3. `R8 / lock_equivalent_reduce_and_readd`
4. `R9 / reverse_restart_as_new_position`
5. 任何持仓内 add-on BUY
6. 任何把 cooldown 结果误写成“完整立花系统已可验证”的说法

---

## 9. 下一张卡

`N3k` 完成后的 next main queue card 固定为：

`N3l / Tachibana pilot-pack unit-regime overlay`

它只允许回答：

1. `FIXED_NOTIONAL_CONTROL / SINGLE_LOT_CONTROL / reduced-unit tag` 是否改变当前 pilot-pack 读数
2. `CD10` 这个 provisional cooldown leader 在不同 unit regime 下是否保持稳定
3. 哪些 unit-regime 只属于治理标签，哪些开始影响结果解释

---

## 10. 正式结论

当前 `N3k Tachibana pilot-pack formal cooldown matrix` 的正式结论固定为：

1. cooldown family 已从 short-window smoke 进入正式长窗证据
2. `CD2` 当前是 no-op overlay
3. `CD5` 当前是 first effective cooldown
4. `CD10` 当前是 control/proxy 双线一致的 provisional cooldown leader
5. 下一步应进入 `unit-regime overlay`，而不是回头重谈 pilot 边界

---

## 11. 一句话结论

`N3k` 已把 Tachibana pilot-pack 的 cooldown family 跑成正式读数：`CD2` 出局，`CD5` 生效，`CD10` 领跑，而且这个结论不是 proxy 独有现象，而是 control/proxy 双线一致出现的。`
