# Normandy N1.6 FB Dossier Record

**日期**：`2026-03-12`  
**阶段**：`Normandy / N1.6`  
**对象**：`FB focused dossier 首轮结论固定`  
**状态**：`Active`

---

## 1. 目标

本文用于把 `Normandy / N1.6` 的首轮 `FB focused dossier` 结论固定下来。

本记录只回答一个问题：

`FB 这个第二个自带 alpha 候选，现在到底是稳定补充型 alpha，还是仅仅“勉强通过门槛”的脆弱候选。`

---

## 2. 参考依据

### 2.1 上游结论

1. `normandy/03-execution/records/01-phase-n1-bof-conclusion-record-20260312.md`
2. `normandy/03-execution/records/02-phase-n1-5-second-alpha-record-20260312.md`

上游已经固定：

1. `BOF` 保持当前 baseline
2. `FB` 是首轮唯一通过 `second alpha candidate` 门槛的非 `BOF` 候选

### 2.2 当前证据

1. `normandy/03-execution/evidence/normandy_volman_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t001652__volman_alpha_matrix.json`
2. `normandy/03-execution/evidence/normandy_volman_alpha_digest_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t015510__volman_alpha_digest.json`
3. `normandy/03-execution/evidence/normandy_volman_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t001652__fb_candidate_report.json`

---

## 3. 当前 dossier 结果

`FB dossier` 当前给出的结论是：

1. `qualification = qualified_second_alpha_candidate_with_risk_flags`
2. `FB` 已通过第二个 alpha 候选门槛
3. 但当前同时带有四个风险标记：
   - `low_sample_count`
   - `dominant_bucket_dependency`
   - `bullish_failure_observed`
   - `edge_below_bof_control`

核心指标如下：

| Label | Trade Count | EV | PF | MDD | Participation | Overlap vs BOF | Incremental Trades |
|---|---:|---:|---:|---:|---:|---:|---:|
| `BOF_CONTROL` | 277 | 0.01609 | 2.6121 | 0.13267 | 0.80523 | 1.00000 | 0 |
| `FB` | 33 | 0.01450 | 3.4433 | 0.05908 | 1.00000 | 0.00000 | 33 |

环境桶拆解显示：

1. `NEUTRAL`：`31` 笔，`EV=0.02201`
2. `BULLISH`：`2` 笔，`EV=-0.10197`

也就是说：

1. `FB` 当前的正向 edge 主要几乎全部落在 `NEUTRAL`
2. 它还没有表现出跨环境稳定性

---

## 4. 正式结论

当前 `N1.6` 的正式结论固定为：

1. `FB` 继续保留为第二个自带 alpha 候选
2. 但当前不能把它表述成“已经稳定成立的第二主形态”
3. 它更准确的状态是：
   - `通过门槛`
   - `独立性成立`
   - `样本仍小`
   - `环境依赖明显`
4. 因此下一步不能直接升主线，也不应急着宣布它接近 `BOF`

换句话说：

`FB 现在是成立的候选，但还不是完成稳定性证明的候选。`

---

## 5. 后续动作

`FB` 后续优先级固定为：

1. 先做 `regime slicing`
2. 再做 `first-pullback purity audit`
3. 最后在 `BOF_CONTROL` 对照下做最简 `exit decomposition`

当前不建议：

1. 直接让 `FB` 进入主线
2. 直接把 `FB` 和 `BOF` 做简单并集
3. 因为当前正 `EV` 就跳过稳定性验证

---

## 6. 一句话结论

`FB` 当前已经证明自己不是空候选，但它仍是“通过门槛且带风险标记”的第二个 alpha 候选；下一步应继续做 focused provenance，而不是直接升格。`
