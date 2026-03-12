# Normandy N2 BOF Control Baseline Exit Decomposition Record

**日期**：`2026-03-13`  
**阶段**：`Normandy / N2 baseline lane`  
**对象**：`BOF_CONTROL baseline diagnosis formal readout`  
**状态**：`Active`

---

## 1. 目标

本文用于把 `Normandy / N2 baseline lane` 围绕 `BOF_CONTROL` 的第一轮长窗 formal readout 固定下来。

本记录只回答三个问题：

1. `BOF_CONTROL` 当前更像是 `买错`，还是 `卖坏`
2. 当前统一 Broker 出场语义是否正在系统性吞掉 `BOF_CONTROL` 已被证明的 raw alpha
3. `execution friction` 是否已经足够大，足以成为当前第一主因

---

## 2. 参考依据

### 2.1 上游治理口径

1. `normandy/03-execution/12-phase-n2-bof-control-baseline-exit-decomposition-card-20260313.md`
2. `normandy/03-execution/records/01-phase-n1-bof-conclusion-record-20260312.md`
3. `normandy/03-execution/records/10-phase-n1-12-bof-pinbar-stability-or-no-go-record-20260313.md`
4. `normandy/03-execution/records/00-normandy-interim-conclusions-20260312.md`

### 2.2 当前 formal evidence

1. `normandy/03-execution/evidence/normandy_bof_control_exit_matrix_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t213635__bof_control_exit_matrix.json`
2. `normandy/03-execution/evidence/normandy_bof_control_exit_digest_dtt_v0_01_dtt_pattern_only_w20230103_20260224_t215256__bof_control_exit_digest.json`

### 2.3 实现口径说明

本轮 `N2 baseline lane` 使用的是：

1. `same-entry-set` 口径
2. 固定 `BOF_CONTROL` 已成交 entry set
3. 只改 exit layer，不回头改 entry layer
4. 修正后的 paired lifecycle 读取口径：`entry_seq` 只对已成交 `BUY` 事件排序，不再混入未成交 detected signals

换句话说：

`本记录使用的是修正 pairing 后的正式重跑结果，不采用早先那份 262 笔的歪口径产物。`

---

## 3. N2 baseline lane 核心结果

当前 formal digest 已把本轮结论固定为：

1. `control_label = CONTROL_REALIZED`
2. `best_counterfactual_label = STOP_ONLY`
3. `diagnosis = exit_damage_mixed`
4. `decision = keep_baseline_lane_open_but_do_not_rewrite_priority_yet`

当前 control baseline 读数固定为：

| 对象 | Trade Count | EV | PF | Total PnL | Avg Hold Days |
|---|---:|---:|---:|---:|---:|
| `CONTROL_REALIZED` | `277` | `0.01609` | `2.61207` | `405776.24` | `15.42` |
| `TIGHT_EXIT` | `277` | `0.00178` | `1.96208` | `-488.78` | `8.00` |
| `LOOSE_EXIT` | `277` | `0.02293` | `3.01548` | `567123.98` | `27.68` |
| `STOP_ONLY` | `277` | `0.12492` | `15.01630` | `2753012.79` | `69.34` |
| `TRAIL_ONLY` | `277` | `0.01324` | `2.07447` | `370269.17` | `18.42` |

control 的 exit reason breakdown 固定为：

1. `TRAILING_STOP = 140`
2. `STOP_LOSS = 129`
3. `FORCE_CLOSE = 8`

---

## 4. 当前到底更像 `买错` 还是 `卖坏`

### 4.1 不是 `execution friction` 主导

当前正式可以写死：

1. `CONTROL_REALIZED.failed_exit_attempts_total = 0`
2. 四个 counterfactual 变体的 `failed_exit_attempts_total` 也都是 `0`
3. 本轮没有形成 `halt / limit-down / no-market-data` 持续堆积导致的 exit failure 主因

因此：

`execution friction` 当前不是 `BOF_CONTROL` 这轮 baseline diagnosis 的主因。

### 4.2 也不是“entry 完全买错”

当前 `BOF_CONTROL` 本身仍然保持：

1. `trade_count = 277`
2. `EV = +0.01609`
3. `PF = 2.61207`
4. `total_pnl = 405776.24`

这说明：

1. `BOF_CONTROL` 的 raw alpha 仍然存在
2. 当前问题不能被粗暴写成 `entry invalid`
3. `买错` 不是本轮最准确的 formal 裁决

### 4.3 当前真正可见的伤害，集中在 trailing-stop 路径

最关键的对照不是 `TRAIL_ONLY`，而是：

