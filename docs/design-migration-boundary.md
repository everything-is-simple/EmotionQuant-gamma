# 设计迁移边界声明

**版本**: `blueprint 切换版`  
**状态**: `Active`  
**最后更新**: `2026-03-08`  
**变更规则**: `仅允许在 blueprint / docs 的职责边界发生变化时修订。`

---

## 1. 定位

本文只做一件事：

`正式声明 EmotionQuant-gamma 的新版设计权威层已经迁移到 blueprint/。`

---

## 2. 权威分层

当前仓库从此固定为 4 层：

1. `blueprint/`
   - 新版设计权威层
   - 所有新设计正文、完整设计、实现方案、执行拆解都只写这里

2. `docs/spec/`
   - 治理 / roadmap / evidence / records / status
   - 负责推进、验收、记录，不重新发明设计

3. `docs/design-v2/`
   - 历史基线与兼容桥接层
   - `v0.01 Frozen` 历史基线继续保留在这里
   - 不再承载新版主线设计正文

4. `docs/reference/` / `docs/Strategy/` / `docs/observatory/` / `docs/workflow/`
   - 参考、理论、评审、运维、流程辅助层
   - 不作为新版设计权威源

---

## 3. 强制规则

1. 所有新设计，只能进入 `blueprint/`。
2. `docs/` 不再新增新版算法正文、模块正文、系统正文。
3. `docs/` 允许新增的内容，只限于：
   - 状态
   - records
   - evidence
   - roadmap
   - 入口导航
   - 兼容跳转
   - 历史说明
4. 若旧 `docs/` 与 `blueprint/` 冲突，以 `blueprint/` 为准。
5. 若 `v0.01 Frozen` 历史基线与新版设计冲突，历史回看以 `docs/design-v2/01-system/system-baseline.md` 为准；当前实现与未来设计以 `blueprint/` 为准。
6. 不允许为了实现方便，回到 `docs/` 里补写新版设计。

---

## 4. 当前权威入口

| 类型 | 路径 | 用途 |
|---|---|---|
| 新版设计总入口 | `blueprint/README.md` | 新版设计空间总入口 |
| 完整设计 SoT | `blueprint/01-full-design/` | 新版设计正文 |
| 当前实现方案 | `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md` | 当前唯一实现方案 |
| 当前执行拆解 | `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md` | 当前 phase / task / checklist |
| 历史基线 | `docs/design-v2/01-system/system-baseline.md` | `v0.01 Frozen` 历史口径 |
| 当前治理状态 | `docs/spec/common/records/development-status.md` | 当前状态、风险与阶段推进 |

---

## 5. 使用方法

1. 讨论“新设计是什么”，进入 `blueprint/`。
2. 讨论“当前做到哪、证据在哪、Gate 是否通过”，进入 `docs/spec/`。
3. 讨论“旧版历史基线是什么”，进入 `docs/design-v2/01-system/system-baseline.md`。
4. 讨论“理论来源 / 评审方法 / 运维步骤 / 执行流程”，进入对应辅助目录。

---

## 6. 迁移完成标准

下面 3 条同时成立，才算切换完成：

1. `AGENTS.md` 与 `docs/*/README.md` 的权威入口全部改指向 `blueprint/`
2. `docs/` 不再把 `design-v2/` 或 `spec/` 描述成“当前设计正文”
3. 后续新增设计文件只进入 `blueprint/`
