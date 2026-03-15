# Phase N3 Tachibana Tradebook Contract Card

**状态**: `Active`  
**日期**: `2026-03-15`  
**对象**: `Tachibana tradebook contract formalization`

---

## 1. 定位

`N3` 不是直接开跑“立花系统回测”。  
它先解决一个更基础的问题：

`我们到底拿什么当立花方法的正式真值载体。`

---

## 2. 开工前提

开工前必须先继承：

1. `normandy/README.md`
2. `normandy/02-implementation-spec/10-tachibana-quantifiable-execution-system-spec-20260315.md`
3. `normandy/01-full-design/90-research-assets/tachibana-crowd-failure-minimal-contract-note-20260312.md`

---

## 3. 当前目标

`N3` 当前只做三件事：

1. 明确 `tradebook scaffold` 才是第一层 formal carrier
2. 不再把口头理解当成“立花原书真值”
3. 为后面的 `replay ledger / state transition / rule candidate matrix` 打底

---

## 4. 固定边界

本卡固定边界为：

1. 不宣称“原始全量交易账已经复原”
2. 不直接进入回测 runner
3. 不偷带 `probe -> mother promotion / add-on BUY / re-add`

---

## 5. 任务拆解

### N3-A Truth Carrier Freeze

目标：

1. 明确第一层真值载体是 `ledger scaffold`
2. 写清哪些字段必须进入 formal contract

### N3-B Replay Readiness Boundary

目标：

1. 写清当前哪些内容还只是 scaffold
2. 明确不能把 scaffold 误写成“已经可机读重放”

### N3-C Next-Card Handoff

目标：

1. 把下一步固定到样本阻塞与事实源修正
2. 不让 Tachibana 又滑回“以后再说”

---

## 6. 建议输出

本卡建议至少落下：

1. `tradebook scaffold evidence`
2. `tradebook contract record`

---

## 7. 出场条件

`N3` 只有在以下条件成立时才允许出场：

1. 已写死 tradebook scaffold 是第一层 formal carrier
2. 已写死当前还不能把它冒充成完整事实账
3. 已把下一步切到 `N3a / source blocker`

---

## 8. 一句话任务

`先把立花方法的真值载体定下来，再谈验证；别用口头理解假装自己已经有了完整交易账。`
