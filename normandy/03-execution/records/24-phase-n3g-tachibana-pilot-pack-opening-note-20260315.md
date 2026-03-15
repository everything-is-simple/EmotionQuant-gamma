# Phase N3g Tachibana Pilot-Pack Opening Note

**日期**: `2026-03-15`  
**阶段**: `Normandy / N3g`  
**对象**: `Tachibana pilot-pack opening boundary`  
**状态**: `Active`

---

## 1. 目标

本文用于把这轮立花整理成果，正式收成一张可执行 `pilot-pack` 的开工边界。

它不讨论“完整立花系统是否已经实现”。

它也不再重复写一篇立花说明文。

它只回答 4 件事：

1. 当前到底允许打开哪些规则
2. 当前 pilot 必须复用哪条已有 `positioning lane`
3. 当前 pilot 的 control baseline 固定是什么
4. 哪些未解规则与问题设置必须先挡住

一句话说：

`N3g` 的职责不是宣布“立花系统已可验证”，而是把“当前仓库里哪一部分能诚实开跑、哪一部分必须先挡住”写死。

---

## 2. Formal Inputs

`N3g` 的正式输入固定为：

1. `normandy/03-execution/evidence/tachibana_state_transition_candidate_table_20260315.md`
2. `normandy/03-execution/evidence/tachibana_replay_ledger_contract_note_20260315.md`
3. `normandy/03-execution/evidence/tachibana_replay_ledger_1976_02_1976_12_20260315.csv`
4. `normandy/03-execution/evidence/tachibana_validation_rule_candidate_matrix_20260315.md`
5. `normandy/03-execution/records/23-phase-n3f-tachibana-validation-rule-candidate-matrix-record-20260315.md`
6. `positioning/03-execution/records/07-phase-p6-partial-exit-contract-freeze-record-20260314.md`
7. `positioning/03-execution/records/08-phase-p7-partial-exit-null-control-matrix-record-20260314.md`
8. `positioning/03-execution/records/09-phase-p8-partial-exit-family-replay-record-20260315.md`
9. `positioning/03-execution/records/partial-exit-lane-opening-note-20260314.md`

其中，当前 `原书路径真值` 固定依赖：

1. `tachibana_state_transition_candidate_table_20260315.md`
2. `tachibana_replay_ledger_*`

也就是说，后续 pilot 验证什么，不再靠口头理解，而只认：

`书页语义 -> replay ledger -> candidate/rule table`

---

## 3. 固定继承的前提

`N3g` 开工时固定继承以下前提：

1. `entry baseline = legacy_bof_baseline / BOF_CONTROL`
2. `no IRS`
3. `no MSS`
4. `signal_date = T / execute_date = T+1 / fill = T+1 open`
5. `Signal = BUY-only / long-only`
6. `STOP_LOSS / FORCE_CLOSE = hard full exit`
7. `position_id` 继续沿用 `P6` 已冻结的 formal schema
8. `FIXED_NOTIONAL_CONTROL = canonical operating control baseline`
9. `SINGLE_LOT_CONTROL = floor sanity control`

同时写死：

1. 当前 `partial-exit lane` 不是 `sizing lane` 的补救包
2. `FIXED_NOTIONAL_CONTROL + SINGLE_LOT_CONTROL` 这对 control 只负责给 pilot 提供冻结基线
3. 任何 sizing residual watch 都不得借 `pilot-pack` 重新偷渡回来

一句话说：

`pilot-pack` 当前继承的是第三战场的冻结前提，不是重开 sizing 争论。

---

## 4. Pilot-Pack 正式边界

当前 `pilot-pack` 的正式边界固定为：

1. 正式标签只能是 `Tachibana migratable subset on current BOF stack`
2. 当前只允许打开 `R4 + R5 + R6 + R7 + R10`
3. 不得把当前 pilot 宣称为 `Tachibana full system`

当前 5 条允许打开的规则，正式解释固定为：

1. `R4 / reduce_to_core_partial_exit`
   当前第一工程代理固定为 `TRAIL_SCALE_OUT_25_75`
2. `R5 / terminal_full_exit`
   继续固定复用 `FULL_EXIT_CONTROL` 的 canonical full-exit 路径
3. `R6 / flat_rest_cooldown`
   必须在同一 `BOF` 栈上展开 `0 / 2 / 5 / 10` bar cooldown family
4. `R7 / unit_regime_control`
   第一轮只允许以 `FIXED_NOTIONAL_CONTROL / SINGLE_LOT_CONTROL / reduced-unit tag` 进入
