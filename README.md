# EmotionQuant

EmotionQuant 是面向中国 A 股的情绪驱动量化系统。

## 设计入口

- `v0.01` 历史基线：[`docs/design-v2/01-system/system-baseline.md`](docs/design-v2/01-system/system-baseline.md)
- `v0.01-plus` 当前主开发线：[`docs/spec/v0.01-plus/README.md`](docs/spec/v0.01-plus/README.md)
- 当前主开发线设计权威层：[`blueprint/README.md`](blueprint/README.md)
- 当前治理状态：[`docs/spec/common/records/development-status.md`](docs/spec/common/records/development-status.md)

当前主线执行链路：

`Selector 初选 -> BOF 触发 -> IRS 排序 -> MSS 控仓位 -> Broker 执行`

说明：
- `v0.01` 已冻结为历史尝试，仅作对照、回退与回归验证。
- `v0.01-plus` 是当前主开发线。
- `backtrader` 仅负责交易日历推进与数据喂入；风控、撮合、仓位和状态机由自研 `Broker` 内核实现。

## 快速开始

### 环境配置

**推荐目录结构**：
```text
G:\
├── EmotionQuant-gamma\      # 代码 + 文档（本仓库）
├── EmotionQuant_data\       # 本地数据库（不进 Git）
└── EmotionQuant-temp\       # 临时文件（不进 Git）
```

**配置步骤**：
1. 复制 `.env.example` 为 `.env`
2. 填写 `TUSHARE_TOKEN`
3. 设置 `DATA_PATH=G:\EmotionQuant_data`
4. 需要时设置 `LOG_PATH=G:\EmotionQuant-temp\logs`

详细配置：[`docs/operations/setup-guide.md`](docs/operations/setup-guide.md)

### 安装依赖

```bash
pip install -e .
pip install -e ".[dev]"
pytest -v
```

### 基本使用

```bash
python main.py fetch --start 2020-01-01 --end 2024-12-31
python main.py build --layers all
python main.py backtest --start 2020-01-01 --end 2024-12-31 --patterns bof
python main.py run
```

## 目录结构

```text
EmotionQuant-gamma/
├── blueprint/              # 新版设计权威层（full design / implementation spec / execution）
├── src/                    # 实现代码（6 模块）
├── tests/                  # 自动化测试（unit/integration/patches）
├── scripts/                # 工具脚本（data/backtest/report/ops/setup）
├── docs/                   # 文档总入口（见 docs/README.md）
│   ├── design-v2/          # 历史基线与历史总览（不再承载现行设计正文）
│   ├── Strategy/           # 理论母本与方法论溯源
│   ├── observatory/        # 观察、评审与复盘
│   ├── spec/               # 分版本归档与当前主开发线材料
│   ├── steering/           # 治理铁律与不可越界约束
│   ├── reference/          # 外部参考资料
│   └── workflow/           # 固定执行流程
├── .env.example
├── pyproject.toml
├── main.py
└── README.md
```

## 相关文档

- 配置指南：[`docs/operations/setup-guide.md`](docs/operations/setup-guide.md)
- 文档导航：[`docs/README.md`](docs/README.md)
- 当前状态：[`docs/spec/common/records/development-status.md`](docs/spec/common/records/development-status.md)
- 主线路线图：[`docs/spec/v0.01-plus/roadmap/v0.01-plus-roadmap.md`](docs/spec/v0.01-plus/roadmap/v0.01-plus-roadmap.md)
- Agent 规则：[`AGENTS.md`](AGENTS.md)

## 许可证

MIT（见 [`LICENSE`](LICENSE)）
