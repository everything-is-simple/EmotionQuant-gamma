# G2 卡: 历史寿命分布与 65/95 校准

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. 目标

把 `magnitude` 与 `duration` 的历史分布正式做成第四战场的“历史尺”，回答：

`当前这段波段，在它自己的历史分布里，是普通、强，还是极端？`

---

## 2. 本卡范围

1. 建立 `lifespan distribution` 研究读数
2. 固定 `P65 / P95` 三段分带
3. 输出当前波段的年龄带或强度带标签
4. 为 `G4` 和 `G6` 提供统一的分布口径

---

## 3. 输入

1. `l3_gene_wave`
2. `l3_stock_gene`
3. `G1` 已确认的三子因子排序

---

## 4. 输出

1. 幅度分布带
2. 时长分布带
3. `wave_age_band` 或等价正式字段
4. `P65 / P95` 口径说明与回放读数

---

## 5. 完成标准

1. 能稳定区分普通波段、强波段、极端波段
2. 不再只盯两个尾巴，能保留中段强弱差异
3. 至少有一个结果可回写 `l3_stock_gene`
4. 不把分带直接等价成交易信号

---

## 6. 明确不做

1. 不把 `65 / 95` 扩写成参数森林
2. 不在本卡重写 `1-2-3 / 2B`
3. 不在本卡引入指数和行业镜像尺

---

## 7. 结案结论

本卡已完成。  
当前第四战场已正式具备 `G2` 所需的三类正式输出：

1. `l3_stock_gene` 已增加：
   - `current_wave_magnitude_p65 / p95`
   - `current_wave_duration_p65 / p95`
   - `current_wave_magnitude_band / current_wave_duration_band / current_wave_age_band`
2. `l3_gene_wave` 已增加：
   - `magnitude_p65 / p95`
   - `duration_p65 / p95`
   - `magnitude_band / duration_band / wave_age_band`
3. 主库已新增 `l3_gene_distribution_eval`，用于记录窗口结束日的自历史分布带与基础赔率读数

截至 `2026-02-24` 的主库真实回放结果表明：

1. `magnitude` 的三段分带已经能稳定拉开“普通 / 强 / 极端”差异
2. `duration` 的分带已可稳定落库，但解释力仍明显弱于 `magnitude`
3. `65 / 95` 在第四战场中已被固定为“历史位置标签”，而不是新的交易参数森林

下一张主线卡应按顺序进入 `G3 / structure label calibration`。

---

## 8. 文档入口

1. 配套 record：[`records/05-phase-g2-percentile-band-calibration-record-20260316.md`](records/05-phase-g2-percentile-band-calibration-record-20260316.md)
2. 配套 evidence：[`evidence/05-phase-g2-percentile-band-calibration-evidence-20260316.md`](evidence/05-phase-g2-percentile-band-calibration-evidence-20260316.md)
