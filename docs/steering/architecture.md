# 技术架构

**版本**: `v0.01-plus 主线替代版`  
**状态**: `Active`  
**封版日期**: `不适用（Active SoT）`  
**变更规则**: `允许在不改变 v0.01 Frozen 历史基线的前提下，按当前主开发线设计与实现反馈受控修订。`  
**上游文档**: `docs/design-migration-boundary.md`, `blueprint/README.md`, `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`

## 当前主线架构口径

1. `v0.01 Frozen` 是历史架构基线，不再代表当前主开发线。
2. `v0.01-plus` 当前主线架构固定为：`Selector 初选 -> BOF 触发 -> IRS 排序 -> MSS 控仓位 -> Broker 执行`。
3. 任何文档若继续把 `MSS/IRS` 写成 `Selector` 前置漏斗，均应视为历史说明，而非当前执行口径。

## 数据流

```text
fetcher  -> 写 L1
cleaner  -> 读 L1 写 L2
builder  -> 统一调度 L2/L3 生成
mss      -> 读 L2_market_snapshot 写 l3_mss_daily
irs      -> 读 l2_industry_daily 写 l3_irs_daily
selector -> 读 L1/L2 基础字段，输出候选池（内存）
strategy -> 读 L2 + 候选池，执行 BOF，写 l3_signals + l3_signal_rank_exp
broker   -> 读排序信号 + l3_mss_daily，写 L4 订单/成交
report   -> 读 L3 + L4，输出报告与归因
backtest -> 读 L1-L3 历史，调用 broker 内核，写 L4
```

模块间不直接调用内部实现；通过 DuckDB 表和契约对象交互。

## L1-L4 数据分层

| 层 | 定位 | 写入者 | 核心表 |
|----|------|--------|--------|
| L1 | 原始数据（API直取） | fetcher.py | l1_stock_daily, l1_index_daily, l1_stock_info, l1_trade_calendar |
| L2 | 加工数据（算一次到处用） | cleaner.py | l2_stock_adj_daily, l2_industry_daily, l2_market_snapshot |
| L3 | 算法输出 | mss/irs/strategy | l3_mss_daily, l3_irs_daily, l3_signals, l3_signal_rank_exp |
| L4 | 历史分析缓存 | broker/report | l4_orders, l4_trades, l4_stock_trust, l4_daily_report, l4_pattern_stats |

## 模块职责

| 模块 | 当前主线职责 |
|------|-------------|
| Data | 拉取、清洗、落库、生成统一数据层 |
| Selector | 基础过滤 + 规模控制 + `preselect_score` |
| Strategy | `BOF` 触发 + `IRS` 排序 + sidecar 排名落地 |
| Broker | 读取排序信号，结合 `MSS` 执行风险覆盖与撮合 |
| Backtest | 历史回测，调 broker 内核 |
| Report | 统计、归因、证据沉淀 |

## 模块间数据契约（contracts.py）

| 契约 | 当前主线方向 | 核心字段 |
|------|-------------|---------|
| MarketScore | MSS -> Broker / Risk | date, score, signal |
| IndustryScore | IRS -> Strategy / Ranker | date, industry, score, rank |
| StockCandidate | Selector -> Strategy | code, industry, score, preselect_score |
| Signal | Strategy -> Broker | signal_id, code, signal_date, action, strength, pattern, reason_code |
| Order | Broker 内部 | order_id, signal_id, code, action, quantity, execute_date, pattern, is_paper, status, reject_reason |
| Trade | Broker -> Report | trade_id, order_id, code, execute_date, action, price, quantity, fee, pattern, is_paper |

说明：
- 当前迁移期排序真相源在 `l3_signal_rank_exp`，不强行一次性改 formal `Signal` schema。
- `strength` 继续保留为兼容字段；排序解释依赖 sidecar 字段。

## 目录结构

```text
src/
├── data/           # fetcher.py, cleaner.py, builder.py, store.py
├── selector/       # selector.py（基础过滤与规模控制）、mss.py、irs.py
├── strategy/       # pas_bof.py, registry.py, strategy.py, ranker.py
├── broker/         # broker.py, risk.py, matcher.py
├── backtest/       # engine.py
├── report/         # reporter.py
├── contracts.py    # pydantic 模块边界契约
└── config.py       # 全局配置
```

## CLI 入口

```text
python main.py fetch
python main.py build --layers=l2,l3
python main.py build --layers=all --force
python main.py backtest --start=2023-01-01
python main.py backtest --patterns=bof
python main.py run
```
