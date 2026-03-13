# Partial-Exit Contract Spec

**日期**: `2026-03-14`  
**对象**: `第三战场 P6 当前唯一 partial-exit contract freeze`  
**状态**: `Active`

---

## 1. 目标

本文只定义第三战场当前唯一 `partial-exit / scale-out` 契约方案。

它只回答：

`在不比较哪种卖法更优之前，Broker / Backtest / Report / Trace 应该怎样表达“部分减仓”。`

它不回答：

1. 哪个 `partial-exit family` 最优
2. 哪个参数组合最值得默认升级
3. 是否立即打开 `PX1 / cross-exit sensitivity`

---

## 2. 当前代码真相源

`P6` 当前正式承认以下代码真相源：

1. `src/contracts.py`
2. `src/broker/broker.py`
3. `src/broker/matcher.py`
4. `src/broker/risk.py`
5. `src/backtest/engine.py`
6. `src/report/reporter.py`
7. `src/data/store.py`
8. `tests/unit/broker/test_broker.py`
9. `tests/patches/broker/test_broker_trace_semantics_regression.py`

当前代码事实固定为：

1. `SignalActionType = BUY only`
2. `SELL` 订单不来自上游信号，而由 `Broker.generate_exit_orders()` 和回测末日 `force_close` 自行生成
3. `generate_exit_orders()` 当前只会为整仓生成一张 `SELL`，其数量固定等于 `pos.quantity`
4. `Broker._has_pending_sell(code)` 当前按 `code` 粒度禁止重复挂出 `SELL`
5. `Matcher` 当前是 `单订单 -> 单次撮合 -> 单 Trade`
6. `OrderStatus` 当前只有 `PENDING / FILLED / REJECTED / EXPIRED`
7. `resolve_order_origin()` 当前只有 `UPSTREAM_SIGNAL / EXIT_STOP_LOSS / EXIT_TRAILING_STOP / FORCE_CLOSE`
8. `Reporter._pair_trades()` 已经支持按数量做 FIFO 配对，但当前 paired 输出不携带 `position_id / exit_leg` 等结构化身份
9. `Broker._apply_position_trade()` 对 `SELL` 已能处理 `remain > 0`，但当前运行语义仍是“默认全平退出”

一句话说：

`当前代码并不是完全不能减仓，而是执行内核已经有“数量剩余”能力，但契约、ID、trace 和 report 还没有把它正式表达出来。`

---

## 3. 当前冻结前提

`P6` 当前固定继承以下前提：

1. `entry baseline = legacy_bof_baseline`
2. `no IRS`
3. `no MSS`
4. `signal_date = T / execute_date = T+1 / fill = T+1 open`
5. `sizing baseline = FIXED_NOTIONAL_CONTROL operating + SINGLE_LOT_CONTROL floor sanity`

同时写死：

1. `Signal` 继续只表达 `BUY`
2. 上游 `Selector / Strategy` 不直接产生 `SELL`
3. `partial-exit lane` 不得把 sizing residual watch 偷渡成 baseline

---

## 4. P6 Freeze Decision

### 4.1 v1 partial-exit 表达方式

`P6` 把 v1 partial-exit 契约固定为：

1. `部分减仓 = 多张 SELL 订单`
2. `每张 SELL 订单 = 一个明确 exit leg`
3. `每张 SELL 订单仍只允许一次撮合，产出一笔 Trade`
4. `P6` 不引入“单张订单内部 partial fill”语义

这意味着：

`v1 只扩“多腿退出”，不扩“单腿多次成交”。`

### 4.2 v1 兼容边界

当前必须继续保持以下 hard compatibility：

1. `STOP_LOSS = hard full exit`
2. `FORCE_CLOSE = hard full exit`
3. `partial-exit` 只允许作用于非紧急退出路径
4. `一只股票 / 一个 position 同一时刻只允许一张 pending SELL`
5. `T+1 Open` 撮合语义不变

一句话说：

`v1 partial-exit 不是放松止损，而是在保留 stop-loss / force-close 全平语义的前提下，给非紧急退出路径增加多腿表达能力。`

---

## 5. 必须冻结的契约字段

### 5.1 Position 层

当前 `Position` 内部状态至少必须补齐：

1. `position_id`
2. `entry_signal_id`
3. `entry_order_id`
4. `entry_trade_id`
5. `initial_quantity`
6. `remaining_quantity`
7. `exit_leg_filled_count`
8. `last_exit_date`
9. `last_exit_reason`

冻结规则：

`position_id` 当前固定以开仓 `BUY order_id` 为稳定身份。`

### 5.2 Order 层

当前 `Order` 至少必须补齐以下 partial-exit 识别字段：

1. `position_id`
2. `exit_plan_id`
3. `exit_leg_seq`
4. `exit_leg_count`
5. `exit_reason_code`
6. `is_partial_exit`
7. `remaining_qty_before`
8. `target_qty_after`

冻结规则：

`BUY` 订单这些字段允许为空；`SELL` 订单一旦进入 partial-exit 语义，上述字段必须齐。`

### 5.3 Trade 层

当前 `Trade` 至少必须补齐：

1. `position_id`
2. `exit_plan_id`
3. `exit_leg_seq`
4. `is_partial_exit`
5. `remaining_qty_after`

冻结规则：

