# AGENTS.md

本文件为自动化代理提供最小、可执行的仓库工作规则。与 `AGENTS.en.md`、`CLAUDE.md`、`CLAUDE.en.md`、`WARP.md`、`WARP.en.md` 内容等价，面向通用代理运行时。

---

## 1. 文档定位

- 作用：给自动化代理提供最小、可执行的仓库工作规则。
- **权威设计入口**：`docs/design-v2/rebuild-v0.01.md`（重构设计文档，单一事实源）
- 旧版设计/治理文档已归档至 `docs/archive/`（只读）

---

## 2. 系统定位

EmotionQuant 是面向中国 A 股的情绪驱动量化系统。

- 个人项目，单开发者
- 执行模型：**四周增量交付**（每周产出可独立验证的交付物）
- 文档服务实现，不追求"文档完美"

---

## 3. 铁律ﾈ10 条ﾉ

1. **选股 = MSS + IRS**，交易时机 = PAS，风控执行独立。三者不混。
2. **MSS 只看市场级**，不碰行业和个股。
3. **IRS 只看行业级**，不碰市场温度和个股形态。
4. **PAS 只看个股形态**，不把 MSS/IRS 分数当输入。
5. **同一原始观测只归属一个因子**，禁止跨因子重复计分。
6. **模块间只传“结果契约”**（pydantic 对象），不传内部中间特征。
7. **每个模块可独立单测**，不依赖其他模块启动。
8. **Backtest 和纸上交易共用同一个 broker 内核**。
9. **路径/密钥禁止硬编码**，统一经 config.py 注入。
10. **执行语义固定为 T+1 Open**：signal_date=T，execute_date=T+1，成交价=T+1 开盘价。

详见：`docs/design-v2/rebuild-v0.01.md` §1

---

## 4. 开发流程

- 执行模型：四周增量交付（见 rebuild-v0.01.md §9）
- 每周产出可独立验证的交付物（可跑的代码 + 通过的测试）
- 分支命名：`rebuild/{module}`，合并目标 `main`

---

## 5. 数据契约

模块间传递 pydantic 对象（contracts.py）：
- `MarketScore`（MSS → Selector）
- `IndustryScore`（IRS → Selector）
- `StockCandidate`（Selector → Strategy）
- `Signal`（Strategy → Broker）
- `Order` / `Trade`（Broker 内部 → Report）

代码中使用英文，注释/文档/UI 使用中文。统一 `snake_case`。
L1 层用 `ts_code`（TuShare 格式），L2+ 层用 `code`ﾈ6 位纯代码）。

详见：`docs/design-v2/rebuild-v0.01.md` §5

---

## 6. 数据架构

DuckDB 单库存储，通过 L1-L4 分层解耦。数据根目录通过 `DATA_PATH` 环境变量注入（仓库外独立目录）。

| 层级 | 内容 |
|------|------|
| L1 | 原始数据（API 直取，fetcher.py 写入） |
| L2 | 加工数据（复权价/均线/量比/市场截面/行业日线） |
| L3 | 算法输出（MSS/IRS/PAS/基因库） |
| L4 | 历史分析缓存（订单/成交/报告） |

**依赖规则**：L2 只读 L1；L3 只读 L1/L2；L4 只读 L1/L2/L3。禁止反向依赖。

详见：`docs/design-v2/rebuild-v0.01.md` §4.1

---

## 7. 架构分层ﾈ6 模块ﾉ

| 模块 | 职责 |
|----|------|
| Data | 拉数据、清洗、落库、缓存算法输出 |
| Selector | MSS 市场情绪 + IRS 行业轮动 + 基因库过滤 → 候选池 |
| Strategy | PAS 形态检测（突破/回踩）→ 交易信号 |
| Broker | 风控 + 撒合（回测和纸上交易共用内核） |
| Backtest | 历史回测（backtrader 单引擎） |
| Report | 回测报告 + 每日选股报告 + 预警 |

---

## 8. 治理结构

### 8.1 目录定位

| 目录 | 定位 |
|------|------|
| `docs/design-v2/` | 新版设计文档（rebuild-v0.01.md 为唯一权威入口） |
| `docs/design/` | 旧版设计（待归档） |
| `docs/archive/` | 历史归档（只读） |

