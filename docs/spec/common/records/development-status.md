# EmotionQuant 开发状态（重启版模板）

**状态**: Active（正式治理）  
**最后更新**: 2026-03-06
**当前阶段**: Rebuild Week 1（v0.01 文档口径已封口，Week1 Data Layer 差距审计已完成，正在准备实现收口）

---

## 1. 权威入口（SoT）

| 类型 | 路径 | 说明 |
|---|---|---|
| 设计总纲 | `docs/design-v2/system-baseline.md` | 当前唯一设计口径 |
| 路线图 | `docs/spec/v0.01/roadmap/v0.01-mvp-roadmap.md` | 周级推进计划 |
| 模块实现卡 | `docs/spec/v0.01/roadmap/v0.01-mvp-spec-*.md` | 模块拆解与验收 |
| 工作流 | `.kiro/steering/6A-WORKFLOW.md` | 固定执行流程 |
| 技术债 | `docs/spec/common/records/debts.md` | 风险与欠账追踪 |
| 资产复用 | `docs/spec/common/records/reusable-assets.md` | 可复用沉淀 |

---

## 2. 当前总体状态

| 项目 | 结论 | 备注 |
|---|---|---|
| 系统设计 | ✅ 已完成终审并定稿 | 16轮沙盘评审通过，S0/S1=0 |
| 系统治理 | ✅ 已完成沙盘评审并定稿 | 11项偏差已修复，S0/S1=0 |
| 根配置与入口文件 | ✅ 已完成终审并定稿 | 根文件审计 15 项偏差全部修复，S0/S1=0 |
| 代码实现 | 进行中 | 基线已跑通，当前按 Week1 差距审计结果收口 |

---

## 3. 迭代看板（四周）

| 周次 | 目标 | 对应 spec | 状态 |
|---|---|---|---|
| Week 1 | Data 层可运行闭环 | `v0.01-mvp-spec-01-data-layer.md` | TODO |
| Week 2 | Selector + Strategy（BOF） | `v0.01-mvp-spec-02-selector.md`, `v0.01-mvp-spec-03-strategy.md` | TODO |
| Week 3 | Broker + Backtest | `v0.01-mvp-spec-04-broker.md`, `v0.01-mvp-spec-05-backtest-report.md`（engine.py 部分） | TODO |
| Week 4 | Report + 联调 + 纸上交易 | `v0.01-mvp-spec-05-backtest-report.md` | TODO |

---

## 4. 本周执行区（滚动维护）

### 4.1 本周目标

- [ ] 填写本周目标（1-3 条）

### 4.2 进行中任务

| 任务 | 负责人 | 开始日期 | 状态 | 阻塞 |
|---|---|---|---|---|
| v0.01 Week1 实现准备（Data Layer） | wangweiyun | 2026-03-04 | TODO | 无 |

### 4.3 已完成任务

