# Phase P6 Partial-Exit Contract Freeze Record

**日期**: `2026-03-14`  
**阶段**: `Positioning / P6`  
**对象**: `第三战场第七张执行卡 formal readout`  
**状态**: `Closed`

---

## 1. 目标

本文用于把 `P6 / partial-exit contract freeze` 的正式结论写死。

这张 record 只回答 5 件事：

1. 当前代码里的 Broker exit 真相源到底是什么
2. partial-exit v1 当前决定怎样表达
3. 哪些字段、ID 和状态机必须先冻结
4. `P7` control 组应该怎样定义
5. 哪些兼容路径必须保持不变

---

## 2. Formal Inputs

本卡正式输入固定为：

1. `positioning/03-execution/records/06-phase-p5-sizing-lane-closeout-record-20260314.md`
2. `positioning/03-execution/records/sizing-lane-migration-boundary-table-20260314.md`
3. `positioning/03-execution/records/partial-exit-lane-opening-note-20260314.md`
4. `src/contracts.py`
5. `src/broker/broker.py`
6. `src/broker/matcher.py`
7. `src/broker/risk.py`
8. `src/backtest/engine.py`
9. `src/report/reporter.py`
10. `src/data/store.py`
11. `tests/unit/broker/test_broker.py`
12. `tests/patches/broker/test_broker_trace_semantics_regression.py`
13. `positioning/02-implementation-spec/02-partial-exit-contract-spec-20260314.md`

---

## 3. 当前代码真相源读数

当前正式读数固定为：

1. `Signal` 当前只允许 `BUY`
2. 退出单当前只来自 `Broker` 自己，而不来自上游 signal
3. `generate_exit_orders()` 当前只会按整仓数量创建 `SELL`
4. `Matcher` 当前是 `一张订单 -> 一笔成交`
5. `Reporter` 已经支持数量 FIFO 配对，但当前 paired 输出不携带 `position_id / exit_leg`
6. `Broker._apply_position_trade()` 已能维护 `remaining quantity`，但当前缺少 formal partial-exit contract

一句话说：

`partial-exit 当前不是执行引擎完全不会做，而是“引擎局部可做、契约还没冻结”。`

---

## 4. 正式冻结裁决

`P6` 的正式裁决固定为：

1. `Signal remains BUY-only`
2. `partial_exit_v1 = multi-sell-leg contract`
3. `single_order_partial_fill = not_in_scope`
4. `STOP_LOSS = hard full exit`
5. `FORCE_CLOSE = hard full exit`
6. `one_pending_sell_per_position = yes`
7. `position_id must be introduced before P7 / P8`

同时写死：

1. `position_id = entry BUY order_id`
2. `exit_plan_id / exit_leg_id / exit_leg_seq` 必须成为 formal identity
3. `l4_orders / l4_trades / broker_order_lifecycle_trace_exp` 必须补 position-aware 字段
4. `reporter` 后续必须从纯 `code + FIFO` 过渡到 `position-aware pairing`

---

## 5. P7 Control Definition

`P6` 当前把 `P7` 的 control 组正式写定为：

### 5.1 Operating Control Pair

1. `FULL_EXIT_CONTROL + FIXED_NOTIONAL_CONTROL`
2. `NAIVE_TRAIL_SCALE_OUT_50_50_CONTROL + FIXED_NOTIONAL_CONTROL`

### 5.2 Floor Sanity Pair

1. `FULL_EXIT_CONTROL + SINGLE_LOT_CONTROL`
2. `NAIVE_TRAIL_SCALE_OUT_50_50_CONTROL + SINGLE_LOT_CONTROL`

其中：

1. `STOP_LOSS` 继续 hard full exit
2. `NAIVE_TRAIL_SCALE_OUT_50_50_CONTROL` 只在 `TRAILING_STOP` 路径上引入 50/50 scale-out
3. A 股一手约束导致无法分腿时，允许退化为 full exit

---

## 6. 必须保持的兼容路径

当前必须保持不变的兼容路径固定为：

1. `T+1 Open` 执行语义
2. `force_close` 作为窗口末统一清仓例外
3. `BUY` 侧风控、撮合、trace 语义不改
4. 当前 full-exit 路径必须仍能作为 partial-exit contract 的 degenerate case

---

## 7. 下一张卡

`P6` 完成后的 next main queue card 固定为：

`P7 / partial-exit null control matrix`

它当前只允许回答：

1. `FULL_EXIT_CONTROL` 与 `NAIVE_TRAIL_SCALE_OUT_50_50_CONTROL` 的 control 对照
2. operating 与 floor 两套 control baseline 的参与一致性和 pnl shape

---

## 8. 正式结论

当前 `P6 partial-exit contract freeze` 的正式结论固定为：

1. 第三战场 partial-exit lane 已完成 contract freeze
2. partial-exit v1 当前正式采用：
   - `多 SELL 腿`
   - `单腿单次成交`
   - `Signal 仍只发 BUY`
3. `STOP_LOSS / FORCE_CLOSE` 当前继续保持 hard full exit
4. `position_id / exit_plan_id / exit_leg_id` 已被正式提升为必须补齐的身份层
5. `P7` 的 control pair 已正式写定
6. 第三战场主队列正式切到 `P7 / partial-exit null control matrix`

---

## 9. 一句话结论

`P6` 已把“怎么表达分批卖”正式写死了：不是改单内部分成交，而是补 position-aware 的多腿 SELL 契约；下一步不再争论 contract，而是去跑 `P7` control matrix。
