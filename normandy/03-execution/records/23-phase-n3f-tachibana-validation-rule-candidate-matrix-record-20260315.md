# Phase N3f Tachibana Validation Rule-Candidate Matrix Record

**日期**: `2026-03-15`  
**阶段**: `Normandy / N3f`  
**对象**: `Tachibana 规则候选矩阵正式冻结`  
**状态**: `Closed`

---

## 1. 目标

本卡只回答 5 件事：

1. `C1-C9` 当前应被翻译成哪些最小规则单元  
2. 哪些规则能直接挂到现有 EmotionQuant 战场  
3. 哪些规则需要先补轻量执行能力  
4. 哪些规则只能先作为结构等价物搜索  
5. 当前现有栈下最合适的立花 pilot 应是什么

---

## 2. Formal Inputs

本卡正式输入固定为：

1. `normandy/03-execution/evidence/tachibana_state_transition_candidate_table_20260315.md`
2. `normandy/03-execution/evidence/tachibana_validation_rule_candidate_matrix_20260315.md`
3. `normandy/03-execution/evidence/emotionquant_tachibana_module_reuse_triage_table_20260315.md`
4. `src/contracts.py`
5. `src/broker/risk.py`
6. `src/backtest/partial_exit_null_control.py`
7. `src/backtest/positioning_partial_exit_family.py`
8. `positioning/03-execution/records/07-phase-p6-partial-exit-contract-freeze-record-20260314.md`
9. `positioning/03-execution/records/09-phase-p8-partial-exit-family-replay-record-20260315.md`

---

## 3. 正式裁决

当前正式裁决固定为：

1. 当前规则候选集固定为 `R1-R10`
2. 当前可直接挂现有栈的 rule pack 固定为：  
   `R4 + R5 + R6 + R7 + R10`
3. `R2 / R3 / R8` 当前统一判定为 `blocked_by_addon_buy_gap`
4. `R9` 当前统一判定为 `structural_equivalent_only`
5. 当前 pilot 不得宣称为“完整立花系统”，只能宣称为：  
   `Tachibana migratable subset on current BOF stack`

---

## 4. 关键理由

### 4.1 为什么 pilot 不是从试单加码开始

因为当前主线执行器在已持仓时会拒绝同标的重复开仓。  
这使得：

1. `probe -> mother promotion`
2. `same-side add ladder`
3. `reduce -> re-add`

都还不能诚实落地。

因此如果现在硬开“立花母单加码验证”，只会得到伪读数。

### 4.2 为什么 `reduce_to_core` 应该先开

因为它同时满足 3 个条件：

1. 已有原书语义支持
2. 已有现成工程载体
3. 已在 `P8` 中出现 retained queue 读数

也就是说，它不是理念最完整的一簇，但却是：

`当前最有机会跑出第一批可信验证结果的一簇`

### 4.3 为什么 cooldown 必须跟着一起开

因为如果只做 `reduce_to_core`，不做 `flat/rest`，立花方法会被再次误缩成“更细一点的止盈”。  
而立花真正的节律，是：

`进 -> 扩 -> 收 -> 平 -> 休息 -> 再来`

---

## 5. 正式产出物

本卡正式产出固定为：

`normandy/03-execution/evidence/tachibana_validation_rule_candidate_matrix_20260315.md`

---

## 6. 下一张卡

本卡完成后的 next main queue card 固定为：

`N3g / Tachibana pilot-pack opening note`

它只允许回答：

1. 当前 pilot-pack 的正式规则边界
2. pilot-pack 的 control baseline
3. pilot-pack 应复用哪条 positioning 战场
4. pilot-pack 不允许偷带哪些未解规则

---

## 7. 一句话结论

`N3f` 已经把立花从状态簇推进成规则候选矩阵；当前最诚实的推进方式不是追求一步到位，而是先把 `reduce-to-core + full-exit + cooldown + unit regime` 跑成第一批可验证 pilot。
