# Normandy N2A-3 Two-Stage Trailing Probe Record

**日期**: `2026-03-13`  
**阶段**: `Normandy / N2A-3 two-stage trailing probe`  
**对象**: `BOF_CONTROL trailing-stop two-stage preservation probe formal readout`  
**状态**: `Active`

---

## 1. 目标

本文用于把 `Normandy / N2A` 在 `profit-gated` 路线之后继续收窄的第三轮 formal readout 固定下来。

这张 record 只回答三个问题：

1. 在 `PROFIT_GATED_TRAIL_25P` 已被证明“有改善但机制不干净”之后，保留早期 `8% trailing-stop`、只在后段放宽 trailing，能不能产出更干净的 preservation 机制
2. `POST_15P_TRAIL_9P / POST_17_5P_TRAIL_10P / POST_20P_TRAIL_10P` 里，哪一个是当前最像样的两阶段 trailing 候选
3. 本轮结果是否已经足以支持默认 trailing-stop 语义改写，或让 `N2A` 继续向 promotion 方向推进

---

## 2. 参考依据

### 2.1 上游治理口径

1. `normandy/03-execution/13-phase-n2a-targeted-trailing-stop-follow-up-card-20260313.md`
2. `normandy/03-execution/records/13-phase-n2a-targeted-trailing-stop-follow-up-record-20260313.md`
3. `normandy/03-execution/records/14-phase-n2a-2-profit-gated-micro-sweep-record-20260313.md`
4. `normandy/03-execution/records/00-normandy-interim-conclusions-20260312.md`

### 2.2 当前 formal evidence

1. `normandy/03-execution/evidence/normandy_bof_control_fat_tail_preservation_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t003631__bof_control_fat_tail_preservation.json`
2. `normandy/03-execution/evidence/normandy_bof_control_fat_tail_preservation_digest_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t003703__bof_control_fat_tail_preservation_digest.json`

---

## 3. 本轮固定研究范围

本轮 probe 继续固定在同一批 `BOF_CONTROL` 已成交 entry set 上。

硬约束没有变化：

1. 只研究 `CONTROL_REALIZED.exit_reason = TRAILING_STOP` 的 `140` 笔 trade 子集
2. 保留当前 `hard stop = 5%`
3. 保留当前早期 `trail width = 8%`
4. 不改 entry set
5. 不重开 `delay-only family`
6. 不把本轮结果翻译成“默认 trailing-stop 现在就该改写”
7. 不因为本轮结果而解锁 `promotion lane`

因此，本轮只比较 3 个两阶段 trailing 变体：

1. `POST_15P_TRAIL_9P`
2. `POST_17_5P_TRAIL_10P`
3. `POST_20P_TRAIL_10P`

它们的共同结构是：

1. 早期继续沿用当前 `8% trailing-stop`
2. 只有在利润已经进入指定区间后，才把 trailing 放宽到 `9% / 10%`
3. 不把早期 trailing 整段关掉

本轮沿用的路径分类保持不变：

1. `legitimate_protection = 99`
2. `ambiguous_mixed = 22`
3. `fat_tail_winner_cut = 19`

---

## 4. Two-Stage Probe 核心结果

当前 3 个两阶段变体的 formal 读数如下：

| 变体 | Overall PnL Delta vs Control | Overall Capture vs STOP_ONLY | Fat-Tail Capture vs STOP_ONLY | Protection Damage vs STOP_ONLY | 当前判读 |
|---|---:|---:|---:|---:|---|
| `POST_15P_TRAIL_9P` | `+257880.15` | `0.1099` | `0.0970` | `0.0319` | 当前最佳 |
| `POST_20P_TRAIL_10P` | `+236440.49` | `0.1007` | `0.0927` | `0.0410` | 次优 |
| `POST_17_5P_TRAIL_10P` | `+229797.27` | `0.0979` | `0.0920` | `0.0446` | 略弱于 `20P/10P` |

当前 digest 已把排名固定为：

1. `POST_15P_TRAIL_9P`
2. `POST_20P_TRAIL_10P`
3. `POST_17_5P_TRAIL_10P`

也就是说：

1. 当前最佳候选已经从 `profit-gated activation` 转成了 `two-stage trailing loosening`
2. `POST_15P_TRAIL_9P` 在 3 个局部机制里形状最干净
3. 但这 3 个变体都还没有达到 “clean preservation candidate” 的级别

