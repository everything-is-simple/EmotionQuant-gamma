# Phase P4 Sizing Retained-Or-No-Go Record

**日期**: `2026-03-14`  
**阶段**: `Positioning / P4`  
**对象**: `第三战场第五张执行卡 formal readout`  
**状态**: `Closed`

---

## 1. 目标

本文用于把 `P4 / sizing retained-or-no-go` 的正式结论写死。

这张 record 只回答 5 件事：

1. `P2 + P3` 合并后，第三战场 sizing lane 当前是否存在 retained candidate
2. `WILLIAMS_FIXED_RISK / FIXED_RATIO` 应被正式裁成什么级别
3. 其余首批 sizing family 应各自落到什么治理位置
4. `PX1 / cross-exit sensitivity` 当前为何继续保持锁住
5. 下一张主干卡应如何转到 sizing lane closeout

---

## 2. Formal Evidence

本卡正式证据固定为：

1. `positioning/03-execution/evidence/positioning_p2_sizing_family_dtt_bof_control_no_irs_no_mss_w20230103_20260224_formal__sizing_family_matrix.json`
2. `positioning/03-execution/evidence/positioning_p2_sizing_family_digest_dtt_bof_control_no_irs_no_mss_w20230103_20260224_formal__sizing_family_digest.json`
3. `positioning/03-execution/evidence/positioning_p3_single_lot_sanity_dtt_bof_control_no_irs_no_mss_w20230103_20260224_formal__single_lot_sanity_matrix.json`
4. `positioning/03-execution/evidence/positioning_p3_single_lot_sanity_digest_dtt_bof_control_no_irs_no_mss_w20230103_20260224_formal__single_lot_sanity_digest.json`

同时固定承认以下 formal records：

1. `positioning/03-execution/records/02-phase-p1-null-control-matrix-record-20260313.md`
2. `positioning/03-execution/records/03-phase-p2-sizing-family-replay-record-20260314.md`
3. `positioning/03-execution/records/04-phase-p3-single-lot-sanity-replay-record-20260314.md`

窗口固定为：

`2023-01-03 -> 2026-02-24`

冻结前提固定为：

1. `entry baseline = legacy_bof_baseline / no IRS / no MSS`
2. `signal_date = T / execute_date = T+1 / fill = T+1 open`
3. `exit semantics = current Broker full-exit stop-loss + trailing-stop`
4. `canonical operating control = FIXED_NOTIONAL_CONTROL`
5. `floor sanity control = SINGLE_LOT_CONTROL`
6. `P4` 只读取现有 formal evidence，不重开 family replay

---

## 3. Retained-Or-No-Go Decision Table

### 3.1 Retained

当前正式 retained 列表为空：

`retained = []`

### 3.2 Residual Watch

当前只保留为 residual watch 的对象是：

1. `WILLIAMS_FIXED_RISK`
2. `FIXED_RATIO`

原因固定为：

1. 它们在 `P2` 的 `FIXED_NOTIONAL_CONTROL` 环境下确实交出过 provisional retained 级别读数
2. 但在 `P3` 被拉回 `SINGLE_LOT_CONTROL` 后，都没有通过 `sanity_survivor` 门槛
3. 因此当前只能保留为 residual watch，不能继续写成 retained candidate

### 3.3 Watch

当前继续保留为 watch 的对象是：

1. `FIXED_RISK`
2. `FIXED_VOLATILITY`
3. `FIXED_CAPITAL`
4. `FIXED_PERCENTAGE`

原因固定为：

1. 它们在 `P2` 中只有轻微改善或与 control 基本持平
2. 当前没有进入 `P3` 的资格
3. 当前证据不足以升级，但也不足以直接写成 no-go

### 3.4 No-Go

当前正式 `no_go` 的对象是：

`FIXED_UNIT`

该结论直接继承 `P2 formal record`，当前不重审。

---

## 4. 正式裁决

`P4` 的正式裁决固定为：

1. `diagnosis = no_retained_sizing_candidate`
2. `decision = close_sizing_lane_selection_and_move_to_closeout`
3. `retained = []`
4. `residual_watch = [WILLIAMS_FIXED_RISK, FIXED_RATIO]`
5. `watch = [FIXED_RISK, FIXED_VOLATILITY, FIXED_CAPITAL, FIXED_PERCENTAGE]`
6. `no_go = [FIXED_UNIT]`
7. `PX1 / cross-exit sensitivity` 继续保持锁住

这里必须同时写死一条边界：

`residual watch != retained candidate`

也就是说：

`WILLIAMS_FIXED_RISK / FIXED_RATIO` 当前最多只能作为“曾经最接近 retained 的候选”留档，不能再被口头上当成 sizing lane 的已证答案。`

---

## 5. 已明确与未明确

当前已经明确的：

1. sizing lane 当前没有 retained candidate
2. `WILLIAMS_FIXED_RISK / FIXED_RATIO` 当前都不具备继续打开 `PX1` 的资格
3. `FIXED_UNIT` 已经可以从 sizing 主队列中彻底退出
4. 第三战场当前不能把任何 sizing formula 迁回主线当默认仓位

当前还未回答的：

1. sizing lane 的阶段性战果应如何收口成 migration boundary
2. 没有 retained candidate 的前提下，partial-exit lane 应以什么姿态开工
3. 哪些结论只对 `current full-exit semantics` 成立，哪些可以沉淀成跨 lane 的治理资产

---

## 6. 下一张卡

`P4` 完成后的 next main queue card 固定为：

`P5 / sizing lane closeout / migration boundary`

`P5` 的职责固定为：

1. 把 `P0 ~ P4` 的 sizing lane 结果压成阶段性 closeout
2. 明确哪些结论可迁回主线，哪些只能留在研究线
3. 给 `P6 / partial-exit contract freeze` 写清 opening boundary

---

## 7. 正式结论

当前 `P4 sizing retained-or-no-go` 的正式结论固定为：

1. 第三战场 sizing lane 当前不存在 retained sizing candidate
2. `WILLIAMS_FIXED_RISK / FIXED_RATIO` 都只能保留为 residual watch
3. `FIXED_RISK / FIXED_VOLATILITY / FIXED_CAPITAL / FIXED_PERCENTAGE` 继续保留为 watch
4. `FIXED_UNIT` 维持正式 `no_go`
5. `PX1 / cross-exit sensitivity` 当前继续锁住
6. 第三战场主队列转入 `P5 sizing lane closeout / migration boundary`

---

## 8. 一句话结论

`P4` 已把第三战场 sizing lane 正式裁成 no-retained-candidate case：当前没有任何仓位公式可以被诚实地写成 retained。`
