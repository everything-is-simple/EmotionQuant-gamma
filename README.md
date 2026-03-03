# EmotionQuant

EmotionQuant 是面向中国 A 股的情绪驱动量化系统。

## 设计文档

唯一权威入口：[`docs/design-v2/rebuild-v0.01.md`](docs/design-v2/rebuild-v0.01.md)

系统文档基线：`v0.01 正式版`（封版日期：`2026-03-03`；后续仅允许勘误与链接修复，不修改执行口径）
封版记录：[`docs/design-v2/release-v0.01-formal.md`](docs/design-v2/release-v0.01-formal.md)

涵盖：6 模块架构、MSS/IRS/PAS 因子体系、L1-L4 数据分层、pydantic 契约、四周落地计划。

回测口径说明：`backtrader` 仅用于交易日历推进与数据喂入；风控、撮合、仓位与状态机由自研 `Broker` 内核实现。

## 快速开始

```bash
# 安装依赖
pip install -e .

# 开发依赖
pip install -e ".[dev]"

# 运行测试
pytest -v
```

## 目录结构

- `src/` — 实现代码（Data / Selector / Strategy / Broker / Backtest / Report）
- `tests/` — 自动化测试
- `docs/design-v2/` — 新版设计文档
- `docs/archive/` — 历史归档（只读）

## 环境配置

复制 `.env.example` 为 `.env` 并填入实际值。关键变量：

- `TUSHARE_TOKEN` — TuShare API token
- `DATA_PATH` — 数据根目录（仓库外独立目录）

## 许可证

MIT（见 [`LICENSE`](LICENSE)）
