# Normandy N2A Targeted Trailing-Stop Follow-Up Record

**日期**：`2026-03-13`  
**阶段**：`Normandy / N2A targeted trailing-stop follow-up`  
**对象**：`BOF_CONTROL trailing-stop path decomposition formal readout`  
**状态**：`Active`

---

## 1. 目标

本文用于把 `Normandy / N2A targeted trailing-stop follow-up` 围绕 `BOF_CONTROL` 的第一轮长窗 formal readout 固定下来。

本记录只回答三个问题：

1. `TRAILING_STOP` 触发的 `BOF_CONTROL` trade 里，当前 uplift 更像结构性可重复问题，还是少数极端样本
2. 当前 `STOP_ONLY` 的巨大 uplift，到底更像 `repeatable trend-premature-exit`，还是 `small cluster of outlier truncation`
3. 本轮结论是否足以支持全局改写当前主线 trailing-stop 语义

---

## 2. 参考依据

### 2.1 上游治理口径

1. `normandy/03-execution/13-phase-n2a-targeted-trailing-stop-follow-up-card-20260313.md`
2. `normandy/03-execution/records/12-phase-n2-bof-control-baseline-exit-decomposition-record-20260313.md`
3. `normandy/03-execution/records/00-normandy-interim-conclusions-20260312.md`

### 2.2 当前 formal evidence

1. `normandy/03-execution/evidence/normandy_bof_control_trailing_stop_followup_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t222104__bof_control_trailing_stop_followup.json`
2. `normandy/03-execution/evidence/normandy_bof_control_trailing_stop_digest_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t222124__bof_control_trailing_stop_digest.json`

---

## 3. N2A follow-up 核心结果

当前 formal digest 已把本轮结论固定为：

1. `diagnosis = small_cluster_of_outlier_truncation`
2. `decision = investigate_fat_tail_preservation_before_global_change`
3. `followup_status = completed`

本轮研究对象固定为：

1. `BOF_CONTROL` 已成交 entry set 中
2. `CONTROL_REALIZED.exit_reason = TRAILING_STOP` 的子集
3. 在相同 entry set 下比较 `LOOSE_EXIT / STOP_ONLY / TRAIL_ONLY`

当前 trailing-stop 子集读数固定为：

| 对象 | Trade Count | EV | PF | Total PnL | Avg Hold Days |
|---|---:|---:|---:|---:|---:|
| `CONTROL_TRAILING_STOP_SUBSET` | `140` | `0.09647` | `5.45803` | `1145079.06` | `23.46` |
| `LOOSE_EXIT` | `140` | `0.10792` | `5.07321` | `1261672.95` | `36.58` |
| `STOP_ONLY` | `140` | `0.31180` | `17.39552` | `3492315.61` | `130.14` |
| `TRAIL_ONLY` | `140` | `0.09647` | `5.45803` | `1145079.06` | `23.46` |

路径分类统计固定为：

1. `legitimate_protection = 99`
2. `fat_tail_winner_cut = 19`
3. `ambiguous_mixed = 22`
4. `repeatable_trend_premature_exit = 0`

收益集中度读数固定为：

1. `positive_stop_only_delta_total = 3238766.18`
2. `top10_positive_delta_share = 0.74879`
3. `fat_tail_winner_cut_delta_share = 0.93408`
4. `repeatable_trend_delta_share = 0.0`

---

## 4. 当前 trailing-stop 伤害到底是什么形状

### 4.1 不是整条路径 uniformly 卖坏

如果当前 trailing-stop 是一条可重复、广泛存在的 trend-premature-exit 机制，那么本轮应当看到：

1. `repeatable_trend_premature_exit` 占比显著
2. `LOOSE_EXIT` 能在大量样本上稳定改善
3. 正向 uplift 不会高度集中在极少数 trade

但当前长窗 formal readout 给出的结果正相反：

1. `repeatable_trend_premature_exit_count = 0`
2. `LOOSE_EXIT` 虽略有改善，但远弱于 `STOP_ONLY`
3. `STOP_ONLY` 的正向 uplift 有 `74.88%` 集中在 top10 案例中
4. `fat_tail_winner_cut` 仅 `19` 笔，却贡献了 `93.41%` 的正向 delta

因此：

`当前 trailing-stop 的伤害，不像一条普遍、均匀、可直接全局放宽的 repeatable exit bug。`