---

## 5. 为什么 `POST_15P_TRAIL_9P` 更干净，但仍然不够

### 5.1 它比 `PROFIT_GATED_TRAIL_25P` 更像“机制改善”，而不是“早期 trailing 直接关掉”

`POST_15P_TRAIL_9P` 当前给出的核心读数是：

1. `overall_total_pnl_delta_vs_control = +257880.15`
2. `overall_capture_share_vs_stop_only = 0.1099`
3. `fat_tail_capture_share_vs_stop_only = 0.0970`
4. `legitimate_protection_damage_share_vs_stop_only = 0.0319`

对比上轮 `PROFIT_GATED_TRAIL_25P`：

1. `POST_15P_TRAIL_9P` 的 `fat-tail capture` 更低：`0.0970 < 0.1744`
2. 但 `protection damage` 也大幅压低：`0.0319 << 0.4684`
3. 它的含义更接近“保留早期保护、只在进入趋势后轻微放宽”，而不是“把早期 trailing 基本关掉去赌大赢家”

因此，本轮可以正式写死：

`two-stage trailing family` 的结构确实比 `25P profit gate` 更干净。

### 5.2 但它仍然没有形成 clean preservation candidate

这一步必须写死，不然后面又会把“更干净”误读成“已经可升格”。

`POST_15P_TRAIL_9P` 的问题是：

1. 它只保住了 `9.70%` 的 fat-tail uplift
2. 它整体只拿回了 `10.99%` 的 `STOP_ONLY` 总 uplift
3. 它虽然明显减少了 protection damage，但改善幅度仍不足以支撑默认语义改写
4. 其余两条近邻候选也没有给出更强、更稳的优势

换句话说：

1. 本轮证明了“更干净的局部机制”是可能存在的
2. 但当前这条最好的机制仍然太弱，不能被写成 `targeted_preservation_candidate_found`
3. `N2A` 目前仍停留在 diagnosis lane，不进入 promotion 解释

因此，本轮最准确的 formal 裁决只能写成：

`no_clean_preservation_candidate_yet`

而不能写成：

`clean_preservation_candidate_found`

---

## 6. 当前 formal readout

本轮 `N2A-3 two-stage trailing probe` 的正式裁决固定为：

1. `best_candidate = POST_15P_TRAIL_9P`
2. `diagnosis = no_clean_preservation_candidate_yet`
3. `decision = hold_n2a_verdict_and_continue_only_if_new_targeted_hypothesis_exists`
4. `default_trailing_stop_rewrite = no`
5. `promotion_lane_unlocked = no`

用一句更完整的话说：

围绕两阶段 trailing 机制做窄 probe 后，`POST_15P_TRAIL_9P` 已经成为当前更干净的局部 preservation 候选，但它仍不足以支持默认 trailing-stop 语义改写，也不足以把 `N2A` 从 targeted diagnosis lane 推进成新的升格通道。

---

## 7. 对 Normandy 主队列意味着什么

当前治理动作固定为：

1. `N2A-3` formal readout 已完成
2. `N2 baseline lane` 继续保持打开
3. `N2A` 当前不再默认沿 `profit-gated 25P` 扩扫
4. 若继续，只允许在出现新的 `targeted mechanism hypothesis` 时再开 follow-up
5. 不把本轮结果翻译成全局 trailing-stop rewrite
6. 不把本轮结果翻译成 `promotion lane` 解锁

---

## 8. 正式结论

当前 `N2A-3 two-stage trailing probe` 的正式结论固定为：

1. `two-stage trailing loosening` 确实比 `PROFIT_GATED_TRAIL_25P` 更像合理的局部机制
2. `POST_15P_TRAIL_9P` 是当前最干净的两阶段 trailing 候选
3. 但它仍然没有形成 `clean preservation candidate`
4. 当前没有证据支持“主线默认 trailing-stop 应立刻改写”
5. 当前也没有证据支持“`N2A` 已经产出可继续升格的 preservation mechanism”
6. `N2 promotion lane` 继续锁住

---

## 9. 一句话结论

`N2A-3` 已经把 fat-tail preservation 从 `profit-gated activation` 继续收窄到两阶段 trailing loosening，并把 `POST_15P_TRAIL_9P` 固定成当前更干净的局部机制；但它仍然不够强，不足以改默认 trailing-stop 语义，也不足以解锁 `promotion lane`。