### 8.2 单一事实源（SoT）

`docs/design-v2/rebuild-v0.01.md` 是系统设计的唯一权威文件（架构/模块/契约/铁律/计划）。

### 8.3 归档规则

- 归档命名：`archive-{model}-{version}-{date}`
- 归档目录只读，不再迭代
- 旧版设计文档归档至 `docs/archive/archive-docs-toplevel-v5-20260301/`
- 旧版治理文档归档至 `docs/archive/archive-steering-v6-20260301/`

---

## 9. 质量门控

- 命令可运行、测试可复现、产物可检查
- 硬编码检查、A 股规则检查
- 有效测试优先于覆盖率数字
- TODO/HACK/FIXME：开发中允许，合并前必须清理

---

## 10. 核心算法约束

- 选股 = MSS + IRS，交易时机 = PAS，风控执行独立。三者不混
- MSS 只看市场级，IRS 只看行业级，PAS 只看个股形态
- 同一原始观测只归属一个因子，禁止跨因子重复计分
- 模块间只传“结果契约”（pydantic 对象），不传内部中间特征

详见：`docs/design-v2/rebuild-v0.01.md` §1 铁律 + §4 模块边界

---

## 11. 技术栈口径

- Python `>=3.10`
- 数据：DuckDB 单库存储
- 数据源：TuShare（主）+ AKShare（备）
- 回测：backtrader 单引擎
- GUI：MVP 阶段命令行，GUI 延后

详见：`docs/design-v2/rebuild-v0.01.md` §6

---

## 12. 仓库远端

- `origin`: `${REPO_REMOTE_URL}`（定义见 `.env.example`）
- `backup`: `${REPO_BACKUP_REMOTE_URL}`（定义见 `.env.example`，本地 remote 名称建议 `backup`）

---

## 13. 历史说明

旧版所有设计/治理文档已归档至 `docs/archive/`（只读）：
- `archive-docs-toplevel-v5-20260301/` — 旧版 roadmap/system-overview/module-index/naming-conventions/naming-contracts/technical-baseline
- `archive-steering-v6-20260301/` — 旧版 6A-WORKFLOW/系统铁律/CORE-PRINCIPLES/GOVERNANCE-STRUCTURE/TRD/模板
- `designv1/` / `reference/` / `sos/` — 更早期历史

新版设计权威入口：`docs/design-v2/rebuild-v0.01.md`

---

## 14. 执行计划

当前执行计划见 `docs/design-v2/rebuild-v0.01.md` §9（四周计划）。

## 15. Git 认证基线

- TLS 后端基线：优先 `openssl`（`git config --global http.sslbackend openssl`，允许仓库内覆盖）。
- 受限沙箱会话中，认证 `git push` 建议在非沙箱或提权模式执行，确保凭据交互与存储路径可访问。

## 16. MCP 基线

推荐 MCP 服务：
- `context`（Context7 文档/上下文检索）
- `fetch`（HTTP 内容抓取）
- `filesystem`（跨目录文件操作）
- `sequential-thinking`（多步推理）
- `mcp-playwright`（浏览器自动化）

Skill 与 MCP 边界：
- Skill 是流程说明/模板。
- MCP 是运行时工具。
- Skill 不替代 MCP。

默认触发策略：
- 版本敏感 API/框架问题优先 `context`。
- 无需浏览器渲染的网页内容优先 `fetch`。
- 非简单文件读写优先 `filesystem`。
- 多分支决策与复杂排障优先 `sequential-thinking`。
- UI 流程与截图回放优先 `mcp-playwright`。

Bootstrap：
- 一键：`powershell -ExecutionPolicy Bypass -File scripts/setup/bootstrap_dev_tooling.ps1`
- 仅 MCP：`powershell -ExecutionPolicy Bypass -File scripts/setup/configure_mcp.ps1 -ContextApiKey <your_key>`
- 可选 MCP 目标目录：`-CodexHome <path>`（默认：项目内 `.tmp/codex-home`）
- 仅 Hooks：`powershell -ExecutionPolicy Bypass -File scripts/setup/configure_git_hooks.ps1`
- 仅 Skills 检查：`powershell -ExecutionPolicy Bypass -File scripts/setup/check_skills.ps1`
