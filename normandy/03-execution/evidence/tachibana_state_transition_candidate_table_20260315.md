# Tachibana State-Transition Candidate Table

**文档版本**: `v0.01`  
**文档状态**: `Active`  
**日期**: `2026-03-15`  
**适用范围**: `Normandy / Tachibana state-transition candidate formalization`

---

## 1. 目标

本表用于把立花方法从：

`方法页语义 + 月度交易表事件`

压成：

`可验证的状态迁移候选集`

这里的关键词是：

`candidate`

也就是说，本文不是宣称这些转移已经全部成为最终规则，而是先把哪些动作值得进入正式验证队列写死。

---

## 2. Formal Inputs

本文正式输入固定为：

1. `normandy/03-execution/evidence/tachibana_execution_semantics_evidence_table_20260315.md`
2. `normandy/03-execution/evidence/tachibana_replay_ledger_contract_note_20260315.md`
3. `normandy/03-execution/evidence/tachibana_replay_ledger_1976_02_1976_12_20260315.csv`
4. `normandy/03-execution/evidence/emotionquant_tachibana_module_reuse_triage_table_20260315.md`
5. `normandy/02-implementation-spec/10-tachibana-quantifiable-execution-system-spec-20260315.md`

---

## 3. 当前已观测 transition 集

当前 `1976-02 -> 1976-12` replay ledger 已实际观测到的 transition 为：

1. `enter_short`
2. `enter_long`
3. `add_short`
4. `add_long`
5. `cover_short_partial`
6. `reduce_long`
7. `cover_short_to_flat`
8. `exit_long_to_flat`
9. `lock_long_against_short`
10. `add_short_locked`
11. `reduce_short_locked`
12. `unlock_short`
13. `reverse_short_to_long`

这说明当前最可靠的不是抽象猜测，而是已经能落到一批真实发生过的状态迁移。

---

## 4. 候选状态迁移表

| 候选簇 | 书页证据 | 对应 replay transition | 标准状态路径 | `position_id` 规则 | 可否迁回当前 A 股 BOF 主线 | 当前裁决 |
|---|---|---|---|---|---|---|
| `C1 试单入场` | `B0288`, `B0294` | `enter_long`, `enter_short` | `flat -> single_side` | 新开一场交易必须新建 `position_id`，`leg_id=1` | `部分可迁回` | 保留为正式候选 |
| `C2 母单扩张` | `B0288`, `B0295` | `add_long`, `add_short` | `single_side -> same_side_larger` | 延续当前 `position_id`，每次加码 `leg_id + 1` | `部分可迁回` | 保留为正式候选 |
| `C3 单边减仓` | `B0288`, `B0293` | `reduce_long`, `cover_short_partial` | `single_side -> same_side_smaller` | 延续当前 `position_id`，视为同一战役内减仓腿 | `长仓侧可直接迁回` | 保留为正式候选 |
| `C4 全平离场` | `B0288`, `B0293`, `B0294`, `B0305` | `exit_long_to_flat`, `cover_short_to_flat` | `single_side -> flat` | 当前 `position_id` 结束，不得与下次重开复用 | `长仓侧可直接迁回` | 保留为高优先候选 |
| `C5 锁单测试` | `B0288`, `B0294`, `B0295` | `lock_long_against_short`, `add_short_locked`, `reduce_short_locked`, `unlock_short` | `single_side -> locked -> single_side` | 锁单期间不得新开 `position_id`，仍属于同一场交易 | `不能原样迁回` | 保留为结构类候选 |
| `C6 反向再出发` | `B0294`, `B0295` | `reverse_short_to_long` | `single_side(A) -> single_side(B)` | 发生方向反转后必须新建 `position_id` | `不能原样迁回` | 保留为边界候选 |
| `C7 全平休息` | `B0288`, `B0293`, `B0294`, `B0305` | 由 `*_to_flat` 后的空窗体现 | `flat -> rest -> reentry` | `rest` 不属于旧 `position_id`，重开后新编号 | `可迁回` | 保留为高优先候选 |
| `C8 单位制度` | `B0288`, `B0295`, `B0304` | 非单一 transition；体现为 `units / lot_size_regime` 变化 | `same_state -> different_unit_regime` | 不直接切换 `position_id`，但必须记 regime tag | `可迁回` | 保留为制度变量候选 |
| `C9 实验段隔离` | `B0304` | `1976-10 -> 1976-12` 的 `100股试验段` | `normal_regime -> experimental_regime` | 不以收益优劣直接并入常规样本 | `可迁回为样本标签` | 保留为样本治理候选 |

