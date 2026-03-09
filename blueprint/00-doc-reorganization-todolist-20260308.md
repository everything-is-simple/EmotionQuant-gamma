# 跨版本文档整理 TodoList

**状态**: `Active`  
**日期**: `2026-03-09`  
**目标仓库**: `G:\EmotionQuant-gamma`  
**源版本**:

1. `G:\EmotionQuant\EmotionQuant-beta\docs`
2. `G:\EmotionQuant\EmotionQuant-beta\Governance`
3. `G:\EmotionQuant\EmotionQuant-alpha\docs`
4. `G:\EmotionQuant\EmotionQuant-alpha\Governance`
5. `G:\EmotionQuant-gamma\docs`

---

## 0. 总目标

把三版文档重新厘清成 3 层：

1. `Full Design SoT`
2. `Implementation Spec`
3. `Execution / Evidence / Status`

并且固定一条工作顺序：

`先冻结完整设计 -> 再裁实现方案 -> 再拆 roadmap / phase / spec / task`

---

## 1. 已完成事项

### 1.1 权威入口与目录分层

- [x] `gamma` 已固定为唯一当前执行仓库。
- [x] `alpha / beta` 已降级为设计资产来源，不再作为当前正文落点。
- [x] `blueprint/` 已立成新版设计权威层。
- [x] `docs/spec/` 已收口为治理 / roadmap / evidence / records / status 层。
- [x] `docs/design-v2/` 已收口为 `v0.01 Frozen` 历史基线层。
- [x] `docs/README.md`、`docs/design-v2/README.md`、`docs/spec/v0.01-plus/README.md` 已统一改成入口导航文。
- [x] `development-status.md` 已显式声明不再承担当前主线设计正文。

### 1.2 跨版本清点与对象锁定

- [x] 已列出 `alpha / beta / gamma` 三版关键设计入口。
- [x] 已产出跨版本对象映射总表。
  - 产物：`blueprint/01-full-design/01-cross-version-object-mapping-matrix-20260308.md`
- [x] 已锁定当前主线第一批 5 个关键对象。
  - `Selector`
  - `PAS-trigger / BOF`
  - `IRS-lite`
  - `MSS-lite`
  - `Broker / Risk`
- [x] 其余对象已暂时降级为“保留入口和边界，不进入当前补原子批次”。

### 1.3 第一层 Full Design 与下游拆解

- [x] 已产出 5 份 `contract supplement`，先把当前主线字段、trace、fallback 和时序边界钉住。
  - `03-selector-contract-supplement-20260308.md`
  - `04-pas-trigger-bof-contract-supplement-20260308.md`
  - `05-irs-lite-contract-supplement-20260308.md`
  - `06-mss-lite-contract-supplement-20260308.md`
  - `07-broker-risk-contract-supplement-20260308.md`
- [x] 已产出当前主线唯一 implementation spec 首稿。
  - 产物：`blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
- [x] 已产出当前主线 execution breakdown 首稿。
  - 产物：`blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`

### 1.4 第二层 Full Design 推进

- [x] 已补 `PAS` 最小可交易形态层正文版。
  - 产物：`blueprint/01-full-design/08-pas-minimal-tradable-design-20260309.md`
- [x] 已补 `IRS` 最小可交易排序层正文版。
  - 产物：`blueprint/01-full-design/09-irs-minimal-tradable-design-20260309.md`
- [x] 已补 `MSS` 最小可交易风控层正文版。
  - 产物：`blueprint/01-full-design/10-mss-minimal-tradable-design-20260309.md`
- [x] 已补设计来源登记。
  - 产物：`blueprint/01-full-design/11-design-source-register-20260309.md`

### 1.5 机器检查

- [x] `scripts/ops/check_docs.ps1` 当前全绿。

---

## 2. 剩余事项

### 2.1 Full Design 最后封口

- [x] 把 `10` 从“骨架版”补成“正文版”。
- [x] 对 `PAS / IRS / MSS` 三个对象补齐统一 6 段结构：
  - 职责
  - 输入
  - 输出
  - 不负责什么
  - 决策规则 / 算法
  - 失败模式与验证证据
- [x] 把 `03/04/05/06/07` 的角色正式收口为 `contract annex`，并固定 `08/09/10` 为各自主正文，避免并列成双 SoT。

### 2.2 来源与标签收口

- [ ] 基于 `11-design-source-register-20260309.md`，把“来源文件 / 回收内容 / 裁掉内容”继续补到对象级正文中。
- [ ] 给当前第一批关键对象补齐统一标签判断：
  - `历史基线`
  - `可复用设计资产`
  - `已过时实现口径`
  - `当前主线入口`
  - `证据 / 状态 / 治理`

### 2.3 下游文档同步

- [ ] 基于 `08/09/10` 主正文，回写 `02-implementation-spec/` 的上游锚点和表述。
- [ ] 基于 `08/09/10` 主正文，确认 `03-execution/` 是否还存在任何“提前替设计做决定”的语句。
- [ ] 待主正文收口后，再决定是否需要给 `docs/spec/v0.01-plus/roadmap/` 做二次降噪。

### 2.4 进入实现前的最后门槛

- [ ] `01-full-design/` 内部不再自相矛盾：
  - 不再一边说“细原子还没补够”，一边直接进入实现
- [ ] 当前主线每个关键对象只有一个主正文落点，其他文档都退为补充、附录或下游裁剪文
- [ ] 然后才正式进入 `Phase 0 / Task P0-A ~ P0-E`

---

## 3. 完成标准

满足以下条件，才算这轮文档整理真正完成：

- [x] 三版文档资产来源已显式登记清楚。
- [x] `gamma` 的 `Full Design / Implementation Spec / Execution` 已彻底隔离。
- [x] `PAS / IRS / MSS` 已全部进入“正文版”。
- [x] `contract supplement` 与主正文的主次关系已收口清楚。
- [x] `Frozen` 文档只承担历史基线，不再被误读为当前正文。
- [x] implementation / execution 不再替设计层补语义。
- [x] `check_docs.ps1` 持续全绿。

---

## 4. 当前建议顺序

从本清单改写后，推荐顺序固定为：

1. 先把 `08/09/10` 的来源登记和 annex 关系同步固化
2. 再回写 `02-implementation-spec/` 的上游锚点和表述
3. 再确认 `03-execution/` 去掉替设计做决定的语句
4. 最后才进入 `Phase 0`
