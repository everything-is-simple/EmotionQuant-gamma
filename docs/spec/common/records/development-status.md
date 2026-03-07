# EmotionQuant 开发状态（重启版模板）

**状态**: Active（v0.01 Frozen + v0.01-plus 主线替代切换）  
**最后更新**: 2026-03-08
**当前阶段**: Mainline MVP Strengthening（`v0.01` 已冻结为历史尝试；`v0.01-plus` 已升格为当前主开发线；当前目标不再只是跑通 lite 链路，而是把 `PAS / IRS / MSS` 补到最小可交易强度）

---

## 1. 权威入口（SoT）

| 类型 | 路径 | 说明 |
|---|---|---|
| v0.01 历史基线 | `docs/design-v2/01-system/system-baseline.md` | 已冻结的历史设计基线 |
| v0.01-plus 设计入口 | `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md` | 当前主开发线的 DTT 设计入口 |
| v0.01 历史路线图 | `docs/spec/v0.01/roadmap/v0.01-mvp-roadmap.md` | v0.01 冻结执行计划（历史参考） |
| 当前主线 | `docs/spec/v0.01-plus/README.md` | v0.01-plus 当前主开发线入口 |
| 当前主线实现卡 | `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-01-selector-strategy.md` | Selector / Strategy 主线替代实现卡 |
| 工作流 | `docs/workflow/6A-WORKFLOW.md` | 固定执行流程 |
| 当前状态 | `docs/spec/common/records/development-status.md` | 当前治理状态、历史摘要与重启条件 |
| 技术债 | `docs/spec/common/records/debts.md` | 风险与欠账追踪 |
| 资产复用 | `docs/spec/common/records/reusable-assets.md` | 可复用沉淀 |

---

## 2. 当前总体状态

| 项目 | 结论 | 备注 |
|---|---|---|
| 系统设计 | ✅ 已完成终审并定稿 | 16 轮沙盘评审通过，S0/S1=0 |
| 系统治理 | ✅ 已完成沙盘评审并定稿 | 11 项偏差已修复，S0/S1=0 |
| 根配置与入口文件 | ✅ 已完成终审并定稿 | 根文件审计 15 项偏差全部修复，S0/S1=0 |
| 文档路径与状态口径 | ✅ 已完成 | 正式入口、断链修复与检查脚本已收口 |
| 权威入口一致性审计 | ✅ 已完成 | README / AGENTS / docs/*/README 的 SoT、状态与版本入口已统一复核 |
| 入口机器检查 | ✅ 已完成 | `check_doc_authority.ps1` 已覆盖 README / AGENTS / docs/*/README |
| 统一预检入口 | ✅ 已完成 | `preflight.ps1` 已收口为统一入口，默认覆盖 docs + config，完整模式可扩展 lint + test |
| 文档状态语义 | ✅ 已完成 | `Frozen / Active / Draft` 已形成单独治理规则，避免各目录自行发散 |
| 开发依赖与 full 预检 | ✅ 已完成 | `ruff / mypy / pytest` 已接通；受限沙箱会话下完整 `pytest` 可能需要提权执行 |
| v0.01-plus 版本决策 | ✅ 已完成 | 定义为当前主开发线，用于替代 legacy top-down；`v0.01` 保持 Frozen 历史基线 |
| v0.01-plus 文档骨架 | ✅ 已完成 | `README / roadmap / spec / gate / data-contract` 已建立 |
| 主线切换口径 | ✅ 已完成 | `v0.01-plus` 目录、状态记录与设计草案已按“主线替代版”重写 |
| 代码实现 | 进行中 | 当前已开始落地 `variant / run_id / sidecar / selector / strategy / backtest` 的主线切换 |

---

## 3. 当前工作看板（2026-03-07）

