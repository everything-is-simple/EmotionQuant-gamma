# EmotionQuant 重构设计文档

**版本**: v0.01
**创建日期**: 2026-03-01
**状态**: 待审批

---

## 内容概览

本文档是 EmotionQuant 系统重构的第一份正式设计文件。原系统存在严重的架构膨胀问题（128 Governance 文件、70+ 设计文档、三套回测引擎、四层数据架构、Integration"三三制"集成层），全部推翻，重建最小可用系统。

本文档定义：6 个模块的边界与职责、MSS/IRS/PAS 三套因子的精简方案、模块间数据契约、开源依赖栈、4 周落地计划。

---

## 1. 铁律（全体成员必须遵守）

1. **选股 = MSS + IRS**，交易时机 = PAS，风控执行独立。三者不混。
2. **MSS 只看市场级**，不碰行业和个股。
3. **IRS 只看行业级**，不碰市场温度和个股形态。
4. **PAS 只看个股形态**，不把 MSS/IRS 分数当输入，只看价格和量。
5. **同一原始观测只归属一个因子**，禁止跨因子重复计分。（由架构数据流保证，不设注册表）
6. **模块间只传"结果契约"**（pydantic 对象），不传内部中间特征。
7. **pydantic 只校验模块边界对象**，不逐行校验 DataFrame。
8. **每个模块可独立单测**，不依赖其他模块启动。
9. **Backtest 和纸上交易共用同一个 broker 内核**，保证回测/实盘语义一致。
10. **执行语义固定为 T+1 Open**：signal_date=T（T日收盘后生成信号），execute_date=T+1，成交价=T+1 开盘价。禁止 T 日收盘价成交（未来函数）。

### 技术约束

- **Python** ≥3.10
- **行业分类**：申万一级（31 个），TuShare 原生支持
- **交易时段**：9:30-11:30, 13:00-15:00（沪深交易所）
- **最小交易单位**：100 股（1 手）
- **数据根目录**：`DATA_PATH` 环境变量注入（仓库外独立目录），config.py 读取

---

## 2. 系统架构（6 模块，通过 L1-L4 解耦）

模块之间不直接调用，通过 DuckDB 表（L1-L4）交互。逻辑上有依赖关系，物理上各自独立。

```text
fetcher  ──写→  L1 表  （批量下载/断点续传/多线程）
cleaner  ──读 L1 → 写→  L2 表  （向量化计算，不逐行循环）
builder  ──统一调度 L2/L3/L4 生成（增量/全量/指定日期）
mss.py   ──读 L2 → 写→  L3 表│
irs.py   ──读 L2 → 写→  L3 表│  可并行
pas.py   ──读 L2 → 写→  L3 表│
gene.py  ──读 L2 → 写→  L3 表│
selector ──读 L3 → 写→  候选池
strategy ──读 L3 + 候选池 → 写→  最终信号
broker   ──读 信号 → 写→  L4 表
report   ──读 L3 + L4 → 写→  L4 报告
backtest ──读 L1-L3 历史 → 调用 broker 内核 → 写 L4
```

**三种关系并存**：
1. **逻辑依赖**：串行的 — selector 需要 data 的产出才能算
2. **物理解耦**：通过 DuckDB 表（L1→L2→L3→L4），每个模块独立读写，不直接调用彼此
3. **故障隔离**：任一模块挂了，已持久化的数据不受影响，修复后从断点重跑

| 场景 | 纯串行后果 | 有 L1-L4 后果 |
|------|-----------|---------------|
| fetcher 挂了 | 全链路停 | L2/L3 历史数据仍在，其他模块用历史数据照常跑 |
| MSS 算错了 | strategy 拿到错误输入 | 修复后重跑 mss.py，只覆盖 l3_mss_daily 当天行，下游重跑即可 |
| broker 挂了 | 没有成交记录 | L3 信号已持久化，修复后 broker 重跑，幂等键保证不重复 |

### 2.1 模块解耦原则：独立计算 + 可配置编排

6 个模块通过 L1-L4 数据层解耦。每个模块独立读表、独立计算、独立写表，互不直接调用。

```text
独立计算层（各自读表 → 算 → 写表，互不调用）：
  MSS:   读 l2_market_snapshot  → 算市场温度  → 写 l3_mss_daily
  IRS:   读 l2_industry_daily   → 算行业评分  → 写 l3_irs_daily   （可与 MSS 并行）
  PAS:   读 l2_stock_adj_daily  → 检测形态    → 写 l3_signals     （读 L2 复权日线，不重算均线/量比）
  GENE:  读 l2_stock_adj_daily(250日) → 算基因画像  → 写 l3_stock_gene  （可与上述并行）

编排层（只在 selector.py / strategy.py 里，漏斗逻辑可配置）：
  selector.py:  读 l3_mss_daily（开关）+ 读 l3_irs_daily（漏斗）+ 读 l3_stock_gene（质量过滤）→ 输出候选池
  strategy.py:  读 候选池 + 读 l3_signals  → 输出最终信号
```

**“改一处”的影响范围**：
- 改 MSS 公式 → 只改 `mss.py`，IRS/PAS/selector 代码不动（下游读到的分数会变，但那是数据依赖，不是代码耦合）
- 改漏斗逻辑（比如 BEARISH 改为减仓而不是全停）→ 只改 `selector.py`，MSS/IRS/PAS 代码全不动
- 改 PAS 形态 → 只改 `pas_breakout.py`，MSS/IRS 完全无感
- fetcher 今天挂了 → L1 没有新数据，但 L2/L3 历史数据仍在，其他模块可用历史数据继续跑

**编排层的漏斗逻辑**（selector.py 内部）：

```text
全市场 ~5000 股
    │
    ▼ MSS 开关（读 l3_mss_daily）── ENABLE_MSS_GATE=true 时生效，关闭则跳过
    │ BULLISH → 放行 ┃ BEARISH → 当日不出手
    │
    ▼ IRS 漏斗（读 l3_irs_daily）── ENABLE_IRS_FILTER=true 时生效，关闭则全行业放行
    │ 筛选 Top-N 强势行业
    │
    ▼ 基因库过滤（读 l3_stock_gene）── ENABLE_GENE_FILTER=true 时生效（第 2 迭代）
    │ gene_score > 阈值 → 放行 ┃ 衰股基因过重 → 排除
    │
    ▼ 基础过滤（流动性 / 市值）
    │
候选池 ~50-100 股
    │
    ▼ PAS 触发（读 l3_signals）
    │
交易信号 ~0-10 只 → Broker（信任检查 → 真单 / 模拟单 / 跳过）
```

