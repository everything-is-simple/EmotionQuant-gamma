# Normandy N1.12 BOF Pinbar Stability Or No-Go Record

**日期**：`2026-03-13`  
**阶段**：`Normandy / N1.12`  
**对象**：`BOF retained branch stability or no-go formal readout`  
**状态**：`Active`

---

## 1. 目标

本文用于把 `Normandy / N1.12` 的 `BOF retained branch stability or no-go` 结论固定下来。

本记录只回答两个问题：

1. `N1.11` retained branch 是否已经足够稳定、足够纯，值得打开 `N2 / controlled exit decomposition`
2. 若答案是否定，`BOF family` 当前应如何收口

---

## 2. 参考依据

### 2.1 上游结论

1. `normandy/03-execution/records/09-phase-n1-11-bof-pinbar-quality-provenance-record-20260313.md`
2. `normandy/03-execution/10-phase-n1-12-bof-pinbar-stability-or-no-go-card-20260312.md`

### 2.2 当前证据

1. `normandy/03-execution/evidence/normandy_bof_quality_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t132536__bof_quality_matrix.json`
2. `normandy/03-execution/evidence/normandy_bof_quality_digest_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t143141__bof_quality_digest.json`
3. `normandy/03-execution/evidence/normandy_bof_quality_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t132536__bof_quality_stability_report.json`

---

## 3. N1.12 核心结果

`bof_quality_stability_report` 当前已经把本轮结论固定为：

1. `retained_branch_label = BOF_KEYLEVEL_PINBAR`
2. `stability_status = branch_no_go`
3. `decision = branch_no_go_keep_bof_control`
4. `stability_flags = [negative_signal_year_slices, single_bucket_dependency]`

这意味着：

1. `BOF_KEYLEVEL_PINBAR` 虽然在 `N1.11` 中成为 retained branch
2. 但它没有通过稳定性与 purity 审核
3. 因此当前不能打开 `N2`
4. `BOF_CONTROL` 继续保持 `Normandy` 唯一 baseline

---

## 4. retained branch 当前为什么 formal no-go

### 4.1 跨年切片没有站稳

当前 signal-year slices 固定为：

| Signal Year | Trade Count | Avg Gross Return | Win Rate | Avg Quality Score |
|---|---:|---:|---:|---:|
| `2023` | `4` | `-0.01224` | `0.2500` | `84.85341` |
| `2024` | `10` | `+0.08715` | `0.6000` | `80.01161` |
| `2025` | `6` | `-0.01476` | `0.5000` | `82.66704` |
| `2026` | `1` | `+0.00598` | `1.0000` | `75.24432` |

当前正式写死：

1. `meaningful_negative_signal_years = [2023, 2025]`
2. `meaningful_positive_signal_years = [2024]`

这说明：

1. retained branch 的正向读数没有跨年稳定铺开
2. 真正能撑住整条分支的主要是 `2024`
3. `2023 / 2025` 已经形成带样本的负切片

### 4.2 它对单一环境桶依赖过强

当前环境读数固定为：

1. `best_environment_bucket = NEUTRAL`
2. `best_environment_trade_count = 20`
3. `dominant_environment_share = 0.95238`

当前 retained branch 的环境 breakdown 只有两桶：

1. `NEUTRAL`
   - `trade_count = 20`
   - `EV = +0.03943`
   - `PF = 1.98982`
2. `BULLISH`
   - `trade_count = 1`
   - `EV = -0.08408`
   - `PF = 0.0`

这说明：

1. retained branch 的 edge 基本全部压在 `NEUTRAL`
2. 一旦离开主环境桶，当前没有证据证明它还能稳定存活
3. 因此 `single_bucket_dependency` 不是修辞，而是 formal stability flag

### 4.3 retained branch 太窄，不足以支撑 N2

当前 candidate summary 固定为：

1. `trade_count = 21`
2. `trade_share_vs_bof_control = 0.07581`
3. `selected_to_fill_ratio = 1.0`
4. `incremental_buy_trades_vs_bof_control = 6`

这说明：

1. 它的 selected / executed gap 并不坏
2. 但它在当前系统里的 share 仍然过窄
3. 这种窄分支即使有局部高质量表现，也不足以在跨年不稳的情况下直接打开 `N2`

### 4.4 最差负样本并没有被隔离在单一点位事故

当前 negative examples 包括：

1. `2023-03-06 / 300750 / -7.29%`
2. `2024-01-25 / 300015 / -8.25%`
3. `2024-06-26 / 601127 / -6.26%`
4. `2025-07-02 / 002455 / -6.15%`
5. `2025-10-27 / 689009 / -7.69%`
6. `2025-12-08 / 002402 / -7.78%`

这说明：

`当前 retained branch 的负 trade 不是只坏在一个季度或单次 accident，而是跨年份、跨样本持续存在。`

---

## 5. 为什么当前必须回到 `BOF_CONTROL`

`N1.12` 当前 formal 结论不是“这个 branch 没有任何价值”，而是：

1. 它不足以成为 `N2 eligible object`
2. 它不足以改写 `BOF_CONTROL` 的唯一 baseline 地位
3. 它目前更适合被记作：
   - `retained_once_but_not_stable_enough`
   - `branch_no_go`

也就是说：

`N1.12` 回到 `BOF_CONTROL`，不是因为 BOF quality split 完全没有信息，而是因为最好的 retained branch 依然没通过 stability gate。`

---

## 6. 正式结论

当前 `N1.12` 的正式结论固定为：

1. `BOF_KEYLEVEL_PINBAR` 虽然在 `N1.11` 中成为 retained branch，但当前正式 `branch_no_go`
2. `BOF family` 当前没有任何 branch 达到 `N2` 开放门槛
3. 当前最准确的 family-level 裁决应固定为：
   - `keep_bof_control_baseline_only`
   - `hold_n2`
   - `end_current_bof_quality_branch_promotion`
4. `Normandy` 当前不再继续推进这支 retained branch

换句话说：

`N1.12` 已经把“BOF family 里最好的 retained branch 能不能进入 N2”这个问题正式回答成了否定。`

---

## 7. 后续动作

对 `BOF family` 而言，当前后续动作固定为：

1. 结束 `BOF_KEYLEVEL_PINBAR` 的继续升格
2. 保持 `BOF_CONTROL` 为唯一 baseline / control
3. 不把 `BOF quality split` 的局部亮点误读成“已经可以开 exit decomposition”

对 `Normandy` 主队列而言，当前后续动作固定为：

1. `N2 / controlled exit decomposition` 继续锁住
2. 主队列不再围绕 `BOF quality branch promotion` 继续前推
3. 后续研究转向：
   - `Tachibana refinement or backlog retention`
   - 观察池与后备研究队列的治理收口

---

## 8. 一句话结论

`N1.12` 已经把 BOF family 这场仗读到头了：`BOF_KEYLEVEL_PINBAR` 虽然是最好的 retained branch，但它依然没有跨过稳定性门槛，因此当前正式结论只能是 `branch_no_go, keep BOF_CONTROL as sole baseline`。`
