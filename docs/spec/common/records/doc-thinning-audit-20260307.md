# 第二轮文档瘦身与归档审查（2026-03-07）

## 1. 审查目标

1. 压缩主导航中的低价值历史入口，避免历史报告与当前有效入口并列。
2. 明确 `docs/spec/README.md` 与 `docs/spec/INDEX.md` 的分工，减少重复叙述。
3. 复核 `G:\EmotionQuant-temp` 与仓库内 archive 候选，确认是否存在需要立即清理的对象。

## 2. 调整原则

1. 不删除历史文件，只做入口降级与角色重标注。
2. 当前有效入口优先回到 `README.md`、`docs/README.md`、`docs/spec/README.md`、`docs/spec/common/records/development-status.md`。
3. 一次性检查报告、桥接审计、整理报告仅保留追溯价值，不作为当前执行导航。

## 3. 导航层调整

| 对象 | 原状态 | 新状态 | 处理说明 |
|---|---|---|---|
| `docs/REORGANIZATION-COMPLETE-REPORT.md` | 根 README 前门引用 | 历史整理记录 | 从 `README.md` / `README.en.md` 的相关文档列表移除，仅保留追溯说明 |
| `docs/operations/root-files-check-report.md` | 运维 README 中的普通检查报告 | 历史审计记录 | 说明改为“仅供追溯 2026-03-07 的一次性检查动作” |
| `docs/spec/common/bridge-review-20260304.md` | common README 中的普通跨版本文档 | 历史桥接审计记录 | 明确“不作为当前执行入口” |
| `docs/spec/INDEX.md` | 与 `docs/spec/README.md` 角色重叠 | 轻量静态索引 | 保留，但声明以 `docs/spec/README.md` 为主入口 |
| `docs/spec/v0.01/records/cleanup-candidates-20260306.md` | v0.01 README 中的普通记录入口 | 历史清理记录 | 明确仅供追溯 |

## 4. 临时目录与 archive 候选复核

### 4.1 `G:\EmotionQuant-temp`

| 路径 | 观察 | 结论 |
|---|---|---|
| `G:\EmotionQuant-temp\backtest\v001-base-baseline-20260306.duckdb` | 约 1.50 GB，属于工作副本/基线库 | 保留，符合 temp/backtest 职责 |
| `G:\EmotionQuant-temp\repo-archives\evidence.tar` | 小体积归档 | 保留，符合 repo-archives 职责 |
| `G:\EmotionQuant-temp\repo-archives\v0.01.tar` | 小体积归档 | 保留，符合 repo-archives 职责 |

结论：`EmotionQuant-temp` 当前结构和内容符合“临时工作副本 + 归档副本”定位，无需立即清理。

### 4.2 仓库内 archive 候选

对仓库执行 `*.zip / *.tar / *.7z` 扫描，未发现归档文件落入 Git 工作树。

结论：仓库内当前不存在需要迁出的 archive 文件。

## 5. 保留与后续建议

1. 保留所有历史报告文件，但避免继续把它们放入根 README 或阶段主入口的首屏导航。
2. 后续若新增一次性检查报告，优先放在 `docs/spec/common/records/` 或对应目录下，并显式标注“历史审计记录”。
3. `scripts/ops/check_doc_links.ps1` 应继续作为文档变更后的固定回归检查。

## 6. 本轮结论

1. 文档主入口已进一步压实，当前有效入口与历史追溯入口的边界更清晰。
2. `EmotionQuant-temp` 与仓库内 archive 候选未发现需要立即处理的风险项。
3. 第二轮整理应视为“入口秩序修复”，不是“继续扩写文档”。