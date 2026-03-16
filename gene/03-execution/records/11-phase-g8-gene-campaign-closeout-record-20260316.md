# G8 记录: 第四战场收口已完成

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. 目标

本文用于把 `G8 / gene campaign closeout` 的正式裁决写死。

这张记录只回答五件事：

1. 第四战场当前定义过的主线卡与正式记录是否已经全部闭环
2. 第四战场这一轮最终到底留下了什么
3. 哪些结论可以迁回主线治理，哪些只能继续留在研究线
4. `GX1 / GX2` 现在到底是什么身份
5. 未来若继续第四战场，只允许开什么类型的新卡

---

## 2. Formal Inputs

`G8` 本轮只承认以下 formal inputs：

1. `gene/03-execution/evidence/11-phase-g8-gene-campaign-closeout-evidence-20260316.md`
2. `gene/03-execution/04-phase-card-catalog-20260316.md`
3. `gene/03-execution/records/01-phase-g0-wave-ruler-opening-record-20260316.md`
4. `gene/03-execution/records/02-professional-speculation-principles-map-20260316.md`
5. `gene/03-execution/records/03-professional-speculation-principles-system-ingestion-matrix-20260316.md`
6. `gene/03-execution/records/04-phase-g1-factor-attribution-baseline-record-20260316.md`
7. `gene/03-execution/records/05-phase-g2-percentile-band-calibration-record-20260316.md`
8. `gene/03-execution/records/06-phase-g3-structure-label-calibration-record-20260316.md`
9. `gene/03-execution/records/07-phase-g4-self-history-ruler-validation-record-20260316.md`
10. `gene/03-execution/records/08-phase-g5-market-industry-index-mirror-ruler-record-20260316.md`
11. `gene/03-execution/records/09-phase-g6-bof-pb-cpb-conditioning-record-20260316.md`
12. `gene/03-execution/records/10-phase-g7-mss-irs-refactor-or-retire-record-20260316.md`

当前明确不做：

1. 不新增新的主库 replay 或信号回测
2. 不把 closeout 写成主线 promotion 决定
3. 不自动打开 `GX1 / GX2`
4. 不把 `G5 / G6` 直接回写成当前默认运行参数

---

## 3. 收官判定

当前第四战场这轮战役的收官判定固定为：

1. `all_defined_gene_main_queue_cards_closed = yes`
2. `all_formal_gene_records_closed = yes`
3. `active_gene_main_queue = none`
4. `gx1_status = conditional_only`
5. `gx2_status = conditional_only`
6. `future_gene_reentry_requires = explicit_mainline_migration_package_or_new_targeted_hypothesis`
7. `current_gene_boundary = historical_wave_ruler_plus_mirror_ruler_plus_conditioning_readout_plus_mss_irs_retire_boundary`

这意味着：

`第四战场当前不是“还有旧卡没跑完”，而是主队列已经正式收完。`

---

## 4. 第四战场最终完成了什么

### 4.1 对象层与正式表合同已完成

`G0` 已把第四战场第一版对象层正式落下：

1. `price-only wave ruler` 术语冻结
2. `l3_stock_gene / l3_gene_wave / l3_gene_event` DuckDB 合同
3. `build_l3()` -> `compute_gene()` 接线

### 4.2 个股自历史标尺已完成第一版正式验证

`G1 ~ G4` 已把第一版自历史标尺正式收成：

1. `magnitude` 是当前最强子因子
2. `P65 / P95` 与 `wave_age_band` 是历史位置标签，不是交易参数
3. `duration_percentile = PRIMARY_RULER`
4. `gene_score = KEEP_COMPOSITE`
5. 第四战场当前更像“过热 / 衰竭 / 历史极端尺”，不是强 continuation 尺

### 4.3 市场层与行业层镜像入口已完成

`G5` 已把第四战场正式扩到：

1. `l3_gene_mirror(MARKET / INDUSTRY)`
2. `mirror_gene_rank`
3. `primary_ruler_rank`
4. `support_rise_ratio`
5. 市场层的 `support_strong_ratio / support_new_high_ratio`

