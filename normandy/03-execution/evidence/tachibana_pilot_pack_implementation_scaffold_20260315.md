# Tachibana Pilot-Pack Implementation Scaffold

**文档版本**: `v0.01`  
**文档状态**: `Active`  
**日期**: `2026-03-15`  
**适用范围**: `Normandy / Tachibana pilot-pack implementation scaffold`

---

## 1. 目标

`N3h` 已经把 pilot-pack 压成了执行分流表。  
`N3i` 要做的不是再裁决“该不该做”，而是把 implementation 面收窄成：

`哪些文件需要新增，哪些文件只做最小改动，哪些地方明确不动。`

因此本文只回答 4 件事：

1. `E1` 的正式入口如何落到仓库里的实际 runner
2. `E2` 的 cooldown family 最小实现应挂在哪一层
3. `E3` 的 tag / report glue 需要补哪些最小字段与 payload
4. 哪些核心层明确不在这轮实现里改写

---

## 2. Formal Inputs

本文正式输入固定为：

1. `normandy/03-execution/evidence/tachibana_pilot_pack_executable_matrix_20260315.md`
2. `normandy/03-execution/records/25-phase-n3h-tachibana-pilot-pack-executable-matrix-record-20260315.md`
3. `normandy/03-execution/records/24-phase-n3g-tachibana-pilot-pack-opening-note-20260315.md`
4. `positioning/03-execution/records/07-phase-p6-partial-exit-contract-freeze-record-20260314.md`
5. `positioning/03-execution/records/08-phase-p7-partial-exit-null-control-matrix-record-20260314.md`
6. `positioning/03-execution/records/09-phase-p8-partial-exit-family-replay-record-20260315.md`
7. `scripts/backtest/run_positioning_partial_exit_family_matrix.py`
8. `scripts/backtest/run_positioning_partial_exit_family_digest.py`
9. `src/backtest/engine.py`
10. `src/backtest/positioning_partial_exit_family.py`
11. `src/backtest/partial_exit_null_control.py`
12. `src/config.py`
13. `src/report/reporter.py`
14. `src/data/store.py`

---

## 3. 实现总原则

`N3i` 当前固定遵守下面 5 条实现原则：

1. `E1` 必须复用现有 `positioning partial-exit family` 载体，不重写新引擎
2. `E2` 的 cooldown 只允许作为 `signal gating / runner orchestration` 轻量扩展接入，不改 Broker 核心语义
3. `E3` 的 `unit_regime` 只允许先做显式 tag 与 output glue，不引入新 sizing 公式
4. `E4` 继续作为治理覆盖层贯穿输出，不在这轮新增交易逻辑
5. `RiskManager -> ALREADY_HOLDING` 这条硬边界不得被绕开

---

## 4. 最小文件图

当前 implementation scaffold 固定为下面这组文件图：

| 工作包 | 新增文件 | 最小改动文件 | 作用 | 当前裁决 |
|---|---|---|---|---|
| `E1_formal_entry` | `scripts/backtest/run_normandy_tachibana_pilot_pack_matrix.py`、`scripts/backtest/run_normandy_tachibana_pilot_pack_digest.py`、`src/backtest/normandy_tachibana_pilot_pack.py` | 无或仅 very-thin import glue | 给 `reduce_to_core proxy replay` 一个 Normandy 自有正式入口，但底层继续复用 `positioning_partial_exit_family` | `must_do` |
| `E2_cooldown_runner` | 继续复用 `src/backtest/normandy_tachibana_pilot_pack.py` | `src/backtest/engine.py`、`src/config.py` | 在不改 Broker 核心的前提下，为 `0 / 2 / 5 / 10` bar cooldown 提供最小 signal filter hook | `must_do` |
| `E3_tag_report_glue` | 无必须新增文件；优先复用 `src/backtest/normandy_tachibana_pilot_pack.py` payload builder | `src/config.py`、`src/report/reporter.py` 或 wrapper payload 层 | 把 `unit_regime_tag / reduced_unit_scale / experimental_segment_policy` 写进 matrix/digest 输出 | `must_do_but_keep_thin` |
| `E4_governance_overlay` | 无 | wrapper digest / record writer | 确保所有 pilot 输出继续声明 `experimental_100_share` 不并入 canonical aggregate | `must_do_governance_only` |

---

## 5. E1 正式入口

### 5.1 正式入口文件

`E1` 的正式入口固定落成以下 3 个文件：

1. `src/backtest/normandy_tachibana_pilot_pack.py`
2. `scripts/backtest/run_normandy_tachibana_pilot_pack_matrix.py`
3. `scripts/backtest/run_normandy_tachibana_pilot_pack_digest.py`

### 5.2 为什么 `E1` 不该另写新逻辑

因为 `E1` 当前真正要做的只是：

`把 FULL_EXIT_CONTROL vs TRAIL_SCALE_OUT_25_75 这组 pilot 入口正式化`

所以底层应直接复用：

1. `build_positioning_partial_exit_family_scenarios()`
2. `run_positioning_partial_exit_family_matrix()`
3. `build_positioning_partial_exit_family_digest()`

`E1` 当前不应做的事固定为：

1. 不重写 partial-exit family builder
2. 不重写 Broker exit 语义
3. 不把 `TRAIL_SCALE_OUT_33_67 / TRAIL_SCALE_OUT_50_50` 升格为默认主入口

### 5.3 第一轮 CLI 口径

`E1` 的第一轮 CLI 口径固定建议为：

```text
python scripts/backtest/run_normandy_tachibana_pilot_pack_matrix.py --start 2023-01-03 --end 2026-02-24
python scripts/backtest/run_normandy_tachibana_pilot_pack_digest.py --matrix <matrix_json>
```