**漏斗每步可独立开关**，config.py 控制。关掉任意一步即可做对照实验：
- 只跑 PAS（全关）→ 纯形态交易，不管大盘和行业
- MSS + PAS（关 IRS）→ 管大盘时机，不限行业
- IRS + PAS（关 MSS）→ 管行业轮动，不管大盘情绪
- 全开（默认）→ 最严格漏斗

- **MSS 回答**：今天该不该做？（时机维度）
- **IRS 回答**：做哪些行业？（空间维度）
- **PAS 回答**：这只股票现在买不买？（触发维度）

### 2.2 代码设计：OOP 与纯函数的分工

原则：有多态或有状态的用 OOP，纯计算的用函数。不强制全 OOP，也不强制全函数式。

**用 OOP（有多态 / 有状态）**：

| 模块 | 类 | 用 OOP 的原因 |
|------|-----|---------------|
| fetcher.py | `DataFetcher`(ABC) → `TuShareFetcher` / `AKShareFetcher` | 多态：主备切换，调用方不感知 |
| store.py | `Store` | 有状态：持有 DuckDB 连接，提供 L1-L4 类型化读写 |
| pas_breakout.py | `PatternDetector`(ABC) → `BreakoutDetector` | 多态：后续加 `PullbackDetector` 时统一接口 |
| broker/ | `Broker`（组合 `RiskManager` + `Matcher`） | 有状态：持有持仓/资金；回测和纸上交易共用同一实例 |

```python
# DataFetcher 多态示例
class DataFetcher(ABC):
    @abstractmethod
    def fetch_stock_daily(self, codes, start, end) -> pd.DataFrame: ...

class TuShareFetcher(DataFetcher): ...   # 主
class AKShareFetcher(DataFetcher): ...   # 备
# fetcher.py: 主挂了自动降级到备，调用方不感知

# PatternDetector 多态 + 注册表
class PatternDetector(ABC):
    name: str                    # 形态唯一标识，如 "breakout"
    @abstractmethod
    def detect(self, df: pd.DataFrame) -> Optional[Signal]: ...

class BreakoutDetector(PatternDetector):
    name = "breakout"            # MVP
class PullbackDetector(PatternDetector):
    name = "pullback"            # 第 2 迭代

# registry.py: 配置驱动，随时装配
ACTIVE_PATTERNS = ["breakout"]   # 由 config.py 控制，新增形态只改这一行
COMBINATION_MODE = "ANY"         # ANY / ALL / VOTE（§4.3 详述）
# strategy.py: 只遍历 ACTIVE_PATTERNS 中注册的 detector

# Broker 有状态示例
class Broker:
    def __init__(self, risk: RiskManager, matcher: Matcher):
        self.portfolio: dict     # 当前持仓
        self.cash: float         # 可用资金
    def process_signal(self, signal: Signal) -> Optional[Trade]: ...
```

**用纯函数（无状态、无多态）**：

| 模块 | 用纯函数的原因 |
|------|---------------|
| mss.py | 输入 DataFrame → 输出 MarketScore，无状态、无变体 |
| irs.py | 同上 |
| gene.py | 输入 250 日 DataFrame → 输出基因评分，无状态 |
| selector.py | 读 L3 表 + 过滤逻辑，纯编排 |
| reporter.py | 数据聚合输出，无状态 |

---

## 3. 目录结构

```text
EmotionQuant-gamma/
├── docs/
│   ├── design-v2/           # 新版设计文档（本文档）
│   └── archive/             # 旧版设计归档
├── src/
│   ├── data/                # 模块1: Data
│   │   ├── fetcher.py       # L1 下载工具（批量/断点续传/多线程）
│   │   ├── builder.py       # L2/L3/L4 增量生成工具
│   │   ├── cleaner.py       # L1→L2 清洗加工逻辑
│   │   └── store.py         # DuckDB 存取（单写者/批量/WAL）
│   ├── selector/            # 模块2: Selector
│   │   ├── mss.py           # MSS 市场情绪因子
│   │   ├── irs.py           # IRS 行业轮动因子
│   │   ├── gene.py          # 牛股基因/衰股基因画像
│   │   └── selector.py      # 合并逻辑 → 输出候选池
│   ├── strategy/            # 模块3: Strategy
│   │   ├── pattern_base.py  # PatternDetector ABC
│   │   ├── pas_breakout.py  # PAS 突破形态：突破
│   │   ├── pas_pullback.py  # PAS 突破形态：回踩（第 2 迭代）
│   │   ├── registry.py      # 形态注册表 + 组合配置
│   │   └── strategy.py      # 信号汇总（只读注册表，遍历活跃形态）
│   ├── broker/              # 模块4: Broker（风控+撮合）
│   │   ├── risk.py          # 仓位管理、止损、T+1
│   │   └── matcher.py       # 撮合引擎（回测/纸上交易共用）
│   ├── backtest/            # 模块5: Backtest
│   │   └── engine.py        # backtrader 封装（调用 broker 内核）
│   ├── report/              # 模块6: Report
│   │   └── reporter.py      # 回测报告 + 每日选股报告
│   ├── contracts.py         # pydantic 模块边界契约
│   └── config.py            # 全局配置
├── tests/
├── pyproject.toml
└── main.py                  # 入口
```

---

## 4. 模块边界定义

### 4.1 Data

**职责**：拉数据、清洗、落库、缓存算法输出。零业务逻辑（不做策略判断，只做数据读写）。
**输入**：股票代码列表 + 日期范围
**技术**：TuShare 为主（稳定、接口规范），AKShare 兜底（免费但爬取式接口不稳定），DuckDB 单库存储

#### 数据分层（L1-L4）

保留 L1-L4 概念分层，但不建旧版的门禁/校验/版本管理基础设施。实现上就是 DuckDB 里的表分组，store.py 统一读写。

**L1 — 原始数据**（API 直取，fetcher.py 写入）

