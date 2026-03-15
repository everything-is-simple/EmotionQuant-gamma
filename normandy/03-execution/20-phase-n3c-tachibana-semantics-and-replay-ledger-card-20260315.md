# Phase N3C Tachibana Semantics And Replay Ledger Card

**状态**: `Active`  
**日期**: `2026-03-15`  
**对象**: `Tachibana execution semantics and replay ledger`

---

## 1. 定位

`N3c` 不是回测卡。  
它是把立花方法从“书上故事”压成：

`可被 replay 的状态转移账本。`

---

## 2. 开工前提

1. `normandy/03-execution/19-phase-n3b-tachibana-rear-pages-source-correction-card-20260315.md`
2. `normandy/03-execution/records/19-phase-n3b-tachibana-rear-pages-source-correction-record-20260315.md`

---

## 3. 当前目标

1. 把执行语义写成 evidence table
2. 把事实源压成 replay ledger
3. 明确 ledger 是 state-transition-aware 的，而不是随手摘录

---

## 4. 固定边界

1. 不宣称完整系统可验证
2. 不跳过语义表直接写规则矩阵
3. 不把 ledger 写成没有语义约束的流水账

---

## 5. 任务拆解

### N3C-1 Execution Semantics Table

目标：

1. 写清 entry / reduce / full exit / reverse 等语义
2. 标出当前能确认和不能确认的部分

### N3C-2 Replay Ledger Build

目标：

1. 生成可复核的 ledger
2. 让后面 state transition 候选表有正式输入

---

## 6. 出场条件

1. 已落执行语义表
2. 已落 replay ledger
3. 已把下一步切到 `N3d / module reuse triage`

---

## 7. 一句话任务

`把立花方法先翻译成能回放的账，再谈哪些规则能迁回来。`
