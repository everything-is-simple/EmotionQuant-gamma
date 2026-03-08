# 跨版本文档整理 TodoList

**状态**: `Active`  
**日期**: `2026-03-08`  
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

## 1. 整理铁律

- [ ] 以 `gamma` 为唯一落地仓库，不回退到 `alpha / beta` 作为当前执行仓库。
- [ ] `alpha / beta` 只作为设计资产来源，不直接覆盖 `gamma`。
- [ ] 不再用 `MVP` 裁掉核心算法语义，只裁实现范围。
- [ ] 不再让 `development-status` 承担设计正文。
- [ ] 不再让 `Frozen` 文档承担当前主线正文。
- [ ] 当前主线只保留一套稳定设计入口，不允许同一对象分散在多份正文里互相打架。

---

## 2. 先做版本清点

### 2.1 建立跨版本总表

- [x] 列出 `alpha / beta / gamma` 三版中所有关键设计文档入口。
- [ ] 给每份文档打标签：
  - `历史基线`
  - `可复用设计资产`
  - `已过时实现口径`
  - `当前主线入口`
  - `证据 / 状态 / 治理`
- [x] 建一个“对象 -> 文档来源”矩阵，至少覆盖：
  - Selector
  - PAS / BOF
  - IRS
  - MSS
  - Broker / Risk
  - Data Layer
  - Backtest / Report

### 2.2 锁定当前主线对象

- [x] 明确当前主线只先收 5 个关键对象：
  - Selector
  - PAS-trigger / BOF
  - IRS-lite
  - MSS-lite
  - Broker / Risk
- [x] 其余对象先不扩写，只保留入口和边界。

---

## 3. 再做文档分层

### 3.1 Full Design SoT 层

位置建议：

- `docs/design-v2/02-modules/`
- `docs/design-v2/03-algorithms/core-algorithms/`

Todo：

- [ ] 每个关键对象只保留一份当前正文。
- [ ] 每份正文统一 6 段结构：
  - 职责
  - 输入
  - 输出契约
  - 不负责什么
  - 决策规则 / 算法
  - 失败模式与验证证据
- [ ] `Frozen` 文档只保留历史口径和跳转链接。
- [ ] `down-to-top-integration.md` 只做集成骨架，不替代细案。

### 3.2 Implementation Spec 层

位置建议：

- `docs/spec/v0.01-plus/roadmap/`
- `docs/spec/v0.01-plus/governance/`

Todo：

- [ ] 为当前主线保留唯一实现方案入口。
- [ ] 每份实现方案只回答：
  - 这次实现什么
  - 不实现什么
  - 用什么契约
  - 如何验证 done
- [ ] 禁止在实现方案里重新发明算法定义。
- [ ] spec 只裁能力范围，不改设计本体。

### 3.3 Execution / Evidence / Status 层

位置建议：

- `docs/spec/common/records/`
- `docs/spec/v0.01-plus/evidence/`
- `docs/spec/v0.01-plus/records/`

Todo：

- [ ] `development-status.md` 只保留状态、风险、看板、版本记录。
- [ ] evidence 只保留实验与结果，不写设计正文。
- [ ] records 只保留阶段结论、归因与变更记录。
- [ ] 一次性整理报告不进入主入口首屏。

---

## 4. 再做跨版本资产回收

### 4.1 从 beta 回收什么

- [ ] 回收 `beta` 中成熟的设计深度。
- [ ] 优先回收：
  - information-flow
  - data-models
  - api
  - algorithm 骨架
- [ ] 只回收“设计原子”和“表达结构”，不回收已被淘汰的 top-down 语义。

### 4.2 从 alpha 回收什么

- [ ] 回收 `alpha` 中已经跑过多轮审视的治理结构和沉淀。
- [ ] 优先回收：
  - records 的组织方式
  - steering 的约束表达
  - cards / roadmap 的拆解粒度经验
- [ ] 不把旧治理体系整套搬回 `gamma`。

### 4.3 回收方法

- [ ] 每次只回收一个对象，不做全量搬运。
- [ ] 每次回收都写清楚：
  - 来源文件
  - 回收了什么
  - 为什么保留
  - 为什么裁掉其他部分

---

## 5. 再做 gamma 收口

### 5.1 当前主线入口

- [ ] `docs/design-v2/README.md` 明确当前主线入口。
- [ ] `docs/design-v2/03-algorithms/core-algorithms/README.md` 明确 5 个关键对象入口。
- [ ] `docs/spec/v0.01-plus/README.md` 只做当前主线实现入口。
- [ ] `docs/README.md` 只做总导航，不重复正文。

### 5.2 Frozen 文档收口

- [ ] 把 `selector-design.md` 改成纯历史文档。
- [ ] 把 `strategy-design.md` 改成纯历史文档。
- [ ] 把 `broker-design.md` 改成纯历史文档。
- [ ] 对仍保留的历史正文统一加“当前主线跳转入口”。

### 5.3 状态文档收口

- [ ] 给 `development-status.md` 加显式边界声明。
- [ ] 把设计解释从 status 文档移走。
- [ ] 把“当前主线是否 GO / NO-GO”保留在 status，而不是写到算法正文里。

---

## 6. 再做执行闭环

### 6.1 先冻结 Full Design SoT

- [ ] 把当前主线 5 个关键对象的正文冻结成第一版稳定设计。
- [ ] 之后实现期不允许随手改设计。

### 6.2 再裁唯一 Implementation Spec

- [ ] 从稳定设计里裁一版当前实现方案。
- [ ] 该实现方案必须明确：
  - 本轮目标
  - 非目标
  - 契约
  - 测试
  - artifact
  - done 标准

### 6.3 最后再拆 roadmap / phase / task

- [ ] roadmap 只从 Implementation Spec 往下拆。
- [ ] phase 只拆实现步骤，不改算法定义。
- [ ] task 只对实现、测试、证据负责。

---

## 7. 完成标准

满足以下条件，才算这轮文档整理完成：

- [ ] 三版文档资产来源被梳理清楚。
- [ ] `gamma` 中 3 层结构被明确隔离。
- [ ] 当前主线 5 个关键对象都有独立稳定正文。
- [ ] `Frozen` 文档不再承担当前主线正文。
- [ ] `development-status.md` 不再承担设计解释。
- [ ] roadmap / phase / spec 只从实现方案往下拆。
- [ ] `check_docs.ps1` 全绿。

---

## 8. 建议执行顺序

按下面顺序做，不跳步：

1. 先做跨版本总表
2. 再锁定 5 个关键对象
3. 再收 `Full Design SoT`
4. 再裁 `Implementation Spec`
5. 再清 `development-status / evidence / records`
6. 最后才整理 roadmap / phase / task

---

## 9. 本轮起点

本轮整理建议从下面 3 件事开始：

- [x] 先补一份“跨版本对象映射总表”
  - 产物：`blueprint/01-full-design/01-cross-version-object-mapping-matrix-20260308.md`
- [x] 再检查当前 5 个关键对象的正文是否还缺设计原子
  - 产物：`blueprint/01-full-design/02-mainline-design-atom-gap-checklist-20260308.md`
- [ ] 再把 `v0.01-plus` 当前实现方案改成只承担实现职责