| 表名 | 用途 | 字段 | API 来源 |
|------|------|------|----------|
| `l1_stock_daily` | 个股日线（未复权） | ts_code, date, open, high, low, close, volume, amount, pre_close, adj_factor, is_halt, up_limit, down_limit, total_mv, circ_mv | TuShare `daily()` + `daily_basic()` 合并；OHLCV 来自 daily，市值来自 daily_basic |
| `l1_index_daily` | 大盘指数日线 | ts_code, date, open, high, low, close, volume, amount | TuShare `index_daily()` |
| `l1_stock_info` | 股票基础信息 + 行业映射 | ts_code, name, industry, list_date, effective_from | TuShare `stock_basic()` + 行业分类接口；低频更新 |
| `l1_trade_calendar` | 交易日历 | date, is_trade_day, prev_trade_day, next_trade_day | TuShare `trade_cal()` |

> `l1_stock_daily` 需要两次 API 调用（daily + daily_basic）合并为一张表。fetcher 分别拉取后按 (ts_code, date) 合并再写入。
> `total_mv`（总市值，万元）和 `circ_mv`（流通市值，万元）用于 selector 基础过滤（市值筛选）。
> `list_date` 用于排除次新股（上市不足 60 天的不入候选池）。

**股票代码格式约定**：
- **L1 层**：存储 TuShare 原始格式 `ts_code`（如 `000001.SZ`），保持与 API 一致，便于回查
- **L2+ 层**：cleaner.py 转换为纯代码 `code`（如 `000001`），系统内部统一使用
- 转换时机：L1→L2 清洗时一次性转换，不在其他地方做

**L2 — 加工数据**（API 直取不到、需简单加工、供下游多处调用，cleaner.py / builder.py 写入）

L2 的定位不是“聚合”，而是“算一次、存起来、到处用”。复权价、涨跌幅、均线、量比这些每个下游都要，不该每次重算。空间换时间。

| 表名 | 用途 | 字段 | 加工逻辑 |
|------|------|------|----------|
| `l2_stock_adj_daily` | 个股复权日线 + 常用派生指标 | code, date, adj_open, adj_high, adj_low, adj_close, volume, amount, pct_chg, ma5, ma10, ma20, ma60, volume_ma20, volume_ratio | 从 `l1_stock_daily` 的 adj_factor 算前复权价；pct_chg = (adj_close - prev_adj_close) / prev_adj_close；MA/量比用滚动窗口向量化计算 |
| `l2_industry_daily` | 行业日线（用于 IRS） | industry, date, pct_chg, amount, stock_count, rise_count, fall_count | 按 `l1_stock_industry_map` 从 `l1_stock_daily` 聚合；pct_chg = 成分股等权平均 |
|| `l2_market_snapshot` | 全市场截面统计（用于 MSS） | date, total_stocks, rise_count, fall_count, strong_up_count, strong_down_count, limit_up_count, limit_down_count, touched_limit_up_count, new_100d_high_count, new_100d_low_count, continuous_limit_up_2d, continuous_limit_up_3d_plus, continuous_new_high_2d_plus, high_open_low_close_count, low_open_high_close_count, pct_chg_std, amount_volatility | 从 `l1_stock_daily` 按日聚合；各字段计算逻辑见 MSS 六因子公式（§4.2） |

> `strong_up_count` / `strong_down_count` 必须按板块涨跌停幅度分别计算：主板阈值 ±5%（= 0.50×10%），创业板/科创板 ±10%（= 0.50×20%），ST ±2.5%（= 0.50×5%）。不允许全市场统一用固定 ±5%。

> `l2_stock_adj_daily` 是下游的基础表：PAS 读它算形态，gene.py 读它算基因，backtest 读它做回测。不再各自从 L1 重算复权和均线。

**L3 — 算法输出**（核心算法写入，空间换时间）

| 表名 | 用途 | 写入者 | 字段 |
|------|------|---------|------|
| `l3_mss_daily` | MSS 每日评分历史 | mss.py | date, score, signal, 各因子分数 |
| `l3_irs_daily` | IRS 每日行业评分历史 | irs.py | date, industry, score, rank, rs_score, cf_score |
| `l3_signals` | PAS 每日信号历史 | pas_breakout.py | signal_id, code, signal_date, action, strength, pattern |
| `l3_stock_gene` | 个股基因画像 | gene.py | code, calc_date, bull_score, bear_score, gene_score, limit_up_freq, streak_up_avg, new_high_freq, strength_ratio, resilience, limit_down_freq, streak_down_avg, new_low_freq, weakness_ratio, fragility |

> L3 持久化后，回测不需要每天重算 MSS/IRS/基因，直接读表。大硬盘空间换算法时间。

**L4 — 历史分析缓存**（系统运行产生，加速复盘/报告）

| 表名 | 用途 | 写入者 | 字段 |
|------|------|---------|------|
| `l4_orders` | 订单历史 | broker/risk.py | Order 全字段 |
| `l4_trades` | 成交历史（含模拟单） | broker/matcher.py | Trade 全字段（含 is_paper） |
| `l4_stock_trust` | 个股信任分级 | broker/risk.py | code, tier(ACTIVE/OBSERVE/BACKUP), consecutive_losses, last_demote_date, last_promote_date, updated_at |
| `l4_daily_report` | 每日运行报告 | report/reporter.py | date, candidates_count, signals_count, trades_count, win_rate, avg_win, avg_loss, profit_factor, expected_value, max_drawdown, max_consecutive_loss, skewness, rolling_ev_30d, sharpe_30d |
| `l4_pattern_stats` | 每形态表现统计 | report/reporter.py | date, pattern, trade_count, win_rate, avg_win, avg_loss, profit_factor, expected_value |

> IRS 字段闭合：industry_amount_delta = l2_industry_daily.amount - lag(amount, 1)，market_amount_total = Σ(l1_stock_daily.amount)。

**store.py 职责**：统一管理 L1-L4 全层级读写。建表、upsert、查询、幂等控制都在这一个文件里。

#### 下载工具（fetcher.py）

L1 数据获取是每天都要跑的工具，必须健壮。设计原则：少调 API、大块存储、断点续传。

**批量下载 + 指定时间跨度**：
- 支持 `fetch(data_type, start_date, end_date)` — 一次拉整段时间，不是一天一天调 API
- TuShare 多数接口支持日期范围查询，充分利用，减少调用次数
- 初始化拉 3 年历史时，按月分批，不一次拉全部（避免超时/限流）

