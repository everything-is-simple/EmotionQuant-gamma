# Positioning Campaign Closeout

**文档版本**: `v0.01`  
**文档状态**: `Active`  
**日期**: `2026-03-15`  
**适用范围**: `Positioning / P9 campaign closeout map, migration boundary, and future backlog`

---

## 1. 目标

`P9` 要回答的不是“再补哪组 partial-exit 参数”，而是：

`把第三战场这一轮“买多少 / 卖多少”的战役结果正式收官，并把能迁什么、不能迁什么写死。`

---

## 2. Formal Inputs

本文正式输入固定为：

1. `positioning/03-execution/records/01-phase-p0-baseline-freeze-record-20260313.md`
2. `positioning/03-execution/records/02-phase-p1-null-control-matrix-record-20260313.md`
3. `positioning/03-execution/records/03-phase-p2-sizing-family-replay-record-20260314.md`
4. `positioning/03-execution/records/04-phase-p3-single-lot-sanity-replay-record-20260314.md`
5. `positioning/03-execution/records/05-phase-p4-sizing-retained-or-no-go-record-20260314.md`
6. `positioning/03-execution/records/06-phase-p5-sizing-lane-closeout-record-20260314.md`
7. `positioning/03-execution/records/07-phase-p6-partial-exit-contract-freeze-record-20260314.md`
8. `positioning/03-execution/records/08-phase-p7-partial-exit-null-control-matrix-record-20260314.md`
9. `positioning/03-execution/records/09-phase-p8-partial-exit-family-replay-record-20260315.md`
10. `positioning/03-execution/records/partial-exit-lane-opening-note-20260314.md`
11. `positioning/03-execution/records/partial-exit-control-definition-note-20260314.md`
12. `positioning/03-execution/records/sizing-lane-migration-boundary-table-20260314.md`
13. `positioning/03-execution/evidence/positioning_p1_null_control_dtt_bof_control_no_irs_no_mss_w20230103_20260224_t043316__null_control_matrix.json`
14. `positioning/03-execution/evidence/positioning_p1_null_control_digest_dtt_bof_control_no_irs_no_mss_w20230103_20260224_t052647__null_control_digest.json`
15. `positioning/03-execution/evidence/positioning_p2_sizing_family_dtt_bof_control_no_irs_no_mss_w20230103_20260224_formal__sizing_family_matrix.json`
16. `positioning/03-execution/evidence/positioning_p2_sizing_family_digest_dtt_bof_control_no_irs_no_mss_w20230103_20260224_formal__sizing_family_digest.json`
17. `positioning/03-execution/evidence/positioning_p3_single_lot_sanity_dtt_bof_control_no_irs_no_mss_w20230103_20260224_formal__single_lot_sanity_matrix.json`
18. `positioning/03-execution/evidence/positioning_p3_single_lot_sanity_digest_dtt_bof_control_no_irs_no_mss_w20230103_20260224_formal__single_lot_sanity_digest.json`
19. `positioning/03-execution/evidence/positioning_p7_partial_exit_null_control_dtt_bof_control_no_irs_no_mss_partial_exit_w20230103_20260224_t100644__partial_exit_null_control_matrix.json`
20. `positioning/03-execution/evidence/positioning_p7_partial_exit_null_control_digest_dtt_bof_control_no_irs_no_mss_partial_exit_w20230103_20260224_t124711__partial_exit_null_control_digest.json`
21. `positioning/03-execution/evidence/positioning_p8_partial_exit_family_dtt_bof_control_no_irs_no_mss_partial_exit_family_w20230103_20260224_t162218__partial_exit_family_matrix.json`
22. `positioning/03-execution/evidence/positioning_p8_partial_exit_family_digest_dtt_bof_control_no_irs_no_mss_partial_exit_family_w20230103_20260224_t162247__partial_exit_family_digest.json`

---

## 3. Campaign Map

第三战场这一轮可以压成两段主线加两张条件卡：

| 战役段 | 回答的问题 | 正式结果 |
|---|---|---|
| `P0 ~ P5 / sizing lane` | 在 frozen baseline 下到底该怎么买多少 | 当前 `no retained sizing candidate`，只留下 control baseline、watch 分层和治理边界 |
| `P6 ~ P8 / partial-exit lane` | 在 fixed sizing baseline 下到底该怎么卖多少 | partial-exit 契约已冻结，`FULL_EXIT_CONTROL` 继续为 canonical control，首批 ratio family 已跑出 retained queue |
| `PX1 / cross-exit sensitivity` | sizing 结论是否跨 exit 仍稳定 | 当前继续 locked，未被本轮自动打开 |
| `PX2 / targeted mechanism follow-up` | retained partial-exit 是否值得做更窄机制假设 | 当前只保留为条件卡，必须显式 hypothesis 才能打开 |

