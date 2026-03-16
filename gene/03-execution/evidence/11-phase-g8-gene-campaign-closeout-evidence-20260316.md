# G8 Evidence: 第四战场收口证据汇总

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. Formal Inputs

| 来源 | 当前正式产物 | 对 `G8` 的直接含义 |
|---|---|---|
| `G0` | `l3_stock_gene / l3_gene_wave / l3_gene_event` | 第四战场已有独立对象层与正式表合同 |
| `G1` | `l3_gene_factor_eval` 与 `magnitude strongest` | 子因子基线已形成正式排序 |
| `G2` | `l3_gene_distribution_eval`、`P65 / P95`、`wave_age_band` | 历史位置标签已完成正式校准 |
| `G3` | `confirmed_turn_type + 123_STEP1/2/3 + 2B_TOP/BOTTOM` | 结构标签已完成正式化 |
| `G4` | `l3_gene_validation_eval`、`duration_percentile = PRIMARY_RULER` | 个股自历史尺已完成第一版正式验证 |
| `G5` | `l3_gene_mirror`、双榜、宽度比率 | 市场/行业镜像入口已形成 |
| `G6` | `l3_gene_conditioning_eval`、五形态条件层 | 第四战场已能向第二战场提供环境解释层 |
| `G7` | `MSS / IRS retire memo` | 旧模块的去留与替代入口已写死 |

---

## 2. 已完成的正式交付

### 2.1 正式表

1. `l3_stock_gene`
2. `l3_gene_wave`
3. `l3_gene_event`
4. `l3_gene_factor_eval`
5. `l3_gene_distribution_eval`
6. `l3_gene_validation_eval`
7. `l3_gene_mirror`
8. `l3_gene_conditioning_eval`

### 2.2 正式标签与正式读数

1. `magnitude_percentile / duration_percentile / extreme_density_percentile`
2. `current_wave_magnitude_band / current_wave_age_band`
3. `turn_confirm_type / 123_STEP1 / 123_STEP2 / 123_STEP3`
4. `2B_TOP / 2B_BOTTOM`
5. `decision_tag / primary_ruler_metric / primary_ruler_value`
6. `mirror_gene_rank / primary_ruler_rank`
7. `BOF / BPB / PB / TST / CPB` 的 pattern-conditioning delta

### 2.3 正式文档入口

1. `gene/README.md`
2. `gene/02-implementation-spec/01-price-only-wave-ruler-spec-20260316.md`
3. `gene/03-execution/records/07-phase-g4-self-history-ruler-validation-record-20260316.md`
4. `gene/03-execution/records/08-phase-g5-market-industry-index-mirror-ruler-record-20260316.md`
5. `gene/03-execution/records/09-phase-g6-bof-pb-cpb-conditioning-record-20260316.md`
6. `gene/03-execution/records/10-phase-g7-mss-irs-refactor-or-retire-record-20260316.md`

---

## 3. 第四战场最终读法

当前 `G0 ~ G7` 压成一句话，正式固定为：

1. 第四战场已经证明 `price-only historical wave ruler` 可以独立成立
2. 当前最稳的个股主尺是 `duration_percentile`
3. 整体读法更像“过热 / 衰竭 / 历史极端尺”，不是强 continuation 尺
4. 市场与行业镜像入口已形成，但必须保留 `mirror_gene_rank + primary_ruler_rank + width ratios`
5. 五形态条件层已形成，但当前只应作为 `Normandy` 的环境解释层
6. 旧 `MSS-lite` 已正式退役，旧 `IRS-lite` 已退役旧分数字义并改由 `G5` 接管问题域

---

## 4. 与其他战场的正式接口

### 4.1 对 `Normandy`

1. 提供 `MARKET / INDUSTRY / STOCK` 的历史环境背景
2. 提供 `BOF / BPB / PB / TST / CPB` 的环境差异读数
3. 不直接改写主 alpha，也不自动升格为硬过滤器

### 4.2 对 `Positioning`

1. 可提供 cohort 标签与环境分层
2. 不直接进入 sizing / partial-exit baseline
3. 若未来要消费，必须另开 targeted validation

### 4.3 对 `blueprint`

1. 当前可迁的是治理边界与正式入口
2. 不可偷迁的是默认运行参数
3. 若未来要吸收 `G5 / G6`，必须显式走 migration package

---

## 5. Closeout Decision

当前 `G8` 的证据裁决可压成以下五条：

1. `all_defined_gene_main_queue_cards_closed = yes`
2. `all_formal_gene_records_closed = yes`
3. `active_gene_main_queue = none`
4. `GX1 / GX2 = conditional_only`
5. `future_gene_reentry_requires = explicit_mainline_migration_package_or_new_targeted_hypothesis`

这意味着第四战场现在不是 backlog 队列，而是已经形成一套可长期维护的正式研究边界。
