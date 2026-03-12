# Normandy N1.9 FB Detector Refinement Record

**日期**：`2026-03-12`  
**阶段**：`Normandy / N1.9`  
**对象**：`FB cleaner vs boundary refinement formal readout`  
**状态**：`Active`

---

## 1. 目标

本文用于把 `Normandy / N1.9` 的 `FB detector refinement` 结论固定下来。

本记录只回答两个问题：

1. `FB` 当前真正 carrying edge 的 retained branch 是哪一支
2. 该分支当前是否已经足够稳到可以直接打开 `N2`

---

## 2. 参考依据

### 2.1 上游结论

1. `normandy/03-execution/records/05-phase-n1-7-fb-stability-and-purity-record-20260312.md`
2. `normandy/03-execution/06-phase-n1-9-fb-detector-refinement-card-20260312.md`

### 2.2 当前证据

1. `normandy/03-execution/evidence/normandy_fb_refinement_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t083246__fb_refinement_matrix.json`
2. `normandy/03-execution/evidence/normandy_fb_refinement_digest_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t094924__fb_refinement_digest.json`

---

## 3. N1.9 核心结果

`fb_refinement_digest` 当前已经把本轮结论固定为：

1. `branch_leader = FB_BOUNDARY`
2. `refinement_verdict = boundary_branch_promoted`
3. `decision = boundary_stability_follow_up_before_n2`
4. `positive_edge_branches = [FB_BOUNDARY]`
5. `refined_second_alpha_candidates = [FB_BOUNDARY]`

换句话说：

`当前 FB family 的 alpha 不是由 cleaner(0/1 touch) 在撑，而是由 boundary(2 touch) 分支在撑。`

### 3.1 cleaner vs boundary 直接对比

| Branch | Trade Count | EV | PF | Max Drawdown |
|---|---:|---:|---:|---:|
| `FB_CLEANER` | `16` | `-0.00349` | `4.07839` | `0.07143` |
| `FB_BOUNDARY` | `17` | `+0.03143` | `3.24845` | `0.02544` |

这里需要固定两点：

1. `FB_CLEANER` 的 textbook-clean 语义并没有保住总 EV
2. `FB_BOUNDARY` 不仅保住正 EV，而且相对 `BOF_CONTROL` 仍给出：
   - `expected_value_delta_vs_bof_control = +0.01534`
   - `profit_factor_delta_vs_bof_control = +0.63638`

### 3.2 retained branch 的稳定性补充

`FB_BOUNDARY` 虽然胜出，但稳定性仍不能被写成“已解决”。

当前 digest 已把下面两条风险同时写死：

1. `single_bucket_dependency`
2. `negative_signal_year_slices`

对应读数如下：

1. `dominant_environment_share = 0.94118`
2. `best_environment_bucket = NEUTRAL`，其中：
   - `trade_count = 16`
   - `EV = +0.04078`
3. `BULLISH` 仅 `1` 笔，且 `EV = -0.11829`

按 signal-year 重建后，`FB_BOUNDARY` 当前读数为：

| Signal Year | Trade Count | Avg Gross Return | Win Rate | Avg Strength |
|---|---:|---:|---:|---:|
| `2023` | `5` | `+0.07680` | `0.4000` | `0.7095` |
| `2024` | `2` | `-0.09484` | `0.0000` | `0.8367` |
| `2025` | `7` | `+0.05316` | `0.4286` | `0.7620` |
| `2026` | `3` | `-0.00118` | `0.3333` | `0.7216` |

这说明：

1. `boundary` 分支已经比 family-level `FB` 更像真正 retained branch
2. 但它仍没有摆脱：
   - `NEUTRAL` 主导
   - `2024` 负切片
   - `2026` 近零偏负
   这三条稳定性警告

### 3.3 cleaner 分支为什么退出主队列

`FB_CLEANER` 当前应正式退出 `FB` 主队列的原因已经足够明确：

1. 总 EV 转负：`-0.00349`
2. `2023 / 2024` 两个 signal-year 都为负
3. 它的 edge 没有因为“更 textbook-clean”而自然提升

因此当前不能把 `cleaner` 继续保留为“更纯、更该优先”的默认假设。

---

## 4. 正式结论

当前 `N1.9` 的正式结论固定为：

1. `FB family` 当前 retained branch 已经明确收敛到 `FB_BOUNDARY`
2. `FB_CLEANER` 退出 `FB` 主研究队列，降级为观测分支
3. `FB_BOUNDARY` 当前已经通过：
   - 正 EV
   - 样本密度
   - 与 `BOF_CONTROL` 的第二 alpha 门槛
4. 但 `FB_BOUNDARY` 仍未通过“可直接打开 N2”的稳定性门槛
5. 因此当前最准确的裁决应固定为：
   - `boundary_branch_promoted`
   - `retained_branch = FB_BOUNDARY`
   - `still_fragile_after_refinement`
   - `boundary_stability_follow_up_before_n2`

换句话说：

`N1.9` 已经把“当前 FB alpha 到底来自哪一支”这个问题回答清楚了，但它还没有把“boundary 分支已经稳定到可以直接解 exit”这个问题回答成肯定。`

---

## 5. 后续动作

`FB` 当前后续动作固定为：

1. 以 `FB_BOUNDARY` 作为新的 retained branch
2. 先做 `FB_BOUNDARY focused stability follow-up`
3. 只有在 boundary 分支进一步证明：
   - 跨年不再持续发散
   - bucket 不再过度单一
   才允许进入 `N2 / controlled exit decomposition`

对 `Normandy` 主队列而言，当前优先级应固定为：

1. `FB_BOUNDARY stability follow-up before N2`
2. `N1.10 / SB refinement or no-go`
3. `N2 / controlled exit decomposition` 继续暂缓

---

## 6. 一句话结论

`FB detector refinement` 已经把当前 retained branch 固定为 `FB_BOUNDARY`：它保住了 `FB` 家族真正的正向 edge，而 `FB_CLEANER` 没有；但由于 boundary 分支仍表现出 `NEUTRAL` 过度集中与 `2024 / 2026` 负切片，它现在还不能直接打开 `N2`。`
