# Phase P9 Positioning Campaign Closeout Record

**日期**: `2026-03-15`  
**阶段**: `Positioning / P9`  
**对象**: `第三战场第十张执行卡 formal closeout`  
**状态**: `Closed`

---

## 1. 目标

本文用于把 `P9 / positioning campaign closeout` 的正式裁决写死。

这张 record 只回答 5 件事：

1. 第三战场这一轮最终完成了什么
2. `buy sizing` 与 `partial-exit` 各自最终确认了什么
3. 哪些结论可以迁回主线，哪些只能继续留在研究线
4. `PX1 / PX2` 现在到底是什么身份
5. 未来若继续第三战场，只允许开什么类型的新卡

---

## 2. Formal Inputs

`P9` 只承认以下 formal inputs：

1. `positioning/03-execution/evidence/positioning_campaign_closeout_20260315.md`
2. `positioning/03-execution/records/01-phase-p0-baseline-freeze-record-20260313.md`
3. `positioning/03-execution/records/02-phase-p1-null-control-matrix-record-20260313.md`
4. `positioning/03-execution/records/03-phase-p2-sizing-family-replay-record-20260314.md`
5. `positioning/03-execution/records/04-phase-p3-single-lot-sanity-replay-record-20260314.md`
6. `positioning/03-execution/records/05-phase-p4-sizing-retained-or-no-go-record-20260314.md`
7. `positioning/03-execution/records/06-phase-p5-sizing-lane-closeout-record-20260314.md`
8. `positioning/03-execution/records/07-phase-p6-partial-exit-contract-freeze-record-20260314.md`
9. `positioning/03-execution/records/08-phase-p7-partial-exit-null-control-matrix-record-20260314.md`
10. `positioning/03-execution/records/09-phase-p8-partial-exit-family-replay-record-20260315.md`
11. `positioning/03-execution/records/partial-exit-lane-opening-note-20260314.md`
12. `positioning/03-execution/records/partial-exit-control-definition-note-20260314.md`
13. `positioning/03-execution/records/sizing-lane-migration-boundary-table-20260314.md`

当前明确不做：

1. `不新增 replay`
2. `不自动打开 PX1`
3. `不自动打开 PX2`
4. `不把 provisional retained queue 写成主线默认参数`

---

## 3. 收官判定

当前第三战场这轮战役的收官判定固定为：

1. `all_defined_positioning_main_queue_cards_closed = yes`
2. `all_formal_positioning_main_queue_records_closed = yes`
3. `active_positioning_main_queue = none`
4. `px1_status = locked`
5. `px2_status = conditional_only`
6. `future_positioning_reentry_requires = explicit_mainline_migration_package_or_new_targeted_mechanism_hypothesis`

这意味着：

`第三战场当前不是还有旧卡没跑完，而是主队列已经正式收完。`

---

## 4. 第三战场最终完成了什么

### 4.1 Sizing Lane 已正式收官

`P0 ~ P5` 已把 sizing lane 正式收成：

1. frozen baseline 已锁定
2. `FIXED_NOTIONAL_CONTROL` 与 `SINGLE_LOT_CONTROL` 已锁定为控制尺子
3. 首批 sizing family 已完成 retained-or-no-go 裁决
4. 当前 `retained sizing candidate = none`

### 4.2 Partial-Exit Lane 已完成首轮正式 family readout

`P6 ~ P8` 已把 partial-exit lane 正式收成：

1. contract / state-machine / trace boundary 已冻结
2. `FULL_EXIT_CONTROL` 继续保持 canonical control baseline
3. 首批 trailing ratio family 已形成 retained queue
4. 当前 provisional leader = `TRAIL_SCALE_OUT_25_75`

### 4.3 第三战场当前真正留下来的是什么

这轮第三战场真正 retained 下来的，不是“新的默认公式”，而是：

1. 一套 frozen baseline discipline
2. 一套 control hierarchy
3. 一套 retained / watch / no-go 治理边界
4. 一组未来能否再开的条件卡规则

