# G7 记录: MSS / IRS 改造或退役决策已完成

**状态**: `Completed`  
**日期**: `2026-03-16`

---

## 1. 目标

本记录用于把第四战场 `G7 / MSS-IRS refactor-or-retire decision` 的正式裁决写死。

这张记录只回答四件事：

1. 旧 `MSS / IRS` 哪些问题仍然有价值
2. 旧 `MSS / IRS` 哪些实现与语义已经应当退役
3. 第四战场当前给出的替代入口是什么
4. 当前是否需要触发 `GX2 / targeted migration package`

---

## 2. Formal Inputs

`G7` 本轮只承认以下 formal inputs：

1. `gene/03-execution/evidence/10-phase-g7-mss-irs-decision-evidence-20260316.md`
2. `gene/03-execution/records/07-phase-g4-self-history-ruler-validation-record-20260316.md`
3. `gene/03-execution/records/08-phase-g5-market-industry-index-mirror-ruler-record-20260316.md`
4. `gene/03-execution/records/09-phase-g6-bof-pb-cpb-conditioning-record-20260316.md`
5. `docs/spec/v0.01-plus/records/v0.01-plus-phase-2-exit-20260311.md`
6. `docs/spec/v0.01-plus/records/v0.01-plus-phase-3-exit-20260311.md`
7. `docs/spec/v0.01-plus/records/v0.01-plus-phase-4-gate-decision-20260311.md`
8. `docs/spec/v0.01-plus/records/v0.01-plus-phase-4-gate-replay-size-only-overlay-20260311.md`

当前明确不做：

1. 不新增新的回测或主库重算
2. 不在本卡继续微调旧 `MSS / Broker`
3. 不在没有显式 migration package 的情况下回写主线默认参数

---

## 3. 决策摘要

当前 `G7` 的正式决策矩阵固定为：

| 对象 | 保留的问题 | 退役的旧实现/旧语义 | 正式结论 | 替代入口 |
|---|---|---|---|---|
| `IRS-lite` | 行业相对强弱、行业相对位置 | 旧 `IndustryScore.score -> signal.irs_score` 单分数字义 | `RETIRE_OLD_IMPLEMENTATION_KEEP_PROBLEM` | `G5 / l3_gene_mirror(INDUSTRY)` |
| `MSS-lite` | 市场过热、宽度转弱、背景降温 | 旧 `MarketScore.signal -> risk_regime -> Broker capacity overlay` 路径 | `RETIRE_OLD_IMPLEMENTATION` | `G5 / l3_gene_mirror(MARKET)` |

也就是说：

1. 旧 `IRS` 不是“继续升级”
2. 旧 `MSS` 不是“再修一轮参数”
3. 第四战场保留的是它们原来试图回答的问题，不保留旧实现本身的升级资格

---

## 4. 为什么旧 IRS 不再保留为未来主入口

### 4.1 旧 `IRS` 证明过“排名问题存在”，但没证明“旧分数体系成立”

`Phase 2` 的正式口径已经写死：

1. `IRS ranking chain completed`
2. `absolute score calibration not yet claimed`

这说明旧 `IRS` 当前最多证明了：

`行业排序问题是一个真实问题`

但没有证明：

`旧 irs_score 这套单分数字义已经足够稳，可以继续当未来主入口`

### 4.2 第四战场已经给出了更干净的行业替代口径

`G5` 已经正式把行业镜像尺落到 `l3_gene_mirror`，并且写死了两件关键事：

1. 必须同时保留 `mirror_gene_rank` 和 `primary_ruler_rank`
2. 真正稳定能进入镜像层的辅助确认是宽度比率，而不是旧 `MSS / IRS` 语义包

这意味着旧 `IRS` 当年想回答的“行业相对强弱”问题没有消失，  
但更合适的入口已经从：

`旧 IndustryScore / irs_score`

切换成了：

`行业镜像尺 + 主尺排序 + 宽度辅助确认`

### 4.3 因此当前对旧 IRS 的正式裁决

当前固定为：

1. 退役旧 `IRS-lite` 的未来升级资格
2. 不再把旧 `irs_score` 作为行业主入口继续漂
3. 保留其历史 replay / evidence 身份
4. 用 `G5` 的行业镜像尺接管问题域

---

## 5. 为什么旧 MSS 正式退役

### 5.1 旧 `MSS` 证明过“会真实改 Broker”，但没证明“值得继续当默认路径”

`Phase 3` 只证明了：

1. `MSS` 状态层已正式落库
2. Broker 已按 `risk_regime` 消费容量倍率
3. `regime sensitivity` 有真实证据

但同一份正式记录也明确写定：

`MSS 已在当前短窗证明收益改进`

这句话当前不能写。

### 5.2 Gate 与 remediation 已经把旧 MSS 的升级空间压实了

`Phase 4 / Gate` 的正式裁决是 `NO-GO`，而且已经明确：

1. `IRS` 排序层不是这轮主嫌疑
2. 主要变化发生在 `MSS -> Broker` 的容量执行层