### 4.2 当前更像少数 fat-tail winners 被提前砍掉

本轮最强的案例结构都具备同样特征：

1. `control` 在较早时点以 `TRAILING_STOP` 出场
2. `STOP_ONLY` 会把它延长成更晚的 `FORCE_CLOSE` 大赢家
3. `TRAIL_ONLY` 基本不改善，说明问题不在 hard-stop 被误杀
4. `LOOSE_EXIT` 只对个别样本有有限帮助，无法复制 `STOP_ONLY` 的极大 uplift

这说明：

1. 当前主要损失并不来自 `hard stop` 本身
2. 当前最可疑的是 `trailing-stop` 在极少数长趋势赢家上过早截断持仓
3. 这些案例是高价值样本，但并不代表整个 `TRAILING_STOP` 子集都该被统一重写

因此本轮最准确的 formal 裁决应写成：

`当前 trailing-stop damage 主要表现为 small cluster of fat-tail outlier truncation。`

### 4.3 为什么不能直接把结论翻译成“取消 trailing-stop”

这一步必须写死，不然后续治理会跑偏。

虽然 `STOP_ONLY` 的 uplift 很大，但当前同样存在：

1. `legitimate_protection = 99`
2. `negative_stop_only_case_count = 107`
3. `LOOSE_EXIT` 并没有复制出同等级别的系统性收益改善

这说明：

1. 当前 trailing-stop 在大多数样本上仍然承担了真实保护作用
2. 真正的问题集中在少数极高价值趋势赢家
3. 直接全局取消 trailing-stop，会把 `N2A` 的 targeted diagnosis 误读成 global rewrite

因此本轮 formal record 必须明确写死：

`N2A 的结论不支持当前主线立刻全局取消 trailing-stop。`

---

## 5. 当前 formal readout

本轮 `N2A targeted trailing-stop follow-up` 的正式裁决固定为：

1. `global_trailing_stop_rewrite = no`
2. `repeatable_trend_premature_exit_pattern = no`
3. `small_cluster_of_outlier_truncation = yes`
4. `primary_follow_up_direction = fat_tail_preservation`
5. `promotion_lane_unlocked = no`

用一句更完整的话说：

`BOF_CONTROL` 当前最可疑的 exit 伤害，不是大面积、可重复、均匀存在的 trailing-stop 结构性失效，而是少数 fat-tail winners 被提前砍掉；因此下一步若继续，只能做 targeted fat-tail preservation decomposition，而不是全局改写默认 trailing-stop 语义。

---

## 6. 对 Normandy 主队列意味着什么

当前治理动作固定为：

1. `N2A` 第一轮 formal readout 已完成
2. `N2 baseline lane` 继续保持打开，但当前结论从 `mixed trailing-stop damage` 细化为 `small cluster of outlier truncation`
3. `N2 promotion lane` 继续锁住
4. 不把 `N2A` 结果误读成 branch promotion
5. 不把 `STOP_ONLY` 的 uplift 误读成主线默认参数应该立刻改写

如果继续沿这条 lane 往下挖，下一步只应该是：

`针对 fat-tail preservation 做更细的 targeted exit semantics decomposition。`

---

## 7. 正式结论

当前 `N2A targeted trailing-stop follow-up` 的正式结论固定为：

1. `TRAILING_STOP` 子集内确实存在可观 uplift
2. 这份 uplift 高度集中在少数 fat-tail winners
3. 当前没有证据支持“repeatable trend-premature-exit 是普遍主因”
4. 当前更准确的裁决是：`small_cluster_of_outlier_truncation`
5. 当前最准确的治理动作应固定为：
   - `keep_bof_control_as_baseline`
   - `keep_n2_baseline_lane_open`
   - `refine_trailing_stop_follow_up_toward_fat_tail_preservation`
   - `promotion_lane_still_locked`
   - `do_not_globally_rewrite_trailing_stop_yet`

---

## 8. 一句话结论

`N2A` 已经把 `BOF_CONTROL` 的 trailing-stop 问题正式读细了：当前不是“整个 trailing-stop 机制都在系统性卖坏”，而是“少数 fat-tail winners 被提前砍掉”；所以可以继续深挖 fat-tail preservation，但不能据此直接全局取消 trailing-stop。`
