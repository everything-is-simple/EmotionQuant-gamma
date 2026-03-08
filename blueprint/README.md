# Blueprint

**状态**: `Active`  
**日期**: `2026-03-08`

---

## 1. 定位

`blueprint/` 是 `EmotionQuant-gamma` 根目录下的全新设计空间。

它的职责只有一个：

`承载新版、分层清晰、与旧 docs 体系明确隔离的设计书。`

这里不是旧 `docs/` 的补丁区，也不是一次性整理报告的堆放区。

---

## 2. 和旧体系的边界

旧体系仍然保留在：

1. `docs/`
2. `G:\EmotionQuant\EmotionQuant-beta\docs`
3. `G:\EmotionQuant\EmotionQuant-beta\Governance`
4. `G:\EmotionQuant\EmotionQuant-alpha\docs`
5. `G:\EmotionQuant\EmotionQuant-alpha\Governance`

这些内容现在只作为：

1. 历史基线
2. 设计资产来源
3. 对照与回退参考

不再作为 `blueprint/` 的正文存放位置。

---

## 3. 分层结构

`blueprint/` 目前固定为 3 层：

1. `01-full-design/`
   - 完整设计 SoT
   - 一旦冻结，不因实现压力随意改写

2. `02-implementation-spec/`
   - 从完整设计中裁出的当前实现方案
   - 只定义本轮实现范围，不重写算法本体

3. `03-execution/`
   - roadmap / phase / task / checklists
   - 只服务执行，不承担设计正文

---

## 4. 当前入口

当前已经落下的入口文件有：

- `00-doc-reorganization-todolist-20260308.md`
- `01-full-design/01-cross-version-object-mapping-matrix-20260308.md`
- `01-full-design/02-mainline-design-atom-gap-checklist-20260308.md`
- `01-full-design/03-selector-contract-supplement-20260308.md`
- `01-full-design/04-pas-trigger-bof-contract-supplement-20260308.md`
- `01-full-design/05-irs-lite-contract-supplement-20260308.md`
- `01-full-design/06-mss-lite-contract-supplement-20260308.md`
- `01-full-design/07-broker-risk-contract-supplement-20260308.md`
- `02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
- `03-execution/01-current-mainline-execution-breakdown-20260308.md`

它们分别负责：

1. 定整理顺序和收口标准
2. 定跨版本对象来源
3. 定当前主线 5 个关键对象还缺哪些设计原子
4. 定 `Selector` 的正式候选契约、兼容映射与 trace 口径
5. 定 `PAS-trigger / BOF` 的输入快照、formal signal、trace 与 sidecar 边界
6. 定 `IRS-lite` 的行业层契约、signal 附着规则与 fallback 口径
7. 定 `MSS-lite` 的市场层契约、overlay 矩阵与执行归因口径
8. 定 `Broker / Risk` 的正式执行契约、幂等键、时序与生命周期追溯口径
9. 从 `01-full-design/` 裁出当前主线唯一实现方案首稿
10. 把唯一实现方案拆成可直接执行的 phase / task / checklist

---

## 5. 使用规则

1. 先写 `01-full-design/`，再写 `02-implementation-spec/`，最后才写 `03-execution/`。
2. 不允许在 `03-execution/` 里重新发明设计。
3. 不允许再把 `development-status`、一次性 evidence、旧 `Frozen` 正文当作当前设计正文。
4. 若需要复用 `alpha / beta` 的成熟设计，只能提炼后写入 `blueprint/`，不能直接把旧文档当当前正文。

---

## 6. 当前目标

当前 `01-full-design/` 第一批 5 个关键对象已经补齐：

1. Selector
2. PAS-trigger / BOF
3. IRS-lite
4. MSS-lite
5. Broker / Risk

当前 `02-implementation-spec/` 也已经落下第一份正文：

1. `01-current-mainline-implementation-spec-20260308.md`

当前 `03-execution/` 也已经落下第一份正文：

1. `01-current-mainline-execution-breakdown-20260308.md`

下一步进入：

1. `Phase 0 / Task P0-A ~ P0-E`
2. 先做契约与 trace 收口
