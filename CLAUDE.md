# CLAUDE.md

本文件为自动化代理提供最小、可执行的仓库工作规则。与 `AGENTS.md`、`AGENTS.en.md`、`CLAUDE.md`、`CLAUDE.en.md`、`WARP.md`、`WARP.en.md` 内容等价，面向通用代理运行时。

**文档版本**：`v0.01-plus 主线替代版`  
**文档状态**：`Active`  
**封版日期**：`不适用（Active SoT）`  
**变更规则**：`允许在不改变 v0.01 Frozen 历史基线的前提下，按当前主开发线实现与 Gate 结果受控修订。`

---

## 1. 文档定位

- 作用：给自动化代理提供最小、可执行的仓库工作规则。
- **v0.01 历史基线入口**：`docs/design-v2/01-system/system-baseline.md`（冻结版系统基线）
- **当前主开发线入口**：`docs/spec/v0.01-plus/README.md`
- **当前设计 SoT**：`docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md`
- 分阶段文档统一归档至 `docs/spec/`；参考资料统一位于 `docs/reference/`
- **当前治理状态**：`docs/spec/common/records/development-status.md`（当前状态、历史摘要与重启条件）

---

## 2. 系统定位

EmotionQuant 是面向中国 A 股的情绪驱动量化系统。

- 个人项目，单开发者
- 执行模型：**四周增量交付**（每周产出可独立验证的交付物）
- 文档服务实现，不追求“文档完美”

---

## 3. 当前主线铁律（v0.01-plus）

1. **当前主线执行链路 = Selector 初选 -> BOF 触发 -> IRS 排序 -> MSS 控仓位 -> Broker 执行。**
2. **v0.01 Frozen 继续保留为历史对照与回退参考，不再充当当前主线。**
3. **Selector 只做基础过滤与规模控制，不做 MSS gate / IRS filter 交易决策。**
4. **IRS 只做行业级横截面增强，不做前置硬过滤。**
5. **MSS 只做市场级风险调节，不进入个股横截面总分。**
6. **PAS 是框架层概念，当前主线实现仍仅 BOF。**
7. **模块间只传结果契约，不传内部中间特征。**
8. **Backtest 和纸上交易共用同一个 broker 内核。**
9. **路径/密钥禁止硬编码**，统一经 `config.py` 注入。
10. **执行语义固定为 T+1 Open**：`signal_date=T`，`execute_date=T+1`，成交价=`T+1` 开盘价。

详见：`docs/spec/v0.01-plus/README.md` 与 `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md`

---

## 4. 开发流程

- 执行模型：四周增量交付
- 每周产出可独立验证的交付物（可跑的代码 + 通过的测试）
- 分支命名：`rebuild/{module}`，合并目标 `main`

---

## 5. 数据契约

模块间传递 pydantic 对象（`contracts.py`）：
- `MarketScore`（MSS 计算输出；当前主线消费者为 `Broker / Risk`）
- `IndustryScore`（IRS 计算输出；当前主线消费者为 `Strategy / Ranker`）
- `StockCandidate`（Selector -> Strategy）
- `Signal`（Strategy -> Broker）
- `Order` / `Trade`（Broker 内部 -> Report）

代码中使用英文，注释/文档/UI 使用中文。统一 `snake_case`。
L1 层用 `ts_code`（TuShare 格式），L2+ 层用 `code`（6 位纯代码）。

详见：`docs/spec/v0.01-plus/governance/v0.01-plus-data-contract-table.md`

---

## 6. 数据与目录纪律

DuckDB 单库存储，通过 L1-L4 分层解耦。数据根目录通过 `DATA_PATH` 环境变量注入（仓库外独立目录）。

| 层级 | 内容 |
|------|------|
| L1 | 原始数据（API 直取，fetcher.py 写入） |
| L2 | 加工数据（复权价/均线/量比/市场截面/行业日线） |
| L3 | 算法输出（MSS/IRS/PAS(BOF)/Gene分析） |
| L4 | 历史分析缓存（订单/成交/报告） |

**依赖规则**：L2 只读 L1；L3 只读 L1/L2；L4 只读 L1/L2/L3。禁止反向依赖。

**目录纪律（强制）**：
- `G:\EmotionQuant-gamma` 只放代码、文档、配置与必要脚本，不放运行时缓存、临时 DuckDB、测试临时目录。
- `G:\EmotionQuant_data` 存放本地数据库、日志与长期数据产物。
- `G:\EmotionQuant-temp` 存放临时文件、运行副本、实验缓存与中间产物。

---

## 7. 架构分层（6 模块）

| 模块 | 职责 |
|----|------|
| Data | 拉数据、清洗、落库、缓存算法输出 |
| Selector | 基础过滤 + 规模控制 + `preselect_score` |
| Strategy | `BOF` 触发 + `IRS` 排序 |
| Broker | `MSS` 风控覆盖 + 撮合（回测和纸上交易共用内核） |
| Backtest | 历史回测（backtrader 单引擎；仅时钟推进/数据喂入，交易内核为自研 Broker） |
| Report | 回测报告 + 每日选股报告 + 预警 |