---

## 4. What This Campaign Actually Solved

这轮 `Positioning` 真正解决掉的事，正式固定为：

1. 把 `legacy_bof_baseline / no IRS / no MSS` 下的 sizing 与 partial-exit 问题拆成两条独立治理线
2. 把第三战场 control 体系正式写死为：
   - `FIXED_NOTIONAL_CONTROL = canonical operating sizing baseline`
   - `SINGLE_LOT_CONTROL = floor sanity baseline`
   - `FULL_EXIT_CONTROL = canonical partial-exit control baseline`
3. 把 sizing lane 正式裁成 `no retained candidate case`
4. 把 partial-exit lane 正式跑出 retained queue，并明确当前 `provisional leader = TRAIL_SCALE_OUT_25_75`
5. 把未来能迁回主线的内容收窄成 `control baseline + governance boundary + migration constraint`

一句话说：

`第三战场这轮完成的是“把 sizing/partial-exit 的治理边界和 retained queue 写死”，不是“直接产出新的主线默认仓位/卖出系统”。`

---

## 5. Final Readout By Lane

### 5.1 Buy Sizing Lane

当前 `buy sizing` 的正式结论固定为：

1. `retained sizing candidate = none`
2. `WILLIAMS_FIXED_RISK / FIXED_RATIO = residual watch`
3. `FIXED_RISK / FIXED_VOLATILITY / FIXED_CAPITAL / FIXED_PERCENTAGE = watch`
4. `FIXED_UNIT = no_go`
5. `single-lot sanity` 已证明此前 provisional retained 并不足以升格

### 5.2 Partial-Exit Lane

当前 `partial-exit` 的正式结论固定为：

1. 契约边界已经冻结为 `多 SELL 腿 + 单腿单次成交`
2. `FULL_EXIT_CONTROL` 继续是 canonical control baseline
3. retained queue 已出现：
   - `TRAIL_SCALE_OUT_25_75`
   - `TRAIL_SCALE_OUT_33_67`
   - `TRAIL_SCALE_OUT_50_50`
4. watch queue 固定为：
   - `TRAIL_SCALE_OUT_67_33`
   - `TRAIL_SCALE_OUT_75_25`
5. `TRAIL_SCALE_OUT_25_75` 当前只是 provisional leader，不等于 control promotion

---

## 6. Mainline Migration Summary

当前第三战场能迁回主线的正式摘要如下：

1. `baseline freeze first, then family replay`
2. `operating control baseline` 与 `floor sanity baseline` 必须分开
3. `FULL_EXIT_CONTROL` 当前仍是 partial-exit lane 的 canonical control
4. `provisional retained != default promotion`
5. `partial-exit lane` 不替 `sizing lane` 擦屁股
6. 若要迁主线，迁的是治理边界与负面约束，不是直接迁一条新的 sizing / exit 默认公式

---

## 7. What Must Stay In Research

以下内容当前只能继续留在研究线：

1. `WILLIAMS_FIXED_RISK / FIXED_RATIO` 的 residual-watch 身份
2. `TRAIL_SCALE_OUT_25_75` 的 provisional-leader 身份
3. `TRAIL_SCALE_OUT_33_67 / 50_50` 的 retained queue 身份
4. `TRAIL_SCALE_OUT_67_33 / 75_25` 的 watch 身份
5. 任何尚未通过新 hypothesis 的机制想象

这些都还不能翻译成：

`主线默认今天就该改。`

---

## 8. Future Backlog Gate

`P9` 收官后，如果未来还要继续第三战场，只允许两种开法：

1. `explicit mainline migration package`
   - 用于把已经足够硬的治理边界迁入主线 SoT
2. `new targeted mechanism hypothesis`
   - 用于打开 `PX1` 或 `PX2` 这种条件卡

这意味着未来不允许：

1. 续跑旧 `P0 ~ P9` 主队列
2. 无假设重扫 sizing / partial-exit 参数
3. 把 retained / watch 结果偷抬成默认项

---

## 9. Permanent No-Fake List

收官后，以下内容继续永久挡住：

1. 不宣称第三战场已经产出主线默认 sizing 公式
2. 不宣称 `TRAIL_SCALE_OUT_25_75` 已升级为 canonical control
3. 不宣称 `residual watch` 等于 retained candidate
4. 不宣称 `watch queue` 等于 mainline-ready candidates
5. 不把 `PX1 / PX2` 的条件卡语义抹掉

---

## 10. 一句话结论

`P9` 把第三战场这一轮正式收官了：sizing lane 被裁成 no-retained case，partial-exit lane 跑出了 retained queue，但能迁回主线的依然只是 control 边界、治理约束和负面条件，而不是新的默认公式。