**断点续传**：
- store.py 维护元数据表 `_meta_fetch_progress`：每个数据类型的最后成功日期
- `fetch_incremental()` 自动从上次成功位置继续，不重复拉已有数据
- 拉取失败不更新进度，下次自动重试该批次

**多线程并行（不同数据类型）**：
- stock_daily、index_daily、industry_map、trade_calendar 四种数据可并行拉取（不同 API 接口，不争抢配额）
- 同一接口内串行（TuShare 单 token 限流）
- 每次 API 调用间 sleep（尊重限流，默认 0.3s）

**批量写入 DuckDB**：
- 收集一批数据到 DataFrame，再一次性 bulk insert，不逐行写
- 典型流程：API 返回 DataFrame → 类型校验 → `store.bulk_upsert(table, df)`

#### DuckDB 使用规范

DuckDB 单进程单写者，必须正视锁问题：

- **单写者原则**：同一时刻只有一个进程/线程写入。fetcher 多线程拉数据时，各线程先拉到内存 DataFrame，统一由主线程顺序写入
- **批量写入**：禁止逐行 INSERT。统一使用 `INSERT INTO ... SELECT * FROM df`（DuckDB 原生支持从 DataFrame 批量插入）
- **WAL 模式**：启用 WAL（Write-Ahead Logging），避免写入失败导致数据损坏
- **连接管理**：store.py 持有唯一连接，其他模块通过 store 读写，不自己开连接

#### L2/L3/L4 生成工具（builder.py）

每天跑完 fetcher 后，要生成 L2/L3/L4。不是手动调函数，而是专门的生成工具：

```text
python main.py build --layers=l2         # 只生成 L2
python main.py build --layers=l2,l3      # 生成 L2 + L3
python main.py build --layers=all        # 全部重建
python main.py build --layers=l3 --start=2024-01-01 --end=2024-12-31  # 指定日期范围
```

**增量生成**：
- 每层检查目标表的 max(date)，只算新日期
- 支持强制全量重建（`--force`），用于公式修改后重算历史

**计算原则（L2/L3/L4 通用）**：
- **禁止逐行循环**：不用 `for row in df.iterrows()`，用 pandas 向量化操作或 DuckDB SQL 聚合
- **大块处理**：一次读一段日期的全市场数据，向量化算完，批量写入。不是一天一天、一只一只处理
- **优先用 DuckDB SQL**：聚合类计算（l2_market_snapshot、l2_industry_daily）直接用 SQL，比 pandas groupby 快
- **滚动窗口用 pandas**：均线、量比等滚动计算用 `df.rolling().mean()`，不写循环
- **写入一次性**：算完整块结果后 `store.bulk_upsert()`，不边算边写

### 4.2 Selector（选谁）

**职责**：从全市场筛选候选股票池。只回答"选谁"，不输出交易动作。
**输入**：全市场 OHLCV + 大盘指数 + 行业指数
**输出**：`List[StockCandidate]`（code, industry, score）

#### MSS — 市场情绪因子（6 因子，保留原设计公式）

MSS 判断"该不该入场"，是选股的前置开关。

**六因子体系**（三基础 85% + 三增强 15%）：

| 因子 | 组内权重 | 总权重 | 语义 |
|------|---------|--------|------|
| 大盘系数 | 20% | 17% | 参与度（上涨覆盖率） |
| 赚钱效应 | 40% | 34% | 上行扩张（涨停率/新高率/强势股率） |
| 亏钱效应 | 40% | 34% | 下行压力（炸板率/跌停率/弱势股率） |
| 连续性 | 33.3% | 5% | 持续性（连板/连续新高） |
| 极端因子 | 33.3% | 5% | 尾部活跃（高开低走+低开高走） |
| 波动因子 | 33.3% | 5% | 离散度（涨跌幅标准差/成交额波动率） |

**归一化函数（MSS/IRS/基因库 三系统共用）**：

```text
def zscore_normalize(value, mean, std) -> float:
    """Z-Score 归一化，映射到 0-100"""
    if std == 0: return 50.0                      # 零波动 → 中性分
    z = (value - mean) / std
    return clip((z + 3) / 6 × 100, 0, 100)        # [-3σ,+3σ] → [0,100]

# mean/std 来源：
#   MVP 阶段：首次部署用离线 baseline（2015-2025 历史样本）硬编码
#   后续迭代：每日收盘后按滚动窗口（默认 120 日）增量更新
#   缺失兜底：某因子缺 mean/std → 返回 50（中性分）
```

核心公式（已验证，直接复用）：

```text
# 大盘系数
market_coefficient_raw = rise_count / total_stocks
market_coefficient = zscore_normalize(market_coefficient_raw)

# 赚钱效应
# strong_up_ratio 必须按板块分别计算阈值（不能全市场统一用 ±5%）：
#   主板: pct_chg >= 0.50 × 10% = 5%
#   创业板/科创板: pct_chg >= 0.50 × 20% = 10%
#   ST: pct_chg >= 0.50 × 5% = 2.5%
# strong_down_ratio 对称处理
profit_effect_raw = 0.4×limit_up_ratio + 0.3×new_high_ratio + 0.3×strong_up_ratio
profit_effect = zscore_normalize(profit_effect_raw)

# 亏钱效应（越高=下行压力越大，温度中用 100-loss_effect）
loss_effect_raw = 0.3×broken_rate + 0.2×limit_down_ratio + 0.3×strong_down_ratio + 0.2×new_low_ratio
loss_effect = zscore_normalize(loss_effect_raw)

# 连续性
continuity_raw = 0.5×continuous_limit_up_ratio + 0.5×continuous_new_high_ratio
continuity = zscore_normalize(continuity_raw)

# 极端因子
extreme_raw = panic_tail_ratio + squeeze_tail_ratio
extreme = zscore_normalize(extreme_raw)

# 波动因子
# amount_volatility 原始量纲差异大，先归一再 zscore：
amount_volatility_ratio = amount_volatility / (amount_volatility + 1_000_000)
volatility_raw = 0.5×pct_chg_std + 0.5×amount_volatility_ratio
volatility = zscore_normalize(volatility_raw)

# 市场温度
# 语义说明：loss_effect 和 volatility 是负面指标（越高越差），
# 所以温度公式中取 (100 - x) 做方向翻转：
#   - 亏钱效应高 → 100-loss_effect 低 → 温度低（亏钱多=市场冷）
#   - 波动率高   → 100-volatility 低  → 温度低（高波动=高风险=降温）
temperature = 0.17×market_coefficient + 0.34×profit_effect
            + 0.34×(100 - loss_effect) + 0.05×continuity
            + 0.05×extreme + 0.05×(100 - volatility)
```

