# Normandy N1.10 SB Refinement Or No-Go Record

**日期**：`2026-03-12`  
**阶段**：`Normandy / N1.10`  
**对象**：`SB refinement or no-go formal readout`  
**状态**：`Active`

---

## 1. 目标

本文用于把 `Normandy / N1.10` 的 `SB refinement or no-go` 结论固定下来。

本记录只回答两个问题：

1. `SB` 当前 full detector 路线是否还值得继续占用主队列
2. 若答案是否定，是否存在一个值得保留的窄 watch branch

---

## 2. 参考依据

### 2.1 上游结论

1. `normandy/03-execution/records/02-phase-n1-5-second-alpha-record-20260312.md`
2. `normandy/03-execution/08-phase-n1-10-sb-refinement-or-no-go-card-20260312.md`

### 2.2 当前证据

1. `normandy/03-execution/evidence/normandy_volman_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t001652__volman_alpha_matrix.json`
2. `normandy/03-execution/evidence/normandy_volman_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t001652__sb_refinement_report.json`

---

## 3. N1.10 核心结果

`sb_refinement_report` 当前已经把本轮结论固定为：

1. `refinement_status = full_detector_no_go_watch_branch_only`
2. `refinement_verdict = current_sb_detector_no_go_narrow_watch_branch_only`
3. `decision = freeze_full_sb_and_shift_main_queue`
4. `next_main_queue_card = N1.11 / Tachibana detector refinement or backlog retention`

这意味着：

1. `SB` 当前 full detector 路线已经足够明确地进入 `no-go`
2. 但 `SB` family 里还保留了一个窄 `watch branch`
3. 这个 watch branch 只够 backlog / 观察，不够继续占用 `Normandy` 主队列

---

## 4. 为什么当前 full detector 直接 no-go

### 4.1 长窗主读数已经过线地坏

`SB` 当前 formal summary 固定为：

1. `trade_count = 648`
2. `EV = -0.01455`
3. `PF = 2.09091`
4. `MDD = 0.64103`
5. `overlap_rate_vs_bof_control = 0.0`
6. `incremental_buy_trades_vs_bof_control = 648`

这说明：

1. `SB` 的独立性并不是问题
2. 问题出在它虽然高度独立，但 full detector 仍在持续产出负 edge
3. `MDD` 已经大到不能被解释成“只是 rough prototype”

### 4.2 时间切片不是局部事故，而是跨年持续偏负

按 paired trade 重建后，当前 signal-year 读数如下：

| Signal Year | Trade Count | Avg Gross Return | Win Rate | Avg Strength |
|---|---:|---:|---:|---:|
| `2023` | `232` | `-0.01253` | `0.2543` | `0.8359` |
| `2024` | `208` | `-0.02021` | `0.2548` | `0.8351` |
| `2025` | `187` | `-0.00808` | `0.2513` | `0.8569` |
| `2026` | `21` | `+0.01184` | `0.3810` | `0.8569` |

当前正式写死：

1. `meaningful_negative_signal_years = [2023, 2024, 2025]`
2. `meaningful_positive_signal_years = [2026]`

这说明当前 `SB` 的正向读数并没有跨年份站稳，反而是负向切片占主导。

### 4.3 正向环境桶太小，不能拿来给 full detector 洗白

当前环境读数固定为：

1. `best_environment_bucket = BEARISH`
2. `best_environment_trade_count = 19`
3. `best_environment_share = 0.02932`
4. `dominant_environment_bucket = NEUTRAL`
5. `dominant_environment_share = 0.95216`

也就是说：

1. `SB` 唯一正向环境只占总交易的 `2.93%`
2. 真正主导样本的是 `NEUTRAL`
3. 而主导环境本身仍是负 `EV`

因此当前不能把 `SB` 解释成“只是需要更精细 regime filter”，因为正向 bucket 本身太小。

### 4.4 detector 过宽已经不是感觉，而是 formal 事实

当前 pairing diagnostics 固定为：

1. `selected_entry_count = 4157`
2. `buy_fill_count = 648`
3. `executed_entry_count = 648`
4. `paired_trade_count = 648`

