# 技术架构

**版本**: `v0.01 正式版`  
**状态**: `Frozen`  
**封版日期**: `2026-03-03`  
**变更规则**: `仅允许勘误、链接修复与说明性澄清；若治理口径调整，必须先修订上游 baseline。`  
**上游文档**: `docs/design-v2/01-system/system-baseline.md`

## 冻结区与冲突处理

1. 本文档属于冻结区；默认只允许勘误、链接修复与说明性澄清。若涉及执行语义、模块边界或口径调整，必须进入后续版本处理。
2. 若本文档与 `docs/design-v2/01-system/system-baseline.md` 冲突，以 baseline 为准，并应同步回写本文档。
3. 当前治理状态与是否恢复实现，以 `docs/spec/common/records/development-status.md` 为准。
4. 版本证据、回归结果与阶段记录，统一归档到 `docs/spec/<version>/`。

## v0.01 冻结口径

1. 形态触发器采用注册表，但仅启用 `BOF`。
2. 扫描采用两阶段：全市场粗筛（5000 -> 约200）后执行形态精扫。
3. 执行语义固定：T 日信号，T+1 开盘成交。
4. 回测与纸上交易共用 Broker 内核，禁止双语义。
5. MSS/IRS 必须按 `BOF baseline -> BOF+MSS -> BOF+MSS+IRS` 消融验证。
6. `ENABLE_GENE_FILTER` 在 v0.01 强制关闭，仅允许事后分析。

## 数据流

```
fetcher  ──写→  L1 表
cleaner  ──读 L1 → 写→  L2 表
builder  ──统一调度 L2/L3 生成（L4 由 broker/report 运行时写入）
mss/irs/gene ──读 L2 → 写→  L3 表（可并行）
selector ──读 L3 → 输出候选池（内存，不落库）
strategy ──读 L2 + 候选池 → 调用 pas_*.py → 写→  l3_signals
broker   ──读 信号 → 写→  L4 表
report   ──读 L3 + L4 → 写→  L4 报告
backtest ──读 L1-L3 历史 → 调用 broker 内核 → 写 L4
```

模块间不直接调用，通过 DuckDB 表（L1→L2→L3→L4）交互。

## L1-L4 数据分层

| 层 | 定位 | 写入者 | 核心表 |
|----|------|--------|--------|
| L1 | 原始数据（API直取） | fetcher.py | l1_stock_daily, l1_index_daily, l1_stock_info, l1_trade_calendar |
| L2 | 加工数据（算一次到处用） | cleaner.py | l2_stock_adj_daily, l2_industry_daily, l2_market_snapshot |
| L3 | 算法输出 | mss/irs/strategy/gene | l3_mss_daily, l3_irs_daily, l3_signals, l3_stock_gene |
| L4 | 历史分析缓存 | broker/report | l4_orders, l4_trades, l4_stock_trust, l4_daily_report, l4_pattern_stats |

## 股票代码格式

- **L1 层**：TuShare 原始格式 `ts_code`（如 `000001.SZ`）
- **L2+ 层**：纯代码 `code`（如 `000001`）
- 转换时机：L1→L2 清洗时一次性转换（`cleaner.py`），不在其他地方做

## DuckDB 规范

- **单写者原则**：同一时刻只有一个进程/线程写入
- **批量写入**：禁止逐行 INSERT，统一 `INSERT INTO ... SELECT * FROM df`
- **WAL 模式**：启用 Write-Ahead Logging
- **连接管理**：store.py 持有唯一连接，其他模块通过 store 读写，不自己开连接
- **幂等**：`trade_date + module` 为幂等键，同一天重跑不产生重复数据（upsert）

## 目录结构

```
src/
├── data/           # fetcher.py, cleaner.py, builder.py, store.py
├── selector/       # mss.py, irs.py, gene.py, selector.py
├── strategy/       # pattern_base.py, pas_bof.py(活跃), pas_*.py(在册), registry.py, strategy.py
├── broker/         # broker.py, risk.py, matcher.py
├── backtest/       # engine.py
├── report/         # reporter.py
├── contracts.py    # pydantic 模块边界契约
└── config.py       # 全局配置
tests/
main.py             # CLI 入口
```

## 模块间数据契约（contracts.py）

| 契约 | 方向 | 核心字段 |
|------|------|---------|
| MarketScore | MSS → Selector | date, score(0-100), signal(BULLISH/NEUTRAL/BEARISH) |
| IndustryScore | IRS → Selector | date, industry, score, rank |
| StockCandidate | Selector → Strategy | code, industry, score |
| Signal | Strategy → Broker | signal_id, code, signal_date, action(BUY in v0.01), strength(0-1), pattern, reason_code |
| Order | Broker 内部 | order_id, signal_id, code, action, quantity, execute_date, pattern, is_paper, status, reject_reason |
| Trade | Broker → Report | trade_id, order_id, code, execute_date, action, price, quantity, fee, pattern, is_paper |

## 依赖栈

| 库 | 用途 |
|----|------|
| tushare | 数据获取（主） |
| akshare | 数据获取（备，TuShare 不可用时降级） |
| duckdb | 本地存储 |
| backtrader | 回测引擎（唯一） |
| pandas | 数据处理 |
| pydantic | 模块边界契约 |
| loguru | 日志 |
| tenacity | 网络重试（fetcher 失败重试 3 次） |

## CLI 入口

```
python main.py fetch                          # 拉取增量数据
python main.py build --layers=l2,l3           # 生成 L2+L3
python main.py build --layers=all --force     # 全量重建
python main.py backtest --start=2023-01-01    # 回测
python main.py backtest --patterns=bof        # 单形态回测（v0.01）
python main.py run                            # 每日全链路
```





