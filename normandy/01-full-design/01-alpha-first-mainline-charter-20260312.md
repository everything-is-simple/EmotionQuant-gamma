# Normandy Alpha-First Mainline Charter

**状态**: `Active`  
**日期**: `2026-03-12`  
**对象**: `第二战场正式设计总纲`  
**变更规则**: `只允许在上游正式 record / gate / SoT 已变更后同步修订；不得先于正式裁决改写。`

---

## 1. 定位

本文不是新的版本基线，也不是新的 phase card。

本文只做一件事：

`把 Normandy 第二战场已经被正式记录推出来的开发宗旨、架构思想、对象分层和升格法，收敛成一份可直接执行的 full-design 总纲。`

这里写死三条边界：

1. `Normandy` 是研究线，不是新的版本线。
2. `Normandy` 不直接改写 `blueprint / v0.01-plus` 主线裁决。
3. `Normandy` 只负责回答：
   - 谁天生有 alpha
   - 谁只是在放大 alpha
   - 谁其实在吞掉 alpha

---

## 2. 为什么现在必须激活 Full Design

`2026-03-12` 之前，`Normandy` 的 `01-full-design/` 只是占位层。

现在这个占位条件已经失效，因为下面这些结论已经被正式 record 固定：

1. `BOF` 已重新钉实为当前唯一可信的 `PAS raw alpha baseline`
2. `FB` 已成为当前唯一通过门槛的第二 alpha 候选，但带风险标记
3. `SB` 已被明确判为“保留对象，但先走 refinement 队列”
4. `TACHI_CROWD_FAILURE` 已形成 formal contract，但当前只保留为 `observation-only`
5. `MSS / Broker` 微调救主线这条路已经被 `Phase 4 / 4.1` 判为不成立

因此现在不再适合只靠执行卡和 interim record 推进。

现在必须把：

1. 第二战场到底在解决什么问题
2. 第二战场的系统架构应该怎么理解
3. 什么对象属于 baseline / promotion queue / no-go queue
4. 候选如何合法升格回主线

正式写进 `01-full-design/`。

---

## 3. 开发宗旨

第二战场的开发宗旨固定为：

`看清迷雾，寻找 alpha；辨别胜利者是谁、失败者是谁，然后选择站对。`

更具体地说，系统当前不再把主要问题写成：

`怎样继续微调一条已经输掉的整链。`

系统当前把主要问题重写为：

1. 哪些 `PAS / entry object` 天生就有 raw alpha
2. 哪些模块只是放大已经存在的 alpha
3. 哪些模块当前在吞掉 alpha

所以第二战场的根本方法也固定为：

`先认出胜利者，再让系统服务胜利者。`

这里还要再写死一条方法论边界：

`我们的系统只能重拆积木、重搭积木；不能靠局部参数微调伪造胜利。`

---

## 4. 架构思想

当前系统的正式主链仍然是：

`Selector -> PAS -> IRS -> MSS -> Broker -> Backtest / Report -> Gate`

但第二战场对这条主链的理解顺序，必须改成 `alpha-first`：

1. 先固定 `BOF` 尺子
2. 再证明谁有独立 `PAS raw alpha`
3. 再做 `stability / purity`
4. 再做 `exit decomposition`
5. 最后才允许把胜出对象重新接回 `IRS / MSS / Broker`

这意味着：

1. alpha 的主要胜负，发生在 `PAS / entry`
2. `IRS` 的职责是放大已被证明的赢家，而不是当前置裁判
3. `MSS` 的职责是控制市场环境和容量伤害，而不是创造赢家
4. `Broker` 的职责是把语义落实成真实执行，而不是代替策略层宣判赢家

换句话说：

