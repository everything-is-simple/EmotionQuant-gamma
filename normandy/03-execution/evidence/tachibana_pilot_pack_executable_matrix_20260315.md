# Tachibana Pilot-Pack Executable Matrix

**文档版本**: `v0.01`  
**文档状态**: `Active`  
**日期**: `2026-03-15`  
**适用范围**: `Normandy / Tachibana pilot-pack executable boundary`

---

## 1. 目标

`N3g` 已经把 pilot-pack 的开工边界写死。  
`N3h` 要做的不是重讲边界，而是把这条边界压成：

`哪些包现在就能运行，哪些包只差轻量扩展，哪些包只能做治理覆盖层。`

因此本文只回答 4 件事：

1. 当前 pilot-pack 应拆成哪些最小执行包
2. 每个执行包应复用哪个现成载体或 runner
3. 哪些执行包现在就能跑，哪些还需要轻量扩展
4. 后续 implementation card 应按什么顺序开工

---

## 2. Formal Inputs

本文正式输入固定为：

1. `normandy/03-execution/evidence/tachibana_state_transition_candidate_table_20260315.md`
2. `normandy/03-execution/evidence/tachibana_validation_rule_candidate_matrix_20260315.md`
3. `normandy/03-execution/records/24-phase-n3g-tachibana-pilot-pack-opening-note-20260315.md`
4. `positioning/03-execution/records/07-phase-p6-partial-exit-contract-freeze-record-20260314.md`
5. `positioning/03-execution/records/08-phase-p7-partial-exit-null-control-matrix-record-20260314.md`
6. `positioning/03-execution/records/09-phase-p8-partial-exit-family-replay-record-20260315.md`
7. `positioning/03-execution/records/partial-exit-lane-opening-note-20260314.md`
8. `scripts/backtest/run_positioning_partial_exit_family_matrix.py`
9. `scripts/backtest/run_positioning_partial_exit_family_digest.py`
10. `src/backtest/partial_exit_null_control.py`
11. `src/backtest/positioning_partial_exit_family.py`

---

## 3. 执行状态定义

为避免“允许进入 pilot-pack”与“已经存在可运行入口”混写，本文固定 4 种执行状态：

1. `ready_now`
   现有仓库已经有可直接复用的 runner 与载体
2. `ready_after_lightweight_extension`
   方向已固定，但还缺一个轻量 runner、tag 或 orchestration glue
3. `governance_overlay_only`
   不要求新交易逻辑，只要求在输出层做隔离、标记或汇总
4. `blocked_outside_pilot`
   不属于当前 pilot-pack，禁止偷带

---

## 4. Pilot-Pack Executable Matrix

| 执行包 | 对应规则 | 当前要验证什么 | 现成载体 / runner | 第一轮固定运行形状 | 正式 baseline | 预期产物 | 当前状态 |
|---|---|---|---|---|---|---|---|
| `E1_reduce_to_core_proxy_replay` | `R4 + R5` | `TRAIL_SCALE_OUT_25_75` 作为 `reduce_to_core` 工程代理时，是否相对 `FULL_EXIT_CONTROL` 形成可信 retained readout | `scripts/backtest/run_positioning_partial_exit_family_matrix.py` + `run_positioning_partial_exit_family_digest.py` + `src/backtest/positioning_partial_exit_family.py` | 至少跑 `FULL_EXIT_CONTROL + TRAIL_SCALE_OUT_25_75`；`TRAIL_SCALE_OUT_33_67 / TRAIL_SCALE_OUT_50_50` 只保留为 side references | `FULL_EXIT_CONTROL` on `FIXED_NOTIONAL_CONTROL` | `pilot-pack reduce-to-core proxy matrix + digest + record readout` | `ready_now` |
| `E2_cooldown_overlay_family` | `R6 + R5` | `full exit -> rest` 是否能把当前子集从“更细一点的止盈”推进成正式 `flat / rest discipline` | 复用 `BOF` baseline 与 `P6` 的 `position_id + 多 SELL 腿` 契约；需新建最小 `cooldown family` runner | 固定只开 `0 / 2 / 5 / 10` bar cooldown；且必须与 `FULL_EXIT_CONTROL`、`TRAIL_SCALE_OUT_25_75` 同栈比较 | `FULL_EXIT_CONTROL` + frozen `BOF` baseline | `cooldown family matrix + digest` | `ready_after_lightweight_extension` |
| `E3_unit_regime_overlay` | `R7` | `FIXED_NOTIONAL_CONTROL / SINGLE_LOT_CONTROL / reduced-unit tag` 是否改变当前可迁回子集的治理读数 | 复用 `P7` / `P8` 现成控制线与报告链；需补显式 `unit_regime` tag 与 reduced-unit overlay | 第一轮只允许比较 `FIXED_NOTIONAL_CONTROL`、`SINGLE_LOT_CONTROL` 与 `reduced-unit tag`；不得引入新 sizing 公式 | `FIXED_NOTIONAL_CONTROL + SINGLE_LOT_CONTROL` | `unit regime overlay note / matrix slice` | `ready_after_lightweight_extension` |
| `E4_experimental_segment_isolation` | `R10` | `experimental_100_share` 段是否继续从 canonical aggregate 中剥离 | `tradebook ledger`、`replay ledger`、`Normandy/Positioning` 报告治理链 | 不改交易逻辑，只在汇总与报告层隔离 `experimental_100_share` | `canonical aggregate excludes experimental_100_share` | `segmented summary + governance note` | `governance_overlay_only` |

