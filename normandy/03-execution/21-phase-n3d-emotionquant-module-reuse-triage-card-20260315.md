# Phase N3D EmotionQuant Module Reuse Triage Card

**状态**: `Active`  
**日期**: `2026-03-15`  
**对象**: `EmotionQuant module reuse triage for Tachibana validation`

---

## 1. 定位

`N3d` 只做一件事：

`现有 EmotionQuant 仓库里，哪些东西能直接复用，哪些只能改造复用，哪些必须明确退出。`

---

## 2. 开工前提

1. `normandy/03-execution/20-phase-n3c-tachibana-semantics-and-replay-ledger-card-20260315.md`
2. `normandy/03-execution/records/20-phase-n3c-tachibana-semantics-and-replay-ledger-record-20260315.md`

---

## 3. 当前目标

1. 做模块复用分流
2. 给后面的 pilot-pack 确定可借壳载体
3. 禁止“为了立花重写一整套新引擎”

---

## 4. 固定边界

1. 不重写 Broker
2. 不偷解 `ALREADY_HOLDING`
3. 不拿不可复用资产硬凑可用

---

## 5. 任务拆解

### N3D-1 Direct Reuse

目标：

1. 找出现成可直接借壳的模块
2. 记录复用理由

### N3D-2 Adapted Reuse

目标：

1. 标出需要薄包装的模块
2. 写清最低改造成本

### N3D-3 Explicit Exit

目标：

1. 把当前不该碰的主线能力挡住
2. 为 pilot-pack 定边界

---

## 6. 出场条件

1. 已形成 reuse triage table
2. 已写死可复用/改造复用/退出主线三类分流
3. 已把下一步切到 `N3e / state transition candidate table`

---

## 7. 一句话任务

`先看仓库里哪套壳能借，再决定立花先搬哪一小块。`
