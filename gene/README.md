# Gene

**状态**: `Active`  
**日期**: `2026-03-16`

---

## 1. 定位

`gene/` 是 `EmotionQuant-gamma` 根目录下的第四战场研究线，专门回答一个问题：

`当前这只股票当前这段走势，在它自己的历史里算什么级别？`

它不是版本线，不替代 `blueprint/`，也不直接改写当前主线。它的职责是先做“历史尺”，再决定哪些旧模块值得改造，哪些旧模块应该退役。

---

## 2. 边界

第四战场固定遵守以下边界：

1. 不重开 `Normandy` 的 alpha provenance 问题
2. 不重开 `Positioning` 的 sizing / partial-exit 问题
3. 先做个股价格对象层，不先把 `MSS / IRS` 当答案
4. 先冻结 `趋势 / 波段 / 转折 / 新高新低` 的术语
5. 先给全市场一把历史尺，再决定 `MSS / IRS` 是改造还是退役

---

## 3. 目录结构

`gene/` 固定沿用三层结构：

1. `01-full-design/`
2. `02-implementation-spec/`
3. `03-execution/`

另保留：

4. `90-archive/`

---

## 4. 卡体系

第四战场完整卡体系固定为 `11` 张：

1. 必选主线卡 `9` 张：`G0 ~ G8`
2. 可选条件卡 `2` 张：`GX1 ~ GX2`

主线顺序固定为：

1. `G0`: 对象层脚手架
2. `G1`: 三子因子解释力基线
3. `G2`: 历史寿命分布与 `65 / 95` 校准
4. `G3`: `1-2-3 / 2B` 结构标签校准
5. `G4`: 个股自历史标尺验证
6. `G5`: 指数 / 行业 / 大盘镜像尺
7. `G6`: `BOF / BPB / PB / TST / CPB` 条件层统计
8. `G7`: `MSS / IRS` 改造或退役决策
9. `G8`: 第四战场收口

条件卡：

1. `GX1`: 目标检测器重写
2. `GX2`: 目标迁移包

---

## 5. 当前目标

第四战场第一阶段只做三件事：

当前执行状态：

1. 已完成：`G0 / G1 / G2 / G3 / G4 / G5 / G6`
2. 当前下一张主线卡：`G7 / MSS-IRS refactor-or-retire decision`

1. 定义 `趋势 / 波段 / 波段主流 / 趋势逆流 / 转折 / 新高新低`
2. 用 `波动幅度 + 波动时间 + 新高新低密度` 建立历史波段数据库
3. 输出个股自历史分位、`z-score` 与横截面排序

第一版只消费 `l2_stock_adj_daily`，不依赖 `MSS / IRS`，也不直接进入实时漏斗。

---

## 6. 当前入口

- `01-full-design/01-stock-historical-trend-ruler-charter-20260316.md`
- `01-full-design/02-professional-speculation-principles-theory-annex-20260316.md`
- `02-implementation-spec/01-price-only-wave-ruler-spec-20260316.md`
- `03-execution/01-phase-g0-wave-ruler-opening-card-20260316.md`
- `03-execution/02-phase-g1-g2-g3-g6-backlog-20260316.md`
- `03-execution/03-phase-g1-factor-attribution-baseline-card-20260316.md`
- `03-execution/04-phase-card-catalog-20260316.md`
- `03-execution/05-phase-g2-percentile-band-calibration-card-20260316.md`
- `03-execution/06-phase-g3-structure-label-calibration-card-20260316.md`
- `03-execution/07-phase-g4-self-history-ruler-validation-card-20260316.md`
- `03-execution/08-phase-g5-market-industry-index-mirror-ruler-card-20260316.md`
- `03-execution/09-phase-g6-bof-pb-cpb-conditioning-card-20260316.md`
- `03-execution/evidence/09-phase-g6-five-pattern-conditioning-evidence-20260316.md`
- `03-execution/10-phase-g7-mss-irs-refactor-or-retire-card-20260316.md`
- `03-execution/11-phase-g8-gene-campaign-closeout-card-20260316.md`
- `03-execution/12-phase-gx1-targeted-detector-rewrite-card-20260316.md`
- `03-execution/13-phase-gx2-targeted-migration-package-card-20260316.md`
- `03-execution/records/01-phase-g0-wave-ruler-opening-record-20260316.md`
- `03-execution/records/02-professional-speculation-principles-map-20260316.md`
- `03-execution/records/03-professional-speculation-principles-system-ingestion-matrix-20260316.md`
- `03-execution/records/04-phase-g1-factor-attribution-baseline-record-20260316.md`
- `03-execution/records/05-phase-g2-percentile-band-calibration-record-20260316.md`
- `03-execution/records/06-phase-g3-structure-label-calibration-record-20260316.md`
- `03-execution/records/07-phase-g4-self-history-ruler-validation-record-20260316.md`
- `03-execution/records/08-phase-g5-market-industry-index-mirror-ruler-record-20260316.md`
- `03-execution/records/09-phase-g6-bof-pb-cpb-conditioning-record-20260316.md`
- `90-archive/README.md`