默认入口固定为：

1. `FULL_EXIT_CONTROL`
2. `TRAIL_SCALE_OUT_25_75`

side references 只允许显式打开：

1. `TRAIL_SCALE_OUT_33_67`
2. `TRAIL_SCALE_OUT_50_50`

---

## 6. E2 Cooldown Runner

### 6.1 最小挂载层

`E2` 的 cooldown 不应落在 `RiskManager`，也不应直接改 `Broker` 持仓规则。

当前最小挂载层固定为：

`run_backtest() signal -> broker.process_signals() 之间`

也就是说：

1. 先照常跑 `select_candidates()`
2. 再照常跑 `generate_signals()`
3. 然后在 `broker.process_signals()` 之前插入一个可选 `signal_filter hook`
4. 由该 hook 根据 `same code + full exit date + cooldown bars` 决定哪些信号先挡掉

### 6.2 最小代码位点

`E2` 当前最小代码位点固定为：

1. `src/backtest/engine.py`
   给 `run_backtest()` 增加可选 `signal_filter` hook
2. `src/config.py`
   增加 `entry_cooldown_trade_days` 与 `tachibana_pilot_mode` 这类最小配置项
3. `src/backtest/normandy_tachibana_pilot_pack.py`
   实现 `0 / 2 / 5 / 10` bar cooldown scenario builder 与 filter

### 6.3 当前明确不做的

`E2` 当前明确不做：

1. 不改 `RiskManager` 的 `ALREADY_HOLDING`
2. 不加 `probe_state`
3. 不加 `mother promotion`
4. 不把 cooldown 解释成新的 entry detector

### 6.4 第一轮输出字段

`E2` 第一轮 matrix payload 至少应补出：

1. `entry_cooldown_trade_days`
2. `cooldown_blocked_signal_count`
3. `cooldown_blocked_signal_share`
4. `cooldown_scope = same_code_after_full_exit`

---

## 7. E3 Tag / Report Glue

### 7.1 第一轮 tag 只落 output layer

`E3` 当前第一轮不要求扩表到 `l4_orders / l4_trades / broker trace`。

第一轮正确做法固定为：

`先把 unit regime tag 落到 scenario / matrix / digest payload`

这意味着当前最小必备字段固定为：

1. `unit_regime_tag`
2. `reduced_unit_scale`
3. `pilot_pack_component`
4. `experimental_segment_policy`

### 7.2 为什么第一轮不改表

因为当前 `unit regime` 主要承担的是：

1. 场景身份
2. 治理标签
3. 报告切片

而不是新增成交语义。

所以第一轮应优先把 tag 放在：

1. scenario dataclass
2. matrix payload
3. digest payload
4. record readout

只有当后续真的需要做：

`per-trade unit regime slicing`

才允许再回头扩 `Store schema`。

### 7.3 最小改动位点

`E3` 当前最小改动位点固定为：

1. `src/config.py`
   增加 `tachibana_unit_regime_tag`、`tachibana_reduced_unit_scale`
2. `src/backtest/normandy_tachibana_pilot_pack.py`
   在 scenario 与 payload 中写出 `unit_regime_tag / reduced_unit_scale / experimental_segment_policy`
3. `scripts/backtest/run_normandy_tachibana_pilot_pack_digest.py`
   把这些字段贯穿到 digest 结论与 summary

### 7.4 当前明确不做的

`E3` 当前明确不做：

1. 不重开 sizing family
2. 不引入新的 sizing formula
3. 不让 `reduced_unit` 变成另一个仓位优化实验

---

## 8. E4 贯穿方式

`E4` 当前继续只作为治理覆盖层存在。

所以它在 implementation scaffold 里的落点固定为：

1. matrix payload 明确写 `experimental_segment_policy = isolate_from_canonical_aggregate`
2. digest summary 明确写 canonical aggregate 不并入 `experimental_100_share`
3. record readout 明确把实验段汇总写成 sidecar，而不是主结论

---

## 9. 明确不动的核心层

`N3i` 当前明确不动以下核心层：

1. `src/broker/risk.py` 中 `ALREADY_HOLDING` 的主约束
2. `src/broker/broker.py` 的 BUY-only 主线
3. `src/contracts.py` 的 `SignalActionType = BUY`
4. `src/report/reporter.py` 的 position-aware pairing 主逻辑
5. 任何 `probe -> mother -> add-on BUY` 相关契约

一句话说：

`N3i` 只补 pilot-pack 的最小入口、cooldown hook 与 tag glue，不碰当前仓库还没准备好的执行能力。`

---

## 10. 下一张卡

`N3i` 写完后，下一张主队列卡固定应转向：

`N3j / Tachibana pilot-pack runner implementation`

它只允许回答：

1. `run_normandy_tachibana_pilot_pack_matrix.py` 如何正式落成
2. `run_backtest()` 的 `signal_filter hook` 如何最小接入
3. `unit_regime_tag / reduced_unit_scale / experimental_segment_policy` 如何贯穿 matrix/digest payload

它明确不允许回答：

1. 是否顺手打开 `R2 / R3 / R8 / R9`
2. 是否重写 Broker 成为立花原书执行器
3. 是否把 `reduced_unit` 升格成新的 sizing lane

---

## 11. 一句话结论

`N3i` 已把 Tachibana pilot-pack 的实现面压缩到一个最小改动包：用 Normandy 自有 thin runner 固定 `E1` 入口，用 `engine signal_filter hook` 承接 `E2` cooldown，用 scenario/payload tag 承接 `E3` unit regime 与 `E4` 治理隔离，而不碰 Broker 核心和 add-on BUY 缺口。`
