# Normandy N1.8 Tachibana Contrary Alpha Record

**日期**：`2026-03-12`  
**阶段**：`Normandy / N1.8`  
**对象**：`TACHI_CROWD_FAILURE 首轮 contrary alpha 结论固定`  
**状态**：`Active`

---

## 1. 目标

本文用于把 `Normandy / N1.8` 的首轮 `Tachibana contrary alpha` 结论固定下来。

本记录只回答一个问题：

`立花义正最小可执行 detector —— TACHI_CROWD_FAILURE —— 在当前 A 股日线 / T+1 Open 语义下，是否已经形成独立 alpha。`

---

## 2. 参考依据

### 2.1 理论与上游结论

1. `docs/Strategy/PAS/tachibana-yoshimasa-analysis.md`
2. `normandy/01-full-design/90-research-assets/tachibana-crowd-failure-minimal-contract-note-20260312.md`
3. `normandy/README.md`
4. `normandy/02-implementation-spec/05-tachibana-contrary-alpha-search-spec-20260312.md`
5. `normandy/03-execution/05-phase-n1-8-tachibana-contrary-alpha-card-20260312.md`
6. `normandy/03-execution/records/01-phase-n1-bof-conclusion-record-20260312.md`

### 2.2 当前证据

1. `normandy/03-execution/evidence/normandy_tachibana_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t053148__tachibana_alpha_matrix.json`
2. `normandy/03-execution/evidence/normandy_tachibana_alpha_digest_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t061103__tachibana_alpha_digest.json`

---

## 3. N1.8 长窗结果

首轮正式长窗固定为：

1. `window = 2023-01-03 ~ 2026-02-24`
2. `dtt_variant = v0_01_dtt_pattern_only`
3. `control = BOF_CONTROL`
4. `candidate = TACHI_CROWD_FAILURE`

核心结果如下：

| Label | Trade Count | EV | PF | MDD | Participation | Overlap vs BOF | Incremental Trades |
|---|---:|---:|---:|---:|---:|---:|---:|
| `BOF_CONTROL` | 277 | 0.01609 | 2.6121 | 0.13267 | 0.80523 | 1.00000 | 0 |
| `TACHI_CROWD_FAILURE` | 20 | -0.01242 | 2.2522 | 0.06300 | 1.00000 | 0.95000 | 1 |

候选规则回读结果固定为：

1. `positive_edge_ok = false`
2. `sample_density_ok = true`
3. `complementary_edge_ok = false`
4. `contrary_alpha_candidate = false`

环境桶读数显示：

1. `NEUTRAL`：`19` 笔，`EV = -0.01516`
2. `BEARISH`：`1` 笔，`EV = +0.03974`

也就是说：

1. `TACHI_CROWD_FAILURE` 已经形成可审判样本，不再是零触发对象
2. 但它当前并没有形成正向 standalone edge
3. 它和 `BOF_CONTROL` 的执行重叠很高，增量交易只有 `1` 笔

---

## 4. 正式结论

当前 `N1.8` 的正式结论固定为：

1. `TACHI_CROWD_FAILURE` 当前 detector 已形成首轮可审判样本
2. 但它没有通过首轮 contrary alpha 门槛
3. 当前更准确的裁决是：
   - `overlap_with_bof_or_not_independent`
   - 同时保持 `observation_only`
4. 这条裁决针对的是：
   - `当前 minimal contract`
   - `当前 detector`
   - `当前 A 股日线 + T+1 Open` 语义
5. 它不等于：
   - `立花义正整套理论已经 no-go`
   - `Tachibana 研究线永久关闭`

换句话说：

`当前最小 detector 已经能触发，但它还没有证明自己是独立 contrary alpha；它更像 BOF 边界附近的高重叠对象，而不是当前的第二胜者。`

---

## 5. 边界与后续动作

`TACHI_CROWD_FAILURE` 当前后续动作固定为：

1. 不进入 `N2 / controlled exit decomposition`
2. 不进入当前主线升格讨论
3. 不被写成当前 `PAS` 新形态
4. 若未来继续推进，只允许进入：
   - `deeper detector refinement`
   - 或 `Tachibana backlog retention`

对 `Normandy` 主队列而言，当前优先级应回到：

1. `N1.7 / FB stability and purity`
2. `N1.9 / SB refinement or no-go`
3. `Tachibana` 作为延后 refinement 线保留

---

## 6. 一句话结论

`TACHI_CROWD_FAILURE` 当前已经从“纯理论对象”推进成“可审判对象”，但首轮正式长窗表明它仍未形成独立 contrary alpha；当前结论应固定为 observation-only，并把主队列优先级交还给 FB stability。`