| 工作项 | 目标 | 主要落点 | 状态 |
|---|---|---|---|
| 路径收口 | 统一 SoT / 评审标准 / 模块设计 / 算法设计 / 观察台入口 | `README*`, `AGENTS*`, `docs/`, `docs/spec/` | completed |
| 状态收口 | 将当前仓库状态回写为“暂停 v0.01 实现，先做文档治理” | `README*`, `development-status.md`, `v0.01-mvp-roadmap.md` | completed |
| 检查脚本 | 增加文档路径与链接检查，避免旧路径回流 | `scripts/ops/check_doc_links.ps1` | completed |
| 文档瘦身 | 历史入口降级、总导航去重、子目录 README 去重 | `docs/README.md`, `docs/*/README.md` | completed |
| 历史分段 | 将旧实现期整理为阶段摘要 + 关键证据索引 | `development-status.md` | completed |
| 入口一致性审计 | 统一 README / AGENTS / docs/*/README 对 SoT、状态与版本入口的表述 | `docs/reference/README.md`, `docs/operations/README.md`, `docs/steering/README.md`, `docs/spec/common/records/authority-entry-audit-20260307.md` | completed |
| 次级 README 清理与口径脚本 | 收口次级 README 并新增口径一致性机器检查 | `docs/reference/a-stock-rules/README.md`, `docs/design-v2/03-algorithms/core-algorithms/README.md`, `docs/spec/*/README.md`, `scripts/ops/check_doc_authority.ps1` | completed |
| 统一预检入口与状态语义 | 将 `preflight` 扩成统一开发入口，并冻结文档状态语义 | `scripts/ops/preflight.ps1`, `scripts/ops/check_repo_config.ps1`, `docs/steering/document-status.md` | completed |
| 文档状态语义机器检查 | 将 `Frozen / Active / Draft` 规则脚本化并并入 docs gate | `scripts/ops/check_doc_status.ps1`, `scripts/ops/check_docs.ps1` | completed |
| 开发依赖与 full 预检打通 | 安装 `dev` 依赖并跑通 `ruff / mypy / pytest` | `pyproject.toml`, `scripts/ops/preflight.ps1`, `tests/integration/backtest/test_backtest_engine.py` | completed |
| v0.01-plus 版本切分 | 将 `v0.01-plus` 从 `v0.01 Frozen` 中切出并建立单独版本目录 | `docs/spec/v0.01-plus/`, `system-baseline.md`, `selector-design.md` | completed |
| v0.01-plus 主线升格 | 将 `v0.01-plus` 从独立实验版提升为当前主开发线 | `docs/spec/v0.01-plus/`, `development-status.md`, `down-to-top-integration.md` | completed |
| v0.01-plus 主线开工 Gate | 固化主线切换矩阵、run 命名、sidecar 与脚本入口 | `docs/spec/v0.01-plus/roadmap/`, `docs/spec/v0.01-plus/governance/`, `src/`, `scripts/backtest/` | in_progress |

---

## 4. 本周执行区（滚动维护）

分段说明：`2026-03-07` 起归入“文档治理期”；`2026-03-02` 至 `2026-03-06` 的实现与联调记录归入“旧实现期（历史摘要）”。

### 4.1 本周目标

- [x] 收口旧路径与真实断链
- [x] 统一当前状态口径
- [x] 增加文档路径检查脚本
- [x] 历史报告入口降级与临时归档审查
- [x] 合并总导航重复叙述并分段整理历史记录
- [x] 完成 README / AGENTS / docs/*/README 权威入口一致性审计
- [x] 完成次级 README 清理与权威入口机器检查脚本
- [x] 完成 `v0.01-plus` 独立实验版切分与最小文档骨架
- [x] 完成 `v0.01-plus` 从独立实验版到当前主开发线的治理切换

### 4.2 进行中任务

| 任务 | 负责人 | 开始日期 | 状态 | 阻塞 |
|---|---|---|---|---|
| v0.01-plus 主线开工准备（Gate / run 命名 / sidecar / script） | wangweiyun | 2026-03-07 | DOING | 四个执行日逐笔归因、长窗口五场景敏感性与 `BOF` 第一轮内存优化已完成；当前阻塞转为 EG5 七维评审与默认路径切换前的最终收口 |

### 4.3 文档治理期（2026-03-07）

| 日期 | 任务 | 结果 | 证据 |
|---|---|---|---|
| 2026-03-07 | 第二轮文档瘦身 | completed | `README.md`, `README.en.md`, `docs/operations/README.md`, `docs/spec/common/records/doc-thinning-audit-20260307.md` |
| 2026-03-07 | 第三轮文档收口 | completed | `docs/README.md`, `docs/design-v2/README.md`, `docs/Strategy/README.md`, `docs/observatory/README.md`, `docs/spec/common/records/development-status.md` |
| 2026-03-07 | 权威入口一致性审计 | completed | `docs/reference/README.md`, `docs/operations/README.md`, `docs/steering/README.md`, `docs/reference/operations/README.md`, `docs/spec/common/records/authority-entry-audit-20260307.md` |
| 2026-03-07 | 次级 README 清理与脚本化审计 | completed | `docs/reference/a-stock-rules/README.md`, `docs/design-v2/03-algorithms/core-algorithms/README.md`, `docs/spec/README.md`, `docs/spec/common/README.md`, `docs/spec/common/records/README.md`, `docs/spec/v0.01/README.md` ~ `docs/spec/v0.06/README.md`, `AGENTS.md`, `scripts/ops/check_doc_authority.ps1` |
| 2026-03-07 | 文档路径检查脚本落地并回归 | completed | `scripts/ops/check_doc_links.ps1` |
| 2026-03-07 | 统一预检入口与文档状态语义 | completed | `scripts/ops/preflight.ps1`, `scripts/ops/check_repo_config.ps1`, `docs/steering/document-status.md`, `.githooks/pre-commit` |
| 2026-03-07 | 文档状态语义机器检查 | completed | `scripts/ops/check_doc_status.ps1`, `scripts/ops/check_docs.ps1`, `docs/steering/document-status.md` |
| 2026-03-07 | 开发依赖与 full 预检打通 | completed | `python -m pip install -e .[dev]`, `scripts/ops/preflight.ps1 -Profile full`, `tests/integration/backtest/test_backtest_engine.py`, `pyproject.toml` |
| 2026-03-07 | `v0.01-plus` 版本切分与文档骨架建立 | completed | `docs/spec/v0.01-plus/README.md`, `docs/spec/v0.01-plus/roadmap/v0.01-plus-roadmap.md`, `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-01-selector-strategy.md`, `docs/spec/v0.01-plus/governance/v0.01-plus-gate-checklist.md`, `docs/spec/v0.01-plus/governance/v0.01-plus-data-contract-table.md`, `docs/design-v2/01-system/system-baseline.md`, `docs/design-v2/02-modules/selector-design.md`, `docs/spec/README.md` |
| 2026-03-07 | `v0.01-plus` 主线升格：独立实验版 -> 当前主开发线 | completed | `docs/spec/v0.01-plus/README.md`, `docs/spec/v0.01-plus/roadmap/v0.01-plus-roadmap.md`, `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-01-selector-strategy.md`, `docs/spec/v0.01-plus/governance/v0.01-plus-gate-checklist.md`, `docs/spec/v0.01-plus/governance/v0.01-plus-data-contract-table.md`, `docs/spec/common/records/development-status.md`, `docs/spec/README.md`, `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md` |
| 2026-03-07 | `v0.01-plus` 运行命名、sidecar 与默认路径收口 | in_progress | `docs/spec/v0.01-plus/governance/v0.01-plus-run-artifact-rules.md`, `src/config.py`, `src/data/store.py`, `src/strategy/ranker.py`, `src/strategy/strategy.py`, `src/backtest/engine.py`, `scripts/backtest/run_v001_plus_dtt_matrix.py`, `scripts/ops/preflight.ps1` |
| 2026-03-07 | `v0.01-plus` 首轮短窗矩阵 + 默认 DTT 幂等 | completed | `docs/spec/v0.01-plus/evidence/matrix_summary_dtt_v0_01_dtt_bof_plus_irs_score_w20260105_20260224_t151041__dtt_matrix.json`, `docs/spec/v0.01-plus/evidence/idempotency_dtt_v0_01_dtt_bof_plus_irs_score_w20260105_20260224_t151843__idempotency_check.json`, `docs/spec/v0.01-plus/records/v0.01-plus-short-window-matrix-20260307.md`, `scripts/backtest/check_idempotency.py` |
| 2026-03-07 | `v0.01-plus` 数据覆盖审计 + 排序拆解 | completed | `docs/spec/v0.01-plus/evidence/coverage_audit_dtt_v0_01_dtt_bof_plus_irs_score_w20260210_20260213_t154048__coverage_audit.json`, `docs/spec/v0.01-plus/evidence/rank_decomposition_dtt_v0_01_dtt_bof_plus_irs_score_w20260105_20260224_t154940__rank_decomposition.json`, `docs/spec/v0.01-plus/records/v0.01-plus-coverage-and-rank-audit-20260307.md`, `scripts/data/audit_trade_date_coverage.py`, `scripts/backtest/run_v001_plus_rank_decomposition.py` |
| 2026-03-08 | `v0.01-plus` 四个执行日逐笔归因 + 长窗口分场景敏感性 | in_progress | `docs/spec/v0.01-plus/evidence/trade_attribution_dtt_v0_01_dtt_bof_only_vs_v0_01_dtt_bof_plus_irs_score_w20260105_20260224_t165536__trade_attribution.json`, `docs/spec/v0.01-plus/evidence/windowed_sensitivity_dtt_v0_01_dtt_bof_only_vs_v0_01_dtt_bof_plus_irs_score_w20251222_20260224_t_after_opt__windowed_sensitivity.json`, `docs/spec/v0.01-plus/records/v0.01-plus-trade-attribution-and-windowed-sensitivity-20260308.md`, `scripts/backtest/run_v001_plus_trade_attribution.py`, `scripts/backtest/run_v001_plus_windowed_sensitivity.py`, `src/data/store.py`, `src/config.py`, `src/strategy/strategy.py`, `src/strategy/ranker.py`, `tests/unit/strategy/test_ranker.py`, `tests/unit/data/test_store.py` |
| 2026-03-08 | `v0.01-plus` 初选消融：`candidate_top_n / preselect_score_mode` | in_progress | `docs/spec/v0.01-plus/evidence/preselect_ablation_dtt_selector_preselect_matrix_w20260105_20260224_t200058__preselect_ablation.json`, `docs/spec/v0.01-plus/records/v0.01-plus-preselect-ablation-20260308.md`, `scripts/backtest/run_v001_plus_preselect_ablation.py`, `src/selector/selector.py`, `src/config.py`, `tests/unit/selector/test_selector_strategy.py`, `tests/unit/core/test_config.py` |

### 4.4 旧实现期（2026-03-02 ~ 2026-03-06）阶段摘要

| 阶段 | 日期 | 摘要 | 关键证据 |
|---|---|---|---|
| 治理重启与封版 | 2026-03-02 ~ 2026-03-03 | 完成治理模板、设计终审、根配置终审与 v0.01 正式版封版 | `docs/spec/v0.01/records/release-v0.01-formal.md`, `docs/observatory/sandbox-review-standard.md` |
| 文档校对闭环 | 2026-03-04 | 完成 roadmap 与 spec-01~05 文档校对、REV-ID 与七维勾选收口 | `docs/spec/v0.01/roadmap/v0.01-mvp-roadmap.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-01-data-layer.md` ~ `spec-05` |
| Week1 Data Layer 收口 | 2026-03-06 | 明确执行库 / raw 源库边界，补齐 Data Layer gap audit 与主入口口径 | `docs/spec/v0.01/records/v0.01-week1-data-layer-gap-audit-20260306.md`, `docs/spec/v0.01/records/v0.01-data-storage-decision-20260306.md`, `docs/spec/v0.01/records/data-root-layout-20260306.md` |
| Week2 Selector / Strategy 联调 | 2026-03-06 | 完成 MSS/IRS/BOF 首批实现收口、smoke、ablation 与分布审计 | `docs/spec/v0.01/evidence/v0.01-week2-selector-strategy-evidence-20260306.md`, `docs/spec/v0.01/evidence/v0.01-selector-distribution-audit-20260306-v2.json`, `docs/spec/v0.01/evidence/v0.01-selector-ablation-short-20260306.json` |
| 算法 SoT 与口径纠偏 | 2026-03-06 | 将 MSS/IRS/PAS 当前算法设计正式收回 `design-v2`，并完成 SW31 / MSS baseline 收口 | `docs/design-v2/03-algorithms/core-algorithms/`, `docs/spec/v0.01/records/v0.01-sw31-and-mss-calibration-20260306.md`, `docs/spec/v0.01/records/v0.01-selector-review-and-sw31-decision-20260306.md` |
| 基线回望与阈值实验 | 2026-03-06 | 完成基线回望、Broker 回望修订与 MSS threshold sweep 短窗消融 | `docs/spec/v0.01/records/v0.01-post-baseline-retrospective-20260306.md`, `docs/spec/v0.01/records/v0.01-threshold-ablation-short-20260306.md` |

### 4.5 旧实现期关键证据索引

| 类别 | 关键文件 | 用途 |
|---|---|---|
| 封版与冻结 | `docs/spec/v0.01/records/release-v0.01-formal.md` | 查看 v0.01 正式版冻结口径 |
| 路线图 | `docs/spec/v0.01/roadmap/v0.01-mvp-roadmap.md` | 查看冻结执行计划与阶段验收口径 |
| Data Layer | `docs/spec/v0.01/records/v0.01-week1-data-layer-gap-audit-20260306.md` | 查看 Week1 差距审计 |
| 数据存储 | `docs/spec/v0.01/records/v0.01-data-storage-decision-20260306.md` | 查看执行库 / raw 源库决策 |
| Selector / Strategy | `docs/spec/v0.01/evidence/v0.01-week2-selector-strategy-evidence-20260306.md` | 查看联调与短窗证据 |
| 分布审计 | `docs/spec/v0.01/evidence/v0.01-selector-distribution-audit-20260306-v2.json` | 查看 MSS/IRS 真实分布 |
| 算法 SoT | `docs/design-v2/03-algorithms/core-algorithms/` | 查看当前算法级设计 |
| SW31 / MSS 校准 | `docs/spec/v0.01/records/v0.01-sw31-and-mss-calibration-20260306.md` | 查看行业链路与 baseline 校准 |
| 回望修订 | `docs/spec/v0.01/records/v0.01-post-baseline-retrospective-20260306.md` | 查看基线跑通后的三分法结论 |
| 阈值实验 | `docs/spec/v0.01/records/v0.01-threshold-ablation-short-20260306.md` | 查看 MSS threshold sweep 结论 |

---

## 5. 每次任务收口必填（A6）

当前按阶段分段维护；旧实现期不再逐条展开流水账，仅保留摘要索引。

### 5.1 文档治理期（2026-03-07）

| 日期 | 任务/PR | run | test | artifact | review | 记录同步 |
|---|---|---|---|---|---|---|
| 2026-03-07 | 第二轮文档瘦身：历史入口降级 + temp/archive 审查 | `powershell -ExecutionPolicy Bypass -File scripts/ops/check_doc_links.ps1` | `powershell -ExecutionPolicy Bypass -File scripts/ops/check_doc_links.ps1` | `README.md`, `README.en.md`, `docs/operations/README.md`, `docs/spec/README.md`, `docs/spec/INDEX.md`, `docs/spec/common/README.md`, `docs/spec/common/records/README.md`, `docs/spec/common/records/doc-thinning-audit-20260307.md` | 主入口/历史入口分层复核 + temp/archive 候选复核 | debts=无变化, status=已同步, assets=无变化, roadmap=无变化, spec=common README/records 已同步 |
| 2026-03-07 | 第三轮文档收口：总导航去重 + 历史记录分段 | `powershell -ExecutionPolicy Bypass -File scripts/ops/check_doc_links.ps1` | `powershell -ExecutionPolicy Bypass -File scripts/ops/check_doc_links.ps1` | `docs/README.md`, `docs/design-v2/README.md`, `docs/Strategy/README.md`, `docs/observatory/README.md`, `docs/spec/common/records/development-status.md` | 总导航去重复核 + 子目录 README 复核 + development-status 分段复核 | debts=无变化, status=已同步, assets=无变化, roadmap=无变化, spec=development-status 已同步 |
| 2026-03-07 | 权威入口一致性审计：reference / operations / steering 收口 | `powershell -ExecutionPolicy Bypass -File scripts/ops/check_doc_links.ps1` | `powershell -ExecutionPolicy Bypass -File scripts/ops/check_doc_links.ps1` | `docs/reference/README.md`, `docs/operations/README.md`, `docs/steering/README.md`, `docs/reference/operations/README.md`, `docs/spec/common/records/authority-entry-audit-20260307.md` | SoT / 当前状态 / 版本入口一致性复核 | debts=无变化, status=已同步, assets=无变化, roadmap=无变化, spec=authority-entry-audit 已同步 |
| 2026-03-07 | 统一预检入口 + 文档状态语义冻结 | `powershell -ExecutionPolicy Bypass -File scripts/ops/preflight.ps1 -Profile hook` | `powershell -ExecutionPolicy Bypass -File scripts/ops/preflight.ps1`; `powershell -ExecutionPolicy Bypass -File scripts/ops/preflight.ps1 -Profile full`（lint 依赖未安装，预期失败） | `scripts/ops/preflight.ps1`, `scripts/ops/check_repo_config.ps1`, `.githooks/pre-commit`, `docs/steering/document-status.md`, `docs/steering/README.md`, `docs/operations/README.md`, `docs/README.md` | 统一入口、hook、配置基线与状态语义复核 | debts=无变化, status=已同步, assets=无变化, roadmap=无变化, spec=development-status 已同步 |
| 2026-03-07 | 文档状态语义机器检查并入 docs gate | `powershell -ExecutionPolicy Bypass -File scripts/ops/check_docs.ps1` | `powershell -ExecutionPolicy Bypass -File scripts/ops/check_docs.ps1` | `scripts/ops/check_doc_status.ps1`, `scripts/ops/check_docs.ps1`, `docs/steering/document-status.md`, `docs/operations/README.md`, `docs/README.md` | 状态字段与封版日期语义复核 | debts=无变化, status=已同步, assets=无变化, roadmap=无变化, spec=development-status 已同步 |
| 2026-03-07 | 文档治理收口：正式路径 + 当前状态 + 检查脚本 | `powershell -ExecutionPolicy Bypass -File scripts/ops/check_doc_links.ps1` | `powershell -ExecutionPolicy Bypass -File scripts/ops/check_doc_links.ps1` | `README.md`, `README.en.md`, `docs/spec/common/records/development-status.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-roadmap.md`, `scripts/ops/check_doc_links.ps1` | 路径扫描 + 断链复核 + 当前状态一致性复核 | debts=无变化, status=已同步, assets=无变化, roadmap=已同步, spec=development-status/v0.01 roadmap 已同步 |
| 2026-03-07 | 次级 README 清理 + 权威入口脚本化审计 | `powershell -ExecutionPolicy Bypass -File scripts/ops/check_doc_authority.ps1` | `powershell -ExecutionPolicy Bypass -File scripts/ops/check_doc_authority.ps1`; `powershell -ExecutionPolicy Bypass -File scripts/ops/check_doc_links.ps1` | `docs/reference/a-stock-rules/README.md`, `docs/design-v2/03-algorithms/core-algorithms/README.md`, `docs/spec/README.md`, `docs/spec/common/README.md`, `docs/spec/common/records/README.md`, `docs/spec/v0.01/README.md` ~ `docs/spec/v0.06/README.md`, `AGENTS.md`, `scripts/ops/check_doc_authority.ps1` | README 入口复核 + 机器检查回归 | debts=无变化, status=已同步, assets=无变化, roadmap=无变化, spec=authority-entry-audit/development-status 已同步 |
| 2026-03-07 | `v0.01-plus` 独立实验版切分：版本包 + Frozen 边界收口 | `powershell -ExecutionPolicy Bypass -File scripts/ops/check_docs.ps1` | `powershell -ExecutionPolicy Bypass -File scripts/ops/check_docs.ps1` | `docs/spec/v0.01-plus/README.md`, `docs/spec/v0.01-plus/roadmap/v0.01-plus-roadmap.md`, `docs/spec/v0.01-plus/roadmap/v0.01-plus-spec-01-selector-strategy.md`, `docs/spec/v0.01-plus/governance/v0.01-plus-gate-checklist.md`, `docs/spec/v0.01-plus/governance/v0.01-plus-data-contract-table.md`, `docs/design-v2/01-system/system-baseline.md`, `docs/design-v2/02-modules/selector-design.md`, `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md`, `docs/spec/README.md`, `docs/spec/common/records/development-status.md` | Frozen / Draft 边界复核 + 版本入口复核 | debts=无变化, status=已同步, assets=无变化, roadmap=v0.01-plus 已同步, spec=v0.01-plus/development-status 已同步 |
| 2026-03-07 | `v0.01-plus` 数据覆盖修复 + 执行约束敏感性 | `python scripts/data/bulk_download.py --start 20260210 --end 20260213 --tables raw_daily,raw_daily_basic,raw_index_daily,raw_limit_list`; `python scripts/data/repair_l1_partitions_from_raw_duckdb.py --start 2026-02-10 --end 2026-02-13`; `python main.py build --layers l2,l3 --start 2026-02-09 --end 2026-02-24`; `python scripts/data/audit_trade_date_coverage.py --dates 2026-02-10 2026-02-11 2026-02-13`; `python scripts/backtest/run_v001_plus_dtt_matrix.py --start 2026-01-05 --end 2026-02-24 --skip-rebuild-l3`; `python scripts/backtest/run_v001_plus_execution_sensitivity.py --start 2026-01-05 --end 2026-02-24 --skip-rebuild-l3` | `python -m pytest tests/unit/data/test_fetcher.py tests/unit/data/test_cleaner.py tests/patches/selector/test_irs_nan_score_regression.py tests/unit/backtest/test_execution_sensitivity.py -q`; `powershell -ExecutionPolicy Bypass -File scripts/ops/check_docs.ps1`; `powershell -ExecutionPolicy Bypass -File scripts/ops/preflight.ps1 -Profile full` | `docs/spec/v0.01-plus/evidence/coverage_audit_dtt_v0_01_dtt_bof_plus_irs_score_w20260210_20260213_t163939__coverage_audit.json`, `docs/spec/v0.01-plus/evidence/matrix_summary_dtt_v0_01_dtt_bof_plus_irs_score_w20260105_20260224_t160708__dtt_matrix.json`, `docs/spec/v0.01-plus/evidence/execution_sensitivity_dtt_v0_01_dtt_bof_only_vs_v0_01_dtt_bof_plus_irs_score_w20260105_20260224_t162521__execution_sensitivity.json`, `docs/spec/v0.01-plus/records/v0.01-plus-short-window-matrix-20260307.md`, `docs/spec/v0.01-plus/records/v0.01-plus-coverage-and-rank-audit-20260307.md`, `scripts/data/audit_trade_date_coverage.py`, `scripts/data/repair_l1_partitions_from_raw_duckdb.py`, `scripts/backtest/run_v001_plus_execution_sensitivity.py`, `src/data/fetcher.py`, `src/data/cleaner.py`, `src/selector/irs.py`, `src/selector/mss_experiments.py` | raw 分区修复、执行库分区重建、DTT 宽约束重跑与 Top-N/仓位敏感性复核 | debts=无变化, status=已同步, assets=无变化, roadmap=v0.01-plus 已同步, spec=records 已同步 |
| 2026-03-08 | `v0.01-plus` 四个执行日逐笔归因 + 长窗口分场景敏感性 | `python scripts/backtest/run_v001_plus_trade_attribution.py --start 2026-01-05 --end 2026-02-24 --execute-dates 2026-01-20,2026-01-30,2026-02-04,2026-02-05 --scenarios top1_pos2:1:2,top50_pos10:50:10 --skip-rebuild-l3`; `python scripts/backtest/run_v001_plus_windowed_sensitivity.py --windows mid_window:2025-12-22:2026-02-24 --scenarios top1_pos1:1:1,top1_pos2:1:2,top2_pos1:2:1,top2_pos2:2:2,top50_pos10:50:10 --memory-limit 4GB --skip-rebuild-l3 --output docs/spec/v0.01-plus/evidence/windowed_sensitivity_dtt_v0_01_dtt_bof_only_vs_v0_01_dtt_bof_plus_irs_score_w20251222_20260224_t_after_opt__windowed_sensitivity.json`; `python scripts/backtest/run_v001_plus_rank_decomposition.py --start 2025-12-22 --end 2026-02-24 --dtt-top-n 2 --max-positions 1 --skip-rebuild-l3` | `python -m py_compile scripts/backtest/run_v001_plus_trade_attribution.py scripts/backtest/run_v001_plus_windowed_sensitivity.py src/data/store.py src/strategy/strategy.py src/strategy/ranker.py src/config.py`; `python -m pytest tests/unit/data/test_store.py tests/unit/strategy/test_ranker.py -q`; `powershell -ExecutionPolicy Bypass -File scripts/ops/preflight.ps1 -Profile full` | `docs/spec/v0.01-plus/evidence/trade_attribution_dtt_v0_01_dtt_bof_only_vs_v0_01_dtt_bof_plus_irs_score_w20260105_20260224_t165536__trade_attribution.json`, `docs/spec/v0.01-plus/evidence/windowed_sensitivity_dtt_v0_01_dtt_bof_only_vs_v0_01_dtt_bof_plus_irs_score_w20251222_20260224_t_after_opt__windowed_sensitivity.json`, `docs/spec/v0.01-plus/records/v0.01-plus-trade-attribution-and-windowed-sensitivity-20260308.md`, `scripts/backtest/run_v001_plus_trade_attribution.py`, `scripts/backtest/run_v001_plus_windowed_sensitivity.py`, `src/data/store.py`, `src/config.py`, `src/strategy/strategy.py`, `src/strategy/ranker.py`, `tests/unit/data/test_store.py`, `tests/unit/strategy/test_ranker.py` | 四个执行日逐笔归因、长窗口五场景敏感性全量跑通、BOF 批量预取/分批计算/临时表落地优化与 `NO-GO` 当前结论 | debts=无变化, status=已同步, assets=无变化, roadmap=v0.01-plus 已同步, spec=records/gate 已同步 |

### 5.2 旧实现期（2026-03-02 ~ 2026-03-06）摘要索引

| 阶段 | run / test 摘要 | artifact / review 摘要 |
|---|---|---|
| 治理重启与封版 | 以模板落地、文档定稿与门禁审计为主，非代码实现期 | `release-v0.01-formal.md`, `sandbox-review-standard.md`, `v0.01-mvp-roadmap.md` |
| Week1 Data Layer | 完成 Data Layer 最小命令验证与对应 pytest 组合 | `v0.01-week1-data-layer-gap-audit-20260306.md`, `v0.01-data-storage-decision-20260306.md` |
| Week2 Selector / Strategy | 完成 smoke、ablation、distribution audit 与对应 pytest 组合 | `v0.01-week2-selector-strategy-evidence-20260306.md`, `v0.01-selector-distribution-audit-20260306-v2.json` |
| 算法 SoT / SW31 / baseline | 完成 SoT 迁移、SW31 收口、MSS baseline calibration 与 threshold sweep | `core-algorithms/`, `v0.01-sw31-and-mss-calibration-20260306.md`, `v0.01-threshold-ablation-short-20260306.md` |

---

## 6. 风险与决策

| 日期 | 类型 | 内容 | 处理策略 | 状态 |
|---|---|---|---|---|
| 2026-03-02 | 治理决策 | 工作流取舍：6A 作为唯一执行流程，RIPER-5 仅保留条件评审思想 | 已并入 `docs/workflow/6A-WORKFLOW.md`，reference 索引同步修订 | closed |
| 2026-03-06 | 实现风险 | Week2 审计显示：MSS 全区间 `768/768` 为 `NEUTRAL`；IRS 旧实现误用 `stock_basic.industry` 形成 `111` 行业桶；全周期三场消融超过 `75` 分钟未收口 | 已落地 SW31 优先与交易日过滤；后续优先处理 MSS baseline 校准、raw 申万成员数据补采/清洗与 ablation 性能问题 | open |
| 2026-03-07 | 治理决策 | `v0.01` 定位收口为冻结的历史尝试；后续实现重启不再回到 `v0.01`，而转入 `v0.01-plus` 主开发线 | `v0.01` 保留为对照与回退参考；当前主线切换工作全部归入 `v0.01-plus` | closed |
| 2026-03-07 | 治理决策 | 历史整理报告与一次性检查报告保留但降级，不再作为主入口导航 | 仅保留追溯价值；当前入口统一回到 `README/docs/spec/common/records` | closed |
| 2026-03-07 | 治理决策 | README / AGENTS / docs/*/README 的权威入口表述统一为 baseline + development-status + docs/spec | 已完成 reference / operations / steering 收口，并留存一致性审计记录 | closed |
| 2026-03-07 | 治理决策 | 次级 README 与 spec 各级 README 已补齐统一入口，后续用脚本做回归检查 | 以 `check_doc_authority.ps1` 与 `check_doc_links.ps1` 双脚本做回归 | closed |
| 2026-03-07 | 治理决策 | `v0.01-plus` 从独立实验版升格为当前主开发线，用于替代 legacy top-down | 仍保留 legacy 对照与回退路径；`v0.02` 不承接本次链路替代工作 | open |
| 2026-03-07 | 实现风险 | raw/execution 覆盖异常已修复；`IRS` 已证明会进入 `Top-N / MAX_POSITIONS / BUY 数量` 约束，但这种执行差异是否能稳定转化为收益改善仍未说明 | 继续补更长窗口收益归因、失败模式说明与 `GO / NO-GO` 判定 | open |
| 2026-03-08 | 实现风险 | `BOF` 第一轮内存优化已让更长窗口五场景全部在 `4GB` 下跑通，但 `top1_pos2 / top2_pos2` 的 `EV/MDD` 改善与 `PF` 变差并存，收益结构仍不稳 | 当前结论先定为 `NO-GO`：保留 legacy 为默认运行路径，继续在 `v0.01-plus` 线内收七维评审与收益稳定性解释 | open |
| 2026-03-08 | 实现风险 | 初选消融已证明 `candidate_top_n / preselect_score_mode` 会直接改变交易结果；短窗下 `volume_ratio_only` 显著优于当前默认，但证据仍局限于短窗 | 暂不直接翻默认；先将 `volume_ratio_only` 作为候选默认值，待更长窗口复核后再决定是否切换 | open |
| 2026-03-08 | 治理决策 | 更长窗口初选消融已完成：当前主线默认初选不切到 `volume_ratio_only` | 继续保持 `CANDIDATE_TOP_N=100` 与 `PRESELECT_SCORE_MODE=amount_plus_volume_ratio`；`volume_ratio_only` 降级为专项实验候选 | closed |

---

## 7. 版本记录

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-03-02 | v1.0 | 重启清零：建立正式模板并切换到 `.kiro` 治理基线 |
| 2026-03-03 | v1.1 | 设计终审定稿 + 治理沙盘评审完成，状态同步 |
| 2026-03-03 | v1.2 | 治理省察完成：steering/record 审计 + 3项 record 同步修复 |
| 2026-03-03 | v1.3 | 根配置文件省察 + 15项偏差修复 + v0.01 正式版封版 |
| 2026-03-04 | v1.4 | 完成 roadmap 与 spec-01~05 文档校对闭环 |
| 2026-03-06 | v1.5 | 完成 Week1 / Week2 的 Data、Selector、Strategy、算法 SoT、SW31、baseline 与阈值实验收口 |
| 2026-03-07 | v1.6 | 文档治理收口：路径修复、入口降级、README 去重、development-status 历史摘要化 |
| 2026-03-07 | v1.7 | 权威入口一致性审计：reference / operations / steering 收口并统一入口表述 |
| 2026-03-07 | v1.8 | 次级 README 清理：a-stock-rules / core-algorithms / spec 各级 README 补齐统一入口，并新增 `check_doc_authority.ps1` |
| 2026-03-07 | v1.9 | `preflight.ps1` 扩成统一开发预检入口，新增 `check_repo_config.ps1`，并冻结 `Frozen / Active / Draft` 文档状态语义 |
| 2026-03-07 | v1.10 | 新增 `check_doc_status.ps1`，将文档状态语义并入 docs gate |
| 2026-03-07 | v1.11 | 安装 `dev` 依赖并接通 `preflight.ps1 -Profile full`；补齐 `mypy/ruff` 配置与回测集成测试前置 |
| 2026-03-07 | v1.12 | 完成 `v0.01-plus` 独立实验版切分：新增 spec 骨架，并将 `system-baseline` / `selector-design` 收回纯 `v0.01 Frozen` 口径 |
| 2026-03-07 | v1.13 | 治理决策翻转：`v0.01` 冻结为历史尝试，`v0.01-plus` 升格为当前主开发线；同步改写 plus 目录、状态入口与 DTT 设计定位 |
| 2026-03-07 | v1.14 | 完成 `v0.01-plus` 首轮短窗矩阵与默认 DTT 幂等验证；Spec-01 验收项与 Gate 前半段回写完成 |
| 2026-03-07 | v1.15 | 完成 `v0.01-plus` 数据覆盖审计与 DTT 排序拆解：确认 raw 源库截断根因，并证明 `IRS` 已影响名次 |
| 2026-03-07 | v1.16 | 完成 raw/execution 覆盖修复、宽约束短窗重跑与 `Top-N / max_positions` 敏感性矩阵：确认 `IRS` 已进入 `Top-N / MAX_POSITIONS / BUY 数量` 约束 |
| 2026-03-08 | v1.17 | 完成四个执行日逐笔归因、更长窗口五场景敏感性与 `BOF` 第一轮内存优化；新增窗口化批处理脚本，并给出当前 `NO-GO` 结论 |




