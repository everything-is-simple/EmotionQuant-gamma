# Phase P6 Partial-Exit Contract Freeze Card

**日期**: `2026-03-14`  
**阶段**: `Positioning / P6`  
**对象**: `第三战场第七张执行卡`  
**状态**: `Closed`

---

## 1. 目标

`P6` 只做一件事：

`在不讨论哪种分批卖法更优之前，先把 Broker 的 partial-exit / scale-out 契约、状态机和回测语义冻结。`

---

## 2. 本卡要回答的问题

1. 部分减仓需要哪些订单 / 成交 / 持仓字段
2. `SELL` 从默认全平扩展到部分减仓后，Broker 状态机如何定义
3. 回测引擎、报告与 trace 需要补哪些契约
4. partial-exit lane 的 control 组应该如何定义
5. 哪些历史路径必须保持兼容

---

## 3. 冻结输入

1. `entry baseline 不变`
2. `sizing baseline 固定继承 P5 closeout baseline（FIXED_NOTIONAL_CONTROL operating + SINGLE_LOT_CONTROL floor sanity）`
3. `不在本卡比较任何 exit family`

---

## 4. 本卡交付物

1. 一份 `partial-exit contract spec`
2. 一张 `P6 formal record`
3. 一张下一卡所需的 `control definition note`

---

## 5. 下一步出口

1. `P7 partial-exit null control matrix`

---

## 6. 一句话结论

`P6` 先冻结“怎么表达分批卖”，再研究“哪种分批卖更好”。`