1. `STOP_ONLY` 相对 control：
   - `EV delta = +0.10883`
   - `PF delta = +12.40423`
   - `PnL delta = +2347236.55`
   - `changed_exit_count_vs_control = 140`
   - `later_exit_count_vs_control = 139`
2. `LOOSE_EXIT` 相对 control：
   - `EV delta = +0.00685`
   - `PF delta = +0.40341`
   - `PnL delta = +161347.74`
3. `TIGHT_EXIT` 相对 control：
   - `EV delta = -0.01431`
   - `PF delta = -0.64999`
   - `PnL delta = -406265.02`
4. `TRAIL_ONLY` 相对 control：
   - `EV delta = -0.00285`
   - `PF delta = -0.53760`
   - `PnL delta = -35507.07`

这组读数说明：

1. 当前 exit damage 确实存在，不是完全无关
2. 真正可疑的不是 `hard stop` 本身，而是当前 `trailing-stop` 对一批大赢家的过早收割
3. 一旦把 trailing-stop 压力拿掉，而保留 `5% hard stop`，收益会出现极大抬升
4. 单独去掉 hard stop、只保留 trailing-stop，并没有更好，反而略差

因此本轮最准确的 exit-level 诊断应写成：

`当前 BOF_CONTROL 的主要 exit 伤害，更像集中型 trailing-stop damage，而不是 execution friction，也不是 hard-stop 本身。`

### 4.4 为什么 formal 结论仍然是 `mixed`

虽然 `STOP_ONLY` 的 uplift 很大，但 digest 仍然没有把它直接裁成 `exit_damage_material -> rewrite priority`，原因也必须写死：

1. `STOP_ONLY` 的正收益提升高度集中在少数 fat-tail winners
2. 它虽然总收益大幅更高，但 `improved_trade_count_vs_control = 32`，同时 `worsened_trade_count_vs_control = 107`
3. 这说明当前 exit 问题不是“所有 trade 都被 uniform 地卖坏了”
4. 更准确的说法是：
   - `当前 trailing-stop 可能正在错杀少数超大赢家`
   - `但这不是一个可以直接无脑全局放宽的 uniform answer`

因此本轮 formal digest 才会固定为：

`exit_damage_mixed`

而不是：

`exit_damage_material`

---

## 5. 当前 formal readout

本轮 `N2 baseline lane` 的正式裁决固定为：

1. `buy_wrong = no`
2. `execution_friction_material = no`
3. `sell_bad = partially_yes`
4. `sell_bad` 当前主要集中在 `trailing-stop path`
5. 但这种伤害当前仍属于 `mixed / concentrated damage`，还不足以单独改写整个主队列优先级

用一句更完整的话说：

`BOF_CONTROL` 当前不是“买错了”，而是“entry 本身有 alpha，但当前 trailing-stop 语义可能正在集中性地提前砍掉少数超大赢家”；不过这条证据还不支持立刻把全部研究重心粗暴改写成 exit-only。

---

## 6. 对 Normandy 主队列意味着什么

当前治理动作固定为：

1. `N2 baseline lane` 第一轮 formal readout 已完成
2. `N2 promotion lane` 继续锁住
3. 不把 `STOP_ONLY` 的巨大 uplift 误读成“主线现在就该取消 trailing-stop”
4. 不把 baseline diagnosis 误读成 branch promotion
5. `Tachibana` 继续留在 backlog / refinement 队列，不在本记录中抢主位

如果继续沿 `N2 baseline lane` 往下挖，下一步只能是：

`针对 trailing-stop 做更细的 targeted decomposition，而不是重开 entry family 混战。`

---

## 7. 正式结论

当前 `N2 baseline lane` 的正式结论固定为：

1. `BOF_CONTROL` 当前不是 `entry invalid`
2. `execution friction` 当前不是第一主因
3. `exit damage` 当前确实存在，而且主要指向 `trailing-stop`
4. 但这份伤害目前仍然属于 `mixed / concentrated damage`
5. 当前最准确的治理裁决应固定为：
   - `keep_bof_control_as_baseline`
   - `keep_n2_baseline_lane_open`
   - `promotion_lane_still_locked`
   - `do_not_rewrite_main_queue_priority_yet`

---

## 8. 一句话结论

`N2 baseline lane` 已经把这个问题正式读出来了：`BOF_CONTROL` 不是买错，execution friction 也不是主因；当前真正可疑的是 trailing-stop 对少数大赢家的集中性伤害，但证据仍属于 mixed signal，所以 baseline lane 保持打开，promotion lane 继续锁住。`
