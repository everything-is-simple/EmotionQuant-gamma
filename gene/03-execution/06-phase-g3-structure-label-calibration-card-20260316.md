# G3 卡: 结构标签校准

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. 目标

把 `1-2-3 / 2B` 从术语描述升级成可回放、可比较、可审计的正式结构标签。

---

## 2. 本卡范围

1. 固定 `confirmed_turn` 口径
2. 固定 `2B_top / 2B_bottom` 口径
3. 视需要拆出 `123_step1 / step2 / step3`
4. 给 `G6` 提供稳定事件标签

---

## 3. 输入

1. `pivot / wave / event` 管线
2. `l3_gene_event`
3. `G2` 的历史分布带
4. 《专业投机原理》里的 `1-2-3 / 2B` 原始语义

---

## 4. 输出

1. 正式结构标签字典
2. 回放一致性读数
3. 如有必要的检测器修订建议
4. 可供 `G6` 消费的标签快照

---

## 5. 完成标准

1. `1-2-3` 不再只是叙述词
2. `2B` 不再只是粗口径失败突破
3. 标签回放稳定，不依赖人工临时改口径
4. 不破坏 `G0 / G1 / G2` 的对象层主结构

---

## 6. 明确不做

1. 不把 `1-2-3 / 2B` 直接宣布为 alpha
2. 不在本卡大量引入辅助指标做主过滤
3. 不抢做 `GX1`，除非一致性问题已实锤阻塞

---

## 7. 结案结论

本卡已完成。  
当前第四战场已经把 `G3` 所需的结构标签正式接入三层对象：

1. `l3_gene_wave`
   - `turn_confirm_type`
   - `turn_step1_date / turn_step2_date / turn_step3_date`
   - `two_b_confirm_type / two_b_confirm_date`
2. `l3_gene_event`
   - `event_family`
   - `structure_direction`
   - `anchor_wave_id`
   - 正式事件类型：`123_STEP1 / 123_STEP2 / 123_STEP3 / 2B_TOP / 2B_BOTTOM`
3. `l3_stock_gene`
   - `latest_confirmed_turn_type / latest_confirmed_turn_date`
   - `latest_two_b_confirm_type / latest_two_b_confirm_date`

截至 `2026-02-24` 的主库真实回放结果表明：

1. `1-2-3` 已不再只是粗 `reversal_tag` 叙述，而是正式 `confirmed_turn` 结构
2. `2B` 已不再只是附带布尔标记，而是正式 `2B_TOP / 2B_BOTTOM` 事件
3. 当前计数一致性已经足以支持进入 `G4`，暂未发现必须立刻打开 `GX1` 的阻塞级问题

下一张主线卡应按顺序进入 `G4 / self-history ruler validation`。

---

## 8. 文档入口

1. 配套 record：[`records/06-phase-g3-structure-label-calibration-record-20260316.md`](records/06-phase-g3-structure-label-calibration-record-20260316.md)
2. 配套 evidence：[`evidence/06-phase-g3-structure-label-calibration-evidence-20260316.md`](evidence/06-phase-g3-structure-label-calibration-evidence-20260316.md)