---

## 5. Buy Sizing 与 Partial-Exit 的最终分层

### 5.1 Buy Sizing

当前正式分层固定为：

1. `retained = []`
2. `residual watch = [WILLIAMS_FIXED_RISK, FIXED_RATIO]`
3. `watch = [FIXED_RISK, FIXED_VOLATILITY, FIXED_CAPITAL, FIXED_PERCENTAGE]`
4. `no_go = [FIXED_UNIT]`

### 5.2 Partial-Exit

当前正式分层固定为：

1. `canonical control = FULL_EXIT_CONTROL`
2. `retained queue = [TRAIL_SCALE_OUT_25_75, TRAIL_SCALE_OUT_33_67, TRAIL_SCALE_OUT_50_50]`
3. `watch queue = [TRAIL_SCALE_OUT_67_33, TRAIL_SCALE_OUT_75_25]`
4. `provisional leader = TRAIL_SCALE_OUT_25_75`

这里必须继续写死：

`provisional leader != formal control promotion`

---

## 6. 哪些结论可以迁回主线

当前可迁回主线的，不是新的 sizing / exit 默认参数，而是以下治理资产：

1. `baseline freeze first`
2. `operating control baseline` 与 `floor sanity baseline` 分开定义
3. `FULL_EXIT_CONTROL` 当前仍是 partial-exit lane canonical control
4. `retained / watch / no-go` 必须先分层再谈 promotion
5. `partial-exit lane` 不修补 `sizing lane`
6. 若未来迁主线，必须走显式 migration package

---

## 7. 哪些结论只能继续留在研究线

当前只能继续留在研究线的内容固定为：

1. `WILLIAMS_FIXED_RISK / FIXED_RATIO` 的 residual-watch 身份
2. `TRAIL_SCALE_OUT_25_75` 的 provisional-leader 身份
3. `TRAIL_SCALE_OUT_33_67 / 50_50` 的 retained-queue 身份
4. `TRAIL_SCALE_OUT_67_33 / 75_25` 的 watch 身份

原因固定为：

1. 它们都还没有被正式提升为主线默认项
2. 它们当前都只证明了“值得保留”，没有证明“值得默认替换”

---

## 8. PX1 / PX2 的当前身份

`P9` 完成后，条件卡身份固定为：

1. `PX1 / cross-exit sensitivity = locked`
2. `PX2 / targeted mechanism follow-up = conditional_only`

这意味着：

1. `P8` 出现 retained queue，并不会自动打开 `PX1`
2. 只有显式提出新的 `targeted mechanism hypothesis`，才允许打开 `PX2`

---

## 9. 未来若继续，只允许怎么继续

当前如果未来要继续第三战场，只允许两种重开方式：

1. `explicit mainline migration package`
2. `new targeted mechanism hypothesis`

当前明确不允许：

1. 续跑旧 `P0 ~ P9`
2. 无假设补跑参数
3. 把 retained / watch 身份直接偷渡成默认项

---

## 10. 正式结论

当前 `P9 positioning campaign closeout` 的正式结论固定为：

1. 第三战场当前定义过的主队列 cards 已全部闭环
2. 第三战场 sizing lane 已正式收成 `no retained candidate case`
3. 第三战场 partial-exit lane 已正式跑出 retained queue，当前 provisional leader = `TRAIL_SCALE_OUT_25_75`
4. 第三战场当前可迁回主线的是治理边界与负面约束，不是新的默认 sizing / exit 公式
5. `PX1` 继续锁住，`PX2` 继续只保留为条件卡
6. 若未来继续，必须新开 `explicit mainline migration package` 或 `new targeted mechanism hypothesis`

---

## 11. 一句话结论

`P9` 已把第三战场正式收官：买多少这条线没有 retained sizing，卖多少这条线已经跑出 retained queue，但现在能带回主线的仍然只是治理边界，不是新的默认公式。