| 日期 | 任务 | 结果 | 证据 |
|---|---|---|---|
| 2026-03-02 | 治理重启：record 三件套 + 6A 正式版模板落地 | completed | `docs/spec/common/records/*.md`, `.kiro/steering/6A-WORKFLOW.md` |
| 2026-03-02 | 治理补丁：6A v1.2 强化 + architecture Order 修正 + 设计文档 4 项修复 | completed | `6A-WORKFLOW.md` v1.2, `architecture.md`, 4 design-v2 docs |
| 2026-03-03 | 设计终审：16轮沙盘评审 + 5项修复 + 定稿门禁通过 | completed | `design-v2/` 全部文档 v1.0, `sandbox-review-standard.md` |
| 2026-03-03 | 治理评审：.kiro 文件沙盘评审 + 11项偏差修复 | completed | `.kiro/` 全部文件 |
| 2026-03-03 | 治理省察：steering/record 对标 sandbox-review-standard + god_view 审计，3项 record 同步修复 | completed | `development-status.md` Week3 spec引用修复, `reusable-assets.md` DES-007新增 |
| 2026-03-03 | 根配置文件省察+15项修复：.env.example 重写、pyproject.toml 依赖栈重建、README 字段同步、CLAUDE/WARP §9质量门控对齐 | completed | `.env.example` `.gitignore` `pyproject.toml` `README{.en}.md` `CLAUDE{.en}.md` `WARP{.en}.md` |
| 2026-03-03 | v0.01 正式版封版：全部文档层通过定稿门禁（sandbox-review-standard §6），spec-01–05 全部 Active | completed | 封版基线：16轮沙盘评审 S0/S1=0，5个文档层通过审计，15项根配置偏差全部封线 |
| 2026-03-03 | 根配置文件终审：.env/pyproject/README/WARP/CLAUDE 对标审计 + 15项偏差修复；roadmap + spec-01~05 状态升格 Active | completed | `.env.example`, `pyproject.toml`, `README*.md`, `WARP*.md`, `CLAUDE*.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-roadmap.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-01-data-layer.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-02-selector.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-03-strategy.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-04-broker.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-05-backtest-report.md` |
| 2026-03-04 | v0.01 spec-01（Data Layer）文档校对：补齐校对证据落点并与 SoT/steering/record/顶层文件交叉核对 | completed | `docs/spec/v0.01/roadmap/v0.01-mvp-spec-01-data-layer.md` |
| 2026-03-04 | v0.01 spec-02~05 文档校对：补齐校对证据落点并与 design/roadmap/steering/record/顶层文件交叉核对 | completed | `docs/spec/v0.01/roadmap/v0.01-mvp-spec-02-selector.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-03-strategy.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-04-broker.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-05-backtest-report.md` |
| 2026-03-04 | v0.01 实现前总校对收口：roadmap 增加“校对完成状态+追溯索引+七维勾选”，spec-01~05 增加 REV-ID 并同步 `docs/spec` | completed | `docs/spec/v0.01/roadmap/v0.01-mvp-roadmap.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-01-data-layer.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-02-selector.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-03-strategy.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-04-broker.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-05-backtest-report.md` |
| 2026-03-06 | v0.01 基线跑通后回望审视：形成“保留不动 / v0.01 立即修订 / v0.02+ 延后”三分法清单 | completed | `docs/spec/v0.01/records/v0.01-post-baseline-retrospective-20260306.md` |
| 2026-03-06 | v0.01 回望修订落地：按实战证据修正 roadmap/spec/design 的实现与验收口径 | completed | `docs/spec/v0.01/roadmap/v0.01-mvp-roadmap.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-01-data-layer.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-02-selector.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-05-backtest-report.md`, `docs/design-v2/data-layer-design.md`, `docs/design-v2/backtest-report-design.md` |
| 2026-03-06 | v0.01 Broker 回望修订落地：补齐确定性主键、显式回测日期、SELL-only trust update、paper 持仓退出约束 | completed | `docs/spec/v0.01/roadmap/v0.01-mvp-spec-04-broker.md`, `docs/design-v2/broker-design.md` |
| 2026-03-06 | Week1 Data Layer 差距审计：完成测试、最小命令验证，并修正 `MIN_AMOUNT` 与 `stock_info.list_status` 默认主链路口径 | completed | `docs/spec/v0.01/records/v0.01-week1-data-layer-gap-audit-20260306.md`, `src/config.py`, `src/data/fetcher.py`, `tests/unit/core/test_config.py`, `tests/unit/data/test_fetcher.py`, `.env.example` |
| 2026-03-06 | 数据存储口径收口：明确执行库 / raw 源库 / Parquet / logs / cache 的职责边界，并补齐 raw bootstrap 主入口 | completed | `docs/spec/v0.01/records/v0.01-data-storage-decision-20260306.md`, `docs/spec/v0.01/records/data-root-layout-20260306.md`, `main.py`, `src/config.py`, `src/data/fetcher.py`, `scripts/data/load_l1_from_raw_duckdb.py`, `tests/unit/data/test_fetcher.py` |
| 2026-03-06 | Week2 Selector/Strategy 首批收口：对齐 MSS/IRS 归一化与阈值、补齐候选解释性、完善组合模式与 lookback 语义 | completed | `src/selector/normalize.py`, `src/selector/mss.py`, `src/selector/irs.py`, `src/selector/selector.py`, `src/strategy/strategy.py`, `tests/unit/selector/test_selector_strategy.py` |
| 2026-03-06 | Week2 联调入口落地：新增消融对照脚本与 selector→strategy smoke 入口，并补齐对应测试 | completed | `src/backtest/ablation.py`, `scripts/backtest/run_week2_ablation.py`, `scripts/backtest/run_selector_strategy_smoke.py`, `tests/unit/backtest/test_ablation.py`, `tests/integration/selector/test_selector_strategy_pipeline.py` |
| 2026-03-06 | Week2 初轮证据落地：消融与 smoke 改为 working copy 执行，产出短窗对照结果与一条真实 BOF 信号样例 | completed | `docs/spec/v0.01/evidence/v0.01-week2-selector-strategy-evidence-20260306.md`, `docs/spec/v0.01/evidence/v0.01-selector-ablation-short-20260306.json`, `docs/spec/v0.01/evidence/v0.01-selector-strategy-smoke-20260306-v2.json`, `src/backtest/ablation.py`, `scripts/backtest/run_week2_ablation.py`, `scripts/backtest/run_selector_strategy_smoke.py`, `src/config.py`, `src/strategy/registry.py`, `src/strategy/strategy.py`, `tests/unit/core/test_config.py`, `tests/unit/selector/test_selector_strategy.py`, `tests/integration/selector/test_selector_strategy_pipeline.py` |
| 2026-03-06 | Week2 分布审计与风险暴露：补齐 MSS/IRS 真实分布证据，修正 IRS 唯一排名，并确认全周期三场消融存在性能阻塞 | completed | `docs/spec/v0.01/evidence/v0.01-selector-distribution-audit-20260306.json`, `docs/spec/v0.01/evidence/v0.01-week2-selector-strategy-evidence-20260306.md`, `src/selector/audit.py`, `scripts/backtest/run_week2_distribution_audit.py`, `src/selector/irs.py`, `src/report/reporter.py`, `src/backtest/engine.py`, `src/backtest/ablation.py`, `tests/unit/report/test_reporter.py`, `tests/unit/selector/test_selector_strategy.py` |
| 2026-03-06 | v0.01 当前版算法设计落地：基于旧版 `core-algorithms` 与当前实现，收口 MSS/IRS/PAS 三份“当前可执行算法设计”文档 | completed | `docs/spec/v0.01/records/v0.01-algorithm-design-overview-20260306.md`, `docs/spec/v0.01/records/v0.01-algorithm-design-mss-20260306.md`, `docs/spec/v0.01/records/v0.01-algorithm-design-irs-20260306.md`, `docs/spec/v0.01/records/v0.01-algorithm-design-pas-20260306.md` |
| 2026-03-06 | Selector 口径审查与 SW31 修正：确认旧行业桶误用 `stock_basic.industry`，落地申万一级成员映射优先、交易日过滤与 IRS 日级最小覆盖约束 | completed | `docs/spec/v0.01/records/v0.01-selector-review-and-sw31-decision-20260306.md`, `main.py`, `src/config.py`, `src/data/store.py`, `src/data/fetcher.py`, `src/data/cleaner.py`, `src/data/builder.py`, `src/selector/selector.py`, `src/selector/irs.py`, `tests/unit/data/test_fetcher.py`, `tests/unit/data/test_cleaner.py`, `tests/unit/core/test_config.py`, `tests/unit/selector/test_selector_strategy.py` |

