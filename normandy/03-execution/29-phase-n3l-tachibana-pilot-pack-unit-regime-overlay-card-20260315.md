# Phase N3L Tachibana Pilot-Pack Unit-Regime Overlay Card

**状态**: `Active`  
**日期**: `2026-03-15`  
**对象**: `Tachibana pilot-pack unit-regime overlay`

---

## 1. 定位

`N3l` 要回答的是：

`pilot-pack 现在到底只有一条 operating unit regime，还是已经有第二条。`

---

## 2. 开工前提

1. `normandy/03-execution/28-phase-n3k-tachibana-pilot-pack-formal-cooldown-matrix-card-20260315.md`
2. `normandy/03-execution/records/28-phase-n3k-tachibana-pilot-pack-formal-cooldown-matrix-record-20260315.md`

---

## 3. 当前目标

1. 对照 `fixed_notional` operating pair
2. 对照 `single_lot` floor pair
3. 写死 `reduced_unit_scale` 当前只是 tag 还是已成 sizing

---

## 4. 固定边界

1. 不把 `single_lot` 误写成第二 operating lane
2. 不把 `reduced_unit_scale` 误写成可执行 sizing
3. 不改写 `N3k` 的 cooldown 结论

---

## 5. 任务拆解

### N3L-1 Operating Vs Floor Readout

目标：

1. 并排比较 `fixed_notional` 和 `single_lot`
2. 判断 proxy 在 floor 下是否退化

### N3L-2 Governance Tag Boundary

目标：

1. 查清 `unit_regime_tag / reduced_unit_scale` 当前落点
2. 写死它们只是 payload tag 还是已进入执行层

---

## 6. 出场条件

1. 已写死 `FIXED_NOTIONAL_CONTROL` 是否仍是唯一 operating regime
2. 已写死 `SINGLE_LOT_CONTROL` 是否只保留为 floor sanity
3. 已把下一步切到 `N3m / experimental-segment isolation`

---

## 7. 一句话任务

`把 unit regime 的边界钉死：谁是真正在跑的，谁只是地板校验。`
