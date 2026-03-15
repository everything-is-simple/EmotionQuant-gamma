# Phase 5A Normandy Migration Boundary Absorption Card

**状态**: `Draft`  
**日期**: `2026-03-15`  
**对象**: `第一战场 / Phase 5A / Normandy migration boundary absorption`

---

## 1. 目标

`Phase 5A` 只做一件事：

`把第二战场已经收官的治理结论和 Tachibana pilot 边界，正式吸收到主线 SoT。`

---

## 2. 本卡要回答的问题

1. `legacy_bof_baseline` 在吸收 Normandy 结论后，当前默认口径是否变化
2. 哪些 Normandy 结论只能迁成治理约束，不能迁成默认参数
3. `baseline diagnosis lane` 与 `promotion lane` 的分离，怎样写成主线硬边界
4. `Tachibana pilot-pack` 当前到底只能以什么身份进入主线
5. 哪些 Normandy 研究结果必须继续留在研究线，不得偷渡回主线

---

## 3. 冻结输入

1. `normandy/03-execution/records/16-phase-normandy-campaign-closeout-record-20260313.md`
2. `normandy/03-execution/records/31-phase-n3n-tachibana-pilot-pack-migration-boundary-record-20260315.md`
3. `normandy/03-execution/records/32-phase-n3o-tachibana-pilot-pack-campaign-closeout-record-20260315.md`
4. `blueprint/01-full-design/09-mainline-system-operating-baseline-20260309.md`
5. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
6. `blueprint/03-execution/07-phase-5-research-line-migration-package-card-20260315.md`
7. `docs/spec/common/records/development-status.md`

当前明确不做：

1. `不新增 replay`
2. `不改写主线默认运行参数`
3. `不提前吸收 Positioning control baseline`
4. `不自动打开任何 targeted mechanism hypothesis`

---

## 4. 本卡交付物

1. 一张 `Phase 5A absorption card`
2. 一组 `mainline SoT delta`
3. 一张 `v0.01-plus Phase 5A record`

---

## 5. 固定边界

1. 不把 `BOF_CONTROL` 写成主线默认运行标签
2. 不把 `N2 / N2A` 的 exit diagnosis 误写成默认 trailing-stop 改写
3. 不把 `BOF quality branch` 误写成新主位
4. 不把 `Tachibana pilot-pack` 写成完整立花系统
5. 不把 `CD5 / CD10`、`single_lot floor`、`noncanonical side references` 偷渡成主线默认 aggregate
6. 不在 `Phase 5A` 里重写 `FIXED_NOTIONAL_CONTROL / SINGLE_LOT_CONTROL / FULL_EXIT_CONTROL`

---

## 6. Done 标准

1. `09-mainline-system-operating-baseline-20260309.md` 明确写入 Normandy absorption boundary
2. `01-current-mainline-implementation-spec-20260308.md` 明确写入当前允许和禁止的 Normandy 实现面
3. `docs/spec/v0.01-plus/records/` 出现对应 formal record
4. `development-status.md` 同步写明 `Phase 5A completed, next = Phase 5B`

---

## 7. 下一步

`Phase 5A` 完成后，下一张固定为：

`Phase 5B / Positioning migration boundary absorption`
