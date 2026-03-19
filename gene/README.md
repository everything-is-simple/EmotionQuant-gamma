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
3. `G2`: 历史寿命分布第一版校准（历史 `65 / 95` round 已归档；forward 口径已转向四分位连续分布）
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

第四战场第一阶段已正式完成，当前执行状态固定为：

1. 已完成：`G0 / G1 / G2 / G3 / G4 / G5 / G6 / G7 / G8`
2. 当前主线队列：`none`
3. 条件卡状态：`GX1 / GX2 = conditional_only`
4. 如未来继续：`explicit_mainline_migration_package_or_new_targeted_hypothesis`

本轮正式完成的主线工作可压成三件事：

1. 定义 `趋势 / 波段 / 波段主流 / 趋势逆流 / 转折 / 新高新低`
2. 用 `波动幅度 + 波动时间 + 新高新低密度` 建立历史波段数据库
3. 输出个股自历史分位、`z-score` 与横截面排序，并扩展到镜像层与条件层

第一版只消费 `l2_stock_adj_daily`，不依赖 `MSS / IRS`，也不直接进入实时漏斗。

---

## 6. 当前入口

- `01-full-design/01-stock-historical-trend-ruler-charter-20260316.md`
- `01-full-design/02-professional-speculation-principles-theory-annex-20260316.md`
- `01-full-design/03-book-core-trend-and-market-lifespan-framework-freeze-20260319.md`
- `02-implementation-spec/01-price-only-wave-ruler-spec-20260316.md`
- `02-implementation-spec/02-market-lifespan-framework-implementation-spec-20260319.md`
- `03-execution/01-phase-g0-wave-ruler-opening-card-20260316.md`
- `03-execution/03-phase-g1-factor-attribution-baseline-card-20260316.md`
- `03-execution/04-phase-card-catalog-20260316.md`
- `03-execution/05-phase-g2-percentile-band-calibration-card-20260316.md`
- `03-execution/06-phase-g3-structure-label-calibration-card-20260316.md`
- `03-execution/07-phase-g4-self-history-ruler-validation-card-20260316.md`
- `03-execution/08-phase-g5-market-industry-index-mirror-ruler-card-20260316.md`
- `03-execution/09-phase-g6-bof-pb-cpb-conditioning-card-20260316.md`
- `03-execution/evidence/09-phase-g6-five-pattern-conditioning-evidence-20260316.md`
- `03-execution/10-phase-g7-mss-irs-refactor-or-retire-card-20260316.md`
- `03-execution/evidence/10-phase-g7-mss-irs-decision-evidence-20260316.md`
- `03-execution/11-phase-g8-gene-campaign-closeout-card-20260316.md`
- `03-execution/evidence/11-phase-g8-gene-campaign-closeout-evidence-20260316.md`
- `03-execution/12-phase-gx1-targeted-detector-rewrite-card-20260316.md`
- `03-execution/13-phase-gx2-targeted-migration-package-card-20260316.md`
- `03-execution/14-phase-gx3-trend-level-context-refactor-card-20260317.md`
- `03-execution/15-phase-gx4-mainstream-countertrend-semantics-card-20260317.md`
- `03-execution/16-phase-gx5-two-b-window-semantics-refactor-card-20260317.md`
- `03-execution/17-phase-gx6-123-three-condition-refactor-card-20260317.md`
- `03-execution/18-phase-gx7-post-refactor-g4-g5-g6-revalidation-card-20260317.md`
- `03-execution/19-phase-gx8-three-level-trend-hierarchy-card-20260318.md`
- `03-execution/20-phase-gx9-book-vs-gene-remediation-package-card-20260319.md`
- `03-execution/21-phase-gx10-lifespan-reference-basis-expansion-card-20260319.md`
- `03-execution/22-phase-gx11-runtime-surface-semantic-cleanup-card-20260319.md`
- `03-execution/23-phase-gx12-post-remediation-gene-and-phase9-revalidation-card-20260319.md`
- `03-execution/24-phase-gx13-post-remediation-g4-g5-g6-rerun-card-20260319.md`
- `03-execution/25-phase-gx14-book-aligned-lifespan-distribution-card-20260319.md`
- `03-execution/26-phase-gx15-market-lifespan-framework-reconstruction-package-card-20260319.md`
- `03-execution/27-phase-gx16-average-lifespan-odds-surface-card-20260319.md`
- `03-execution/28-phase-gx17-book-core-definition-final-freeze-card-20260320.md`
- `03-execution/29-phase-gx18-stock-market-lifespan-surface-schema-refactor-card-20260320.md`
- `03-execution/30-phase-gx19-average-lifespan-engine-completion-card-20260320.md`
- `03-execution/31-phase-gx20-book-figure-renderer-and-formal-report-output-card-20260320.md`
- `03-execution/32-phase-gx21-gene-incremental-builder-card-20260320.md`
- `03-execution/33-phase-gx22-backtest-cache-and-replay-acceleration-card-20260320.md`
- `03-execution/records/12-gene-book-definition-ingestion-ledger-20260317.md`
- `03-execution/records/14-phase-gx3-trend-level-context-refactor-record-20260317.md`
- `03-execution/records/01-phase-g0-wave-ruler-opening-record-20260316.md`
- `03-execution/records/02-professional-speculation-principles-map-20260316.md`
- `03-execution/records/03-professional-speculation-principles-system-ingestion-matrix-20260316.md`
- `03-execution/records/04-phase-g1-factor-attribution-baseline-record-20260316.md`
- `03-execution/records/05-phase-g2-percentile-band-calibration-record-20260316.md`
- `03-execution/records/06-phase-g3-structure-label-calibration-record-20260316.md`
- `03-execution/records/07-phase-g4-self-history-ruler-validation-record-20260316.md`
- `03-execution/records/08-phase-g5-market-industry-index-mirror-ruler-record-20260316.md`
- `03-execution/records/09-phase-g6-bof-pb-cpb-conditioning-record-20260316.md`
- `03-execution/records/10-phase-g7-mss-irs-refactor-or-retire-record-20260316.md`
- `03-execution/records/11-phase-g8-gene-campaign-closeout-record-20260316.md`
- `03-execution/records/20-phase-gx9-book-vs-gene-audit-record-20260319.md`
- `03-execution/records/21-phase-gx10-lifespan-reference-basis-expansion-record-20260319.md`
- `03-execution/records/22-phase-gx11-runtime-surface-semantic-cleanup-record-20260319.md`
- `03-execution/records/23-phase-gx12-post-remediation-gene-and-phase9-revalidation-record-20260319.md`
- `90-archive/README.md`