**输出**：`MarketScore`（date, score: 0-100, signal: BULLISH/NEUTRAL/BEARISH）
**硬边界**：只接收大盘指数数据，不碰行业、不碰个股。

#### IRS — 行业轮动因子（MVP 精简为 2 核心因子）

IRS 判断"选哪些行业"，缩小选股范围。

原设计 6 因子（相对强度 25%、连续性 20%、资金流向 20%、估值 15%、龙头 12%、基因库 8%）。MVP 阶段只保留 2 个信号最强的因子：

| 因子 | 权重 | 说明 |
|------|------|------|
| 相对强度 | 55% | 行业 vs 基准涨跌幅差 |
| 资金流向 | 45% | 行业成交额增量 + 资金占比 |

```text
# 相对强度
relative_strength = industry_pct_chg - benchmark_pct_chg
rs_score = zscore_normalize(relative_strength)

# 资金流向
net_inflow_10d = Σ(industry_amount_delta, window=10)
flow_share = industry_amount / market_amount_total
capital_flow_score = 0.6×zscore_normalize(net_inflow_10d) + 0.4×zscore_normalize(flow_share)

# 行业评分
industry_score = 0.55×rs_score + 0.45×capital_flow_score
```

> 字段来源：industry_amount_delta = industry_daily.amount - lag(amount, 1)；market_amount_total = Σ(stock_daily.amount)。

**输出**：`List[IndustryScore]`（date, industry, score, rank）
**硬边界**：只接收行业指数数据，不碰市场温度、不碰个股。
**后续迭代**：连续性、估值、龙头、基因库 4 个因子视 MVP 效果逐步加回。

#### 牛股基因/衰股基因库（gene.py，第 2 迭代）

给每只股票画一张**长期行为画像**。同一个突破形态，发生在“爱涨停的股”和“常年阴跌的股”上，含金量完全不同。基因库就是给候选池做**质量分层**。

**计算逻辑**：读 `l1_stock_daily` 近 250 个交易日（滚动窗口），每日更新，写入 `l3_stock_gene`。

**牛股基因**（越高 → 历史行为越强势）：

| 基因 | 计算 | 语义 |
|------|------|------|
| 涨停基因 limit_up_freq | 过去 250 日涨停次数 / 250 | 爱涨停 |
| 连涨基因 streak_up_avg | 过去 250 日所有连涨段的平均长度 | 一涨就连涨 |
| 创新高基因 new_high_freq | 过去 250 日创 60 日新高的频率 | 总能突破 |
| 强势基因 strength_ratio | 过去 250 日收盘 > MA20 的比例 | 长期站均线上方 |
| 弹性基因 resilience | 回调 >5% 后恢复前高的平均天数的倒数 | 跌了能快速修复 |

**衰股基因**（对称镜像）：

| 基因 | 计算 | 语义 |
|------|------|------|
| 跌停基因 limit_down_freq | 过去 250 日跌停次数 / 250 | 爱跌停 |
| 连跌基因 streak_down_avg | 连跌段平均长度 | 一跌就连跌 |
| 创新低基因 new_low_freq | 创 60 日新低的频率 | 总在破位 |
| 弱势基因 weakness_ratio | 收盘 < MA20 的比例 | 长期趴在均线下 |
| 脆弱基因 fragility | 反弹后再次跌破前低的频率 | 弹了又跌回去 |

**综合评分**：

```text
bull_score = Σ(bull_gene_i × weight_i)    # 0-100
bear_score = Σ(bear_gene_i × weight_i)    # 0-100
gene_score = bull_score - bear_score       # -100 ~ +100
```

**使用方式（MVP：硬过滤）**：selector.py 中，`gene_score > 阈值` 放行，衰股基因过重的直接排除。阈值默认 -30（宽松，只排除最差的）。后续迭代可改为软加权。

**与现有设计的兼容性**：
- 观测不与 PAS 重复：PAS 看短期形态（price_position/volume_ratio/breakout_strength），基因看长期频率统计（涨停频率/连涨均长/新高频率），计算粒度完全不同
- 不增加耦合：gene.py 只读 L1、只写 L3，selector.py 只多读一张表
- 不是独立系统：基因库不回答新问题，是候选股的质量评估，本质是 selector 漏斗的一级过滤器

> 标记为第 2 迭代。MVP 阶段先不实现，但表结构和漏斗位置先占好，开发时预留接口。

#### 合并逻辑（可配置漏斗）

每步均可通过 config 开关独立启停，默认全开：

1. MSS 判断市场环境 → 开关（BEARISH 时不出手）── `ENABLE_MSS_GATE`
2. IRS 筛选 Top-N 强势行业 → 缩小范围 ── `ENABLE_IRS_FILTER`
3. 基因库过滤 → 排除衰股基因过重的股（第 2 迭代）── `ENABLE_GENE_FILTER`
4. 基础条件过滤（流动性、市值）→ 输出候选池

### 4.3 Strategy（何时买卖）

**职责**：对候选池中每只股票判断买卖时机。只回答"何时买卖"，不回答"选谁"。
**输入**：单只股票 OHLCV DataFrame
**输出**：`Signal`（signal_id, code, signal_date, action: BUY/SELL/HOLD, strength: 0-1, pattern: str, reason_code）

#### PAS — 价格行为形态检测（从评分系统改为形态检测器）

旧设计是三因子加权评分（牛股基因 20% + 结构位置 50% + 行为确认 30%），过于复杂。
重构为独立形态检测器，每个形态一个函数，签名统一：

```python
def detect(df: pd.DataFrame) -> Optional[Signal]
```

**MVP 只实现 pas_breakout（突破形态）**：
- 核心逻辑：价格突破 N 日高点 + 放量确认
- 触发条件：price_position > 阈值 AND volume_ratio > 阈值 AND breakout_strength > 0

**PAS 原始观测归属表**（pas_breakout，3 个观测，全部为个股级）：

