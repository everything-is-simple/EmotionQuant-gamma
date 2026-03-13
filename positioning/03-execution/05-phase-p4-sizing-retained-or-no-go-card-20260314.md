# Phase P4 Sizing Retained-Or-No-Go Card

**日期**: `2026-03-14`  
**阶段**: `Positioning / P4`  
**对象**: `第三战场第五张执行卡`  
**状态**: `Draft`

---

## 1. 目标

`P4` 只做一件事：

`在 P3 / single-lot sanity replay 完成后，把 sizing lane 的 provisional retained candidate 正式裁成 retained / watch / no-go。`

---

## 2. 本卡要回答的问题

1. `WILLIAMS_FIXED_RISK / FIXED_RATIO` 经过 `single-lot sanity replay` 后，谁还站得住
2. 当前是否真的存在可继续升格的 retained sizing candidate
3. 哪些对象需要降级为 `watch`
4. 哪些对象应正式退出 sizing 主队列
5. 后续是否允许打开 `cross-exit sensitivity`

---

## 3. 冻结输入

1. `entry baseline = legacy_bof_baseline / no IRS / no MSS`
2. `exit semantics = current Broker full-exit stop-loss + trailing-stop`
3. `canonical operating control = FIXED_NOTIONAL_CONTROL`
4. `floor sanity control = SINGLE_LOT_CONTROL`
5. `只读取 P2 + P3 formal evidence，不重开 family register`

---

## 4. 本卡交付物

1. 一张 `retained-or-no-go decision table`
2. 一张 `P4 formal record`
3. 如存在 retained candidate，则正式放行 `PX1 / cross-exit sensitivity`

---

## 5. 下一步出口

1. `P5 sizing lane closeout / migration boundary`
2. `PX1 cross-exit sensitivity`（仅在 retained sizing candidate 明确存在后打开）
3. `P6 partial-exit contract freeze`

---

## 6. 一句话结论

`P4` 的职责是把“有候选”裁成“谁真的活、谁只是看起来活”。`
