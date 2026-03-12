# Normandy N2A-2 Profit-Gated Micro-Sweep Record

**日期**: `2026-03-13`  
**阶段**: `Normandy / N2A-2 profit-gated micro-sweep`  
**对象**: `BOF_CONTROL trailing-stop fat-tail preservation micro-sweep formal readout`  
**状态**: `Active`

---

## 1. 目标

本文用于把 `Normandy / N2A targeted trailing-stop follow-up` 继续收窄后的第二轮 formal readout 固定下来。

这张 record 只回答三个问题：

1. 在 `small_cluster_of_outlier_truncation` 已经成立之后，`profit-gated trailing activation` 能不能保住更多 fat-tail uplift
2. 围绕 `25%` 附近做窄 sweep 时，哪一个 gate 是当前最平衡的 preservation 候选
3. 本轮结果是否已经足以支持默认 trailing-stop 语义改写

---

## 2. 参考依据

### 2.1 上游治理口径

1. `normandy/03-execution/13-phase-n2a-targeted-trailing-stop-follow-up-card-20260313.md`
2. `normandy/03-execution/records/13-phase-n2a-targeted-trailing-stop-follow-up-record-20260313.md`
3. `normandy/03-execution/records/00-normandy-interim-conclusions-20260312.md`

### 2.2 当前 formal evidence

1. `normandy/03-execution/evidence/normandy_bof_control_fat_tail_preservation_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t233623__bof_control_fat_tail_preservation.json`
2. `normandy/03-execution/evidence/normandy_bof_control_fat_tail_preservation_digest_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t233639__bof_control_fat_tail_preservation_digest.json`

---

## 3. 本轮固定研究范围

本轮 micro-sweep 继续固定在同一批 `BOF_CONTROL` 已成交 entry set 上。

硬约束没有变化：

1. 只研究 `CONTROL_REALIZED.exit_reason = TRAILING_STOP` 的 `140` 笔 trade 子集
2. 保留当前 `hard stop = 5%`
3. 保留当前 `trail width = 8%`
4. 不改 entry set
5. 不重开 `delay-only family`
6. 不把本轮结果翻译成“默认 trailing-stop 现在就该改写”

因此，本轮只比较 4 个 `profit-gated trailing activation` 变体：

1. `PROFIT_GATED_TRAIL_22_5P`
2. `PROFIT_GATED_TRAIL_25P`
3. `PROFIT_GATED_TRAIL_27_5P`
4. `PROFIT_GATED_TRAIL_30P`

本轮沿用的路径分类保持不变：

1. `legitimate_protection = 99`
2. `ambiguous_mixed = 22`
3. `fat_tail_winner_cut = 19`

---

## 4. Micro-Sweep 核心结果

当前 4 个 gate 的 formal 读数如下：

| 变体 | Overall PnL Delta vs Control | Overall Capture vs STOP_ONLY | Fat-Tail Capture vs STOP_ONLY | Protection Damage vs STOP_ONLY | 当前判读 |
|---|---:|---:|---:|---:|---|
| `PROFIT_GATED_TRAIL_22_5P` | `-50648.06` | `0.0000` | `0.0708` | `0.4371` | 已退化，不成立 |
| `PROFIT_GATED_TRAIL_25P` | `+245488.53` | `0.1046` | `0.1744` | `0.4684` | 当前最佳 |
| `PROFIT_GATED_TRAIL_27_5P` | `+211577.35` | `0.0901` | `0.1749` | `0.5101` | 次优，但 protection damage 更重 |
| `PROFIT_GATED_TRAIL_30P` | `+184897.61` | `0.0788` | `0.1763` | `0.5730` | 仍有 uplift，但 trade-off 更差 |

当前 digest 已把排名固定为：

1. `PROFIT_GATED_TRAIL_25P`
2. `PROFIT_GATED_TRAIL_27_5P`
3. `PROFIT_GATED_TRAIL_30P`
4. `PROFIT_GATED_TRAIL_22_5P`

也就是说：