---

## 5. 每一簇的正式解释

### 5.1 `C1 试单入场`

这是立花方法里最重要的起点。

它的核心不是“先随便买一点”，而是：

`先用极小单位取得市场解释权`

对量化化来说，这意味着：

1. `probe` 必须是正式对象
2. 它不能和“正常开满仓”混写
3. 后续能否升格为 `mother position` 必须是显式判定

### 5.2 `C2 母单扩张`

立花不是均匀加仓，而是离散档位扩张。

当前最适合的量化表达不是连续仓位函数，而是：

`position_id 不变 + leg_id 递增 + unit ladder`

### 5.3 `C3 单边减仓`

这类动作已经能和当前 `partial-exit` 基础设施自然接轨。

因此它是当前最容易迁回 EmotionQuant 主线的一簇：

`long-only entry + multi-leg exit`

### 5.4 `C4 全平离场`

这不是普通止盈止损动作，而是立花系统的身份边界。

一旦全平：

1. 旧 `position_id` 必须结束
2. 后续再入场必须视为新的一场交易
3. 不得把“同标的连续来回操作”误写成同一场战役

### 5.5 `C5 锁单测试`

这是当前最不能被误译的一簇。

它的正式含义不是简单对冲，而是：

`用反向腿测试市场，同时维持母单生存`

所以它虽然不能原样迁回 A 股 BOF 主线，但绝不能被删掉。  
它应被保留为：

`结构等价物搜索对象`

也就是后续去寻找：

`在 long-only / A股 约束下，什么动作最接近锁单的功能`

### 5.6 `C6 反向再出发`

当前样本里已观测到 `reverse_short_to_long`，这说明方向反转不是理论幻想，而是真实动作。

但它不能直接迁回当前 Broker，因为当前执行主线仍是 `BUY-only`。

因此它只能先保留为：

`原书忠实度必保留，A股主线暂不直迁`

### 5.7 `C7 全平休息`

这是最容易被低估、但对你最重要的一簇。

它说明立花系统不是永远在场，而是允许：

`主动离场 -> 休息 -> 再次出发`

这和你一直强调的“给自己一点空间风险，去博一个机会”是同一种东西。  
对系统来说，它意味着：

`flat` 不是空白，而是正式状态。

### 5.8 `C8 单位制度`

书里反复强调小张数、固定交易单位、必要时调整单位。

这说明“每次多少股”不是执行噪音，而是制度变量。  
因此：

1. `fixed_lot`
2. `probe_unit`
3. `mother_unit`
4. `experimental_unit_regime`

都应视为正式变量。

### 5.9 `C9 实验段隔离`

`1976-10 -> 1976-12` 的 `100股试验段` 不能与常规样本混算。

它的价值不在于赚钱，而在于告诉我们：

`立花也会主动做失败试验`

所以后续验证必须保留失败实验样本，而不是只看成功路径。

---

## 6. 当前未进入正式候选主集的 transition

虽然 replay contract 允许更大的状态集，但当前尚未进入正式候选主集的包括：

1. `lock_short_against_long`
2. `unlock_long`
3. `reverse_long_to_short`
4. `rebalance_locked`

它们当前不进主集，不是因为不重要，而是因为：

1. 当前后页样本未稳定观测到
2. 书页 doctrine 虽有暗示，但还不够强
3. 现在就升格会把候选表拉得过宽

因此这些动作当前统一记为：

`backlog transition candidates`

---

## 7. 当前最重要的迁移边界

当前正式迁移边界固定为：

### 7.1 可直接迁回 A 股 BOF 主线的

1. `试单入场`
2. `母单扩张`
3. `单边减仓`
4. `全平离场`
5. `全平休息`
6. `单位制度`

### 7.2 只能寻找结构等价物的

1. `锁单测试`
2. `反向再出发`

### 7.3 只能做样本治理标签的

1. `100股实验段`

---

## 8. 一句话结论

立花方法当前已经可以被压成 9 个正式候选簇，其中真正能直接迁回 EmotionQuant 主线的，是 `试单 / 母单 / 单边减仓 / 全平 / 休息 / 单位制度`；最难但也最值钱的，是 `锁单` 和 `反向再出发` 这两个结构类候选。