这说明：

1. `SB` detector 当前选出了 `4157` 个 selected entries
2. 真正进入买成交的只有 `648`
3. `selected / executed ≈ 6.42x`

因此当前 `SB` 的问题已经不是“轻微偏宽”，而是 full detector 与真实成交之间存在明显脱节。

---

## 5. 为什么仍保留一个窄 watch branch

### 5.1 detector trace 摘要并不支持“越强越好”

当前 selected trace summary 固定为：

1. `avg_trend_gain = 0.27467`
2. `avg_retest_similarity = 0.01709`
3. `avg_w_amplitude = 0.14236`
4. `tight_retest_ratio = 0.64975`
5. `small_w_ratio = 0.24802`
6. `large_w_ratio = 0.47847`
7. `high_trend_ratio = 0.41905`
8. `mid_strength_ratio = 0.47799`

再结合负 trade 样本可见：

`当前 SB 不是“强度越高越安全”，相反，不少最差负样本正落在高 strength / 中大 W / 高 trend gain。`

### 5.2 coarse bucket 已经给出一个可保留的窄分支

当前 `performance_by_w_bucket` 固定为：

1. `small_w = 143 trades / avg_gross_return = +0.00169`
2. `medium_w = 189 trades / avg_gross_return = -0.02477`
3. `large_w = 316 trades / avg_gross_return = -0.01245`

当前 `branch_candidates` 中最强分支固定为：

1. `SB_SMALL_W_MID_STRENGTH`
2. `trade_count = 68`
3. `avg_gross_return = +0.02272`
4. `win_rate = 0.29412`

这说明：

1. `SB` 不是全体完全没救
2. 但正向读数已经明显缩到更窄的 `small_w + mid_strength` 分支
3. 这只够保留成 `watch branch`，还不够继续把 full detector 留在主队列

### 5.3 当前 retained watch branch 的正式身份

当前正式保留的 watch branch 固定为：

1. `retained_watch_branch = SB_SMALL_W_MID_STRENGTH`
2. 定位：`watch_candidate_only`
3. 当前不等于：
   - `new standalone detector`
   - `main-queue retained candidate`
   - `N2 eligible object`

---

## 6. 正式结论

当前 `N1.10` 的正式结论固定为：

1. `SB` 当前 full detector 路线进入 `no-go`
2. `SB` 失败的原因不在独立性，而在：
   - 长窗负 edge
   - 极端 drawdown
   - 跨年负切片
   - 正向环境桶太小
   - detector 过宽
3. `SB_SMALL_W_MID_STRENGTH` 保留为唯一窄 `watch branch`
4. 这个 watch branch 当前只保留 backlog / 回看价值
5. `Normandy` 主队列下一张卡应切到：
   - `N1.11 / Tachibana detector refinement or backlog retention`

换句话说：

`N1.10` 已经把 SB 当前最重要的问题回答成了：full detector 路线 no-go，但 family 内仍有一个窄 watch branch 值得留档。`

---

## 7. 后续动作

对 `SB` 而言，当前后续动作固定为：

1. 冻结 full detector 路线
2. 不再把 `SB` 当作当前第二 alpha 主位竞争者
3. 只保留 `SB_SMALL_W_MID_STRENGTH` 为后续可回看的 micro-contract 候选

对 `Normandy` 主队列而言，当前优先级应固定改写为：

1. `N1.11 / Tachibana detector refinement or backlog retention`
2. `FB_BOUNDARY watch-candidate retention`
3. `SB_SMALL_W_MID_STRENGTH watch-branch backlog`
4. `N2 / controlled exit decomposition` 继续锁住

---

## 8. 一句话结论

`SB` 当前 full detector 路线已经可以正式判为 `no-go`；不过它没有被整个 family 一起判死，`SB_SMALL_W_MID_STRENGTH` 仍被保留为唯一窄 watch branch，但这还不足以继续占用 Normandy 主队列，因此下一张卡应切到 `Tachibana detector refinement or backlog retention`。`
