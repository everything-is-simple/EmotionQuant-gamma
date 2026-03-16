# Gene

**状态**: `Active`  
**日期**: `2026-03-16`

---

## 1. 定位

`gene/` 是 `EmotionQuant-gamma` 根目录下的第四战场设计空间，也是当前仓库专门面向“个股历史波段标尺”的独立研究线。
它只回答一个问题：

`当前这只股票的这一段走势，在它自己的历史里算什么级别。`

这里不是 `blueprint/` 的替代品，也不是对当前 `v0.01-plus` 主线的直接改写。
`Gene` 不是版本线，而是研究线。

---

## 2. 边界

当前仓库已经有三块已知前提：

1. `blueprint/` + `docs/spec/v0.01-plus/` 代表当前主线
2. `normandy/` 回答“买什么 / 为什么打”
3. `positioning/` 回答“打多大 / 怎么退”

因此 `gene/` 的边界固定为：

1. 不重开 `Normandy` 的 alpha provenance 问题
2. 不重开 `Positioning` 的 sizing / partial-exit 问题
3. 不先把 `MSS / IRS` 当答案，而是先做价格对象层
4. 先把 `趋势 / 波段 / 转折 / 新高新低` 的术语冻结
5. 先给全市场一把“历史尺”，再决定 `MSS / IRS` 是改造还是退役

---

## 3. 分层结构

`gene/` 固定沿用 `blueprint/` 的三层结构：

1. `01-full-design/`
2. `02-implementation-spec/`
3. `03-execution/`

另保留：

4. `90-archive/`
   - 保存第四战场正式开线前的早期提案与概念草案

---

## 4. 当前目标

第四战场第一阶段只做三件事：

1. 定义 `趋势 / 波段 / 波段主流 / 趋势逆流 / 转折 / 新高新低`
2. 用 `波动幅度 + 波动时间 + 新高新低密度` 建立历史波段数据库
3. 输出个股自历史分位、z-score 和全市场横截面排序

第一版明确只消费 `l2_stock_adj_daily`，不依赖 `MSS / IRS`，也不直接进入实时漏斗。

---

## 5. 当前入口

- `01-full-design/01-stock-historical-trend-ruler-charter-20260316.md`
- `01-full-design/02-professional-speculation-principles-theory-annex-20260316.md`
- `02-implementation-spec/01-price-only-wave-ruler-spec-20260316.md`
- `03-execution/01-phase-g0-wave-ruler-opening-card-20260316.md`
- `03-execution/02-phase-g1-g2-g3-g6-backlog-20260316.md`
- `03-execution/records/01-phase-g0-wave-ruler-opening-record-20260316.md`
- `03-execution/records/02-professional-speculation-principles-map-20260316.md`
- `03-execution/records/03-professional-speculation-principles-system-ingestion-matrix-20260316.md`
- `90-archive/README.md`