---

## 5. 当前最重要的执行分流

### 5.1 现在就能诚实开跑的

当前可以直接开跑的只有两件事：

1. `E1_reduce_to_core_proxy_replay`
2. `E4_experimental_segment_isolation`

这两件事的共同特点是：

1. 现有仓库已有 runner 或治理载体
2. 不要求新增 `add-on BUY`
3. 不要求改写 Broker 核心
4. 不会误装成“完整立花系统”

### 5.2 只差轻量扩展的

当前可以进入 implementation queue、但还不能宣称已可跑的，是：

1. `E2_cooldown_overlay_family`
2. `E3_unit_regime_overlay`

它们的共同特点是：

1. 边界与问题定义已经冻结
2. 不需要打开 `R2 / R3 / R8 / R9`
3. 但当前仍缺最小 runner、tag 或 orchestration glue

### 5.3 明确不属于 pilot-pack 的

当前统一排除在 executable matrix 之外的，是：

1. `R1_probe_entry`
2. `R2_probe_to_mother_promotion`
3. `R3_discrete_same_side_add_ladder`
4. `R8_lock_equivalent_reduce_and_readd`
5. `R9_reverse_restart_as_new_position`

这些对象当前统一记为：

`blocked_outside_pilot`

---

## 6. Implementation Order

当前 implementation queue 的正式顺序固定为：

1. 先把 `E1_reduce_to_core_proxy_replay` 作为当前可直接执行包写成 pilot 主锚点
2. 再补 `E2_cooldown_overlay_family` 的最小 runner，使 `flat / rest discipline` 有正式比较链
3. 再补 `E3_unit_regime_overlay` 的显式 `unit_regime` / `reduced-unit` 标记
4. 最后让 `E4_experimental_segment_isolation` 贯穿所有 pilot 输出层

这条顺序的意义是：

`先把已经可跑的东西跑诚实，再给 pilot-pack 补最小缺口，而不是反过来先打开 add-on BUY 一类未具备能力。`

---

## 7. 当前最重要的硬边界

当前 executable matrix 必须同时继承下面 5 条硬边界：

1. `TRAIL_SCALE_OUT_25_75` 只是 `reduce_to_core` 的工程代理
2. `FULL_EXIT_CONTROL` 继续保持 canonical control baseline
3. `partial-exit lane` 不替 `sizing lane` 擦屁股
4. `RiskManager -> ALREADY_HOLDING` 仍阻断同标的持仓内再次开仓
5. `pilot-pack != Tachibana full system`

---

## 8. 一句话结论

`N3h` 当前把 Tachibana pilot-pack 压成了 4 个执行包：`E1` 与 `E4` 现在就能诚实开跑，`E2` 与 `E3` 只差轻量扩展即可进入 implementation queue；而 `R1 / R2 / R3 / R8 / R9` 继续被明确挡在 pilot 外。`