| 观测 | 公式 | 语义 | 底层字段 |
|------|------|------|----------|
| price_position | (close - low_Nd) / (high_Nd - low_Nd) | 个股 N 日价格位置 | stock_daily: close, high, low |
| volume_ratio | volume / volume_avg_20d | 个股相对放量 | stock_daily: volume |
| breakout_strength | (close - high_Nd_prev) / high_Nd_prev | 个股突破强度 | stock_daily: close, high |

> 后续新增形态（如 pas_pullback）必须在此表登记观测，确认不与已有观测重复计分。

**pas_pullback（回踩形态）留第 2 迭代。**

**硬边界**：只接收个股 OHLCV，不把 MSS/IRS 分数当输入。

#### PAS 可装配架构

形态检测器必须支持：**随时新增形态**、**单形态独立回测**、**形态自由组合**。

**1. 形态注册表（registry.py，配置驱动）**

config.py 中定义活跃形态列表和组合方式，strategy.py 只加载注册的形态：

```python
# config.py

# ── Selector 漏斗开关（每步可独立关闭，用于对照实验）
ENABLE_MSS_GATE = True                # 关闭 → 不管大盘情绪，全天候交易
ENABLE_IRS_FILTER = True              # 关闭 → 不限行业，全市场选股
ENABLE_GENE_FILTER = False            # 第 2 迭代才开启

# ── PAS 形态配置
PAS_PATTERNS = ["breakout"]           # 当前活跃形态，新增形态只改这一行
PAS_COMBINATION = "ANY"               # 组合模式（见下方）
```

**新增一个形态的完整流程**：
1. 写 `pas_xxx.py`，继承 `PatternDetector`，实现 `detect()` 方法
2. 在 PAS 观测归属表登记观测，确认不与已有观测重复计分
3. 在 `PAS_PATTERNS` 中加入 `"xxx"`
4. 单独跑 `backtest --patterns=xxx` 验证该形态的独立表现
5. 确认正期望后，加入组合

**2. 单形态独立回测**

每个形态可独立跑回测，不依赖其他形态：

```text
# 只跑 breakout 形态的回测
python main.py backtest --patterns=breakout --start=2023-01-01

# 只跑 pullback 形态的回测
python main.py backtest --patterns=pullback --start=2023-01-01

# 两个形态组合回测
python main.py backtest --patterns=breakout,pullback --combination=ANY
```

backtest engine 根据 `--patterns` 参数只加载指定形态的 detector，其余逻辑不变。每个形态的回测结果单独记录到 `l4_pattern_stats`，用于判断哪个形态贡献正期望、哪个该淘汰。

**3. 形态组合模式**

```text
ANY  — 任一形态触发 → 出信号（宽松，信号多）
ALL  — 全部形态同时触发 → 才出信号（严格，信号少但精度高）
VOTE — 每个形态投票（权重=strength），加权超过阈值 → 出信号
```

MVP 只有一个形态，默认 ANY。第 2 个形态加入时组合模式才生效。组合模式的选择直接影响左尾：ALL 模式信号更少但更严格，误触发少，左尾更薄。

### 4.4 Broker（风控 + 撮合）

**职责**：风控检查 + 订单撮合。回测和纸上交易共用此内核。
**输入**：`Signal` + 当前持仓 + 账户状态
**输出**：`Trade`（trade_id, order_id, code, execute_date, action, price, quantity, fee, is_paper）

#### 执行语义（MVP 统一口径）
- signal_date = T：信号在 T 日收盘后产生
- execute_date = next_trade_date(T)：统一在下一交易日执行（依赖 trade_calendar）
- price = T+1 Open：成交价使用执行日开盘价
- 禁止 T 日 Close 成交（未来函数）
- 若 execute_date 当日停牌或一字涨跌停导致不可成交，则订单 REJECTED（回测/纸上同语义）

**risk.py 规则**：

**左尾控制（止损体系，四级防线）**：
- **第零级：日内浮亏即走** — 买入当天（execute_date）收盘价 < 买入价 → 次日开盘强制卖出。入场当天就水下 = 时机判断错误，不等到 -5% 再走。这是最快的一刀
- **第一级：个股止损** — 持仓浮亏 ≥ -5% → 强制卖出（单笔损失封顶）。适用于买入当天收盘微涨但随后走弱的情况
- **第二级：组合回撤止损** — 组合净值从峰值回撤 ≥ 15% → 全部清仓，当日起 MSS 强制置为 BEARISH，冷却 N 个交易日（默认 5 日）
- **第三级：连续亏损熔断** — 连续 N 笔亏损（默认 5 笔）→ 暂停开新仓 M 个交易日（默认 3 日），防止策略失效期持续失血

> 优先级：日内浮亏 > 个股止损 > 移动止盈 > 组合回撤 > 连亏熔断。同一天触发多个规则时，按优先级最高的执行。

**右尾管理（移动止盈，不截断盈利）**：
- **移动止盈**：持仓期间追踪 `max_price = max(每日 high)`，当 `close < max_price × (1 - trailing_stop_pct)` → 触发卖出。`trailing_stop_pct` 默认 8%
- 不设固定止盈线 — 涨多少跟多少，回头了才走。右尾不截断
- 止损和移动止盈同时生效：先触发谁就执行谁

**基础约束**：
- 单只仓位上限（默认 10%）
- T+1 约束（当日买入次日才能卖出）
- 涨跌停不追
- 最大持仓数量（默认 10）

**matcher.py**：
- 执行语义：signal_date=T，execute_date=T+1，成交价=T+1 Open（铁律 #10）
- 成交可用性：若 is_halt=true，或买入时 open>=up_limit，或卖出时 open<=down_limit，则 REJECTED
- 手续费（A股标准费率，MVP 默认值）：
  - commission_rate = 0.0003（万三），min_commission = ¥5
  - stamp_duty_rate = 0.001（千一，仅卖出）
  - transfer_fee_rate = 0.00002（万0.2，买卖双边）
  - fee = max(amount × commission_rate, 5) + sell_amount × stamp_duty_rate + amount × transfer_fee_rate
- 滑点：可配置（slippage_bps），MVP 默认 0
- 实盘适配接口预留，后置实现

#### 个股信任分级（Stock Trust Tier）

broker 在执行信号前，检查目标股票的信任等级。**对反复亏损的股票自动降级**，防止“复仇交易”——系统（和人）天然会想“这次一定能抓住”，降级制度强制打断这个循环。

**三级信任状态**：

