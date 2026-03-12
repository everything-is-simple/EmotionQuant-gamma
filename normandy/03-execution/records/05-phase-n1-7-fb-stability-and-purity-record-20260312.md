# Normandy N1.7 FB Stability And Purity Record

**日期**：`2026-03-12`  
**阶段**：`Normandy / N1.7`  
**对象**：`FB stability / purity 首轮裁决固定`  
**状态**：`Active`

---

## 1. 目标

本文用于把 `Normandy / N1.7` 的首轮 `FB stability / purity` 结论固定下来。

本记录只回答一个问题：

`FB 这条已经成立的第二 alpha 候选，当前是否已经稳定到值得直接进入 N2 exit decomposition，还是仍需先做 detector refinement。`

---

## 2. 参考依据

### 2.1 上游结论

1. `normandy/03-execution/records/02-phase-n1-5-second-alpha-record-20260312.md`
2. `normandy/03-execution/records/03-phase-n1-6-fb-dossier-record-20260312.md`
3. `normandy/03-execution/04-phase-n1-7-fb-stability-and-purity-card-20260312.md`

### 2.2 当前证据

1. `normandy/03-execution/evidence/normandy_volman_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t001652__fb_candidate_report.json`
2. `normandy/03-execution/evidence/normandy_volman_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t001652__fb_stability_report.json`
3. `normandy/03-execution/evidence/normandy_volman_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t001652__fb_purity_audit.json`

---

## 3. N1.7 核心结果

`FB stability report` 当前给出的核心读数固定为：

1. `stability_status = fragile_candidate_not_exit_ready`
2. `decision = detector_refinement_before_n2`
3. `pairing_diagnostics = 33 / 33`，说明当前 snapshot 配对完整，不是缺样本造成的假结论
4. `FB` 已跨 `10` 个季度出现，说明它不是单次爆点对象
5. 但它的正向 edge 仍几乎全部集中在：
   - `NEUTRAL = 31` 笔，`EV = +0.02201`
   - `BULLISH = 2` 笔，`EV = -0.10197`

按 signal-year 重建切片后，当前读数如下：

| Signal Year | Trade Count | Avg Gross Return | Win Rate | Avg Strength |
|---|---:|---:|---:|---:|
| `2023` | 10 | `+0.02013` | `0.3000` | `0.7895` |
| `2024` | 8 | `-0.04151` | `0.1250` | `0.8548` |
| `2025` | 11 | `+0.07241` | `0.3636` | `0.7928` |
| `2026` | 4 | `-0.03315` | `0.2500` | `0.7374` |

这里需要固定两点：

1. `2024` 已经构成带样本密度的负切片，不是“偶然空年”
2. `2026` 也出现负读数，但当前只算小样本补充警告，不单独升格为主裁决

`FB purity audit` 当前给出的核心读数固定为：

1. `purity_verdict = boundary_loaded_detector_refinement_required`
2. `edge_touch_ratio = 0.51515`
3. `edge_depth_ratio = 0.21212`
4. `NOT_FIRST_PULLBACK` 占未选中 detector 尝试的 `0.07023`

这意味着：

1. detector 没有明显把大量非 first-pullback 样本直接混入已选集合
2. 但超过一半的已选样本停在 `prior_ema_touches = 2` 的边界
3. 而且这批边界样本的表现明显好于更干净的 `0/1 touch` 子集

当前 purity 关键对比如下：

| Touch Bucket | Trade Count | Avg Gross Return | Win Rate | Avg Strength |
|---|---:|---:|---:|---:|
| `touch_0_1_cleaner` | 16 | `-0.00186` | `0.1875` | `0.8553` |
| `touch_2_boundary` | 17 | `+0.03311` | `0.3529` | `0.7482` |

换句话说：

`当前 FB 的 alpha 并不是由更 textbook-clean 的 first-pullback 子集撑起来，而更像由 detector 边界附近的 boundary-loaded 样本撑起来。`

---

## 4. 正式结论

当前 `N1.7` 的正式结论固定为：

1. `FB` 继续保留为第二个自带 alpha 候选
2. 但它当前不通过“可直接进入 N2”的稳定性门槛
3. 更准确的裁决应固定为：
   - `qualified_but_fragile`
   - `not_exit_ready`
   - `detector_refinement_before_n2`
4. 当前真正需要回答的，不再是“FB 有没有 alpha”，而是：
   - `FB 的有效 alpha 到底来自 cleaner first-pullback，还是来自 boundary-loaded 子语义`
5. 因此现在直接进入 `BOF vs FB exit decomposition` 会过早

换句话说：

`FB 不是假候选，但它当前也不是已经稳定到可以直接解 exit 的候选；N1.7 已经把下一步固定成 detector refinement，而不是 N2。`

---

## 5. 后续动作

`FB` 当前后续动作固定为：

1. 先拆：
   - `FB cleaner(0/1 touch)`
   - `FB boundary(2 touch)`
2. 再分别做长窗复核
3. 只有 refinement 后仍保住：
   - 正向 edge
   - 跨年稳定性
   - bucket 不过度单一
   才允许进入 `N2 / controlled exit decomposition`

对 `Normandy` 主队列而言，当前优先级应固定为：

1. `FB detector refinement`
2. `N1.9 / SB refinement or no-go`
3. `N2 / controlled exit decomposition` 暂缓，等待 `FB` 重新过稳定性门槛

---

## 6. 一句话结论

`FB` 当前已经证明自己不是空候选，但 `N1.7` 首轮 stability / purity 审核表明：它的正向 edge 仍主要依赖 `NEUTRAL`，且有效收益更像由 boundary-loaded 样本撑起；因此当前正式下一步不是 `N2`，而是先做 `FB detector refinement`。`
