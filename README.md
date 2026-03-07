# EmotionQuant

EmotionQuant 是面向中国 A 股的情绪驱动量化系统。

## 设计文档

唯一权威入口：[`docs/design-v2/system-baseline.md`](docs/design-v2/system-baseline.md)

系统文档基线：`v0.01 正式版`（封版日期：`2026-03-03`；后续仅允许勘误与链接修复，不修改执行口径）
封版记录：[`docs/spec/v0.01/records/release-v0.01-formal.md`](docs/spec/v0.01/records/release-v0.01-formal.md)

涵盖：6 模块架构、MSS/IRS/PAS 因子体系、L1-L4 数据分层、pydantic 契约、四周落地计划。

回测口径说明：`backtrader` 仅用于交易日历推进与数据喂入；风控、撮合、仓位与状态机由自研 `Broker` 内核实现。

## 快速开始

### 环境配置

**推荐目录结构**（代码与数据分离）：
```
G:\
├── EmotionQuant-gamma\      # 代码 + 文档（本仓库）
├── EmotionQuant_data\       # 本地数据库（不进 Git）
└── EmotionQuant-temp\       # 临时文件（不进 Git）
```

**配置步骤**：
1. 复制 `.env.example` 为 `.env`
2. 填写 `TUSHARE_TOKEN`（必填）
3. 设置 `DATA_PATH=G:\EmotionQuant_data`（或其他路径）
4. 设置 `LOG_PATH=G:\EmotionQuant-temp\logs`（可选）

详细配置指南：[`docs/operations/setup-guide.md`](docs/operations/setup-guide.md)

### 安装依赖

```bash
# 安装运行时依赖
pip install -e .

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest -v
```

### 基本使用

```bash
# 1. 拉取数据
python main.py fetch --start 2020-01-01 --end 2024-12-31

# 2. 构建数据层
python main.py build --layers all

# 3. 运行回测
python main.py backtest --start 2020-01-01 --end 2024-12-31 --patterns bof

# 4. 日常运行（Week4 全流程）
python main.py run
```

## 目录结构

```
EmotionQuant-gamma/
├── src/                    # 实现代码（6 模块）
│   ├── data/               # Data 模块（fetcher/cleaner/builder/store）
│   ├── selector/           # Selector 模块（MSS/IRS/Gene/Selector）
│   ├── strategy/           # Strategy 模块（PAS/Registry/Strategy）
│   ├── broker/             # Broker 模块（Risk/Matcher）
│   ├── backtest/           # Backtest 模块（Engine）
│   └── report/             # Report 模块（Reporter）
├── tests/                  # 自动化测试
│   ├── unit/               # 单元测试（按模块组织）
│   ├── integration/        # 集成测试（跨模块调用链）
│   └── patches/            # 补丁/回归测试（历史缺陷防回退）
├── scripts/                # 工具脚本
│   ├── data/               # 数据相关工具
│   ├── backtest/           # 回测相关工具
│   ├── report/             # 报告相关工具
│   ├── ops/                # 运维工具
│   └── setup/              # 环境配置工具
├── docs/                   # 文档总入口（见 docs/README.md）
│   ├── design-v2/          # 系统设计（单一事实源）
│   │   ├── 01-system/      # 系统级设计（system-baseline.md 为 SoT）
│   │   ├── 02-modules/     # 模块级设计
│   │   └── 03-algorithms/  # 算法级设计（MSS/IRS/PAS）
│   ├── Strategy/           # 策略理论基础（MSS/IRS/PAS）
│   ├── observatory/        # 宏观观察与验证
│   ├── spec/               # 分阶段归档（v0.01-v0.06）
│   │   ├── v0.01/          # v0.01 阶段材料
│   │   ├── v0.02/          # v0.02 阶段材料
│   │   ├── ...             # v0.03-v0.06
│   │   └── common/         # 跨版本文档
│   ├── steering/           # 治理铁律（12 条产品铁律）
│   ├── reference/          # 参考资料
│   │   ├── a-stock-rules/  # A股市场规则
│   │   └── operations/     # 运维操作指南
│   └── workflow/           # 工作流程
├── .env.example            # 环境变量模板
├── pyproject.toml          # 项目配置与依赖
├── main.py                 # CLI 入口
└── README.md               # 本文件
```

**文档架构说明**：
- **三大支柱**：`design-v2/`（系统设计）、`Strategy/`（策略理论）、`observatory/`（观察验证）
- **三大支撑**：`steering/`（治理铁律）、`spec/`（分阶段归档）、`workflow/`（工作流程）
- **两大辅助**：`reference/`（参考资料）、`README.md`（总导航）

详见：[`docs/README.md`](docs/README.md) 和 [`docs/REORGANIZATION-COMPLETE-REPORT.md`](docs/REORGANIZATION-COMPLETE-REPORT.md)

## 相关文档

- 📖 **配置指南**：[`docs/operations/setup-guide.md`](docs/operations/setup-guide.md) - 环境配置详细步骤
- 📖 **系统设计**：[`docs/design-v2/system-baseline.md`](docs/design-v2/system-baseline.md) - 系统基线（SoT）
- 📖 **文档导航**：[`docs/README.md`](docs/README.md) - 完整文档索引
- 📖 **开发规则**：[`AGENTS.md`](AGENTS.md) - Agent 开发规则
- 📖 **整理报告**：[`docs/REORGANIZATION-COMPLETE-REPORT.md`](docs/REORGANIZATION-COMPLETE-REPORT.md) - 文档整理报告

## 许可证

MIT（见 [`LICENSE`](LICENSE)）




