# Phase 6C Unified Operating Runbook Refresh Card

**状态**: `Draft`  
**日期**: `2026-03-17`  
**对象**: `第一战场 / Phase 6C / unified operating runbook refresh`

---

## 1. 目标

`Phase 6C` 只做一件事：

`把统一默认系统候选的运行链路、风险开关、人工介入边界和 rollback 规则，刷新成一套统一 runbook。`

---

## 2. 本卡要回答的问题

1. 当前统一默认系统候选到底按什么链路运行
2. 哪些风险开关允许开启，哪些必须保持关闭
3. Gene 在运行面上到底只是 sidecar、shadow，还是已经成为 runtime gate
4. 人工介入允许做到什么程度，什么动作必须被禁止
5. rollback target 和 emergency stop 条件怎么写

---

## 3. 冻结输入

1. `blueprint/03-execution/11-phase-6-unified-default-system-migration-package-card-20260317.md`
2. `blueprint/03-execution/12-phase-6a-promoted-subset-freeze-card-20260317.md`
3. `blueprint/03-execution/13-phase-6b-integrated-end-to-end-validation-card-20260317.md`
4. `docs/spec/v0.01-plus/governance/v0.01-plus-promoted-subset-freeze-20260317.md`
5. `docs/reference/operations/setup-guide.md`
6. `blueprint/01-full-design/09-mainline-system-operating-baseline-20260309.md`

当前明确不做：

1. `不把 runbook 写成算法正文`
2. `不把未过 gate 的对象写成默认开启`
3. `不让人工口头绕过 no-fake boundary`

---

## 4. 本卡交付物

1. 一份 `current mainline operating runbook`
2. 一组 `operations README / root README patch`
3. 一张 `Phase 6C formal record`

---

## 5. Done 标准

1. 运行链路、风险开关、人工边界、rollback 规则都写进统一 runbook
2. `docs/reference/operations/README.md` 出现正式入口
3. `development-status.md` 同步写明 `Phase 6C completed, next = Phase 6 closeout`

---

## 6. 下一步

`Phase 6C` 完成后，下一张固定为：

`Phase 6 closeout / default-system promotion decision record`