---

## 5. 每次任务收口必填（A6）

每个任务完成时，必须在本节追加一行：

| 日期 | 任务/PR | run | test | artifact | review | 记录同步 |
|---|---|---|---|---|---|---|
| 2026-03-02 | 治理重启模板落地 | n/a | n/a | `docs/spec/common/records/*.md`, `.kiro/steering/6A-WORKFLOW.md` | 本次治理评审结论 | debts/status/assets/roadmap 已同步，spec=N/A（治理任务） |
| 2026-03-02 | 治理补丁：6A v1.2 + architecture Order + 设计文档修复 | n/a | n/a | `6A-WORKFLOW.md` v1.2, `architecture.md`, design-v2 docs | 治理评审 | debts=无变化, status=已同步, assets=无变化, roadmap=N/A, spec=N/A（治理任务） |
| 2026-03-03 | 设计终审 + 治理评审 | n/a | n/a | `design-v2/` v1.0定稿, `.kiro/` 11项偏差修复 | 沙盘评审标准 7维检查 | debts=无变化, status=已同步, assets=无变化, roadmap=已同步, spec=N/A（治理任务） |
| 2026-03-03 | 治理省察：steering/record 审计 | n/a | n/a | `development-status.md` Week3 spec引用修复, `reusable-assets.md` DES-007新增 | sandbox-review-standard + god_view 交叉验证 | debts=无变化, status=已同步, assets=已同步, roadmap=无变化, spec=无变化 |
| 2026-03-03 | 根配置文件省察+15项修复 | n/a | n/a | `.env.example`/`pyproject.toml`/`README{.en}.md`/`CLAUDE{.en}.md`/`WARP{.en}.md` | sandbox-review-standard 定稿门禁 | debts=无变化, status=已同步, assets=无变化, roadmap=无变化, spec=无变化 |
| 2026-03-03 | v0.01 正式版封版 | n/a | n/a | 全部 spec-01–05 Active、roadmap Active（正式版）、设计文档 Frozen、根配置对齐 v0.01 | sandbox-review-standard §6 + god_view 全维考核 | debts=无变化, status=已同步, assets=无变化, roadmap=无变化, spec=spec-01 Draft→Active |
| 2026-03-03 | 根配置文件终审 + 文档状态升格（roadmap/spec） | n/a | n/a | `.env.example`, `pyproject.toml`, `README*.md`, `WARP*.md`, `CLAUDE*.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-roadmap.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-01-data-layer.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-02-selector.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-03-strategy.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-04-broker.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-05-backtest-report.md` | sandbox-review-standard §6 定稿门禁 + god_view v0.01 对照 | debts=无变化, status=已同步, assets=无变化, roadmap=已同步, spec=已同步 |
| 2026-03-04 | v0.01 spec-01 文档校对（仅文档，不实现） | n/a | n/a | `docs/spec/v0.01/roadmap/v0.01-mvp-spec-01-data-layer.md` | 设计/路线图/steering/record/顶层文件一致性复核 | debts=无变化, status=已同步, assets=无变化, roadmap=无变化, spec=已同步 |
| 2026-03-04 | v0.01 spec-02~05 文档校对（仅文档，不实现） | n/a | n/a | `docs/spec/v0.01/roadmap/v0.01-mvp-spec-02-selector.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-03-strategy.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-04-broker.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-05-backtest-report.md` | 设计/路线图/steering/record/顶层文件一致性复核 | debts=无变化, status=已同步, assets=无变化, roadmap=无变化, spec=已同步 |
| 2026-03-04 | v0.01 实现前最后一轮总校对（仅文档，不实现） | n/a | n/a | `docs/spec/v0.01/roadmap/v0.01-mvp-roadmap.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-01-data-layer.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-02-selector.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-03-strategy.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-04-broker.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-05-backtest-report.md` | 七维模板逐项勾选复核（Schema/调用链/幂等/状态机/时序/冲突/报告） | debts=无变化, status=已同步, assets=无变化, roadmap=已同步, spec=已同步 |
| 2026-03-06 | v0.01 基线跑通后回望审视 | n/a | n/a | `docs/spec/v0.01/records/v0.01-post-baseline-retrospective-20260306.md` | 基于基线证据、runbook、勘误与路线图/实现卡的文件级修订审查 | debts=无变化, status=已同步, assets=无变化, roadmap=无变化, spec=无变化（本轮先出审查记录） |
| 2026-03-06 | v0.01 回望修订落地 | n/a | n/a | `docs/spec/v0.01/roadmap/v0.01-mvp-roadmap.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-01-data-layer.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-02-selector.md`, `docs/spec/v0.01/roadmap/v0.01-mvp-spec-05-backtest-report.md`, `docs/design-v2/data-layer-design.md`, `docs/design-v2/backtest-report-design.md` | 按基线证据回写实现与验收口径，不触碰 Frozen 主干语义 | debts=无变化, status=已同步, assets=无变化, roadmap=已同步, spec=spec-01/spec-02/spec-05 已同步 |
| 2026-03-06 | v0.01 Broker 回望修订落地 | n/a | n/a | `docs/spec/v0.01/roadmap/v0.01-mvp-spec-04-broker.md`, `docs/design-v2/broker-design.md` | 基于基线经验补齐 Broker 的确定性、时序与信任链路约束，不改 Frozen 语义 | debts=无变化, status=已同步, assets=无变化, roadmap=无变化, spec=spec-04 已同步 |
| 2026-03-06 | Week1 Data Layer 差距审计 + 口径修正 | `python main.py build --layers=l2 --start 2026-01-01 --end 2026-01-02` | `pytest -q tests/unit/core/test_config.py tests/unit/data/test_fetcher.py tests/unit/data tests/unit/core/test_contracts.py tests/unit/selector/test_selector_strategy.py` | `docs/spec/v0.01/records/v0.01-week1-data-layer-gap-audit-20260306.md`, `src/config.py`, `src/data/fetcher.py`, `.env.example`, `tests/unit/core/test_config.py`, `tests/unit/data/test_fetcher.py` | 以 spec-01 为准完成 Gap Audit，并修正默认 `MIN_AMOUNT` 与 `list_status` 口径 | debts=无变化, status=已同步, assets=无变化, roadmap=无变化, spec=spec-01 审计已同步 |
| 2026-03-06 | 数据存储口径收口 + raw bootstrap 主入口 | `python main.py fetch --help` | `pytest -q tests/unit/data/test_fetcher.py tests/unit/core/test_config.py tests/unit/data tests/unit/core/test_contracts.py tests/unit/selector/test_selector_strategy.py` | `docs/spec/v0.01/records/v0.01-data-storage-decision-20260306.md`, `docs/spec/v0.01/records/data-root-layout-20260306.md`, `main.py`, `src/config.py`, `src/data/fetcher.py`, `scripts/data/load_l1_from_raw_duckdb.py`, `tests/unit/data/test_fetcher.py` | 将“执行库 + raw 源库 + 辅助目录”口径写实，并把 raw 导入收敛为主入口能力 | debts=无变化, status=已同步, assets=无变化, roadmap=无变化, spec=spec-01 已同步 |
| 2026-03-06 | Week2 Selector/Strategy 首批收口 | n/a | `pytest -q tests/unit/selector/test_selector_strategy.py tests/unit/data/test_fetcher.py tests/unit/data/test_cleaner.py tests/unit/core/test_contracts.py tests/unit/core/test_config.py` | `src/selector/normalize.py`, `src/selector/mss.py`, `src/selector/irs.py`, `src/selector/selector.py`, `src/strategy/strategy.py`, `tests/unit/selector/test_selector_strategy.py` | 对齐 spec-02/spec-03 的 MSS/IRS 评分口径、候选解释性、组合模式与 lookback 语义 | debts=无变化, status=已同步, assets=无变化, roadmap=无变化, spec=spec-02/spec-03 首批实现已同步 |
| 2026-03-06 | Week2 消融入口 + selector→strategy smoke | `python scripts/backtest/run_week2_ablation.py --help` / `python scripts/backtest/run_selector_strategy_smoke.py --help` | `pytest -q tests/unit/backtest/test_ablation.py tests/integration/selector/test_selector_strategy_pipeline.py tests/unit/selector/test_selector_strategy.py tests/unit/data/test_fetcher.py tests/unit/data/test_cleaner.py tests/unit/core/test_contracts.py tests/unit/core/test_config.py` | `src/backtest/ablation.py`, `scripts/backtest/run_week2_ablation.py`, `scripts/backtest/run_selector_strategy_smoke.py`, `tests/unit/backtest/test_ablation.py`, `tests/integration/selector/test_selector_strategy_pipeline.py` | 落地 spec-02 的三组消融入口与证据输出路径，并把 spec-03 的 select_candidates -> generate_signals 主链做成可跑 smoke | debts=无变化, status=已同步, assets=无变化, roadmap=无变化, spec=spec-02/spec-03 联调入口已同步 |
| 2026-03-06 | Week2 初轮证据落地 + working copy 保护 | `python scripts/backtest/run_selector_strategy_smoke.py --calc-date 2026-01-09 --output docs/spec/v0.01/evidence/v0.01-selector-strategy-smoke-20260306-v2.json --working-db-path .tmp/backtest/selector-strategy-smoke-20260306.duckdb` / `python scripts/backtest/run_week2_ablation.py --start 2026-01-05 --end 2026-02-24 --patterns bof --output docs/spec/v0.01/evidence/v0.01-selector-ablation-short-20260306.json --working-db-path .tmp/backtest/selector-ablation-short-20260306.duckdb` | `pytest -q tests/unit/core/test_config.py tests/unit/selector/test_selector_strategy.py tests/unit/backtest/test_ablation.py tests/integration/selector/test_selector_strategy_pipeline.py` | `docs/spec/v0.01/evidence/v0.01-week2-selector-strategy-evidence-20260306.md`, `docs/spec/v0.01/evidence/v0.01-selector-ablation-short-20260306.json`, `docs/spec/v0.01/evidence/v0.01-selector-strategy-smoke-20260306-v2.json`, `src/backtest/ablation.py`, `scripts/backtest/run_week2_ablation.py`, `scripts/backtest/run_selector_strategy_smoke.py`, `src/config.py`, `src/strategy/registry.py`, `src/strategy/strategy.py`, `tests/unit/core/test_config.py`, `tests/unit/selector/test_selector_strategy.py`, `tests/integration/selector/test_selector_strategy_pipeline.py` | 将消融与 smoke 固定到工作副本，避免误改执行库，并补齐短窗 A/B/C 对照和一条真实 BOF 信号样例 | debts=无变化, status=已同步, assets=无变化, roadmap=spec-02/spec-03 已同步, spec=spec-02/spec-03 已同步 |
| 2026-03-06 | Week2 分布审计 + IRS 唯一排名修正 | `python main.py build --layers=l3 --start=2023-01-03 --end=2026-02-24 --force` / `python scripts/backtest/run_week2_distribution_audit.py --start 2023-01-03 --end 2026-02-24 --output docs/spec/v0.01/evidence/v0.01-selector-distribution-audit-20260306.json --working-db-path .tmp/audit/selector-distribution-20260306.duckdb` | `pytest -q tests/unit/report/test_reporter.py tests/unit/selector/test_selector_strategy.py tests/unit/backtest/test_ablation.py tests/integration/selector/test_selector_strategy_pipeline.py tests/unit/core/test_config.py` | `docs/spec/v0.01/evidence/v0.01-selector-distribution-audit-20260306.json`, `docs/spec/v0.01/evidence/v0.01-selector-ablation-short-20260306.json`, `docs/spec/v0.01/evidence/v0.01-week2-selector-strategy-evidence-20260306.md`, `src/selector/audit.py`, `scripts/backtest/run_week2_distribution_audit.py`, `src/selector/irs.py`, `src/report/reporter.py`, `src/backtest/engine.py`, `src/backtest/ablation.py`, `tests/unit/report/test_reporter.py`, `tests/unit/selector/test_selector_strategy.py` | 产出 MSS/IRS 全区间分布证据，修正 IRS 并列分数的唯一排名，并暴露 MSS 全中性 / IRS 111 桶 / 全周期三场消融性能阻塞三项 Week2 风险 | debts=无变化, status=已同步, assets=无变化, roadmap=spec-02 已同步, spec=spec-02 已同步 |
| 2026-03-06 | v0.01 当前版算法设计文档（MSS/IRS/PAS） | n/a | n/a | `docs/spec/v0.01/records/v0.01-algorithm-design-overview-20260306.md`, `docs/spec/v0.01/records/v0.01-algorithm-design-mss-20260306.md`, `docs/spec/v0.01/records/v0.01-algorithm-design-irs-20260306.md`, `docs/spec/v0.01/records/v0.01-algorithm-design-pas-20260306.md` | 基于 `docs/reference/core-algorithms` 与当前实现/证据的差异，形成“当前可执行算法设计”基线，不触碰 Frozen 的 `design-v2` | debts=无变化, status=已同步, assets=无变化, roadmap=无变化, spec=无变化（records 新增） |
| 2026-03-06 | Selector 评审 + SW31 行业链路修正 | `DATA_PATH=.tmp/verify-sw-chain RAW_DB_PATH=G:\\EmotionQuant_data\\duckdb\\emotionquant.duckdb python main.py fetch --from-raw-db ... --start 2026-01-02 --end 2026-01-31` / `DATA_PATH=.tmp/verify-sw-chain python main.py build --layers l2,l3 --start 2026-01-02 --end 2026-01-31 --force` | `pytest -q tests/unit/data/test_fetcher.py tests/unit/data/test_cleaner.py tests/unit/core/test_config.py tests/unit/selector/test_selector_strategy.py tests/integration/selector/test_selector_strategy_pipeline.py` | `docs/spec/v0.01/records/v0.01-selector-review-and-sw31-decision-20260306.md`, `main.py`, `src/config.py`, `src/data/store.py`, `src/data/fetcher.py`, `src/data/cleaner.py`, `src/data/builder.py`, `src/selector/selector.py`, `src/selector/irs.py`, `tests/unit/data/test_fetcher.py`, `tests/unit/data/test_cleaner.py`, `tests/unit/core/test_config.py`, `tests/unit/selector/test_selector_strategy.py` | 确认旧实现误用 `stock_basic.industry`，切到申万一级成员映射优先，并补上交易日过滤与 IRS 最小行业数门槛；短窗真链路已从 `111` 桶收敛到 `27+未知`，暴露 raw 申万成员源数据仍不完整 | debts=无变化, status=已同步, assets=无变化, roadmap=无变化, spec=spec-01/spec-02 records 已同步 |

