# Phase P4 Sizing Retained-Or-No-Go Card

**日期**: `2026-03-14`  
**阶段**: `Positioning / P4`  
**对象**: `第三战场第五张执行卡`  
**状态**: `Active`

---

## 1. 目标

`P4` 只做一件事：

`在 P3 / single-lot sanity replay 完成后，把 sizing lane 的结果正式裁成 no retained candidate case，并写清 residual watch / no-go 边界。`

---

## 2. 本卡要回答的问题

1. `WILLIAMS_FIXED_RISK / FIXED_RATIO` 在 `P3` 后是否还存在 retained 资格
2. 当前是否应正式写成 `no retained sizing candidate`
3. 哪些对象只保留为 residual watch
4. 哪些对象应正式退出 sizing 主队列
5. 为什么 `PX1 / cross-exit sensitivity` 继续保持锁住

---

## 3. 冻结输入

1. `entry baseline = legacy_bof_baseline / no IRS / no MSS`
2. `exit semantics = current Broker full-exit stop-loss + trailing-stop`
3. `canonical operating control = FIXED_NOTIONAL_CONTROL`
4. `floor sanity control = SINGLE_LOT_CONTROL`
5. `只读取 P2 + P3 formal evidence，不重开 family register`
6. `P3 conclusion = no_candidate_survives_single_lot_sanity`

---

## 4. 本卡交付物

1. 一张 `retained-or-no-go decision table`
2. 一张 `P4 formal record`
3. 一条写死 `PX1` 继续锁住的治理结论

---

## 5. 下一步出口

1. `P5 sizing lane closeout / migration boundary`
2. `P6 partial-exit contract freeze`
3. `PX1 cross-exit sensitivity` 继续保持条件锁定

---

## 6. 一句话结论

`P4` 的职责是把 P3 的 floor 审判结果正式写成 no-retained-candidate case，而不是再替候选找活路。`