| 状态 | 含义 | 信号处理 |
|------|------|----------|
| ACTIVE（操作） | 正常交易 | 真金白银执行 |
| OBSERVE（观察） | 节奏失控 | 模拟执行（记录但不用真钱，is_paper=true） |
| BACKUP（备选） | 严重失控 | 冷藏（信号跳过，不生成模拟单）；30 天后自动回 OBSERVE |

**降级规则**：
- 同一只股票**最近连续 3 笔**买入均亏损 → ACTIVE 降为 OBSERVE。中间有一笔盈利则计数器归零
- OBSERVE 期间模拟验证通过后恢复到 ACTIVE，若真买再亏 → 降为 BACKUP
- 亏损判定标准（统一口径）：execute_date 收盘价 < 买入价 = 亏损（与第零级止损同一标准）

**升级规则**：
- BACKUP：冷藏 30 天后**自动**回到 OBSERVE（不直接回 ACTIVE）
- OBSERVE：至少 1 笔模拟单盈利 → 可升回 ACTIVE（试一单真钱）
- 升级后再亏 → 立即降回上一级

**数据流**：
- 新表 `l4_stock_trust`：持久化每只股票的信任状态
- broker 执行前读取信任等级：ACTIVE → 正常执行，OBSERVE → is_paper=true，BACKUP → 跳过
- 模拟单与真单同表（`l4_trades`），用 `is_paper` 字段区分
- 新股首次出现信号默认为 ACTIVE（无历史记录 = 无前科）

```text
信任状态转换图：

  ACTIVE ──3连亏──→ OBSERVE ──真买又亏──→ BACKUP
    ↑                  ↑                    │
    │ 模拟盈利1次       │ 冷藏30天自动        │
    └──────────────────┘←───────────────────┘
```

### 4.5 Backtest

**职责**：历史回测。
**技术**：backtrader 单引擎（删除旧版 Qlib + 向量化引擎）。
**关键设计**：将 Selector + Strategy 封装为 backtrader Strategy 类，撮合/风控调用 broker 内核。
**输入**：历史数据 + 初始资金 + 策略参数
**输出**：回测报告（收益率、最大回撤、夏普比率、交易明细）

### 4.6 Report

**职责**：生成报告 + 计算统计指标 + 预警检查。系统对数据做统计的核心：关注两个长尾（左尾损失尽可能小、右尾收益尽可能大），确保正期望值且稳定。

#### 核心统计指标体系

reporter.py 每日/每次回测后计算以下指标，写入 `l4_daily_report`：

**期望值指标**（E(V) 是否为正）：

```text
win_rate        = 盈利笔数 / 总笔数
avg_win         = 盈利交易的平均收益率
avg_loss        = 亏损交易的平均亏损率（正数）
profit_factor   = avg_win / avg_loss                     （盈亏比）
expected_value  = win_rate × avg_win - (1-win_rate) × avg_loss  （单笔期望）
```

**左尾指标**（损失有多坏）：

```text
max_single_loss        单笔最大亏损
max_drawdown           最大回撤（净值峰谷）
max_consecutive_loss   最大连续亏损笔数
loss_p5                亏损分布第 5 百分位（最差 5% 的交易亏多少）
```

**右尾指标**（收益有多好）：

```text
max_single_win          单笔最大盈利
avg_holding_days_win    盈利交易平均持仓天数（右尾有没有拿住）
win_p95                 盈利分布第 95 百分位
```

**分布形态**：

```text
skewness    收益分布偏度（>0 右尾叠，好事；<0 左尾叠，危险）
kurtosis    峰度（>3 尾部更厚，极端事件更多）
```

**稳定性指标**（E(V) 是否持续为正）：

```text
rolling_ev_30d   滚动 30 交易日期望值（趋势：E(V) 在变好还是变差）
sharpe           年化夏普比率
calmar           卡玛比率 = 年化收益 / 最大回撤
```

#### 逐形态统计（l4_pattern_stats）

每个 PAS 形态的表现单独追踪：胜率、盈亏比、期望值。用于判断哪个形态贡献正期望、哪个该淘汰。

#### 预警规则（最小实现）

不搞监控平台，reporter.py 每日跑完后检查，命中则 loguru.warning 写日志：

```text
rolling_ev_30d < 0         → "⚠ 30日滚动期望值为负，策略可能失效"
max_consecutive_loss >= 5  → "⚠ 连续亏损 5 笔，建议检查"
max_drawdown > 0.15        → "⚠ 回撤超过 15%"
profit_factor < 1.0        → "⚠ 盈亏比 < 1，期望值为负"
skewness < -0.5            → "⚠ 收益分布左偏，左尾过厚"
```

> 纸上交易阶段为日志预警；后续可升级为自动降级（如回撤 >20% 自动强制 BEARISH）。

#### 报告类型

- **每日选股报告**：候选池 + 信号列表 + 当日统计摘要
- **回测报告**：全量统计指标 + 收益曲线 + 交易明细 + 逐形态统计

### 4.7 跨系统因子/观测汇总

| 系统 | 因子/检测器数 | 原始观测数 | 数据粒度 | 回答的问题 |
|------|-------------|-----------|---------|------------|
| MSS | 6 因子 | 16 (+1 共用分母 total_stocks) | 全市场截面统计 | 今天该不该做？ |
| IRS | 2 因子 | 4 | 行业级聚合 | 做哪些行业？ |
| PAS | 1 检测器 (MVP) | 3 | 个股级 | 这只股票现在买不买？ |
| **合计** | **8 + 1** | **23 + 1 共用分母** | — | — |

**跨系统唯一性保证**：MSS 的 16 个观测全部是全市场聚合统计量，IRS 的 4 个观测全部是行业聚合量，PAS 的 3 个观测全部是单只个股特征。三者读同一张 `stock_daily` 表，但计算粒度完全不同，不存在同一个计算观测被两个系统重复计分。

**MSS 内部跨因子分母复用**（不算重复计分）：
- `limit_up_count` 归属赚钱效应，但在连续性中作 `continuous_limit_up_ratio` 的分母
- `new_100d_high_count` 归属赚钱效应，但在连续性中作 `continuous_new_high_ratio` 的分母

---

## 5. 数据契约（contracts.py）

模块间传递的数据结构，pydantic 定义。只校验模块边界对象，不校验 DataFrame 内部。