`Normandy` 不是在发明新棋子，而是在现有棋子里重新分辨：谁是发光体，谁是放大器，谁是摩擦项。`

---

## 5. 模块职责

### 5.1 `Selector`

1. 只负责基础过滤、规模控制和候选准备
2. 不承担市场 gate、行业硬过滤或最终交易决策
3. 不负责定义赢家

### 5.2 `PAS`

1. 负责识别和证明 entry alpha
2. 当前第二战场的真正主战场就在这里
3. 胜负裁决优先发生在这一层

### 5.3 `IRS`

1. 只做后置行业增强
2. 只允许服务已经证明过的 entry winner
3. 不允许回到前置硬过滤

### 5.4 `MSS`

1. 只做市场级风险覆盖
2. 不进入个股横截面总分
3. 不允许继续被拿来冒充 alpha 修复器

### 5.5 `Broker`

1. 只负责 `T+1 Open` 执行、拒单和生命周期
2. 不负责定义策略真伪
3. 收益好坏的最终归因优先回到 `PAS / entry` 与上游归因链

---

## 6. 当前对象裁决

### 6.1 Baseline / 边界

1. 运行默认口径：`legacy_bof_baseline`
2. 研究默认尺子：`BOF`
3. 当前研发主线：`Normandy alpha-first`

这里必须明确区分：

1. 运行上，站在 `legacy`
2. 研发上，站在 `alpha-first`

### 6.2 Promotion Queue

1. `FB`
   - 当前定位：`qualified_second_alpha_candidate_with_risk_flags`
   - 当前动作：先做 `N1.7 stability / purity`
2. `SB`
   - 当前定位：对象保留，但 detector 过宽
   - 当前动作：进入 `refinement / no-go` 判定队列
3. `TACHI_CROWD_FAILURE`
   - 当前定位：首轮可审判样本，但当前不是独立 alpha
   - 当前动作：只保留为 refinement / backlog

### 6.3 Observation Pool

1. `RB_FAKE`
   - 当前更像 `BOF` 的 Volman 化窄子集
2. `PB / TST / CPB / YTC5_ANY`
   - 当前不再按“谁接班 BOF”的方式平行竞争

### 6.4 No-Go Queue

1. `v0_01_dtt_pattern_plus_irs_mss_score` 作为正式默认运行路径
2. `carryover_buffer(1)` 作为救主线整改候选
3. `size_only_overlay` 作为救主线整改候选
4. `BPB` 当前 standalone detector 路线
5. “继续强化 `MSS hard gate / IRS 前置硬过滤`” 作为系统方向

---

## 7. 合法升格法

第二战场任何候选的升格路径，固定为：

1. 先在研究线证明自己是独立 `raw alpha`
2. 再通过 `stability / purity` 审查
3. 若仍值得继续，进入受控 `exit decomposition`
4. 之后才允许重新接入 `IRS / MSS / Broker`
5. 最后必须用正式 Gate replay 打赢 `legacy_bof_baseline`

在这条路径完成之前：

1. 任何候选都不得直接升格为新 baseline
2. 任何候选都不得直接宣布主线改写
3. 不允许跳过 provenance 去讨论整链胜负

---

## 8. 当前文档与执行物件裁决

当前立即需要补齐的物件，只有两类：

1. `01-full-design/` 正式总纲
2. `01-full-design/README.md` 的激活入口

当前不需要立刻补新的执行卡，原因也固定为：

1. 当前 active card 仍然是 `03-execution/04-phase-n1-7-fb-stability-and-purity-card-20260312.md`
2. `N1.9 / SB refinement or no-go` 与 `N2 / controlled exit decomposition` 的下一张卡，取决于 `N1.7` 的正式结论
3. 在 `N1.7` 结束前，先把架构思想和晋升法写死，比提前堆更多执行卡更重要

换句话说：

`现在最缺的不是更多任务卡，而是一个不再摇摆的研究主线 SoT。`

---

## 9. 上游依据

1. `docs/spec/common/records/system-constitution-v1.md`
2. `docs/spec/common/records/repo-line-map-20260312.md`
3. `blueprint/01-full-design/09-mainline-system-operating-baseline-20260309.md`
4. `docs/spec/v0.01-plus/records/v0.01-plus-phase-4-gate-decision-20260311.md`
5. `docs/spec/v0.01-plus/records/v0.01-plus-phase-4-gate-replay-size-only-overlay-20260311.md`
6. `normandy/03-execution/records/00-normandy-interim-conclusions-20260312.md`
7. `normandy/03-execution/records/01-phase-n1-bof-conclusion-record-20260312.md`
8. `normandy/03-execution/records/02-phase-n1-5-second-alpha-record-20260312.md`
9. `normandy/03-execution/records/03-phase-n1-6-fb-dossier-record-20260312.md`
10. `normandy/03-execution/records/04-phase-n1-8-tachibana-contrary-alpha-record-20260312.md`

---

## 10. 一句话总纲

`运行上站在 legacy，研发上站在 alpha-first；先认出谁天生有 alpha，再让 IRS / MSS / Broker 去服务已经证明过的赢家。`
