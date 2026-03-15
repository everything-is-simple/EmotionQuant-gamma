# Phase N3i Tachibana Pilot-Pack Implementation Scaffold Record

**日期**: `2026-03-15`  
**阶段**: `Normandy / N3i`  
**对象**: `Tachibana pilot-pack implementation scaffold formal readout`  
**状态**: `Closed`

---

## 1. 目标

本文用于把 `N3i / Tachibana pilot-pack implementation scaffold` 的正式实现边界写死。

这张 record 只回答 5 件事：

1. `E1` 的正式入口应如何落成
2. `E2` 的 cooldown family 最小实现应挂在哪一层
3. `E3` 的 tag / report glue 当前应补到什么粒度
4. 哪些核心层明确不在这轮实现里改
5. 下一张主队列卡应如何转向正式 runner implementation

---

## 2. Formal Inputs

本卡正式输入固定为：

1. `normandy/03-execution/evidence/tachibana_pilot_pack_implementation_scaffold_20260315.md`
2. `normandy/03-execution/evidence/tachibana_pilot_pack_executable_matrix_20260315.md`
3. `normandy/03-execution/records/25-phase-n3h-tachibana-pilot-pack-executable-matrix-record-20260315.md`
4. `normandy/03-execution/records/24-phase-n3g-tachibana-pilot-pack-opening-note-20260315.md`
5. `scripts/backtest/run_positioning_partial_exit_family_matrix.py`
6. `scripts/backtest/run_positioning_partial_exit_family_digest.py`
7. `src/backtest/engine.py`
8. `src/backtest/positioning_partial_exit_family.py`
9. `src/config.py`
10. `src/report/reporter.py`
11. `src/data/store.py`
12. `src/broker/risk.py`

---

## 3. 正式裁决

`N3i` 的正式裁决固定为：

1. `E1` 的正式入口固定采用：
   `Normandy thin runner -> positioning partial-exit family core`
2. `E2` 的 cooldown 最小实现固定挂在：
   `run_backtest() signal -> broker.process_signals() 之间的 optional signal_filter hook`
3. `E3` 的第一轮 tag / report glue 固定只落到：
   `scenario + matrix payload + digest payload`
4. `E4` 继续固定为：
   `governance overlay only`
5. `RiskManager / Broker / contracts` 当前继续固定：
   `not_touched_for_addon_buy`

---

## 4. E1 正式入口为什么必须是 thin runner

`E1` 当前正式固定为 thin runner，原因是：

1. `P8` 已经把 `TRAIL_SCALE_OUT_25_75` 跑成 retained leader
2. 现有仓库已有 `run_positioning_partial_exit_family_matrix.py` 与 digest 入口
3. 当前 Normandy 需要的不是再造一套 partial-exit family 逻辑，而是给 pilot-pack 一个正式入口名义与默认 labels

因此当前正确做法固定为：

1. 新增 Normandy 自有 wrapper script
2. 底层继续复用 `positioning_partial_exit_family`
3. 默认只开 `FULL_EXIT_CONTROL + TRAIL_SCALE_OUT_25_75`
4. `33/67` 与 `50/50` 仅作为 side references 显式附带

---

## 5. E2 为什么挂在 engine hook，而不是 RiskManager

`E2` 当前正式挂在 `engine signal_filter hook`，原因固定为：

1. cooldown 是 `entry gating`，不是新增持仓能力
2. 它要挡的是 `full exit` 之后的再入场节律，而不是持仓内加码
3. 如果把它塞进 `RiskManager`，很容易与 `ALREADY_HOLDING`、现金控制、max_positions 逻辑缠在一起
4. 当前最小做法是在 signal 进入 Broker 前做 gating，既不改 Broker 核心，也不伪装成新执行语义

因此当前写死：

1. `run_backtest()` 增加可选 `signal_filter hook`
2. cooldown family 只通过该 hook 拦截信号
3. 第一轮固定只开 `0 / 2 / 5 / 10` bar

---

## 6. E3 为什么只落 output layer

`E3` 当前正式只落到 output layer，原因固定为：

1. `unit_regime` 当前首先是制度变量和治理标签
2. 第一轮并不需要 per-trade 新成交语义
3. 如果现在就扩 `l4_orders / l4_trades / broker trace`，改动面会过宽
4. 当前更诚实的做法是先把 `unit_regime_tag / reduced_unit_scale / experimental_segment_policy` 贯穿到 scenario 与 payload

因此当前正式写死：

1. 第一轮不改 `Store schema`
2. 第一轮不改 reporter pairing 主逻辑
3. 只有当后续确实需要 `per-trade unit regime slicing` 时，才允许回头扩表

---

## 7. 明确不动的内容

当前 `N3i` 明确不动以下内容：

1. `src/broker/risk.py` 中 `ALREADY_HOLDING` 的硬边界
2. `src/broker/broker.py` 的 BUY-only 主线
3. `src/contracts.py` 的 `SignalActionType = BUY`
4. 任何 `probe -> mother promotion`
5. 任何 `same-side add-on BUY`
6. 任何 `reduce -> re-add`
7. 任何新的 sizing formula

这里必须再次写死：

`N3i` 不是实现完整立花执行器，而是把当前 pilot-pack 的最小 runner 改动面收窄。`

---

## 8. 下一张卡

`N3i` 完成后的 next main queue card 固定为：

`N3j / Tachibana pilot-pack runner implementation`

它只允许回答：

1. Normandy thin runner 如何正式落文件
2. `run_backtest()` 的 `signal_filter hook` 如何最小接入且不影响旧路径
3. `unit_regime_tag / reduced_unit_scale / experimental_segment_policy` 如何贯穿 matrix/digest

它明确不允许回答：

1. 是否顺手打开 `R2 / R3 / R8 / R9`
2. 是否把 cooldown 写成新的 detector
3. 是否把 `reduced_unit` 升格成 sizing lane

---

## 9. 正式结论

当前 `N3i Tachibana pilot-pack implementation scaffold` 的正式结论固定为：

1. `E1` 已固定为 Normandy thin runner 包装现有 partial-exit family core
2. `E2` 已固定为 `engine signal_filter hook` 级别的轻量扩展
3. `E3` 已固定为 output-layer tag / report glue，而不是扩表或重写成交语义
4. `E4` 继续保持 governance overlay 身份
5. `Broker / RiskManager / contracts` 当前继续保持不动

---

## 10. 一句话结论

`N3i` 已把 Tachibana pilot-pack 从“执行分流表”进一步推进成“最小实现图”：正式入口走 thin runner，cooldown 走 engine hook，unit regime 先走 payload tag，核心引擎与 add-on BUY 缺口继续保持冻结。`
