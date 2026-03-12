# Normandy N1.9A FB Boundary Stability Follow-up Record

**日期**：`2026-03-12`  
**阶段**：`Normandy / N1.9A`  
**对象**：`FB_BOUNDARY focused stability follow-up formal readout`  
**状态**：`Active`

---

## 1. 目标

本文用于把 `Normandy / N1.9A` 的 `FB_BOUNDARY focused stability follow-up` 结论固定下来。

本记录只回答两个问题：

1. `FB_BOUNDARY` 当前是否已经稳到可以打开 `N2`
2. 若答案是否定的，`Normandy` 主队列下一步应转向哪里

---

## 2. 参考依据

### 2.1 上游结论

1. `normandy/03-execution/records/06-phase-n1-9-fb-detector-refinement-record-20260312.md`
2. `normandy/03-execution/07-phase-n1-9a-fb-boundary-stability-follow-up-card-20260312.md`

### 2.2 当前证据

1. `normandy/03-execution/evidence/normandy_fb_refinement_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t083246__fb_refinement_matrix.json`
2. `normandy/03-execution/evidence/normandy_fb_refinement_digest_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t094924__fb_refinement_digest.json`
3. `normandy/03-execution/evidence/normandy_fb_refinement_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t083246__fb_boundary_stability_report.json`

---

## 3. N1.9A 核心结果

`fb_boundary_stability_report` 当前已经把本轮结论固定为：

1. `stability_status = fragile_boundary_not_n2_ready`
2. `decision = hold_n2_and_demote_boundary_to_watch_candidate`
3. `meaningful_negative_signal_years = [2024, 2026]`
4. `negative_example_years = [2023, 2024, 2025, 2026]`
5. `stability_flags =`
   - `single_bucket_dependency`
   - `negative_signal_year_slices`
   - `losses_not_isolated`
   - `sample_still_small`

### 3.1 retained branch 的正式读数

`FB_BOUNDARY` 当前 formal summary 固定为：

1. `trade_count = 17`
2. `EV = +0.03143`
3. `PF = 3.24845`
4. `MDD = 0.02544`
5. `dominant_environment_share = 0.94118`

这说明：

1. `FB_BOUNDARY` 仍然是 `FB` family 里唯一保住正向 edge 的 retained branch
2. 但它的 edge 依旧几乎全部压在 `NEUTRAL`

### 3.2 focused stability 为什么仍不给放行

按 signal-year 重建后，当前读数如下：

| Signal Year | Trade Count | Avg Gross Return | Win Rate | Avg Strength |
|---|---:|---:|---:|---:|
| `2023` | `5` | `+0.07680` | `0.4000` | `0.7095` |
| `2024` | `2` | `-0.09484` | `0.0000` | `0.8367` |
| `2025` | `7` | `+0.05316` | `0.4286` | `0.7620` |
| `2026` | `3` | `-0.00118` | `0.3333` | `0.7216` |

当前不能放行 `N2` 的原因已足够明确：

1. `2024` 已经形成带样本的明显负切片
2. `2026` 虽然更轻，但仍是小样本偏负
3. 最差负 trade 并不只集中在同一段局部 accident，而是横跨：
   - `2023`
   - `2024`
   - `2025`
   - `2026`

### 3.3 focused stability 的补充读数

本轮 focused report 还固定了两条补充事实：

1. `active_quarters = 8`
2. `negative_examples` 最差样本包括：
   - `2024-10-28 / 300846 / -11.68%`
   - `2026-01-26 / 603993 / -10.32%`
   - `2025-02-27 / 002611 / -9.77%`
   - `2024-03-20 / 002245 / -7.29%`

这意味着：

`当前 boundary 分支的 fragility 并不是“只坏在一个季度”，而更像跨年份、低频但持续存在的负 trade 问题。`

---

## 4. 正式结论

当前 `N1.9A` 的正式结论固定为：

1. `FB_BOUNDARY` 继续保留为 `FB` family 的 retained branch
2. 但它当前仍不通过 `N2 ready` 门槛
3. 最准确的裁决应固定为：
   - `retained_branch_but_watch_candidate`
   - `hold_n2`
   - `do_not_promote_now`
4. 因此 `BOF vs FB_BOUNDARY` 的 `N2 / controlled exit decomposition` 当前继续锁住

换句话说：

`N1.9A` 已经把“boundary 分支有没有稳到可以开 N2”这个问题回答成了否定。`

---

## 5. 后续动作

对 `FB_BOUNDARY` 而言，当前后续动作固定为：

1. 保留 retained branch 身份
2. 但先降级为 `watch candidate`
3. 当前不继续占用 `Normandy` 主队列第一优先级

对 `Normandy` 主队列而言，当前优先级应固定改写为：

1. `N1.10 / SB refinement or no-go`
2. `Tachibana detector refinement or backlog retention`
3. `FB_BOUNDARY` 作为后续可回看的 watch candidate
4. `N2 / controlled exit decomposition` 继续暂缓

---

## 6. 一句话结论

`FB_BOUNDARY` 仍然是 `FB` family 当前唯一值得保留的 retained branch，但 focused stability follow-up 已经证明它还不够稳，不能直接打开 `N2`；因此当前更合理的做法是把它降级为 watch candidate，并把 Normandy 主队列切到 `SB refinement or no-go`。`