`Trade` 必须能回答“这笔成交属于哪一个 position、是哪一腿、成交后还剩多少”。`

### 5.4 Lifecycle Trace 层

`broker_order_lifecycle_trace_exp` 至少必须补齐：

1. `position_id`
2. `exit_plan_id`
3. `exit_leg_seq`
4. `is_partial_exit`
5. `remaining_qty_before`
6. `remaining_qty_after`

冻结规则：

`trace` 必须能解释“哪一腿什么时候创建、什么时候成交/拒绝/过期，以及是否导致 position 关闭”。`

---

## 6. ID 与状态机冻结

### 6.1 ID 规则

当前必须明确补出三类稳定身份：

1. `position_id`
   - 固定为开仓 `BUY order_id`
2. `exit_plan_id`
   - 固定为同一 position 下的一次退出计划身份
3. `exit_leg_id`
   - 固定为 `exit_plan_id + leg_seq`

同时写死：

`build_exit_order_id()` 当前只够表达“单腿全平退出”；一旦进入 partial-exit，必须升级为 leg-aware ID。`

### 6.2 Position 状态机

`P6` 将 position 状态机固定为：

1. `OPEN`
2. `PARTIAL_EXIT_PENDING`
3. `OPEN_REDUCED`
4. `FULL_EXIT_PENDING`
5. `CLOSED`

状态迁移固定为：

1. `BUY FILLED -> OPEN`
2. `OPEN -> PARTIAL_EXIT_PENDING`
   - 当非紧急退出路径创建的 `SELL` 数量 `< remaining_quantity`
3. `OPEN / OPEN_REDUCED -> FULL_EXIT_PENDING`
   - 当 `STOP_LOSS / FORCE_CLOSE` 或最终清仓腿创建
4. `PARTIAL_EXIT_PENDING -> OPEN_REDUCED`
   - 当该腿成交且仍有剩余仓位
5. `FULL_EXIT_PENDING -> CLOSED`
   - 当最终清仓腿成交
6. `PARTIAL_EXIT_PENDING / FULL_EXIT_PENDING -> OPEN / OPEN_REDUCED`
   - 当该腿被 `REJECTED / EXPIRED`

---

## 7. Backtest / Report / Store 冻结要求

### 7.1 Backtest Engine

`engine` 当前固定顺序：

1. `execute_pending_orders`
2. `expire_orders`
3. `generate_exit_orders`
4. `process_signals`
5. `force_close`

`P6` 冻结要求是：

1. 这个时钟顺序不变
2. `generate_exit_orders()` 后续要从“生成单张整仓 SELL”扩成“生成一张 leg-aware SELL”
3. `force_close` 永远直接清空 `remaining_quantity`

### 7.2 Store Schema

当前 `l4_orders / l4_trades / broker_order_lifecycle_trace_exp` 都缺少 `position_id / exit_leg` 粒度字段。

因此 `P6` 冻结为：

1. `P7 / P8` 开工前必须先补 schema
2. 这次补的是 formal schema，不走 optional column 静默兼容

### 7.3 Reporter

`reporter._pair_trades()` 当前已经支持按 `quantity` 做 FIFO 配对。

但 `P6` 明确写死：

1. 报告层不能只靠 `code + FIFO queue` 长期承担 partial-exit 真相源
2. `position_id` 必须进入 report 配对输入
3. paired 输出后续至少要能保留：
   - `position_id`
   - `entry_leg / exit_leg`
   - `exit_reason`
   - `is_partial_exit`

---

## 8. P7 Control Definition Freeze

`P6` 当前把 `P7` 的 control 定义固定为两组双尺子：

### 8.1 Operating Control Pair

1. `FULL_EXIT_CONTROL`
   - 当前 Broker 默认语义
   - `FIXED_NOTIONAL_CONTROL` sizing
2. `NAIVE_TRAIL_SCALE_OUT_50_50_CONTROL`
   - `STOP_LOSS` 仍为 hard full exit
   - 首次 `TRAILING_STOP` 只卖出 `50% remaining quantity`
   - 第二次 `TRAILING_STOP` 或窗口末 `FORCE_CLOSE` 清掉剩余仓位
   - 若 50% 分腿因 A 股一手约束无法成立，则该次触发退化为 full exit

### 8.2 Floor Sanity Pair

1. `FULL_EXIT_CONTROL + SINGLE_LOT_CONTROL`
2. `NAIVE_TRAIL_SCALE_OUT_50_50_CONTROL + SINGLE_LOT_CONTROL`

一句话说：

`P7` 先比较“是否分腿”这件事，不比较复杂 family；而且 stop-loss 仍保持 hard full exit。`

---

## 9. 当前不允许做的事

`P6` 当前明确不允许：

1. 把 `STOP_LOSS` 偷渡成 partial-exit
2. 一上来做“同一张 SELL 订单多次成交”的复杂撮合
3. 不补 `position_id` 就直接开始 `P7 / P8`
4. 让 `Signal` 扩成上游直接发 `SELL`
5. 用 sizing residual watch 作为 partial-exit lane 隐含 baseline

---

## 10. 一句话结论

`P6` 当前唯一契约方案已经写死：Signal 继续只发 BUY，partial-exit v1 用“多张 SELL 腿 + 单腿单次成交”表达，STOP_LOSS / FORCE_CLOSE 保持 hard full exit，P7 先拿 full-exit 对照最朴素的 50/50 trailing scale-out control。
