# Phase N3h Tachibana Pilot-Pack Executable Matrix Record

**日期**: `2026-03-15`  
**阶段**: `Normandy / N3h`  
**对象**: `Tachibana pilot-pack executable matrix formal readout`  
**状态**: `Closed`

---

## 1. 目标

本文用于把 `N3h / Tachibana pilot-pack executable matrix` 的正式裁决写死。

这张 record 只回答 5 件事：

1. `N3g` 冻结的 pilot-pack 当前应拆成哪些最小执行包
2. 哪些执行包现在就能诚实开跑
3. 哪些执行包只差轻量扩展即可进入 implementation queue
4. 哪些规则必须继续挡在 pilot 之外
5. 下一张主队列卡应如何转入 implementation scaffold

---

## 2. Formal Inputs

本卡正式输入固定为：

1. `normandy/03-execution/evidence/tachibana_pilot_pack_executable_matrix_20260315.md`
2. `normandy/03-execution/evidence/tachibana_validation_rule_candidate_matrix_20260315.md`
3. `normandy/03-execution/evidence/tachibana_state_transition_candidate_table_20260315.md`
4. `normandy/03-execution/records/24-phase-n3g-tachibana-pilot-pack-opening-note-20260315.md`
5. `positioning/03-execution/records/07-phase-p6-partial-exit-contract-freeze-record-20260314.md`
6. `positioning/03-execution/records/08-phase-p7-partial-exit-null-control-matrix-record-20260314.md`
7. `positioning/03-execution/records/09-phase-p8-partial-exit-family-replay-record-20260315.md`
8. `positioning/03-execution/records/partial-exit-lane-opening-note-20260314.md`
9. `scripts/backtest/run_positioning_partial_exit_family_matrix.py`
10. `scripts/backtest/run_positioning_partial_exit_family_digest.py`
11. `src/backtest/positioning_partial_exit_family.py`

---

## 3. 正式裁决

`N3h` 的正式裁决固定为：

1. 当前 executable pilot-pack 固定拆成：
   `E1_reduce_to_core_proxy_replay + E2_cooldown_overlay_family + E3_unit_regime_overlay + E4_experimental_segment_isolation`
2. 当前 `ready_now` 的执行包固定为：
   `E1 + E4`
3. 当前 `ready_after_lightweight_extension` 的执行包固定为：
   `E2 + E3`
4. 当前 pilot 外继续明确挡住：
   `R1 / R2 / R3 / R8 / R9`
5. 当前 canonical control baseline 继续固定为：
   `FULL_EXIT_CONTROL`
6. 当前 operating / floor baseline 继续固定为：
   `FIXED_NOTIONAL_CONTROL + SINGLE_LOT_CONTROL`

---

## 4. 为什么当前只有 `E1 + E4` 能直接开

### 4.1 `E1_reduce_to_core_proxy_replay`

这条执行包当前可以直接开，原因固定为：

1. `P8` 已经在同一 frozen baseline 下跑出 `TRAIL_SCALE_OUT_25_75` 的 retained leader 读数
2. 现有仓库已具备 `run_positioning_partial_exit_family_matrix.py` 与对应 digest 入口
3. 它只要求复用 `position_id + 多 SELL 腿` 与 `FULL_EXIT_CONTROL` 对照线
4. 它不会误装成 `probe -> mother promotion`

但必须同时写死：

1. `TRAIL_SCALE_OUT_25_75` 当前只是 `reduce_to_core` 工程代理
2. 它不得被升格成“立花真身”

### 4.2 `E4_experimental_segment_isolation`

这条执行包当前也可以直接开，原因固定为：

1. `R10` 本质上是样本治理，不要求新增交易引擎能力
2. `tradebook ledger / replay ledger / report chain` 已经足够承载 `experimental_100_share` 标签隔离
3. 它只要求 canonical aggregate 不把实验段混算进去

---

## 5. 为什么 `E2 + E3` 只差轻量扩展

### 5.1 `E2_cooldown_overlay_family`

`R6` 当前允许进入 pilot-pack，但还不能直接宣称已可跑，原因固定为：

1. `flat / rest discipline` 的问题定义已经在 `N3f / N3g` 冻结
2. 当前不需要改 Broker 核心，也不需要新开 `add-on BUY`
3. 但仓库里还缺一条正式的 `cooldown family` runner，把 `0 / 2 / 5 / 10` bar cooldown 挂到同一 `BOF` 栈上

因此它当前正式判定为：

`ready_after_lightweight_extension`

### 5.2 `E3_unit_regime_overlay`

`R7` 当前也允许进入 pilot-pack，但还不能直接当作已完成执行包，原因固定为：

1. `FIXED_NOTIONAL_CONTROL + SINGLE_LOT_CONTROL` 的冻结基线已经存在
2. 但当前还缺显式 `unit_regime / reduced-unit tag`
3. 第一轮又被明确禁止引入新的 sizing 公式

因此它当前正式判定为：

`ready_after_lightweight_extension`

---

## 6. 明确继续挡在 pilot 外的内容

当前继续挡在 pilot 外的内容固定为：

1. `R1 / probe_entry`
2. `R2 / probe_to_mother_promotion`
3. `R3 / discrete_same_side_add_ladder`
4. `R8 / lock_equivalent_reduce_and_readd`
5. `R9 / reverse_restart_as_new_position`

这里必须再次写死硬理由：

1. `RiskManager` 当前仍会在已持仓时返回 `ALREADY_HOLDING`
2. 同标的持仓内再次开仓仍未成为现成能力
3. 因此任何 `probe -> mother`、`same-side add-on BUY`、`reduce -> re-add` 都会滑向伪实验
4. `reverse restart` 也仍只属于结构等价物搜索，不属于当前可执行迁回规则

---

## 7. 下一张卡

`N3h` 完成后的 next main queue card 固定为：

`N3i / Tachibana pilot-pack implementation scaffold`

它只允许回答：

1. `E1` 应如何以现有 runner 组织成正式 pilot 入口
2. `E2` 需要新增哪些最小文件或 runner 才能把 cooldown family 挂到当前 BOF 栈
3. `E3` 需要新增哪些最小 tag / report glue 才能形成 unit regime overlay
4. `E4` 应如何贯穿所有 pilot 输出层

它明确不允许回答：

1. 完整立花系统是否已经可验证
2. 是否重开 `promotion lane`
3. 是否顺手打开 `R2 / R3 / R8 / R9`

---

## 8. 正式结论

当前 `N3h Tachibana pilot-pack executable matrix` 的正式结论固定为：

1. pilot-pack 已被正式压成 4 个执行包
2. `E1_reduce_to_core_proxy_replay` 与 `E4_experimental_segment_isolation` 现在就能诚实开跑
3. `E2_cooldown_overlay_family` 与 `E3_unit_regime_overlay` 只差轻量扩展即可进入 implementation queue
4. `FULL_EXIT_CONTROL` 与 `FIXED_NOTIONAL_CONTROL + SINGLE_LOT_CONTROL` 继续保持冻结 baseline 身份
5. `R1 / R2 / R3 / R8 / R9` 连同相关偷带问题继续被挡在 pilot 外

---

## 9. 一句话结论

`N3h` 已把 Tachibana pilot-pack 从“开工边界”推进成“执行分流表”：当前真正能立刻开跑的是 `reduce_to_core proxy replay + experimental segment isolation`，而 cooldown 与 unit regime 进入的是轻量实现队列，不是继续泛化讨论队列。`