接着 `Phase 4.1` 又把旧 `MSS / Broker` 的整改空间一路拆到头：

1. 先确认 `max_positions shrink + position carryover + slot scarcity` 是主因链
2. 再冻结 `carryover_buffer(1)`
3. 最后冻结 `size_only_overlay`

但最终 formal replay 仍然写死：

1. `size_only_overlay` 仍未推翻 `legacy_bof_baseline`
2. `MAX_POSITIONS` 拒单差异已归零后，失败主因已转成 `trade_set + quantity` 路径
3. `Phase 4.1 / MSS-Broker Remediation` 正式关闭

这已经足够说明：

`旧 MSS 不是还差最后一点微调，而是旧执行路径本身不再值得继续 promotion`

### 5.3 第四战场给出的市场替代入口比旧 MSS 更贴题

`G4 ~ G5` 已把第四战场的主口径收口为：

1. 个股/市场/行业的历史极端度、过热度、衰竭度
2. 市场镜像尺 + 宽度比率辅助确认

而不是：

1. 强行把市场单分数翻译成 `risk_on / risk_off`
2. 再把它直接乘到 Broker 容量上

### 5.4 因此当前对旧 MSS 的正式裁决

当前固定为：

1. 旧 `MSS-lite` 正式退役为“历史实现与证据对象”
2. 不再作为未来默认风控 overlay、默认 promotion 路径或继续微调对象
3. 现有代码和 evidence 先保留，不做删除式清理
4. 若未来仍要重开，必须提出新的 targeted hypothesis，而不是续修旧 overlay

---

## 6. 第四战场正式替代入口

当前 `G7` 固定写定第四战场的替代入口为：

### 6.1 市场层

1. `l3_gene_mirror` 里的 `MARKET` 行
2. `primary_ruler_metric / primary_ruler_value`
3. `mirror_gene_rank`
4. `support_rise_ratio`
5. `support_strong_ratio / support_new_high_ratio`

### 6.2 行业层

1. `l3_gene_mirror` 里的 `INDUSTRY` 行
2. `mirror_gene_rank`
3. `primary_ruler_rank`
4. `support_rise_ratio`

### 6.3 形态环境层

1. `l3_gene_conditioning_eval`
2. `BOF / BPB / PB / TST / CPB` 的 pattern-baseline 对照
3. `current_wave_direction / wave_age_band / magnitude_band / 123 / 2B / streak_bucket`

这意味着第四战场当前能提供的是：

1. 市场/行业/个股所处的历史位置
2. 宽度与极端度的背景确认
3. 各类 pattern 在什么环境里更值得打

而不是：

1. 新的主 alpha
2. 新的硬过滤器
3. 旧 `MSS / IRS` 的换皮续命

---

## 7. 依赖处置边界与 GX2 判定

### 7.1 当前不触发 `GX2`

本轮正式写定：

1. `GX2 / targeted migration package = not_triggered`

原因固定为：

1. `G5` 已明确没有出现必须集中迁移旧表、旧脚本、旧入口的阻塞级重构压力
2. 本轮做的是治理裁决，不是代码删除或主线吸收
3. 当前默认路径仍是 `legacy_bof_baseline`，不存在必须立即迁移的运行面切换

### 7.2 当前依赖处置边界

本轮只冻结下面这些边界：

1. 旧 `src/selector/irs.py` 与 `src/selector/mss.py` 继续保留
2. 它们当前只保留为历史 replay、evidence 回看、归档参考对象
3. 不再把它们写成第四战场下一步默认改造对象
4. 若未来要把 `G5 / G6` 正式吸收到主线，必须新开显式 migration package

---

## 8. 当前不该再做的事

`G7` 完成后，当前明确不该再做：

1. 继续沿旧 `MSS / Broker` 做局部倍率微调
2. 把旧 `irs_score` 误读成“行业历史尺已经做好”
3. 把 `G6` 条件层误写成硬过滤器
4. 因为第四战场已有镜像尺，就直接宣布 mainline 默认路径切换
5. 在没有新假设和新 migration package 时继续给旧 `MSS / IRS` 保留 promotion 幻觉

---

## 9. 正式结论

当前 `G7 / MSS-IRS refactor-or-retire decision` 的正式结论固定为：

1. 旧 `IRS-lite` 退役旧实现，不保留旧单分数字义，问题域由 `G5` 行业镜像尺接管
2. 旧 `MSS-lite` 正式退役为历史实现，不再继续作为默认 overlay 或整改主线
3. 第四战场当前给出的正式替代入口是 `G5 / G6`，不是旧 `MSS / IRS` 续修
4. `GX2` 当前不触发
5. `G7` 完成后，第四战场下一张主线卡进入 `G8 / gene campaign closeout`

---

## 10. 一句话结论

`G7` 已把旧 `MSS / IRS` 的去留写死：保留问题，不保留旧实现；第四战场当前真正留下来的，是镜像历史尺和形态环境解释层，而不是旧分数体系的二次翻修。