```python
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from uuid import uuid4

class MarketScore(BaseModel):       # MSS → Selector
    date: date
    score: float                    # 0-100
    signal: str                     # BULLISH / NEUTRAL / BEARISH

class IndustryScore(BaseModel):     # IRS → Selector
    date: date
    industry: str
    score: float
    rank: int

class StockCandidate(BaseModel):    # Selector → Strategy
    code: str
    industry: str
    score: float

class Signal(BaseModel):            # Strategy → Broker
    signal_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    code: str
    signal_date: date               # T：信号产生日
    action: str                     # BUY / SELL / HOLD
    strength: float                 # 0-1
    pattern: str                    # 触发的形态名
    reason_code: str                # 例如：PAS_BREAKOUT
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Order(BaseModel):             # Broker 内部（risk → matcher）
    order_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    signal_id: str                  # 关联 Signal.signal_id
    code: str
    action: str
    quantity: int
    price_limit: Optional[float] = None
    execute_date: date              # T+1：预期执行日（下一交易日）
    status: str = "PENDING"         # PENDING / FILLED / REJECTED
    reject_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Trade(BaseModel):             # Broker → Report
    trade_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    order_id: str                   # 关联 Order.order_id
    code: str
    execute_date: date              # 实际成交日
    action: str
    price: float                    # 实际成交价（T+1 Open）
    quantity: int
    fee: float
    slippage_bps: float = 0.0       # MVP 默认 0（预留扩展）
    is_paper: bool = False          # 模拟单标记（信任等级=OBSERVE 时为 True）
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

> 审计链

---

## 6. 开源依赖

| 库 | 用途 | 替代说明 |
|----|------|----------|
| tushare | 数据获取（主） | 稳定接口，简化旧版双通道为单通道 |
| akshare | 数据获取（备） | TuShare 不可用时自动降级 |
| duckdb | 本地存储 | 替代旧版 L1-L4 四层架构 |
| pyarrow | Parquet 读写 | — |
| backtrader | 回测引擎 | 替代旧版三引擎方案 |
| pandas | 数据处理 | — |
| pydantic | 模块边界契约 | — |
| loguru | 日志 | — |
| tenacity | 网络重试 | fetcher 失败重试 3 次 |

---

## 7. 与旧版对比（删了什么）

| 旧版 | 处理 | 理由 |
|------|------|------|
| Integration 集成层（三三制、4 种模式、700+ 行设计） | 删除 | MSS→IRS→PAS 串行流水线足够，不需要 top_down/bottom_up/dual_verify/complementary |
| ValidationGate 状态机 + contract_version | 删除 | 过早的运维抽象 |
| Data Layer L1-L4 四层架构 + 门禁 | 替换为 DuckDB 单库 | 偏"平台工程"，MVP 不需要 |
| TuShare 双通道（10000 网关 + 5000 官方） | 简化为 TuShare 单通道 + AKShare 兜底 | 双通道过重，单通道够用；AKShare 作为降级备份 |
| 三套回测引擎（Qlib + 向量化 + backtrader） | 只留 backtrader | 三套都没实现，只留一套做到底 |
| 128 个 Governance 文件 | 归档 | 不再维护 |
| IRS 6 因子 | MVP 精简为 2 因子 | 相对强度 + 资金流向信号最强，其余 4 个后续迭代加回 |
| PAS 三因子加权评分 | 改为形态检测器 | 评分系统过重，检测器更直观、可扩展 |
| GUI（Streamlit） | 延后 | MVP 阶段命令行足够 |
|| 监控告警 + 调度编排 | 删除（保留最小运行保障） | 不需要平台级能力，但保留基础重试、日志与幂等 |

---

## 8. 最小运行保障

不建监控平台，但要支撑每日自动跑一遍，必须保留以下最小保障：

- **run_id**：每次运行生成唯一 ID（`{trade_date}_{uuid[:8]}`），所有日志/输出都带 run_id
- **幂等键**：`trade_date + module`；同一天同一模块重跑不产生重复写入（DuckDB upsert）
- **失败重试**：fetcher 网络请求失败自动重试 3 次（tenacity）
- **失败快照**：模块抛异常时，loguru 写入 `logs/{run_id}.log`，包含 traceback + 输入参数
- **运行摘要**：每次 run 结束写 `runs/{run_id}.json`（开始/结束时间、各模块状态、错误摘要）

---

## 9. 四周落地计划

**开发方法论：增量迭代，非瀑布**

四周计划是增量交付，不是瀑布式。每周产出可独立验证的交付物（可跑的代码 + 通过的测试），而非先写完所有设计再统一编码。每周验收后才推进下一周，发现问题立即修正，不积压到最后集成。OOP/纯函数的分工（§2.2）也服务于此：模块可独立开发、独立测试、独立交付。

### 第 1 周：Data + 基础框架
- 搭建项目结构（src/ 目录、pyproject.toml 更新）
- 实现 fetcher.py（TuShare 主 + AKShare 备，拉取日K、大盘指数、行业数据）
- 实现 store.py（DuckDB 建表、标准 OHLCV 存取）
- 实现 contracts.py（全部模块边界契约）
- 实现 config.py（全局配置）
- **验收**：能拉取并存储近 3 年历史数据，contracts 类型校验通过

### 第 2 周：Selector + Strategy
- 实现 mss.py（6 因子市场温度评分）
- 实现 irs.py（2 因子行业轮动评分）
- 实现 selector.py（MSS 开关 + IRS 筛选 + 基础条件过滤）
- 实现 pas_breakout.py（突破形态检测）
- 实现 strategy.py（信号汇总）
- **验收**：能对全市场运行一次选股 + 信号生成，每个模块可独立单测

### 第 3 周：Broker + Backtest
- 实现 risk.py（四级止损、个股信任分级、仓位上限、T+1、涨跌停）
- 实现 matcher.py（模拟撮合、手续费计算、模拟单支持）
- 将 Selector + Strategy 封装为 backtrader Strategy 类
- 跑通第一次完整回测（单策略 pas_breakout）
- **验收**：回测报告能跑出来，收益/回撤/夏普数据合理

### 第 4 周：Report + 纸上交易 + 联调
- 实现 reporter.py（回测汇总 + 每日选股报告）
- 实现纸上交易模式（broker 内核的 paper 模式）
- 全链路联调：data → selector → strategy → broker → report
- **验收**：每日能自动跑一遍完整流程
