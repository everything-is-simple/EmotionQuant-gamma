# Phase N3e Tachibana State-Transition Candidate Table Record

**日期**: `2026-03-15`  
**阶段**: `Normandy / N3e`  
**对象**: `Tachibana 状态迁移候选集正式冻结`  
**状态**: `Closed`

---

## 1. 目标

本卡只回答 5 件事：

1. 立花方法当前可正式冻结为哪些状态迁移候选簇  
2. 哪些候选簇已经被 replay ledger 实际观测到  
3. 哪些候选簇可直接迁回 EmotionQuant 主线  
4. 哪些候选簇只能保留为结构等价物搜索对象  
5. 哪些动作当前只能作为 backlog 或样本治理标签

---

## 2. Formal Inputs

本卡正式输入固定为：

1. `normandy/03-execution/evidence/tachibana_execution_semantics_evidence_table_20260315.md`
2. `normandy/03-execution/evidence/tachibana_replay_ledger_contract_note_20260315.md`
3. `normandy/03-execution/evidence/tachibana_replay_ledger_1976_02_1976_12_20260315.csv`
4. `normandy/03-execution/evidence/emotionquant_tachibana_module_reuse_triage_table_20260315.md`
5. `normandy/03-execution/evidence/tachibana_state_transition_candidate_table_20260315.md`
6. `normandy/02-implementation-spec/10-tachibana-quantifiable-execution-system-spec-20260315.md`

---

## 3. 正式裁决

当前正式裁决固定为：

1. 立花方法当前先冻结为 `9` 个候选簇  
2. 其中 `C1/C2/C3/C4/C7/C8` 可进入 EmotionQuant 主线迁移队列  
3. `C5 锁单测试` 与 `C6 反向再出发` 保留为结构类候选，不得粗暴删去  
4. `C9 100股实验段` 只作为样本治理标签，不得和常规样本混算  
5. backlog transition 当前固定为：  
   `lock_short_against_long / unlock_long / reverse_long_to_short / rebalance_locked`

---

## 4. 关键理由

### 4.1 为什么要先冻结候选簇，而不是直接写规则

因为书中最宝贵的是：

`动作结构`

不是参数值。

如果现在直接写规则，很容易把立花压成：

`几个固定阈值 + 一个 detector`

这会再次丢掉他的方法本体。

### 4.2 为什么全平休息必须升格

因为这不是心理描述，而是制度动作。

它决定：

1. `position_id` 的边界
2. 再入场是否算新一场交易
3. 系统是否允许主动退出市场

### 4.3 为什么锁单不能删

虽然当前主线无法原样实现 long-short 共存，但锁单承担的是：

`维持母单 + 测试市场`

这两个功能。

所以它必须保留为结构搜索对象，否则立花系统会被误缩成“只会分批卖出”。

---

## 5. 正式产出物

本卡正式产出固定为：

`normandy/03-execution/evidence/tachibana_state_transition_candidate_table_20260315.md`

---

## 6. 下一张卡

本卡完成后的 next main queue card 固定为：

`N3f / Tachibana validation rule-candidate matrix`

它只允许回答：

1. `C1-C9` 各自对应什么最小规则表达
2. 哪些规则只做 replay fidelity，不做 A 股迁移
3. 哪些规则可以直接挂到 `positioning` 战场
4. 哪些规则需要先寻找 A 股 long-only 的结构等价物

---

## 7. 一句话结论

`N3e` 已经把立花方法从“很多动作很有感觉”压成了正式候选状态簇；从这一刻起，后续工作不该再泛读，而该进入规则矩阵与迁移验证阶段。