并且已经写死：

1. `mirror_gene_rank` 与 `primary_ruler_rank` 不能偷并成单榜
2. 宽度比率可以进入镜像层
3. 旧 `MSS / IRS` 语义包不能直接借尸还魂

### 4.4 五形态条件层已形成正式解释入口

`G6` 已把第四战场正式扩到：

1. `l3_gene_conditioning_eval`
2. `BOF / BPB / PB / TST / CPB`
3. `current_wave_direction / wave_age_band / magnitude_band / 123 / 2B / streak_bucket`

当前这层正式提供的是：

1. `Normandy` 的环境解释层
2. pattern baseline 与 condition delta 的正式对照
3. “什么环境下更值得打 / 更不值得打”的附加读数

而不是：

1. 新的主 alpha
2. 硬过滤器
3. 当前默认主线参数

### 4.5 旧 `MSS / IRS` 的去留已正式写死

`G7` 已把第四战场对旧模块的治理裁决固定为：

1. `旧 MSS-lite = retire old implementation`
2. `旧 IRS-lite = retire old score semantics while keeping the problem`
3. `旧 IRS` 的问题域改由 `G5 / l3_gene_mirror(INDUSTRY)` 接管
4. `GX2` 当前不触发

因此第四战场这一轮真正 retained 下来的，不是旧分数体系，而是：

1. 历史波段尺
2. 市场/行业镜像尺
3. 五形态环境解释层
4. `MSS / IRS` 退役与迁移边界

---

## 5. 按卡收口的一页表

| 卡 | 回答的问题 | 当前正式留下来的结论 | 状态 |
|---|---|---|---|
| `G0` | 第四战场对象层如何落地 | `price-only` 术语与 `l3_stock_gene / wave / event` 合同已落下 | `Completed` |
| `G1` | 三子因子谁更硬 | `magnitude` 当前最强 | `Completed` |
| `G2` | `65 / 95` 该是什么 | `P65 / P95 + wave_age_band` 是位置标签，不是交易参数 | `Completed` |
| `G3` | `1-2-3 / 2B` 能否正式化 | 已升级为正式结构标签并回写 `wave / event / snapshot` | `Completed` |
| `G4` | 个股自历史尺是否成立 | `duration_percentile = PRIMARY_RULER`；整体更像过热/衰竭尺 | `Completed` |
| `G5` | 市场/行业镜像是否成立 | `MARKET / INDUSTRY` 镜像尺成立，且必须保留双榜与宽度比率 | `Completed` |
| `G6` | 五形态环境层能否形成 | `BOF / BPB / PB / TST / CPB` 条件解释层成立，但不是硬过滤器 | `Completed` |
| `G7` | 旧 `MSS / IRS` 怎么处理 | 保留问题，不保留旧实现；替代入口切到 `G5 / G6` | `Completed` |
| `G8` | 第四战场如何正式收官 | 主队列归零，`GX1 / GX2` 只保留条件身份，未来重开必须显式立项 | `Completed` |

---

## 6. 正式入口清单

第四战场当前正式入口固定为两类。

### 6.1 文档入口

1. `gene/README.md`
2. `gene/01-full-design/01-stock-historical-trend-ruler-charter-20260316.md`
3. `gene/02-implementation-spec/01-price-only-wave-ruler-spec-20260316.md`
4. `gene/03-execution/records/07-phase-g4-self-history-ruler-validation-record-20260316.md`
5. `gene/03-execution/records/08-phase-g5-market-industry-index-mirror-ruler-record-20260316.md`
6. `gene/03-execution/records/09-phase-g6-bof-pb-cpb-conditioning-record-20260316.md`
7. `gene/03-execution/records/10-phase-g7-mss-irs-refactor-or-retire-record-20260316.md`
8. `gene/03-execution/records/11-phase-g8-gene-campaign-closeout-record-20260316.md`

