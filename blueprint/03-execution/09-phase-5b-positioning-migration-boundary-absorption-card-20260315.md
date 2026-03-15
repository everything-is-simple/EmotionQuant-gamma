# Phase 5B Positioning Migration Boundary Absorption Card

**状态**: `Draft`  
**日期**: `2026-03-15`  
**对象**: `第一战场 / Phase 5B / Positioning migration boundary absorption`

---

## 1. 目标

`Phase 5B` 只做一件事：

`把第三战场已经收官的 control hierarchy、retained promotion 边界和条件卡约束，正式吸收到主线 SoT。`

---

## 2. 本卡要回答的问题

1. `FIXED_NOTIONAL_CONTROL / SINGLE_LOT_CONTROL / FULL_EXIT_CONTROL` 迁回主线后，正式身份各是什么
2. 哪些 Positioning 结论只能迁成治理边界，不能迁成默认参数
3. `TRAIL_SCALE_OUT_25_75` 当前在主线里到底只能怎么叫
4. `partial-exit lane 不修补 sizing lane` 该怎样写成主线硬边界
5. `PX1 / PX2` 的身份怎样写成主线条件卡约束

---

## 3. 冻结输入

1. `positioning/03-execution/records/06-phase-p5-sizing-lane-closeout-record-20260314.md`
2. `positioning/03-execution/records/09-phase-p8-partial-exit-family-replay-record-20260315.md`
3. `positioning/03-execution/records/10-phase-p9-positioning-campaign-closeout-record-20260315.md`
4. `positioning/03-execution/records/partial-exit-lane-opening-note-20260314.md`
5. `positioning/03-execution/records/partial-exit-control-definition-note-20260314.md`
6. `positioning/03-execution/records/sizing-lane-migration-boundary-table-20260314.md`
7. `blueprint/01-full-design/09-mainline-system-operating-baseline-20260309.md`
8. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
9. `blueprint/03-execution/07-phase-5-research-line-migration-package-card-20260315.md`

当前明确不做：

1. `不新增 replay`
2. `不改写主线默认 sizing / exit 参数`
3. `不自动打开 PX1 / PX2`
4. `不把 retained queue 写成 canonical control replacement`

---

## 4. 本卡交付物

1. 一张 `Phase 5B absorption card`
2. 一组 `mainline SoT delta`
3. 一张 `v0.01-plus Phase 5B record`

---

## 5. 固定边界

1. 不把 `FIXED_NOTIONAL_CONTROL` 写成主线默认仓位公式
2. 不把 `SINGLE_LOT_CONTROL` 写成第二 operating lane
3. 不把 `FULL_EXIT_CONTROL` 写成已被 retained queue 替代
4. 不把 `TRAIL_SCALE_OUT_25_75` 写成 canonical control
5. 不把 sizing residual watch / watch / no-go 偷渡成 partial-exit baseline
6. 不自动打开 `PX1 / PX2`

---

## 6. Done 标准

1. `09-mainline-system-operating-baseline-20260309.md` 明确写入 Positioning absorption boundary
2. `01-current-mainline-implementation-spec-20260308.md` 明确写入当前允许和禁止的 Positioning 实现面
3. `docs/spec/v0.01-plus/records/` 出现对应 formal record
4. `development-status.md` 同步写明 `Phase 5B completed, next = Phase 5C`

---

## 7. 下一步

`Phase 5B` 完成后，下一张固定为：

`Phase 5C / mainline no-fake governance patch`