5. `R10 / experimental_segment_isolation`
   必须继续把 `experimental_100_share` 段从 canonical aggregate 中单独隔离

同时写死：

1. `TRAIL_SCALE_OUT_25_75` 当前只是 `reduce_to_core` 的工程代理
2. 它不得被冒充成“立花真身”
3. `TRAIL_SCALE_OUT_33_67 / TRAIL_SCALE_OUT_50_50` 只保留为 side candidates，不升格为当前主代理

---

## 5. 指定复用的 Positioning 载体

`N3g` 当前明确不新写一套立花引擎。

当前正确做法固定为：

`把 reduce_to_core + full_exit + cooldown + unit regime + experimental segment isolation 挂到现有 BOF 栈`

对应复用载体固定为：

1. 复用 `P6 / partial-exit contract freeze` 已冻结的 `position_id + 多 SELL 腿` 契约边界
2. 复用 `P7 / partial-exit null control matrix` 已冻结的 `FULL_EXIT_CONTROL` 对照口径
3. 复用 `P8 / partial-exit family replay` 已跑出的 retained queue 读数，尤其是 `TRAIL_SCALE_OUT_25_75`
4. 当前直接工程载体固定为 `src/backtest/partial_exit_null_control.py`
5. 当前直接工程载体固定为 `src/backtest/positioning_partial_exit_family.py`
6. `Normandy` 自身继续承担 `replay ledger + doctrine boundary`，而不是另起一条平行 Broker 主线

换句话说：

`N3g` 不是要重写一套 Tachibana engine，而是把当前可迁回子集压进第三战场现成载体里。`

---

## 6. 明确不得偷带的内容

`N3g` 当前明确不得偷带以下内容：

1. `R1 / probe_entry` 的显式化
2. `R2 / probe_to_mother_promotion`
3. `R3 / discrete_same_side_add_ladder`
4. `R8 / lock_equivalent_reduce_and_readd`
5. `R9 / reverse_restart_as_new_position`
6. 任何 `probe -> mother promotion`、`same-side add-on BUY`、`reduce -> re-add`、`lock`、`reverse restart` 的可执行宣称
7. 任何“当前 pilot 已经验证完整立花系统”的表述
8. 任何重开 `sizing lane`、重写 `MSS / IRS`、或让 `partial-exit lane` 替 sizing lane 擦屁股的问题设置

当前禁止这些内容的硬理由也固定写死：

1. `RiskManager` 当前会在已持仓时返回 `ALREADY_HOLDING`
2. 这意味着同标的持仓内再次开仓仍被主线执行器阻断
3. 因此现在硬跑 `R2 / R3 / R8` 只会得到伪实验
4. `R9` 当前也只能保留为结构等价物搜索，不得冒充成可执行迁回规则

一句话说：

`当前 pilot 只能诚实验证可迁回子集，不能把未具备的 add-on BUY / reverse / lock 能力伪装成已落地功能。`

---

## 7. 下一张卡

`N3g` 写完后，下一张主队列卡固定应转向：

`N3h / Tachibana pilot-pack executable matrix`

它只允许回答：

1. `TRAIL_SCALE_OUT_25_75` 作为 `reduce_to_core` 工程代理时，是否相对 `FULL_EXIT_CONTROL` 形成第一批可信 pilot 读数
2. `0 / 2 / 5 / 10` bar cooldown family 能否把当前子集从“更细一点的止盈”推进成 `flat / rest discipline`
3. `FIXED_NOTIONAL_CONTROL / SINGLE_LOT_CONTROL / reduced-unit tag` 是否改变当前可迁回子集的治理读数
4. `experimental_100_share` 段是否必须继续从 canonical aggregate 中剥离

它明确不允许回答：

1. 完整立花系统是否已经可验证
2. 母单扩张、同向加码、锁单、反向再出发是否已经落地
3. 是否应该重开 `promotion lane`

---

## 8. 一句话结论

`N3g` 的正式意义不是“再写一篇立花说明文”，而是把这轮整理成果收成第一张 executable pilot 的开工边界：只开 `R4 + R5 + R6 + R7 + R10`，复用第三战场 partial-exit 载体，继承 `FIXED_NOTIONAL_CONTROL + SINGLE_LOT_CONTROL` 的冻结基线，并把 `R2 / R3 / R8 / R9` 连同相关偷带问题一并挡在门外。`
