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

它们分别负责：

1. 定整理顺序和收口标准
2. 定跨版本对象来源
3. 定当前主线 5 个关键对象还缺哪些设计原子

---

## 5. 使用规则

1. 先写 `01-full-design/`，再写 `02-implementation-spec/`，最后才写 `03-execution/`。
2. 不允许在 `03-execution/` 里重新发明设计。
3. 不允许再把 `development-status`、一次性 evidence、旧 `Frozen` 正文当作当前设计正文。
4. 若需要复用 `alpha / beta` 的成熟设计，只能提炼后写入 `blueprint/`，不能直接把旧文档当当前正文。

---

## 6. 当前目标

先把以下 5 个关键对象重新沉淀成新版稳定设计：

1. Selector
2. PAS-trigger / BOF
3. IRS-lite
4. MSS-lite
5. Broker / Risk