---

## 8. 治理结构

### 8.1 目录定位

| 目录 | 定位 |
|------|------|
| `docs/design-v2/` | 系统级设计文档（`system-baseline.md` 为 `v0.01 Frozen` 历史基线；`v0.01-plus` 设计入口见 `down-to-top-integration.md`） |
| `docs/spec/` | 分阶段文档单轨入口（v0.01+；按版本目录组织 roadmap/governance/evidence/records） |
| `docs/spec/common/records/` | 跨版本治理记录（development-status / debts / reusable-assets） |
| `docs/reference/` | 参考资料与外部方法论（非执行口径） |

### 8.2 单一事实源（SoT）

`docs/design-v2/01-system/system-baseline.md` 是 `v0.01 Frozen` 的历史权威文件；当前主开发线以 `docs/spec/v0.01-plus/README.md` 与 `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md` 为准。

### 8.3 归档规则

- 分阶段文档统一使用版本目录：`docs/spec/<version>/`
- 当前执行与归档使用同一套版本目录：`docs/spec/<version>/`
- 跨版本治理记录统一位于：`docs/spec/common/records/`
- 系统级设计文档仅存放于：`docs/design-v2/`

---

## 9. 质量门控

- 命令可运行、测试可复现、产物可检查
- 硬编码检查、A 股规则检查
- 有效测试优先于覆盖率数字
- 禁止只提交“裸代码”：涉及关键业务逻辑、时序规则、状态机分支的代码必须有必要注释（说明意图、边界、约束），避免“能跑但不可维护”
- 代码交付必须同时包含：最小可读注释 + 对应测试/验证证据（至少其一可追溯到用例或回归记录）
- TODO/HACK/FIXME：开发中允许，合并前必须清理

---

## 10. 核心算法约束

- 当前主线：`Selector 初选 -> BOF -> IRS 排序 -> MSS 控仓位`
- `MSS` 只看市场级；`IRS` 只看行业级；`PAS` 当前仅 `BOF`
- 同一原始观测只归属一个因子，禁止跨因子重复计分
- 模块间只传“结果契约”（pydantic 对象），不传内部中间特征

---

## 11. 技术栈口径

- Python `>=3.10`
- 数据：DuckDB 单库存储
- 数据源：TuShare（主）+ AKShare（备）
- 回测：backtrader 单引擎（仅时钟推进/数据喂入，交易内核为自研 Broker）
- GUI：MVP 阶段命令行，GUI 延后

---

## 12. 仓库远端

- `origin`: `${REPO_REMOTE_URL}`（定义见 `.env.example`；当前值：`https://github.com/everything-is-simple/EmotionQuant-gamma`）
- `backup`: `${REPO_BACKUP_REMOTE_URL}`（定义见 `.env.example`；当前值：`https://gitee.com/wangweiyun2233/EmotionQuant-gamma`；本地 remote 名称建议 `backup`）
- 推送策略：凡需同步到远端的提交，必须同时推送到 `origin` 与 `backup`；不接受只推送单一远端。

---

## 13. 历史说明

v0.01 历史基线入口：`docs/design-v2/01-system/system-baseline.md`
当前主开发线入口：`docs/spec/v0.01-plus/README.md`
分阶段文档单轨入口：`docs/spec/`
跨版本治理记录：`docs/spec/common/records/`
当前执行入口：`docs/spec/`
外部参考资料：`docs/reference/`

---

## 14. 执行计划

当前执行计划见 `docs/spec/v0.01-plus/README.md` 与 `docs/spec/common/records/development-status.md`；`v0.01` 历史执行计划见 `docs/design-v2/01-system/system-baseline.md`。

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

## 17. 测试与工具目录规范（强制）

### 17.1 tests 目录必须按“类型 + 模块”组织

1. `tests/unit/<module>/`：单元测试（纯函数/单模块）
2. `tests/integration/<module>/`：集成测试（跨模块调用链）
3. `tests/patches/<module>/`：补丁/回归测试（历史缺陷防回退）
4. `<module>` 必须与 `src/` 对齐：`data/selector/strategy/broker/backtest/report/core`
5. 修改 `src/<module>/` 时，必须在对应模块目录补/改测试，不允许散落在 tests 根目录

### 17.2 scripts 目录是唯一工具入口

1. 任何“非系统运行时、但研发/运维必须”的程序统一放在 `scripts/`
2. 按系统域分类：`scripts/data/`、`scripts/backtest/`、`scripts/report/`、`scripts/ops/` 等
3. `scripts/` 下工具不得反向污染 `src/` 运行时依赖（即：业务模块不依赖脚本入口）
4. 新增工具必须放入对应分类目录，不允许散落在仓库根目录

