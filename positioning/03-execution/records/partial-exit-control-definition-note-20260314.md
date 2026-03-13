# Partial-Exit Control Definition Note

**日期**: `2026-03-14`  
**阶段**: `Positioning / P6 -> P7 handoff`  
**对象**: `P7 null control baseline definition`  
**状态**: `Active`

---

## 1. 目标

本文只做一件事：

`把 P7 / partial-exit null control matrix 的 control baseline 定义写死。`

---

## 2. P7 Operating Control Pair

`P7` 当前 operating control pair 固定为：

1. `FULL_EXIT_CONTROL + FIXED_NOTIONAL_CONTROL`
2. `NAIVE_TRAIL_SCALE_OUT_50_50_CONTROL + FIXED_NOTIONAL_CONTROL`

其中：

1. `FULL_EXIT_CONTROL`
   - 当前 Broker 默认语义
   - 一旦 `STOP_LOSS` 或 `TRAILING_STOP` 触发，下一交易日整仓卖出
2. `NAIVE_TRAIL_SCALE_OUT_50_50_CONTROL`
   - `STOP_LOSS` 仍整仓卖出
   - 首次 `TRAILING_STOP` 触发时只卖出 `50% remaining quantity`
   - 第二次 `TRAILING_STOP` 或最终 `FORCE_CLOSE` 清掉剩余仓位

---

## 3. P7 Floor Sanity Pair

`P7` 当前 floor sanity pair 固定为：

1. `FULL_EXIT_CONTROL + SINGLE_LOT_CONTROL`
2. `NAIVE_TRAIL_SCALE_OUT_50_50_CONTROL + SINGLE_LOT_CONTROL`

这组 control 的职责不是给出运营默认值，而是防止：

`partial-exit control 的改善只是在高 deployment 环境下才成立。`

---

## 4. P7 当前唯一允许变化的维度

`P7` 当前只允许变化一个维度：

`exit quantity contract`

因此当前必须保持不变的内容固定为：

1. `entry baseline`
2. `sizing baseline`
3. `T+1 Open`
4. `fee / slippage`
5. `STOP_LOSS hard full exit`
6. `FORCE_CLOSE hard full exit`

---

## 5. A 股一手约束处理

当前 control 定义必须同时遵守 A 股一手约束：

1. 分腿后若任一腿小于 `100` 股，不允许生成零碎无效腿
2. 50/50 分腿在无法形成合法手数时，允许退化为 full exit
3. `P7` 必须把这类退化统计进 digest，而不是静默吞掉

---

## 6. 当前不允许做的事

`P7` 当前明确不允许：

1. 把 `STOP_LOSS` 也改成 partial-exit
2. 直接展开完整 `partial-exit family`
3. 在 control 阶段就做 targeted parameter sweep
4. 把 sizing residual watch 当作 partial-exit baseline

---

## 7. 一句话结论

`P7` 先比“全平”对“最朴素 trailing 50/50 分腿”，而不是一上来比整套 exit family；而且 operating 与 floor 两把尺子都必须保留。
