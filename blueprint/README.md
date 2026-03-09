# Blueprint

**状态**: `Active`  
**日期**: `2026-03-09`

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
- `01-full-design/08-pas-minimal-tradable-design-20260309.md`
- `01-full-design/09-irs-minimal-tradable-design-20260309.md`
- `01-full-design/10-mss-minimal-tradable-design-20260309.md`
- `01-full-design/11-design-source-register-20260309.md`
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
9. 定 `PAS` 最小可交易形态层的算法正文
10. 定 `IRS` 最小可交易排序层的算法正文
11. 定 `MSS` 最小可交易风控层的算法正文
12. 登记当前主线设计来源、回收范围与裁剪边界
13. 存放 `alpha` 导入算法原稿（仅来源留档，不是当前 SoT）
14. 从 `01-full-design/` 裁出当前主线唯一实现方案首稿
15. 把唯一实现方案拆成可直接执行的 phase / task / checklist

## 4.1 设计来源声明

`01-full-design/` 中的算法文件来源：

| 文件/目录 | 来源 | 当前角色 | 说明 |
|------|------|------|------|
| `03-selector-contract-supplement-20260308.md` | gamma 新增 | `Selector contract annex` | 当前主线特有 |
| `04-pas-trigger-bof-contract-supplement-20260308.md` | gamma 新增 | `PAS contract annex` | 当前主线特有 |
| `05-irs-lite-contract-supplement-20260308.md` | gamma 新增 | `IRS contract annex` | 当前主线特有 |
| `06-mss-lite-contract-supplement-20260308.md` | gamma 新增 | `MSS contract annex` | 当前主线特有 |
| `07-broker-risk-contract-supplement-20260308.md` | gamma 新增 | `Broker/Risk contract annex` | 当前主线特有 |
| `08-pas-minimal-tradable-design-20260309.md` | gamma 主线 + alpha/beta 回收 | `PAS 主正文` | 当前唯一现行 `PAS` 正文 |
| `09-irs-minimal-tradable-design-20260309.md` | gamma 主线 + alpha/beta 回收 | `IRS 主正文` | 当前唯一现行 `IRS` 正文 |
| `10-mss-minimal-tradable-design-20260309.md` | gamma 主线 + alpha/beta 回收 | `MSS 主正文` | 当前唯一现行 `MSS` 正文 |
| `90-alpha-imports/` | alpha 导入 | `历史来源留档` | 只保留原稿来源，不参与当前 SoT 排序 |

**迁移原则**：
- `08/09/10` 是当前主线唯一正文
- `90-alpha-imports/` 只保留来源原稿，不与 `08/09/10` 并列成双 SoT
- 从 alpha/beta 回收的正文，保留来源和版本说明，但正文语义以当前主线裁剪稿为准
- 迁移后的文件默认冻结，只在"逻辑错误"或"外部约束变化"时修改

---

## 4.1 设计来源声明

`01-full-design/` 中的算法文件来源：

| 文件 | 来源 | 版本 | 说明 |
|------|------|------|------|
| `08-pas-minimal-tradable-design-20260309.md` | gamma 新写 | - | 基于 beta 四件套 + alpha v3.2.0 提炼 |
| `09-irs-minimal-tradable-design-20260309.md` | gamma 新写 | - | 基于 beta 四件套 + alpha v3.3.0 提炼 |
| `10-mss-minimal-tradable-design-20260309.md` | gamma 新写 | - | 基于 beta 四件套 + alpha v3.2.0 提炼 |
| `11-design-source-register-20260309.md` | gamma 新增 | - | 设计来源登记 |
| `03-selector-contract-supplement-20260308.md` | gamma 新增 | - | 当前主线特有 |
| `04-pas-trigger-bof-contract-supplement-20260308.md` | gamma 新增 | - | 当前主线特有 |
| `05-irs-lite-contract-supplement-20260308.md` | gamma 新增 | - | 当前主线特有 |
| `06-mss-lite-contract-supplement-20260308.md` | gamma 新增 | - | 当前主线特有 |
| `07-broker-risk-contract-supplement-20260308.md` | gamma 新增 | - | 当前主线特有 |

**迁移原则**：

- `08/09/10` 是从 alpha/beta 提炼后的"最小可交易版"，不是完整照搬
- `03-07` 是 gamma 当前主线特有的契约补充文件
- `11` 是设计来源的显式登记
- 所有文件默认冻结，只在"逻辑错误"或"外部约束变化"时修改
- alpha/beta 的完整算法文件保留在原仓库作为参考，不直接迁移到 gamma

**设计资产回收路径**：

1. `beta` 四件套（algorithm / data-models / information-flow / api）提供结构表达
2. `alpha` 算法文（v3.2.0 / v3.3.0）提供边界复核和验收口径
3. `gamma` 的 minimal tradable design 是提炼后的最小可交易版
4. 详细来源登记见 `11-design-source-register-20260309.md`

---

## 5. 使用规则

1. 先写 `01-full-design/`，再写 `02-implementation-spec/`，最后才写 `03-execution/`。
2. 不允许在 `03-execution/` 里重新发明设计。
3. 不允许再把 `development-status`、一次性 evidence、旧 `Frozen` 正文当作当前设计正文。
4. 若需要复用 `alpha / beta` 的成熟设计，只能提炼后写入 `blueprint/`，不能直接把旧文档当当前正文。

---

## 6. 当前目标

当前 `01-full-design/` 第一层 `contract supplement` 已经补齐：

1. Selector
2. PAS-trigger / BOF
3. IRS-lite
4. MSS-lite
5. Broker / Risk

当前 `01-full-design/` 第二层正文推进状态如下：

1. `PAS` 最小可交易形态层正文已落地
2. `IRS` 最小可交易排序层正文已落地
3. `MSS` 最小可交易风控层正文已落地
4. `alpha` 导入原稿已移到 `90-alpha-imports/`
5. 设计来源登记已落地

当前 `02-implementation-spec/` 也已经落下第一份正文：

1. `01-current-mainline-implementation-spec-20260308.md`

当前 `03-execution/` 也已经落下第一份正文：

1. `01-current-mainline-execution-breakdown-20260308.md`

当前下一步不是直接继续补散文，而是按下面顺序收口：

1. 先继续压缩 `docs/Strategy/`，补“保留 / 降级 / 合并”清单
2. 再把 `03/04/05/06/07` 明确收口为 contract annex，并固定 `08/09/10` 为各自主正文
3. 然后进入 `Phase 0 / Task P0-A ~ P0-E`
