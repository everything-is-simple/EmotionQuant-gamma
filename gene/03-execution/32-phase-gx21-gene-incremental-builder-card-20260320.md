# GX21 / Gene 增量构建器卡
**状态**: `Active`
**日期**: `2026-03-20`
**类型**: `incremental builder`
**直接目标目录**: [`../../src/selector/`](../../src/selector/)

---

## 1. 目标

这张卡只回答一个问题：

`A 股全市场的 Gene 与四张寿命面，能不能像采集层一样按脏窗口增量更新，而不是每天全市场重算？`

---

## 2. 本卡要解决的问题

1. 找出受新增数据影响的 `code / date range`
2. 只重算受影响 code 的 Gene 输出
3. 市场级四张表单独增量更新
4. 避免重复删除和全表回卷

---

## 3. 本卡必须交付

1. `dirty scan` 规则
2. `per-code rebuild` 入口
3. `market-only rebuild` 入口
4. `surface refresh` 入口
5. 增量验证与幂等验证

---

## 3A. 四目录落位口径

`GX21` 的增量 builder 必须显式服从四目录纪律：

1. `G:\EmotionQuant-gamma`
   - 放 builder 源码、执行卡、测试、治理记录
2. `G:\EmotionQuant_data`
   - 放正式执行库与正式增量写回结果
3. `G:\EmotionQuant-temp`
   - 放 dirty scan 摘要、临时工作库、性能试跑产物
4. `G:\EmotionQuant-report`
   - 不放 builder 中间件，只消费最终图和报告

---

## 3B. 当前已完成

1. 已有 `dirty scan`、`per-code rebuild`、`market-only rebuild` 脚本与模块入口
2. `build_l3()` 的 Gene 主线已开始消费增量 builder，而不是默认走全量 `compute_gene()`
3. `l3_gene_factor_eval / l3_gene_distribution_eval / l3_gene_validation_eval` 已补上按目标 `calc_date` 的增量刷新
4. `l3_gene_conditioning_sample / l3_gene_conditioning_eval` 已补上“先增量样本，再按目标日聚合”的正式增量路径
5. 定向测试已覆盖：
   - 脏 code 只重建自身核心表
   - 评估表可按目标日重建
   - conditioning sample ledger 与 conditioning eval 可按目标日重建
   - `builder.py` 非 force 路径已接到增量入口

---

## 4. 关闭标准

1. 新增一段日线数据时，不再需要全市场重跑 Gene
2. 个股四张 surface 可按受影响窗口增量刷新
3. 市场表与个股表都能复用统一的增量调度逻辑

---

## 5. 一句话收口

`GX21` 要让 Gene 真正具备生产级增量能力，而不是继续停在研究型全量重建。
