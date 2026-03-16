# G4 卡: 个股自历史标尺验证

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. 目标

验证第四战场最核心的问题：

`当前这只股票当前这段走势，在它自己的历史里算什么级别？`

---

## 2. 本卡范围

1. 验证 `self-history percentile` 的稳定性
2. 检查不同股票之间历史尺是否具有可比较的弱一致性
3. 审核 `gene_score` 是否真能形成可用总尺
4. 固定第四战场对外主读数

---

## 3. 输入

1. `l3_stock_gene`
2. `l3_gene_wave`
3. `G1` 三子因子排序结果
4. `G2` 分布带结果
5. `G3` 结构标签结果

---

## 4. 输出

1. 个股自历史标尺验证报告
2. `gene_score` 保留、重权重或拆解建议
3. 当前波段级别的正式解读口径
4. 对 `G5` 的镜像扩展边界

---

## 5. 完成标准

1. 能明确回答“这段走势在该股自己的历史里排第几”
2. 历史尺不是一次性样本故事，而是可复跑读数
3. 若总分无效，能给出降级为子因子并行读数的决策
4. 产物可以直接服务 `G5` 与 `G6`

---

## 6. 明确不做

1. 不直接把历史尺硬接入实时交易
2. 不在本卡回头重写 `G1 / G2 / G3`
3. 不提前对 `MSS / IRS` 下最终退役结论

---

## 7. 结案结论

本卡已完成。  
当前第四战场已经把 `G4` 所需的自历史验证层正式接入：

1. `Store` schema 升级到 `v8`
2. 新增 `l3_gene_validation_eval`
3. `compute_gene()` 现已自动回写：
   - `gene_score`
   - `magnitude_percentile`
   - `duration_percentile`
   - `extreme_density_percentile`
4. 每次验证固定产出：
   - `monotonicity_score`
   - `avg_daily_rank_corr`
   - `positive_daily_rank_corr_rate`
   - `top / bottom bucket continuation_rate`
   - `decision_tag`

截至 `2026-02-24` 的主库真实读数表明：

1. `duration_percentile` 是当前三子因子里最硬的 `PRIMARY_RULER`
2. `magnitude_percentile` 与 `extreme_density_percentile` 仍保留为 `SUPPORTING_RULER`
3. `gene_score` 当前仍可保留为 `KEEP_COMPOSITE`
4. 整体单调性与日度 rank-corr 较弱，当前历史尺更像“过热/衰竭尺”，而不是强 continuation 尺

下一张主线卡应按顺序进入 `G5 / market-industry-index mirror ruler`。
