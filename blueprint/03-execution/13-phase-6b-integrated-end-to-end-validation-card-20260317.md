# Phase 6B Integrated End-to-End Validation Card

**状态**: `Active`  
**日期**: `2026-03-17`  
**对象**: `第一战场 / Phase 6B / integrated end-to-end validation`

---

## 1. 目标

`Phase 6B` 只做一件事：

`对 Phase 6A 冻结后的统一默认系统候选，做正式长窗 replay、对照矩阵和 gate 裁决。`

---

## 2. 本卡要回答的问题

1. 统一默认系统候选相对当前 baseline 到底改了什么
2. 改动后是否保持端到端稳定、trace 完整和可解释性
3. 统一默认系统候选是否真的值得 promotion，而不是只多了一层叙事
4. 哪些 failure mode 必须直接判 `NO-GO`

---

## 3. 冻结输入

1. `blueprint/03-execution/11-phase-6-unified-default-system-migration-package-card-20260317.md`
2. `blueprint/03-execution/12-phase-6a-promoted-subset-freeze-card-20260317.md`
3. `docs/spec/v0.01-plus/governance/v0.01-plus-promoted-subset-freeze-20260317.md`
4. `blueprint/01-full-design/09-mainline-system-operating-baseline-20260309.md`
5. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`

当前明确不做：

1. `不在验证过程中继续改 freeze scope`
2. `不做 case-by-case cherry-pick`
3. `不因局部亮点跳过 gate`

---

## 4. 本卡交付物

1. 一张 `integrated validation matrix`
2. 一组 `formal evidence bundle`
3. 一张 `Phase 6B formal record`

---

## 5. Done 标准

1. baseline 对照组与 promotion candidate 组同时重跑
2. 长窗与窗口切分 evidence 都落地
3. `GO / NO-GO / HOLD` 判定口径写死
4. `development-status.md` 同步写明 `Phase 6B completed, next = Phase 6C`

---

## 6. 下一步

`Phase 6B` 完成后，下一张固定为：

`Phase 6C / unified operating runbook refresh`
