# EmotionQuant 系统宪法 v1

**状态**: `Active`
**日期**: `2026-03-12`
**对象**: `当前系统不可违背的跨线铁律`
**变更规则**: `只允许在上游正式 SoT / Gate / record 已变更后同步修订；不得先于正式裁决改写。`

---

## 1. 定位

本文不是新的设计正文，也不是新的 phase card。

本文只做一件事：

`把已经被正式记录裁决过的跨线硬约束，编纂成一份统一可引用的系统宪法。`

这里冻结的是：

1. 当前系统的跨线边界
2. 当前默认运行口径
3. alpha 证明与主线升格的合法顺序
4. 模块职责边界
5. 已判 `NO-GO` 路线的复活条件

---

## 2. 使用规则

1. 本文只收录已经被正式记录裁决过的约束，不新增未裁决业务结论。
2. 若与上游 `blueprint/`、`docs/spec/v0.01-plus/records/`、`normandy/` 正式 record 冲突，以上游已裁决文件为准，随后必须同步修订本文。
3. 讨论当前设计正文时，仍以 `blueprint/` 为准；本文负责跨线治理铁律，不替代模块设计正文。
4. 讨论研究线边界时，仍以 `normandy/README.md` 与对应 `record` 为准；本文只把已裁决边界编纂为统一规则。

---

## 3. 十条铁律

1. 历史线、主线、研究线必须永久分治。
   `docs/spec/v0.01` 只承载历史，`blueprint/ + docs/spec/v0.01-plus/` 只承载当前主线，`normandy/` 只承载研究线；研究线不得直接宣布主线改写。

2. 当前正式默认运行路径只能是 `legacy_bof_baseline`。
   在新的正式 record 与 direct Gate replay 明确打赢它之前，任何新链路都不得抢默认。

3. 当前研发主线必须执行 `alpha-first` 顺序。
   先证明 raw alpha 来源，再做 stability / purity，再做 exit decomposition，最后才允许重新接入全链系统验证。

4. `BOF` 是当前唯一固定 baseline / control。
   在出现新的正式胜者之前，`BOF` 不再作为待证对象，而是所有候选的统一尺子。

5. 当前系统主链固定为 `Selector -> PAS -> IRS -> MSS -> Broker -> Backtest / Report -> Gate`。
   不得私自改写为别的职责顺序。

6. `Selector` 只做基础过滤、规模控制和候选准备。
   它不得承担市场 gate、行业硬过滤或最终交易决策。

7. `PAS` 负责识别 alpha 来源；`IRS` 只做后置行业增强；`MSS` 只做市场级风险覆盖。
   `IRS` 不得回到前置硬过滤；`MSS` 不得进入个股横截面总分，也不得回到前置硬 gate。

8. `Broker` 只负责 `T+1 Open` 执行、拒单和生命周期。
   它不负责定义策略真伪；收益好坏的最终判定优先回到 `PAS / entry` 与上游归因链，不允许让执行层代替策略层宣判胜负。

9. 任何候选的升格都必须满足同一条合法路径。
   先在研究线证明自己是独立 alpha，再通过稳定性审查，再用正式 Gate replay 打赢 `legacy_bof_baseline`；否则一律不得升格为新 baseline 或新默认主线。

10. 系统只允许重拆积木、重搭积木，不允许靠局部参数微调伪造胜利。
    当前已被判 `NO-GO` 的路线和候选，未经新的治理段与新证据链，不得借尸还魂。

---

## 4. 上游依据

1. `docs/spec/common/records/repo-line-map-20260312.md`
2. `docs/spec/common/records/development-status.md`
3. `docs/design-migration-boundary.md`
4. `blueprint/01-full-design/09-mainline-system-operating-baseline-20260309.md`
5. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
6. `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`
7. `docs/spec/v0.01-plus/records/v0.01-plus-phase-4-gate-decision-20260311.md`
8. `docs/spec/v0.01-plus/records/v0.01-plus-phase-4-gate-replay-size-only-overlay-20260311.md`
9. `normandy/README.md`
10. `normandy/03-execution/records/00-normandy-interim-conclusions-20260312.md`
11. `normandy/03-execution/records/01-phase-n1-bof-conclusion-record-20260312.md`
12. `normandy/03-execution/records/02-phase-n1-5-second-alpha-record-20260312.md`
13. `normandy/03-execution/records/03-phase-n1-6-fb-dossier-record-20260312.md`

---

## 5. 一句话执行口径

`运行上站在 legacy，研发上站在 alpha-first；先认出胜利者，再让系统服务胜利者。`