### 6.2 数据入口

1. `l3_stock_gene`
2. `l3_gene_wave`
3. `l3_gene_event`
4. `l3_gene_factor_eval`
5. `l3_gene_distribution_eval`
6. `l3_gene_validation_eval`
7. `l3_gene_mirror`
8. `l3_gene_conditioning_eval`

---

## 7. 可迁回主线与必须留在研究线的边界

### 7.1 当前可以迁回主线治理的内容

1. `price-only wave ruler` 的对象语言与表合同
2. `PRIMARY_RULER / composite / mirror dual-rank` 的治理边界
3. 市场/行业镜像层的宽度辅助确认口径
4. `G6` 作为环境解释层而不是硬过滤器的边界
5. 旧 `MSS / IRS` 的退役口径与显式 migration package 门槛

### 7.2 当前只能继续留在研究线的内容

1. `P65 / P95` 与各类分带不允许直接写成交易触发参数
2. `G6` 的 pattern 条件差异不允许直接升格成默认 runtime filter
3. `G5 / G6` 不允许在没有显式 migration package 的情况下改写当前 baseline
4. 第四战场当前全部读数都不等于“已形成新主 alpha”

---

## 8. 与 `Normandy / Positioning / blueprint` 的正式关系

### 8.1 与 `Normandy`

第四战场当前对 `Normandy` 的正式关系固定为：

1. 提供市场/行业/个股所处历史环境
2. 提供五形态条件解释层
3. 帮助回答“哪些 trigger 在什么环境里更值得打”

但不负责：

1. 重写 `Normandy` 的主 alpha
2. 直接改写 `Normandy` 当前 baseline

### 8.2 与 `Positioning`

第四战场当前对 `Positioning` 的正式关系固定为：

1. 只能提供 cohort 标注、环境分层与事后验证标签
2. 不直接进入 sizing / partial-exit baseline
3. 若未来要消费，必须另开显式卡做 targeted validation

### 8.3 与 `blueprint`

第四战场当前对 `blueprint` 的正式关系固定为：

1. 可迁的是治理边界、正式入口与退役决策
2. 不可偷迁的是运行默认参数
3. 若未来吸收 `G5 / G6`，必须显式走 migration package

---

## 9. `GX1 / GX2` 当前身份

当前固定为：

1. `GX1 / targeted detector rewrite = conditional_only`
2. `GX2 / targeted migration package = conditional_only`

其中：

1. `GX1` 只有在现有 detector 一致性已阻塞 `G3 / G4 / G6` 时才允许打开
2. `GX2` 只有在主线真的要集中吸收 `G5 / G6 / G7` 产物时才允许打开

---

## 10. 未来若继续，只允许怎么继续

第四战场若未来继续，当前只允许三种入口：

1. `explicit_mainline_migration_package`
2. `new_targeted_hypothesis`
3. `narrow_follow_up_on_blocking_data_contract_or_detector_consistency`

当前明确不允许：

1. 继续回到旧 `MSS / IRS` 做泛化翻修
2. 在没有新假设时继续做大而泛的参数扫面
3. 不经 formal card 就静默改写主线默认路径

---

## 11. 正式结论

当前 `G8 / gene campaign closeout` 的正式结论固定为：

1. 第四战场定义过的主线卡 `G0 ~ G8` 已全部完成
2. 第四战场当前正式留下的是 `historical wave ruler + mirror ruler + conditioning readout + MSS/IRS retire boundary`
3. 第四战场当前更像“背景尺 / 条件尺 / 退役治理尺”，不是新的默认运行系统
4. `GX1 / GX2` 当前都只保留条件身份
5. 若未来要继续第四战场，只允许通过 `explicit_mainline_migration_package_or_new_targeted_hypothesis`

---

## 12. 一句话结论

`G8` 已把第四战场正式收官：当前真正留下来的不是一套新交易默认参数，而是一套自历史尺、镜像尺、条件解释层和旧模块退役边界。
