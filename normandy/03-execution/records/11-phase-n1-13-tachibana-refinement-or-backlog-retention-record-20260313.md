# Normandy N1.13 Tachibana Refinement Or Backlog Retention Record

**日期**：`2026-03-13`  
**阶段**：`Normandy / N1.13 Tachibana refinement or backlog retention`  
**对象**：`Tachibana contrary alpha formal gate readout`  
**状态**：`Active`

---

## 1. 目标

本文用于把 `Normandy / N1.13` 围绕 `Tachibana contrary alpha` 的正式治理决策固定下来。

本记录只回答三个问题：

1. `TACHI_CROWD_FAILURE` 当前失败到底是 detector 太粗，还是对象本身在当前语义下不值得继续 formalize
2. 是否存在下一条更窄、更可复核的 refinement hypothesis
3. `Tachibana` 这条线下一步应进入 detector refinement，还是正式保留为 backlog retention

---

## 2. 参考依据

### 2.1 上游治理口径

1. `normandy/03-execution/11-phase-n1-13-tachibana-refinement-or-backlog-retention-card-20260313.md`
2. `normandy/03-execution/records/04-phase-n1-8-tachibana-contrary-alpha-record-20260312.md`
3. `normandy/03-execution/records/00-normandy-interim-conclusions-20260312.md`
4. `normandy/02-implementation-spec/05-tachibana-contrary-alpha-search-spec-20260312.md`
5. `normandy/01-full-design/90-research-assets/tachibana-crowd-failure-minimal-contract-note-20260312.md`

### 2.2 当前 formal evidence

1. `normandy/03-execution/evidence/normandy_tachibana_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t053148__tachibana_alpha_matrix.json`
2. `normandy/03-execution/evidence/normandy_tachibana_alpha_digest_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t061103__tachibana_alpha_digest.json`

---

## 3. N1.13 核心结果

当前 formal digest 已把 `TACHI_CROWD_FAILURE` 的读数固定为：

1. `trade_count = 20`
2. `expected_value = -0.01242`
3. `profit_factor = 2.25216`
4. `overlap_rate_vs_bof_control = 0.95`
5. `incremental_buy_trades_vs_bof_control = 1`
6. `positive_edge_ok = false`
7. `sample_density_ok = true`
8. `complementary_edge_ok = false`
9. `contrary_alpha_candidate = false`

当前 formal verdict 固定为：

`TACHI_CROWD_FAILURE 当前未同时满足正 EV、样本密度和增量 alpha 门槛；先保留为 Tachibana 首轮观测对象。`

---

## 4. 当前失败到底是什么性质

### 4.1 不是样本密度问题

`TACHI_CROWD_FAILURE` 当前 `trade_count = 20`，已满足最小样本密度门槛（`min_trade_count = 20`）。

因此：

`当前失败不是因为样本太少。`

### 4.2 不是增量 alpha 问题

`TACHI_CROWD_FAILURE` 当前 `incremental_buy_trades_vs_bof_control = 1`，远低于增量门槛（`min_incremental_trades = 20`）。

同时 `overlap_rate_vs_bof_control = 0.95`，说明它几乎完全重叠于 `BOF_CONTROL`。

因此：

`当前失败的第一主因是：TACHI_CROWD_FAILURE 几乎完全重叠于 BOF_CONTROL，不构成独立的增量 alpha 来源。`

### 4.3 也不是 PF 问题

`TACHI_CROWD_FAILURE` 当前 `profit_factor = 2.25216`，已超过最低门槛（`profit_factor_floor = 1.0`）。

因此：

`当前失败不是因为 PF 太低。`

### 4.4 真正的失败点：负 EV

`TACHI_CROWD_FAILURE` 当前 `expected_value = -0.01242`，未满足正 EV 门槛（`expected_value_must_be_positive = true`）。

同时 `expected_value_delta_vs_bof_control = -0.02851`，说明它相对 `BOF_CONTROL` 是负向 delta。

因此：

`当前失败的第二主因是：TACHI_CROWD_FAILURE 当前 EV 为负，且相对 BOF_CONTROL 是负向 delta。`

---

## 5. 当前失败更像 detector 太粗，还是对象本身不值得继续

### 5.1 当前 minimal contract 的定义

根据 `tachibana-crowd-failure-minimal-contract-note-20260312.md`，当前 `TACHI_CROWD_FAILURE` 的定义固定为：

1. 检测对象：`crowd_failure_signal`
2. 触发条件：市场极端情绪后的反转
3. 执行语义：T+1 Open
4. 出场语义：统一 Broker（stop_loss + trailing_stop）