---

## 7. Mainline Phase 9 Tracker

第四战场当前已经没有新的 hierarchy blocker。  
当前第一战场 `Phase 9` 的真实追踪位是：

1. 当前 active sub-card：`blueprint/03-execution/17.6-phase-9c-formal-combination-freeze-card-20260318.md`
2. 当前下一张 blocked card：`blueprint/03-execution/17.7-phase-9d-gene-package-promotion-ruling-card-20260318.md`

当前 `17.6` 已正式写死：

1. 只允许从 `duration_percentile / reversal_state / context_trend_direction_before` 这 `3` 个 isolated winners 里选组合候选
2. 只允许 `3` 个二元组合加 `1` 个三元组合进入 Phase 9C freeze
3. 明确禁止偷带 `wave_role / current_wave_age_band / mirror / conditioning / gene_score`
4. 当前先做 `formal combination freeze`，不是直接跑组合 replay，更不是提前做 package promotion ruling

这意味着：

1. `GX8` 不再是 `Phase 9C / 9D` 的 blocker
2. `Gene` 的 runtime promotion 仍必须通过第一战场主包推进
3. `17.7` 在 `17.6` 关闭前不能提前写成包级结论

## 8. Post-Closeout Targeted Hypothesis

1. `GX3 / trend-level context refactor`
   - `post-closeout targeted hypothesis`
   - `src/selector/gene.py`
   - `Completed`
   - 配套 record：`03-execution/records/14-phase-gx3-trend-level-context-refactor-record-20260317.md`
2. `GX4 / mainstream-countertrend semantics refactor`
   - `post-closeout targeted hypothesis`
   - `src/selector/gene.py`
   - `Completed`
   - 配套 record：`03-execution/records/15-phase-gx4-mainstream-countertrend-semantics-record-20260318.md`
3. `GX5 / 2B window semantics refactor`
   - `post-closeout targeted hypothesis`
   - `src/selector/gene.py`
   - `Completed`
   - 配套 record：`03-execution/records/16-phase-gx5-two-b-window-semantics-record-20260318.md`
4. `GX6 / 1-2-3 three-condition refactor`
   - `post-closeout targeted hypothesis`
   - `src/selector/gene.py`
   - `Completed`
   - 配套 record：`03-execution/records/17-phase-gx6-123-three-condition-refactor-record-20260318.md`
5. `GX7 / post-refactor G4-G5-G6 revalidation`
   - `post-closeout targeted hypothesis`
   - `src/selector/gene.py`
   - `Completed`
   - 配套 record：`03-execution/records/18-phase-gx7-post-refactor-g4-g5-g6-revalidation-record-20260318.md`
6. `GX8 / three-level trend hierarchy refactor`
   - `post-closeout targeted hypothesis`
   - `src/selector/gene.py`
   - `Completed`
   - 目标：把 `trend_level` 从单层 `INTERMEDIATE` proxy 推到真正三层趋势并存语义
   - 配套 record：`03-execution/records/19-phase-gx8-three-level-trend-hierarchy-record-20260319.md`
