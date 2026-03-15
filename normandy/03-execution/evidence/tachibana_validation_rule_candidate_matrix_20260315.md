# Tachibana Validation Rule-Candidate Matrix

**文档版本**: `v0.01`  
**文档状态**: `Active`  
**日期**: `2026-03-15`  
**适用范围**: `Normandy / Tachibana validation rule candidate matrix`

---

## 1. 目标

`N3e` 已经把立花方法压成了状态迁移候选簇。  
`N3f` 要做的不是再解释语义，而是回答：

`这些候选簇分别应该如何写成最小规则，并挂到哪个验证载体上。`

因此本文只处理 4 件事：

1. 每条规则的最小表达
2. 它是 `replay fidelity`、`A股可迁回` 还是 `结构等价物搜索`
3. 它应挂到仓库哪个现成模块或战场
4. 它当前是 `ready / blocked / governance-only` 的哪一种

---

## 2. Formal Inputs

本文正式输入固定为：

1. `normandy/03-execution/evidence/tachibana_state_transition_candidate_table_20260315.md`
2. `normandy/03-execution/evidence/tachibana_execution_semantics_evidence_table_20260315.md`
3. `normandy/03-execution/evidence/tachibana_replay_ledger_contract_note_20260315.md`
4. `normandy/03-execution/evidence/emotionquant_tachibana_module_reuse_triage_table_20260315.md`
5. `normandy/02-implementation-spec/10-tachibana-quantifiable-execution-system-spec-20260315.md`
6. `src/contracts.py`
7. `src/broker/risk.py`
8. `src/backtest/partial_exit_null_control.py`
9. `src/backtest/positioning_partial_exit_family.py`
10. `positioning/03-execution/records/07-phase-p6-partial-exit-contract-freeze-record-20260314.md`
11. `positioning/03-execution/records/09-phase-p8-partial-exit-family-replay-record-20260315.md`

---

## 3. 验证模式定义

为避免“能验证原书忠实度”和“能迁回当前 A 股主线”混在一起，本文固定 5 种验证模式：

1. `RF`
   `Replay Fidelity`
   只检验是否忠实表达原书动作路径
2. `AM0`
   `A-share Migratable on current stack`
   可以直接挂到当前仓库现有战场
3. `AM1`
   `A-share Migratable after lightweight extension`
   方向正确，但需要先补一个轻量执行能力
4. `SE`
   `Structural Equivalent Search`
   不能原样迁回，只能寻找功能等价物
5. `SG`
   `Sample Governance`
   不属于交易规则，只属于样本与实验治理

---

## 4. 规则候选矩阵