---

## 6. 风险与决策

| 日期 | 类型 | 内容 | 处理策略 | 状态 |
|---|---|---|---|---|
| 2026-03-02 | 治理决策 | 工作流取舍：6A 作为唯一执行流程，RIPER-5 仅保留条件评审思想 | 已并入 `.kiro/steering/6A-WORKFLOW.md`，reference 索引同步修订 | closed |
| 2026-03-06 | 实现风险 | Week2 审计显示：MSS 全区间 `768/768` 为 `NEUTRAL`；IRS 旧实现误用 `stock_basic.industry` 形成 `111` 行业桶；全周期三场消融超过 `75` 分钟未收口 | 已落地 SW31 优先与交易日过滤；后续优先处理 MSS baseline 校准、raw 申万成员数据补采/清洗与 ablation 性能问题 | open |

---

## 7. 版本记录

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-03-02 | v1.0 | 重启清零：建立正式模板并切换到 `.kiro` 治理基线 |
| 2026-03-03 | v1.1 | 设计终审定稿 + 治理沙盘评审完成，状态同步 |
| 2026-03-03 | v1.2 | 治理省察完成：steering/record 审计 + 3项 record 同步修复 |
| 2026-03-03 | v1.3 | 根配置文件省察 + 15项偏差修复 + v0.01 正式版封版：全部文档层均通过定稿门禁 |
| 2026-03-03 | v1.4 | 根配置文件终审（15项偏差修复）+ roadmap/spec-01~05 状态升格 Active |
| 2026-03-04 | v1.5 | 进入 Week1 文档校对：spec-01 补齐“校对证据”落点并完成跨文档一致性复核 |
| 2026-03-04 | v1.6 | 完成 spec-02~05 文档校对与证据化留痕；v0.01 spec-01~05 校对闭环完成 |
| 2026-03-04 | v1.7 | 实现前最后一轮总校对完成：roadmap 新增追溯索引与七维勾选，spec-01~05 统一 REV-ID |
| 2026-03-06 | v1.8 | 完成 v0.01 基线跑通后的回望审视，形成“保留不动 / v0.01 立即修订 / v0.02+ 延后”三分法清单 |
| 2026-03-06 | v1.9 | 完成 v0.01 回望修订首轮落地：roadmap、spec-01/spec-02/spec-05、data-layer/backtest-report 说明性口径已按实战证据更新 |
| 2026-03-06 | v1.10 | 完成 spec-04 / broker-design 回望修订；完成 Week1 Data Layer Gap Audit，并修正 `MIN_AMOUNT` 与 `stock_info.list_status` 默认主链路口径 |
| 2026-03-06 | v1.11 | 明确数据存储口径：执行库 / raw 源库 / Parquet / logs / cache 边界固定，并将 raw bootstrap 并入主入口 |
| 2026-03-06 | v1.12 | 进入 Week2 首批实现收口：MSS/IRS 归一化与阈值对齐，候选解释性与组合模式补齐 |
| 2026-03-06 | v1.13 | Week2 联调入口落地：三组消融对照脚本与 selector→strategy smoke 入口可执行，相关单测/集成测试通过 |
| 2026-03-06 | v1.14 | Week2 初轮证据落地：短窗消融与真实 smoke 证据已产出，working copy 保护补齐，spec-02/spec-03 勾选同步更新 |
| 2026-03-06 | v1.15 | Week2 分布审计完成：IRS 唯一排名修正，MSS/IRS 全区间证据落地，并明确 MSS 全中性 / IRS 111 桶 / 全周期三场消融性能阻塞为当前 open risk |
| 2026-03-06 | v1.16 | 补齐 v0.01 当前版算法设计：形成 Overview + MSS + IRS + PAS 四份实现级算法文档，明确旧版参考与当前可执行口径的边界 |
| 2026-03-06 | v1.17 | 完成 Selector 评审与 SW31 修正：行业链路切到申万一级成员映射优先，L2 仅处理交易日，IRS 增加最小行业覆盖门槛，并确认 raw 申万成员源数据仍待补采 |