7. `GX9 / book-vs-gene remediation package`
   - `post-audit remediation package`
   - `gene / src/selector/gene.py / src/data/store.py`
   - `Completed`
   - 目标：把书义对齐整改拆成寿命基础、运行面语义、强制重验证三张小卡
   - 配套 record：`03-execution/records/20-phase-gx9-book-vs-gene-audit-record-20260319.md`
8. `GX10 / lifespan reference-basis expansion`
   - `targeted semantic implementation`
   - `src/selector/gene.py / src/data/store.py`
   - `Completed`
   - 目标：把寿命轴从 time-only ruler 推进到更接近书义的参考基础
   - 配套 record：`03-execution/records/21-phase-gx10-lifespan-reference-basis-expansion-record-20260319.md`
9. `GX11 / runtime surface semantic cleanup`
   - `targeted contract cleanup`
   - `src/selector/gene.py / src/data/store.py`
   - `Completed`
   - 目标：清理 age-band / context / reversal 的运行面歧义
   - 配套 record：`03-execution/records/22-phase-gx11-runtime-surface-semantic-cleanup-record-20260319.md`
10. `GX12 / post-remediation gene and phase9 revalidation`
   - `forced downstream revalidation`
   - `src/selector/gene.py / src/data/store.py`
   - `Completed`
   - 目标：重审 G4/G5/G6 与 Phase 9 证据是否仍可保留
   - 配套 record：`03-execution/records/23-phase-gx12-post-remediation-gene-and-phase9-revalidation-record-20260319.md`
11. `GX13 / post-remediation G4-G5-G6 rerun`
   - `forced statistical rerun`
   - `scripts/report/run_gx13_post_remediation_revalidation.py`
   - `Active`
   - 目标：把 GX12 已裁定必须重跑的 G4/G5/G6 真正重跑并落新 evidence
12. `GX14 / book-aligned lifespan distribution correction`
   - `book-aligned semantic correction`
   - `src/selector/gene.py / src/data/store.py`
   - `Active`
   - 目标：把寿命统计从 `p65 / p95` 尾部刀改回中级主要走势的四分位连续分布图
13. `GX15 / market lifespan framework reconstruction package`
   - `full gene reconstruction package`
   - `gene/`
   - `Active`
   - 目标：把定义冻结、实现映射、代码重构、统计重跑与记录收口统一到同一条总包里
14. `GX16 / average lifespan odds surface`
   - `targeted semantic implementation`
   - `src/selector/gene.py / src/data/store.py`
   - `Completed`
   - 目标：把图 26-1 的平均寿命 / odds 正式接进 Gene 对象合同
15. `GX17 / book core definition final freeze`
   - `definition freeze`
   - `gene/01-full-design/`
   - `Proposal`
   - 目标：把趋势定义、趋势改变定义与市场寿命框架根口径一次冻结
16. `GX18 / stock-market lifespan surface schema refactor`
   - `schema refactor`
   - `src/data/store.py`
   - `Proposal`
   - 目标：把个股与市场四张寿命面收敛成标准化 schema，而不是物理表爆炸
17. `GX19 / average lifespan engine completion`
   - `engine completion`
   - `src/selector/gene.py`
   - `Proposal`
   - 目标：把 `UNSCALED / NULL odds / COUNTERTREND` 等缺口全部补齐
18. `GX20 / book figure renderer and formal report output`
   - `report productization`
   - `scripts/report/`
   - `Proposal`
   - 目标：把图 11-1 / 26-1 风格的市场寿命图正式输出成系统报告产物
19. `GX21 / gene incremental builder`
   - `incremental builder`
   - `src/selector/`
   - `Proposal`
   - 目标：让 A 股全市场 Gene 与四张寿命面按脏窗口增量更新
20. `GX22 / backtest cache and replay acceleration`
   - `backtest acceleration`
   - `src/backtest/`
   - `Proposal`
   - 目标：把回测从重复读写型 runner 推进到缓存驱动型批量回放

当前 `GX3 ~ GX12` 已完成，当前新增执行位为 `GX13 + GX14 + GX15`，其中 `GX16` 已完成；下一轮系统性清账队列已经展开为 `GX17 ~ GX22`。  
当前第四战场已不再有真正未执行的 hierarchy blocker，但已进入“书义对齐整改”阶段。  
定义整改后的正式收口口径现更新为：

1. `G4 / G5 / G6` 方向结论保留，但统计 evidence 必须重跑
2. `Phase 9` 当前保留 `context / reversal` 的 legacy isolated keep，但 `duration` 相关 follow-up 必须在书义四分位寿命分布 surface 上重开
3. `Gene` 继续保持 `sidecar / dashboard / attribution` 身份，不升格为 runtime hard gate
