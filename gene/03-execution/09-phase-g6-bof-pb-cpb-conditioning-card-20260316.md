# G6 卡: BOF / BPB / PB / TST / CPB 条件层统计

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. 目标

回答：

`接入第四战场历史尺后，BOF / BPB / PB / TST / CPB 在什么波段环境下更值得出手？`

---

## 2. 本卡范围

1. 把第四战场标签回灌到 Normandy 样本
2. 比较 `BOF / BPB / PB / TST / CPB` 在不同历史尺位置下的表现
3. 输出条件层解释读数
4. 为第二战场提供“何时更值得打”的附加约束

---

## 3. 输入

1. Normandy 主信号样本
2. `l3_stock_gene` 当前波段快照
3. `wave_age_band`
4. `1-2-3 / 2B` 正式标签
5. 连续上涨/下跌天数等短期条件层统计

---

## 4. 输出

1. `BOF / BPB / PB / TST / CPB` 条件层读数表
2. 分层后的 hit rate / payoff / MAE / MFE
3. 对早期回调、复杂回调、失败突破的环境解释
4. 回灌 Normandy 的约束建议

---

## 5. 完成标准

1. 至少完成 `BOF / BPB / PB / TST / CPB` 五类信号的条件分层比较
2. 至少有一个第四战场标签显著改善读数
3. 结果能回灌第二战场，但不硬改主 alpha 来源
4. 不碰第三战场的 sizing / partial-exit 设计

---

## 6. 明确不做

1. 不在本卡重做 Normandy alpha provenance
2. 不在本卡讨论 partial-exit
3. 不把条件层直接写死成硬过滤器

---

## 7. 结案结论

本卡已完成。  
当前第四战场已经把 `G6` 所需的条件层正式接入：

1. `Store` schema 保持在 `v10`
2. `l3_gene_conditioning_eval` 继续作为第四战场条件层正式表
3. `compute_gene_conditioning()` 现已直接从 `l2_stock_adj_daily` 重构 `BOF / BPB / PB / TST / CPB` 五类 detector trigger 样本，并按以下标签回灌条件层：
   - `current_wave_direction`
   - `current_wave_age_band`
   - `current_wave_magnitude_band`
   - `latest_confirmed_turn_type`
   - `latest_two_b_confirm_type`
   - `streak_bucket`
4. 每次统计固定产出：
   - `sample_size / hit_rate / avg_forward_return_pct / median_forward_return_pct`
   - `avg_mae_pct / avg_mfe_pct`
   - `delta_vs_pattern_baseline`
   - `edge_tag`
5. 第四战场现已补齐：
   - `gene/03-execution/evidence/`
   - `09-phase-g6-five-pattern-conditioning-evidence-20260316.md`

截至 `2026-02-24` 的主库真实读数表明：

1. `BOF` 仍是五类里 baseline 最强的模式，且 `DOWN + UP_1` 最值得出手，`UP / DOWN_1 / FLAT` 更差
2. `BPB` 已进入正式条件层，但当前主库样本只有 `62`，现阶段只能作为 sparse watch readout，不能硬写成强约束
3. `PB` baseline 仍偏弱，只在 `DOWN` 背景以及 `NORMAL / EXTREME` age band 下出现温和改善
4. `TST` 已形成大样本条件层，当前在 `UP_2_3` 以及 `STRONG / EXTREME magnitude` 下改善，`DOWN_2_3` 更差
5. `CPB` 仍更偏 fresh-base / 无结构确认环境，`NONE / UNSCALED / UP_4P` 更好，而 `EXTREME / 2B_TOP` 更差
6. 这些读数当前应作为条件解释层与优先级约束，不应直接升格为硬过滤器

下一张主线卡应按顺序进入 `G7 / MSS-IRS refactor-or-retire decision`。