这已经是一条最小可执行假设。

### 5.2 是否存在更窄的 refinement hypothesis

若要继续 refinement，只能从以下方向入手：

1. **更严格的触发条件**：
   - 当前 `crowd_failure_signal` 是否太宽
   - 是否需要增加更多前置过滤（如市场环境、行业分布、个股质量）

2. **更精细的执行时机**：
   - 当前 T+1 Open 是否太早
   - 是否需要等待更明确的反转确认

3. **更针对性的出场语义**：
   - 当前统一 Broker 是否不适合 contrary alpha
   - 是否需要专门的 contrary exit semantics

但这些方向都存在同样的问题：

1. 当前 `TACHI_CROWD_FAILURE` 已经是 minimal contract
2. 继续细化会进入"主观补丁"区域
3. 当前 20 笔样本中，95% 重叠于 `BOF_CONTROL`，说明它更像 `BOF` 的子集，而不是独立的 contrary alpha

因此：

`当前不存在明确的、可复核的、非主观补丁的 refinement hypothesis。`

### 5.3 当前更准确的裁决

基于上述分析，当前最准确的裁决应写成：

`TACHI_CROWD_FAILURE 当前失败不是因为 detector 太粗，而是因为它在当前日线语义下，更像 BOF_CONTROL 的高重叠子集，而不是独立的 contrary alpha 来源。`

---

## 6. 当前 formal readout

本轮 `N1.13 Tachibana refinement or backlog retention` 的正式裁决固定为：

1. `detector_too_coarse = no`
2. `object_not_worth_formalize_in_current_semantics = yes`
3. `refinement_hypothesis_exists = no`
4. `decision = keep_tachibana_backlog_only`

用一句更完整的话说：

`TACHI_CROWD_FAILURE` 当前在日线 T+1 Open 语义下，更像 `BOF_CONTROL` 的高重叠子集（95% overlap，仅 1 笔增量），而不是独立的 contrary alpha 来源；当前不存在明确的、可复核的 refinement hypothesis；因此正式把 `Tachibana` 收进 backlog retention，不再占 `Normandy` 主队列。

---

## 7. 对 Normandy 主队列意味着什么

当前治理动作固定为：

1. `N1.13` formal readout 已完成
2. `Tachibana` 正式从 `Normandy` 主队列退出
3. `Tachibana` 保留为 `backlog retention`，不删除理论档案
4. 不把 `Tachibana` 误写成"立花理论整体失败"
5. 不把 `backlog retention` 误读成"永久放弃"

`Tachibana` 当前在 `Normandy` 中的准确层级固定为：

`Outside-PAS but Normandy-relevant research queue / backlog retention`

---

## 8. Tachibana 后续研究方向（backlog）

虽然 `Tachibana` 当前退出主队列，但它仍然保留以下研究价值：

1. **理论骨架留档**：
   - 立花义正的 contrary doctrine
   - crowd-extreme observation framework
   - 执行纪律与风险节奏

2. **可能的后续入口**（非当前主队列）：
   - 若未来出现更明确的 crowd-extreme 样本族
   - 若未来执行语义从 T+1 Open 改为 intraday
   - 若未来 MSS 引入 crowd-sentiment layer

3. **明确不该做的**：
   - 不把 `Tachibana` 粗暴翻译成"把 PAS 反着做"
   - 不把 `backlog retention` 误读成"立刻重开大型研究"
   - 不把理论留档误读成"主队列还该继续烧时间"

---

## 9. 正式结论

当前 `N1.13 Tachibana refinement or backlog retention` 的正式结论固定为：

1. `TACHI_CROWD_FAILURE` 当前失败不是 detector 太粗
2. 真正原因是它在当前语义下更像 `BOF_CONTROL` 的高重叠子集
3. 当前不存在明确的、可复核的 refinement hypothesis
4. 当前最准确的治理动作应固定为：
   - `keep_tachibana_backlog_only`
   - `exit_normandy_main_queue`
   - `retain_theory_dossier`
   - `do_not_reopen_without_new_hypothesis`

---

## 10. 一句话结论

`N1.13` 已经把 `Tachibana` 的治理决策正式读出来了：`TACHI_CROWD_FAILURE` 当前在日线语义下更像 `BOF` 的高重叠子集（95% overlap），不是独立 contrary alpha；当前不存在可复核的 refinement hypothesis；因此正式收进 backlog retention，退出 `Normandy` 主队列，但保留理论档案与后续研究入口。
