# Tachibana Replay Ledger Contract Note

**文档版本**：`v0.01`  
**文档状态**：`Active`  
**日期**：`2026-03-15`  
**适用范围**：`Normandy / Tachibana replay ledger`

---

## 1. 目标

本 note 用来把 `74` 条月度事件，升级成带 `position_id / leg_id / state_transition` 的正式回放台账。

当前回放目标不是精确模拟资金曲线，而是把立花的仓位路径对象化。

---

## 2. 输入

当前输入文件为：

1. `tachibana_book_monthly_tables_1976_02_1976_12_event_extract_20260315.csv`

这份输入已经把书后页事件抽成：

1. `buy_units`
2. `sell_units`
3. `open_long_units`
4. `open_short_units`

---

## 3. 状态定义

当前回放状态只定义四类：

1. `flat`
2. `long_only`
3. `short_only`
4. `locked`

其中 `locked` 明确代表：

`多/空同时存在`

---

## 4. position_id 规则

### 4.1 新 position 启动

以下情况启动新的 `position_id`：

1. `flat -> non-flat`
2. `short_only -> long_only` 的直接反转
3. `long_only -> short_only` 的直接反转

### 4.2 position 延续

以下情况延续当前 `position_id`：

1. 同方向加减仓
2. `short_only -> locked`
3. `long_only -> locked`
4. `locked -> locked`
5. `locked -> single-side`

这条规则的含义是：

`锁单仍被视为同一场战役中的状态变化，不另开 position。`

---

## 5. leg_id 规则

`leg_id_after` 当前表示：

1. 某个 `position_id` 内第几次已确认的事件动作
2. 当新的 `position_id` 启动时重置为 `1`

---

## 6. state_transition 规则

当前至少允许下列转换：

1. `enter_long`
2. `enter_short`
3. `add_long`
4. `add_short`
5. `reduce_long`
6. `cover_short_partial`
7. `exit_long_to_flat`
8. `cover_short_to_flat`
9. `reverse_short_to_long`
10. `reverse_long_to_short`
11. `lock_long_against_short`
12. `lock_short_against_long`
13. `unlock_long`
14. `unlock_short`
15. `add_long_locked`
16. `reduce_long_locked`
17. `add_short_locked`
18. `reduce_short_locked`
19. `rebalance_locked`

---

## 7. 当前最重要的洞见

正式回放台账的意义有三点：

1. 它把 `立花方法` 从语录变成了状态机
2. 它证明 `锁单` 不是边角技巧，而是中间状态
3. 它允许后续把 `BOF entry + Tachibana execution` 真正对接

---

## 8. 当前文件

正式回放台账文件为：

1. `tachibana_replay_ledger_1976_02_1976_12_20260315.csv`

生成脚本为：

1. `scripts/ops/build_tachibana_replay_ledger.py`
