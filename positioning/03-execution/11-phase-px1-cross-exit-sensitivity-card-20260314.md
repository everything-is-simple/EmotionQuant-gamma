# Phase PX1 Cross-Exit Sensitivity Card

**日期**: `2026-03-14`  
**阶段**: `Positioning / PX1`  
**对象**: `第三战场条件卡一`  
**状态**: `Draft`

---

## 1. 触发条件

`只有当 P4 明确产出 retained sizing candidate 时，本卡才允许打开。`

---

## 2. 目标

`PX1` 只做一件事：

`检查 retained sizing candidate 是否只在当前 frozen full-exit semantics 下成立。`

---

## 3. 本卡要回答的问题

1. retained sizing candidate 在不同 exit baseline 下是否仍然稳健
2. 它的优势是否严重依赖当前 exit 语义
3. 如果 exit 一变，当前 sizing retained 结论是否会翻转

---

## 4. 本卡交付物

1. 一份 `cross-exit sensitivity matrix`
2. 一张 `PX1 formal record`

---

## 5. 一句话结论

`PX1` 不是默认主干卡，只有 retained sizing candidate 真出现时才值得打开。`