1. `22.5P` 已经退化到 `overall delta < 0`
2. `25P` 是当前最平衡的 gate
3. `27.5P / 30P` 虽然略多保住一点 fat-tail uplift，但会复制出更重的 protection damage

---

## 5. 为什么 `25P` 是当前最佳，但仍然不够

### 5.1 它确实是当前最平衡的 preservation 候选

`PROFIT_GATED_TRAIL_25P` 当前给出的核心读数是：

1. `overall_total_pnl_delta_vs_control = +245488.53`
2. `overall_capture_share_vs_stop_only = 0.1046`
3. `fat_tail_capture_share_vs_stop_only = 0.1744`
4. `legitimate_protection_damage_share_vs_stop_only = 0.4684`

这说明：

1. 它不是纯退化方案
2. 它比 `22.5P` 更能保住 fat-tail uplift
3. 它比 `27.5P / 30P` 更少复制 protection damage

因此，本轮把它固定成 `best_candidate = PROFIT_GATED_TRAIL_25P` 是成立的。

### 5.2 但它仍然只是 partial trade-off

这一步必须写死，不然后面又会把“当前最佳”误读成“已经可升格”。

`25P` 的问题是：

1. 它只保住了 `17.44%` 的 fat-tail uplift
2. 它整体只拿回了 `10.46%` 的 `STOP_ONLY` 总 uplift
3. 它却复制回了 `46.84%` 的 legitimate protection damage

换句话说：

1. 它能证明 `profit gate` 这条机制线比 `delay-only` 更值得继续挖
2. 但它离“既明显保住 fat-tail，又不明显破坏 protection”还差得远
3. 它不是 clean preservation candidate

因此，本轮最准确的 formal 裁决仍然只能写成：

`partial_preservation_tradeoff_only`

而不能写成：

`targeted_preservation_candidate_found`

---

## 6. 当前 formal readout

本轮 `N2A-2 profit-gated micro-sweep` 的正式裁决固定为：

1. `best_candidate = PROFIT_GATED_TRAIL_25P`
2. `diagnosis = partial_preservation_tradeoff_only`
3. `default_trailing_stop_rewrite = no`
4. `delay_only_family_priority = no`
5. `profit_gated_family_keep_research = yes`
6. `promotion_lane_unlocked = no`

用一句更完整的话说：

围绕 `25%` 附近做窄 micro-sweep 后，`PROFIT_GATED_TRAIL_25P` 已经成为当前最平衡的 preservation 候选，但它仍然只给出部分 trade-off 改善，不能被翻译成默认 trailing-stop 语义改写，也不能借机解锁 `N2 promotion lane`。

---

## 7. 对 Normandy 主队列意味着什么

当前治理动作固定为：

1. `N2A-2` formal readout 已完成
2. `N2 baseline lane` 继续保持打开
3. `N2A` 当前不再做宽泛的 fat-tail preservation 混扫
4. 如果继续，只允许围绕 `PROFIT_GATED_TRAIL_25P` 做更窄的 mechanism-specific follow-up
5. 不重开 entry family
6. 不把本轮结果翻译成全局 trailing-stop rewrite
7. `promotion lane` 继续锁住

---

## 8. 正式结论

当前 `N2A-2 profit-gated micro-sweep` 的正式结论固定为：

1. `profit-gated trailing activation` 确实比 `delay-only` 更值得继续研究
2. `PROFIT_GATED_TRAIL_25P` 是当前最平衡的 preservation 候选
3. 但它仍然只是 `partial trade-off`
4. 当前没有证据支持“已经找到 clean preservation candidate”
5. 当前也没有证据支持“主线默认 trailing-stop 应立刻改写”
6. `N2 promotion lane` 继续锁住

---

## 9. 一句话结论

`N2A-2` 已经把 fat-tail preservation 继续收窄到 `profit-gated trailing` 这条线，并把 `25P` 固定成当前最佳候选；但它仍然只是 partial trade-off，不是 clean candidate，因此还不能改默认语义，也不能解锁 promotion lane。
