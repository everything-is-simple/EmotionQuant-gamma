# G7 卡: MSS / IRS 改造或退役决策

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. 目标

基于 `G4 ~ G6` 的结果，对旧 `MSS / IRS` 做一次不拖泥带水的决策：

`改造成镜像历史尺，还是正式退役？`

---

## 2. 本卡范围

1. 审计旧 `MSS / IRS` 仍然有效的部分
2. 对照 `G5` 镜像尺结果检查是否值得改造
3. 对照 `G6` 条件层结果检查是否还有系统价值
4. 冻结保留、改造、退役三种路径中的一种

---

## 3. 输入

1. `G5` 市场/行业镜像尺结果
2. `G6` 条件层统计结果
3. 现有 `MSS / IRS` 文档、实现与历史读数

---

## 4. 输出

1. `MSS / IRS` 决策备忘录
2. 如保留，给出精简改造边界
3. 如退役，给出退役范围与替代入口
4. 如需迁移，决定是否触发 `GX2`

---

## 5. 完成标准

1. 不再让旧 `MSS / IRS` 以模糊状态继续漂
2. 若保留，必须给出比旧版本更清晰的存在理由
3. 若退役，必须给出仓库入口和依赖处置边界
4. 结论可被 `G8` 直接吸收

---

## 6. 明确不做

1. 不在本卡重做第一战场历史回顾
2. 不因为情感依赖保留旧模块
3. 不在没有证据时直接宣布全面替代

---

## 7. 结案结论

本卡已完成。  
当前 `G7` 的正式裁决固定为：

1. 旧 `MSS-lite` 正式退役为“历史实现与证据对象”
   - 不再作为未来默认路径、默认风控 overlay 或 promotion 候选继续漂
   - 现有代码与文档先保留，用于历史 replay、证据回溯与归档
2. 旧 `IRS-lite` 也不再保留为未来行业评分主入口
   - 保留的是“行业相对强弱/相对位置”这个问题
   - 退役的是旧 `IndustryScore.score -> signal.irs_score` 单分数字义
   - 替代入口改为第四战场 `G5` 的行业镜像尺，而不是继续沿旧 `irs_score` 升级
3. 第四战场给出的正式替代入口固定为：
   - 市场层：`l3_gene_mirror(MARKET)` + `support_rise_ratio / support_strong_ratio / support_new_high_ratio`
   - 行业层：`l3_gene_mirror(INDUSTRY)` + `mirror_gene_rank / primary_ruler_rank / support_rise_ratio`
   - 形态环境层：`l3_gene_conditioning_eval`
4. `GX2 / targeted migration package` 当前不触发
   - 因为本轮没有出现必须集中迁移旧表、旧脚本、旧入口的阻塞级压力
   - 若未来主线要正式吸收 `G5 / G6` 结论，必须新开显式 migration package
5. `G7` 完成后，第四战场下一张主线卡按顺序进入：
   - `G8 / gene campaign closeout`