| Rule ID | 来源簇 | 最小规则表达 | 验证模式 | 当前可挂载体 | 当前阻塞 / 缺口 | 第一验证动作 | 当前状态 |
|---|---|---|---|---|---|---|---|
| `R1_probe_entry` | `C1` | `flat 且 entry 成立时，不开母单，先开 1 个 probe_unit；new position_id；leg_id=1` | `RF + AM0` | `tradebook replay`，以及 `positioning null control / single-lot control` 作为弱代理 | 当前没有显式 `probe_state`，只能先用小单位 entry 近似 | 跑 `single_lot / tiny fixed_notional` 的 probe-only 近似对照 | `ready_as_proxy` |
| `R2_probe_to_mother_promotion` | `C1 + C2` | `probe 存活且确认条件满足时，沿同方向追加母单；position_id 不变；leg_id 递增` | `RF + AM1` | 当前只能挂 `replay ledger`；未来应接新 `probe-promotion lane` | `RiskManager` 当前会因 `ALREADY_HOLDING` 拒绝同标的重复开仓，无法直接加母单 | 先定义 add-on BUY contract，再开最小 2-step promotion family | `blocked_by_engine` |
| `R3_discrete_same_side_add_ladder` | `C2` | `同向扩张只能按离散腿加，不允许每根 bar 连续重算全仓目标` | `RF + AM1` | 当前只能挂 `replay ledger`；未来复用 `positioning sizing` 的 family harness | 同样被 `ALREADY_HOLDING` 阻塞，且当前 sizing lane 只控制初始仓位，不表达 add-leg | 新建 `2-step / 3-step ladder` family，而非继续改 sizing formula | `blocked_by_engine` |
| `R4_reduce_to_core_partial_exit` | `C3` | `不确定或首段兑现时，只减到 core，不全平；position_id 继续` | `AM0` | `partial_exit_null_control`、`positioning_partial_exit_family`、`FULL_EXIT_CONTROL` 对照链 | 当前 partial-exit 主要按 trailing-stop 语义表达，尚未显式区分 `test-leg` 与普通减仓腿 | 以 `25/75`、`33/67` 为核心保留腿候选，验证 `reduce_to_core` 解释力 | `ready_on_existing_stack` |
| `R5_terminal_full_exit` | `C4` | `终局退出时清空剩余仓位；position_id 结束；下一次进场必须新编号` | `AM0` | `FULL_EXIT_CONTROL` 及现有 Broker full-exit path | 无核心阻塞 | 继续作为 canonical control baseline | `already_validated_control` |
| `R6_flat_rest_cooldown` | `C7` | `full exit 后进入 rest；在 cooldown 未解除前禁止重开同一机会` | `RF + AM0` | 新 `cooldown family` 可挂在当前 BOF baseline 上 | 当前没有显式 `rest_state / cooldown` 契约，但不需要改 Broker 核心 | 先做 `0 / 2 / 5 / 10` bar cooldown family | `ready_for_new_lane` |
| `R7_unit_regime_control` | `C8` | `probe_unit / mother_unit / experimental_unit_regime` 必须是显式制度变量，不当作噪音` | `AM0 + SG` | `positioning null control`、`sizing family`、`single_lot sanity` | 当前 unit regime 尚未系统标签化，但已有 fixed_lot / fixed_notional / single_lot 基础 | 先把 `unit regime` 纳入实验标签，再比较 normal vs reduced-unit 子战场 | `partly_ready` |
| `R8_lock_equivalent_reduce_and_readd` | `C5` | `原书是 opposite-leg lock；A股等价物候选是 reduce-to-core 后保留母单，再在确认后 re-add` | `SE` | 前半段可借 `partial_exit family`，后半段未来需 add-on BUY lane | 现有栈能做 `reduce`，不能做持仓中 `re-add`，因此只能先保留为结构等价物搜索 | 待 `R2/R3` 打开后，定义 `reduce->readd` 的最小 family | `blocked_until_addon_buy` |
| `R9_reverse_restart_as_new_position` | `C6` | `原书 reverse；A股等价物候选是 full exit -> rest -> fresh long probe，且新 position_id` | `SE` | 当前只能靠 `replay ledger` 保真；未来可接 `cooldown + probe entry` | 现有主线 `BUY-only`，不能原样回放方向反转 | 在 `R1 + R6` 跑稳后，再开 `exit-and-reenter reset` family | `defer_after_R1_R6` |
| `R10_experimental_segment_isolation` | `C9` | `100股试验段必须单独打标签，不并入 canonical aggregate` | `SG` | `tradebook ledger`、`replay ledger`、治理记录 | 无执行阻塞 | 继续保留 `experimental_100_share` 标签，并在后续报告中单独汇总 | `already_ready` |

---

## 5. 当前最重要的硬边界

### 5.1 现有引擎下不能假装“母单扩张已经可跑”

当前 `RiskManager` 明确会在已持仓时返回：

`ALREADY_HOLDING`

所以：

1. `R2 probe_to_mother_promotion`
2. `R3 discrete_same_side_add_ladder`
3. `R8 lock_equivalent_reduce_and_readd`

当前都不能直接挂到现有 Broker 上。

这意味着：

`现在就硬做“立花母单加码实验”只会做成伪实验。`

### 5.2 现有引擎下第一批可跑的立花子系统

当前最先能在现有栈里诚实落地的，不是完整立花系统，而是：

1. `R4 reduce_to_core_partial_exit`
2. `R5 terminal_full_exit`
3. `R6 flat_rest_cooldown`
4. `R7 unit_regime_control`
5. `R10 experimental_segment_isolation`

换句话说，当前第一批 pilot 不该叫：

`Tachibana full system`

而应叫：

`Tachibana migratable subset on current BOF stack`

### 5.3 `25/75` 现在有了新的解释地位

`P8` 里最强 retained 候选是 `TRAIL_SCALE_OUT_25_75`。  
在 `N3f` 口径下，它不再只是一个 exit ratio，而是当前最接近立花下面这个动作的现成工程代理：

`reduce_to_core`

这很重要，因为它说明立花最先能迁回 A 股主线的，也许不是 `试单加码`，而是：

`轻首腿兑现 + 保留母仓核心`

### 5.4 锁单不该被删，而该被翻译

原书的锁单在当前主线下不能原样实现，但它承担的功能不能丢：

1. `保留母单`
2. `测试不确定性`
3. `等待方向澄清后再处理`

因此当前正确方向不是删除 `C5`，而是把它翻译成：

`reduce_to_core + re-add` 的结构等价物搜索

---

## 6. 当前建议的规则队列

### 6.1 Queue A: 立刻可开

1. `R4 reduce_to_core_partial_exit`
2. `R6 flat_rest_cooldown`
3. `R7 unit_regime_control`
4. `R10 experimental_segment_isolation`

### 6.2 Queue B: 需要轻量扩展后开

1. `R1 probe_entry` 的显式化
2. `R2 probe_to_mother_promotion`
3. `R3 discrete_same_side_add_ladder`

### 6.3 Queue C: 只保留结构搜索

1. `R8 lock_equivalent_reduce_and_readd`
2. `R9 reverse_restart_as_new_position`

---

## 7. 一句话结论

`N3f` 的正式结论不是“立花全部能实现”，而是“现有仓库已经足够跑立花的可迁回子集，其中最先值得开的不是母单加码，而是 reduce-to-core + full-exit + cooldown + unit regime 这一组规则。” 
