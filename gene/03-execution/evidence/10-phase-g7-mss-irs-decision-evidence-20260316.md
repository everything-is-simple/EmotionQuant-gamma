# G7 Evidence: MSS / IRS 决策证据汇总

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. Formal Inputs

| 来源 | 关键读数/关键口径 | 对 `G7` 的直接含义 |
|---|---|---|
| `G4` | 第四战场更像“过热/衰竭尺”，不是强 continuation 尺 | 新入口更适合做背景尺，不支持旧 `MSS / IRS` 式顺势扩容 |
| `G5` | 必须同时保留 `mirror_gene_rank` 和 `primary_ruler_rank`；稳定辅助确认是宽度比率，不是旧语义包 | 旧 `IRS / MSS` 单分数字义已有更好替代 |
| `G6` | 五形态条件层已能解释环境差异，但当前仍是条件解释层，不是硬过滤器 | 第四战场可替代旧解释入口，但不应直接假装是新主 alpha |
| `Phase 2 / IRS` | `IRS ranking chain completed`；`absolute score calibration not yet claimed` | 旧 `IRS` 证明了问题存在，没证明旧分数体系应继续升级 |
| `Phase 3 / MSS` | Broker 已按 `risk_regime` 消费容量倍率；但不宣称收益改进 | 旧 `MSS` 证明了“会改执行”，没证明“值得保留为未来主入口” |
| `Phase 4 / Gate` | `NO-GO`；`IRS` 不是主嫌疑；主要变化在 `MSS -> Broker` 执行层 | 旧 `MSS` 的默认提升路径已被正式否决 |
| `Phase 4.1 / final replay` | `size_only_overlay` 仍未推翻 `legacy_bof_baseline`；`MAX_POSITIONS` 差异归零后仍失败 | 旧 `MSS / Broker` 已不值得继续做局部修修补补 |

---

## 2. 第四战场证据链

### 2.1 `G4`

当前正式读法已收口为：

1. 回答“当前波段有多极端”
2. 不回答“越高分位越该追”
3. 更像过热/衰竭背景尺

### 2.2 `G5`

当前正式市场/行业替代入口已形成：

1. 市场层：`MARKET + width ratios`
2. 行业层：`mirror_gene_rank + primary_ruler_rank + support_rise_ratio`

而且已经明确：

1. 两张榜不能偷并
2. 旧 `MSS / IRS` 语义包不能直接借尸还魂

### 2.3 `G6`

当前正式条件层已形成：

1. `BOF / BPB / PB / TST / CPB`
2. 可以解释 pattern 环境
3. 但不应直接升格为硬过滤器

---

## 3. 旧主线证据链

### 3.1 旧 `IRS`

`Phase 2` 已经写死：

1. 排名链完成
2. 绝对分数历史标定未完成

因此旧 `IRS` 当前只证明：

`行业相对排序有价值`

没有证明：

`旧 irs_score 本身值得继续当未来主入口`

### 3.2 旧 `MSS`

`Phase 3` 已证明：

1. `risk_regime` 会真实改 Broker
2. `signal` 与 `risk_regime` 不是一回事

但 `Phase 4` 与 `Phase 4.1` 已进一步写死：

1. 正式 Gate 为 `NO-GO`
2. 主嫌疑是 `MSS -> Broker` 容量执行层
3. `size_only_overlay` 也没翻盘

因此旧 `MSS` 当前已经不再是“差最后一点微调”的状态。

---

## 4. 决策矩阵

| 对象 | 若保留会遇到的问题 | 当前更合理的判决 | 正式替代入口 |
|---|---|---|---|
| 旧 `IRS-lite` | 会继续把行业问题压扁成单分数，并与 `G5` 两张榜冲突 | `退役旧实现，保留问题域` | `l3_gene_mirror(INDUSTRY)` |
| 旧 `MSS-lite` | 会继续把市场背景硬翻译成 `risk_regime -> capacity overlay`，而该路径已 formal `NO-GO` | `正式退役旧实现` | `l3_gene_mirror(MARKET)` |

---

## 5. GX2 判定

当前正式判定为：

1. `GX2 = not_triggered`

原因：

1. 本轮做的是治理裁决，不是主线吸收或代码拆迁
2. 当前运行默认路径没有发生切换
3. 未来若主线要吸收 `G5 / G6`，必须另开 migration package

---

## 6. Evidence Readout

`G7` 当前最重要的证据结论可以压缩成一句话：

旧 `IRS` 只证明了“行业相对排序问题成立”，旧 `MSS` 只证明了“它会真实改执行”；但第四战场已经拿出了更清楚的镜像历史尺和环境解释层，而旧 `MSS / IRS` 自身的升级路径已分别被“未完成绝对标定”和“formal NO-GO persists”卡死，因此当前最合理的治理裁决不是续修旧实现，而是正式退役旧实现、保留问题并改换入口。
