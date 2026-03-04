# Data Layer 详细设计

**版本**: v0.01 正式版
**创建日期**: 2026-03-01
**状态**: Frozen（与 `system-baseline.md` 对齐）
**封版日期**: 2026-03-03
**变更规则**: 仅允许勘误与说明性修订；执行语义变更需进入 v0.02+。
**对应模块**: `src/data/`（fetcher.py, cleaner.py, builder.py, store.py）
**上游文档**: `architecture-master.md` §4.1
**运维记录**: `docs/spec/v0.01/data-rebuild-runbook-20260303.md`（L1 保留、L2/L3/L4 清理与重建链路）

---

## 1. 设计目标

Data 模块是整个系统的地基：拉数据、清洗、派生指标、持久化。**零业务逻辑**——不做任何策略判断，只保证下游拿到干净、完整、类型正确的数据。

核心约束：
- 单写者（DuckDB 限制）：所有写入经过 store.py，同一时刻只有一个线程写
- 批量操作：禁止逐行 INSERT / iterrows()
- 幂等：同一天同一表重跑不产生重复数据（upsert）
- 断点续传：fetcher 中断后从上次成功位置继续

### 1.1 v0.01 数据运行口径（低频扫描）

1. 本地缓存优先：历史数据一次入库，日常仅做增量更新，禁止每日全量重拉。
2. API 限流优先：按数据类型分批拉取，失败重试后写入 `_meta_fetch_progress`，下次从断点续传。
3. 扫描服务于选股缩池：Data 层需稳定输出 Selector 粗筛必需字段（流动性、停牌、上市天数、波动）。
4. 目标不是全市场高频扫描，而是支持“5000 -> 约200”的低频两阶段扫描。

---

## 2. DuckDB Schema（完整 DDL）

### 2.1 L1 — 原始数据

```sql
-- 个股日线（未复权），fetcher.py 写入
CREATE TABLE IF NOT EXISTS l1_stock_daily (
    ts_code      VARCHAR NOT NULL,   -- TuShare 原始格式 000001.SZ
    date         DATE    NOT NULL,
    open         DOUBLE,
    high         DOUBLE,
    low          DOUBLE,
    close        DOUBLE,
    pre_close    DOUBLE,
    volume       DOUBLE,             -- 成交量（手）
    amount       DOUBLE,             -- 成交额（千元）
    pct_chg      DOUBLE,             -- 涨跌幅（%），TuShare daily() 原生返回
    adj_factor   DOUBLE,             -- 复权因子
    is_halt      BOOLEAN DEFAULT FALSE,
    up_limit     DOUBLE,             -- 涨停价
    down_limit   DOUBLE,             -- 跌停价
    total_mv     DOUBLE,             -- 总市值（万元），来自 daily_basic
    circ_mv      DOUBLE,             -- 流通市值（万元），来自 daily_basic
    PRIMARY KEY (ts_code, date)
);

-- 大盘指数日线
CREATE TABLE IF NOT EXISTS l1_index_daily (
    ts_code      VARCHAR NOT NULL,   -- 如 000001.SH（上证综指）
    date         DATE    NOT NULL,
    open         DOUBLE,
    high         DOUBLE,
    low          DOUBLE,
    close        DOUBLE,
    pre_close    DOUBLE,
    pct_chg      DOUBLE,             -- 涨跌幅（%）
    volume       DOUBLE,
    amount       DOUBLE,
    PRIMARY KEY (ts_code, date)
);

-- 股票基础信息 + 行业映射
CREATE TABLE IF NOT EXISTS l1_stock_info (
    ts_code        VARCHAR NOT NULL,
    name           VARCHAR,
    industry       VARCHAR,           -- 申万一级行业
    market         VARCHAR,           -- 主板/创业板/科创板/北交所
    is_st          BOOLEAN DEFAULT FALSE,
    list_date      DATE,              -- 上市日期
    effective_from DATE    NOT NULL,   -- 信息生效日期（行业变更时新增行）
    PRIMARY KEY (ts_code, effective_from)
);

-- 交易日历
CREATE TABLE IF NOT EXISTS l1_trade_calendar (
    date            DATE    NOT NULL PRIMARY KEY,
    is_trade_day    BOOLEAN NOT NULL,
    prev_trade_day  DATE,
    next_trade_day  DATE
);
```

### 2.2 L2 — 加工数据

```sql
-- 个股后复权日线 + 常用派生指标，cleaner.py 写入
-- 后复权：adj = raw × adj_factor，历史行一旦写入永不变化
CREATE TABLE IF NOT EXISTS l2_stock_adj_daily (
    code         VARCHAR NOT NULL,   -- 纯代码 000001（L2+ 统一格式）
    date         DATE    NOT NULL,
    adj_open     DOUBLE,
    adj_high     DOUBLE,
    adj_low      DOUBLE,
    adj_close    DOUBLE,
    volume       DOUBLE,
    amount       DOUBLE,
    pct_chg      DOUBLE,             -- (adj_close - prev_adj_close) / prev_adj_close
    ma5          DOUBLE,
    ma10         DOUBLE,
    ma20         DOUBLE,
    ma60         DOUBLE,
    volume_ma5   DOUBLE,
    volume_ma20  DOUBLE,
    volume_ratio DOUBLE,             -- volume / volume_ma20
    PRIMARY KEY (code, date)
);

-- 行业日线（申万一级，31 个行业），cleaner.py 写入
CREATE TABLE IF NOT EXISTS l2_industry_daily (
    industry     VARCHAR NOT NULL,   -- 申万一级行业名
    date         DATE    NOT NULL,
    pct_chg      DOUBLE,             -- 成分股等权平均涨跌幅
    amount       DOUBLE,             -- 行业成交额合计
    stock_count  INTEGER,            -- 成分股数量
    rise_count   INTEGER,            -- 上涨股数
    fall_count   INTEGER,            -- 下跌股数
    PRIMARY KEY (industry, date)
);

-- 全市场截面统计（MSS 输入），cleaner.py 写入
CREATE TABLE IF NOT EXISTS l2_market_snapshot (
    date                       DATE NOT NULL PRIMARY KEY,
    total_stocks               INTEGER,
    rise_count                 INTEGER,
    fall_count                 INTEGER,
    strong_up_count            INTEGER,   -- 按板块阈值：主板≥5%, 创业板/科创板≥10%, 北交所≥15%, ST≥2.5%
    strong_down_count          INTEGER,   -- 对称（主板≤-5%, 创业板/科创板≤-10%, 北交所≤-15%, ST≤-2.5%）
    limit_up_count             INTEGER,   -- 涨停
    limit_down_count           INTEGER,   -- 跌停
    touched_limit_up_count     INTEGER,   -- 曾触及涨停但收盘未封住
    new_100d_high_count        INTEGER,   -- 创100日新高
    new_100d_low_count         INTEGER,   -- 创100日新低
    continuous_limit_up_2d     INTEGER,   -- 连续2天涨停
    continuous_limit_up_3d_plus INTEGER,  -- 连续3天以上涨停
    continuous_new_high_2d_plus INTEGER,  -- 连续2天以上创新高
    high_open_low_close_count  INTEGER,   -- 高开低走（open在上1/3, close在下1/3）
    low_open_high_close_count  INTEGER,   -- 低开高走（对称）
    pct_chg_std                DOUBLE,    -- 当日全市场涨跌幅标准差
    amount_volatility          DOUBLE     -- 当日全市场成交额标准差
);
```

### 2.3 L3 — 算法输出

```sql
-- MSS 每日评分
CREATE TABLE IF NOT EXISTS l3_mss_daily (
    date                DATE NOT NULL PRIMARY KEY,
    score               DOUBLE,        -- 0-100 市场温度
    signal              VARCHAR,       -- BULLISH / NEUTRAL / BEARISH
    market_coefficient  DOUBLE,
    profit_effect       DOUBLE,
    loss_effect         DOUBLE,
    continuity          DOUBLE,
    extreme             DOUBLE,
    volatility          DOUBLE
);

-- IRS 每日行业评分
CREATE TABLE IF NOT EXISTS l3_irs_daily (
    date         DATE    NOT NULL,
    industry     VARCHAR NOT NULL,
    score        DOUBLE,
    rank         INTEGER,
    rs_score     DOUBLE,              -- 相对强度分
    cf_score     DOUBLE,              -- 资金流向分
    PRIMARY KEY (date, industry)
);

-- PAS 信号历史
CREATE TABLE IF NOT EXISTS l3_signals (
    signal_id    VARCHAR NOT NULL PRIMARY KEY,
    code         VARCHAR NOT NULL,
    signal_date  DATE    NOT NULL,
    action       VARCHAR NOT NULL,    -- v0.01 运行约束: BUY（SELL 由 broker 内部订单产生）
    strength     DOUBLE,              -- 0-1
    pattern      VARCHAR NOT NULL,    -- v0.01 运行约束: bof（其余保留给后续版本）
    reason_code  VARCHAR,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_signals_date_code ON l3_signals(signal_date, code);

-- 个股基因画像（第2迭代）
CREATE TABLE IF NOT EXISTS l3_stock_gene (
    code              VARCHAR NOT NULL,
    calc_date         DATE    NOT NULL,
    bull_score        DOUBLE,
    bear_score        DOUBLE,
    gene_score        DOUBLE,         -- bull - bear, -100 ~ +100
    limit_up_freq     DOUBLE,
    streak_up_avg     DOUBLE,
    new_high_freq     DOUBLE,
    strength_ratio    DOUBLE,
    resilience        DOUBLE,
    limit_down_freq   DOUBLE,
    streak_down_avg   DOUBLE,
    new_low_freq      DOUBLE,
    weakness_ratio    DOUBLE,
    fragility         DOUBLE,
    PRIMARY KEY (code, calc_date)
);
```

### 2.4 L4 — 历史分析缓存

```sql
-- 订单历史
CREATE TABLE IF NOT EXISTS l4_orders (
    order_id      VARCHAR NOT NULL PRIMARY KEY,
    signal_id     VARCHAR NOT NULL,
    code          VARCHAR NOT NULL,
    action        VARCHAR NOT NULL,
    pattern       VARCHAR NOT NULL,            -- 冗余：来自 Signal.pattern（归因链直连）
    quantity      INTEGER,
    price_limit   DOUBLE,
    execute_date  DATE    NOT NULL,
    is_paper      BOOLEAN DEFAULT FALSE,
    status        VARCHAR DEFAULT 'PENDING',  -- PENDING / FILLED / REJECTED
    reject_reason VARCHAR,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 成交历史
CREATE TABLE IF NOT EXISTS l4_trades (
    trade_id      VARCHAR NOT NULL PRIMARY KEY,
    order_id      VARCHAR NOT NULL,
    code          VARCHAR NOT NULL,
    execute_date  DATE    NOT NULL,
    action        VARCHAR NOT NULL,
    pattern       VARCHAR NOT NULL,            -- 冗余：来自 Order.pattern（_pair_trades 直接读取）
    price         DOUBLE,
    quantity      INTEGER,
    fee           DOUBLE,
    slippage_bps  DOUBLE  DEFAULT 0,
    is_paper      BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 个股信任分级
CREATE TABLE IF NOT EXISTS l4_stock_trust (
    code                VARCHAR NOT NULL PRIMARY KEY,
    tier                VARCHAR DEFAULT 'ACTIVE',  -- ACTIVE / OBSERVE / BACKUP
    consecutive_losses  INTEGER DEFAULT 0,
    on_probation        BOOLEAN DEFAULT FALSE,     -- OBSERVE→ACTIVE 升级后试用期（首笔亏损立即降 BACKUP）
    last_demote_date    DATE,
    last_promote_date   DATE,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 每日运行报告
CREATE TABLE IF NOT EXISTS l4_daily_report (
    date                   DATE NOT NULL PRIMARY KEY,
    candidates_count       INTEGER,
    signals_count          INTEGER,
    trades_count           INTEGER,
    win_rate               DOUBLE,
    avg_win                DOUBLE,
    avg_loss               DOUBLE,
    profit_factor          DOUBLE,
    expected_value         DOUBLE,
    max_drawdown           DOUBLE,
    max_consecutive_loss   INTEGER,
    skewness               DOUBLE,
    rolling_ev_30d         DOUBLE,
    sharpe_30d             DOUBLE
);

-- 每形态表现统计
CREATE TABLE IF NOT EXISTS l4_pattern_stats (
    date           DATE    NOT NULL,
    pattern        VARCHAR NOT NULL,
    trade_count    INTEGER,
    win_rate       DOUBLE,
    avg_win        DOUBLE,
    avg_loss       DOUBLE,
    profit_factor  DOUBLE,
    expected_value DOUBLE,
    PRIMARY KEY (date, pattern)
);
```

### 2.5 元数据表

```sql
-- 下载进度追踪（断点续传）
CREATE TABLE IF NOT EXISTS _meta_fetch_progress (
    data_type     VARCHAR NOT NULL PRIMARY KEY,  -- stock_daily / index_daily / stock_info / trade_cal
    last_success  DATE,                          -- 最后成功拉取的日期
    last_attempt  TIMESTAMP,
    status        VARCHAR DEFAULT 'OK',          -- OK / FAILED
    error_msg     VARCHAR
);

-- 运行记录
CREATE TABLE IF NOT EXISTS _meta_runs (
    run_id        VARCHAR NOT NULL PRIMARY KEY,  -- {trade_date}_{uuid[:8]}
    start_time    TIMESTAMP,
    end_time      TIMESTAMP,
    modules       VARCHAR,                       -- 逗号分隔的模块名
    status        VARCHAR,                       -- SUCCESS / PARTIAL / FAILED
    error_summary VARCHAR
);
```

---

## 3. store.py — 统一存取层

### 3.1 类设计

```python
class Store:
    """
    DuckDB 统一存取层。
    持有唯一连接，所有模块通过 Store 实例读写，不自行开连接。
    """
    def __init__(self, db_path: str):
        self.conn = duckdb.connect(db_path)
        self.conn.execute("PRAGMA enable_wal")
        self._init_tables()              # 执行上述全部 DDL

    # ── 写入 ──
    def bulk_upsert(self, table: str, df: pd.DataFrame) -> int:
        """
        批量 upsert。利用 DuckDB INSERT OR REPLACE 语义。
        返回写入行数。
        """

    def bulk_insert(self, table: str, df: pd.DataFrame) -> int:
        """
        批量 insert（仅用于明确 append-only 且无重跑覆盖需求的表）。
        对 l3_signals/l4_orders/l4_trades 等存在幂等重跑需求的表，必须使用 bulk_upsert。
        """

    # ── 读取 ──
    def read_df(self, sql: str, params: tuple = None) -> pd.DataFrame:
        """
        执行 SQL 查询，返回 DataFrame。
        所有模块的读取统一入口。
        """

    def read_scalar(self, sql: str, params: tuple = None):
        """
        执行 SQL 查询，返回单个标量值。
        查询结果为空时返回 None。
        用于仓位计算等只需读取单值的场景（如 SELECT adj_close ... WHERE code=? AND date=?）。
        """

    def read_table(self, table: str,
                   date_range: tuple[date, date] = None,
                   codes: list[str] = None) -> pd.DataFrame:
        """
        快捷读取整表或按 date/code 过滤。
        自动拼 WHERE 子句。
        """

    # ── 元数据 ──
    def get_fetch_progress(self, data_type: str) -> date | None:
        """返回该数据类型最后成功日期，无记录返回 None。"""

    def update_fetch_progress(self, data_type: str, last_date: date):
        """更新下载进度。"""

    def get_max_date(self, table: str, date_col: str = "date") -> date | None:
        """返回表中最大日期，用于增量生成判断。"""

    # ── 生命周期 ──
    def close(self):
        self.conn.close()
```

### 3.2 关键实现细节

**bulk_upsert 实现**：
```python
def bulk_upsert(self, table: str, df: pd.DataFrame) -> int:
    # 1. 将 df 注册为临时视图
    self.conn.register("_tmp_df", df)
    # 2. INSERT OR REPLACE（DuckDB 要求表有 PK）
    cols = ", ".join(df.columns)
    self.conn.execute(f"INSERT OR REPLACE INTO {table} SELECT {cols} FROM _tmp_df")
    self.conn.unregister("_tmp_df")
    return len(df)
```

**连接管理**：Store 实例在 `main.py` 入口创建，通过参数传递给各模块函数/类。不使用全局单例，便于测试时注入 `:memory:` 数据库。

---

## 4. fetcher.py — 数据下载工具

### 4.1 类设计

```python
class DataFetcher(ABC):
    """数据获取抽象基类，支持主备切换。"""

    @abstractmethod
    def fetch_stock_daily(self, start: date, end: date) -> pd.DataFrame:
        """拉取全市场个股日线（含 daily_basic 合并）。"""

    @abstractmethod
    def fetch_index_daily(self, codes: list[str], start: date, end: date) -> pd.DataFrame:
        """拉取指数日线。"""

    @abstractmethod
    def fetch_stock_info(self) -> pd.DataFrame:
        """拉取股票基础信息 + 行业映射。"""

    @abstractmethod
    def fetch_trade_calendar(self, start: date, end: date) -> pd.DataFrame:
        """拉取交易日历。"""


class TuShareFetcher(DataFetcher):
    """TuShare 主数据源。"""

    def __init__(self, token: str, sleep_interval: float = 0.3):
        self.pro = ts.pro_api(token)
        self.sleep = sleep_interval


class AKShareFetcher(DataFetcher):
    """AKShare 备用数据源。字段需映射到 TuShare 格式。"""
```

### 4.2 fetch_stock_daily 详细流程

```text
fetch_stock_daily(start, end):
    1. 按月分批（避免超时）：
       for month_start, month_end in split_by_month(start, end):
           df_daily  = pro.daily(trade_date=...) 或 pro.daily(start_date, end_date)
           df_basic  = pro.daily_basic(trade_date=...) 取 total_mv, circ_mv
           sleep(0.3)
    2. 按 (ts_code, trade_date) 合并 df_daily + df_basic
    3. 列名映射：trade_date → date
    4. 返回合并后 DataFrame
```

**两次 API 调用合并**：`l1_stock_daily` 需要 `daily()` 的 OHLCV 字段和 `daily_basic()` 的 total_mv/circ_mv。fetcher 内部按 `(ts_code, date)` 做 merge，对外暴露为一张完整表。

### 4.3 主备降级机制

```python
def create_fetcher(config) -> DataFetcher:
    """
    工厂函数：优先 TuShare，失败降级到 AKShare。
    """
    try:
        fetcher = TuShareFetcher(config.TUSHARE_TOKEN)
        fetcher.fetch_trade_calendar(today, today)  # 探活
        return fetcher
    except Exception:
        logger.warning("TuShare 不可用，降级到 AKShare")
        return AKShareFetcher()
```

降级粒度为**整次运行**，不在单次 API 调用级别切换（避免两个数据源混合导致口径不一致）。

### 4.4 断点续传流程

```text
fetch_incremental(data_type, store):
    1. last = store.get_fetch_progress(data_type)
    2. if last is None:
           start = config.HISTORY_START  # 默认 3 年前
       else:
           start = next_trade_day(last)
    3. end = today
    4. if start > end: return  # 已是最新
    5. df = fetcher.fetch_xxx(start, end)
    6. store.bulk_upsert(table, df)
    7. store.update_fetch_progress(data_type, end)
    # 步骤 5 失败不执行 7，下次从 last 重试
```

### 4.5 多线程并行策略

```text
四种数据类型并行拉取（不同 API 接口，不争抢配额）：

Thread-1: fetch_stock_daily()    → DataFrame → 队列
Thread-2: fetch_index_daily()    → DataFrame → 队列
Thread-3: fetch_stock_info()     → DataFrame → 队列
Thread-4: fetch_trade_calendar() → DataFrame → 队列

主线程：从队列中依次取出，顺序调用 store.bulk_upsert()（单写者）
```

使用 `concurrent.futures.ThreadPoolExecutor(max_workers=4)`，每个线程内部串行调用 API（TuShare 单 token 限流），线程间并行。

### 4.6 重试策略（tenacity）

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def _call_api(self, func, **kwargs) -> pd.DataFrame:
    return func(**kwargs)
```

---

## 5. cleaner.py — L1→L2 清洗加工

### 5.1 职责边界

cleaner 读 L1 表，计算派生指标，写 L2 表。**三张 L2 表各有独立的清洗函数**：

```python
def clean_stock_adj_daily(store: Store, start: date, end: date):
    """L1 → l2_stock_adj_daily：后复权 + 均线 + 量比"""

def clean_industry_daily(store: Store, start: date, end: date):
    """L1 → l2_industry_daily：按行业聚合"""

def clean_market_snapshot(store: Store, start: date, end: date):
    """L1 → l2_market_snapshot：全市场截面统计"""
```

### 5.2 clean_stock_adj_daily 计算逻辑

```text
输入：l1_stock_daily (ts_code, date, open, high, low, close, volume, amount, adj_factor)

步骤：
  1. 代码转换：ts_code → code（去掉 .SZ/.SH 后缀）
  2. 后复权（历史行永不变化，增量安全）：
     adj_open  = open  × adj_factor
     adj_high  = high  × adj_factor
     adj_low   = low   × adj_factor
     adj_close = close × adj_factor
     说明：后复权绝对价格不等于盘面价（会偏大），但 pct_chg / 均线 / 形态触发
     全基于相对量，不影响任何策略判断。不需要 latest_adj_factor，无增量漂移风险。
  3. 涨跌幅：pct_chg = (adj_close - prev_adj_close) / prev_adj_close
             用 groupby(code).shift(1) 取前日
  4. 停牌日处理（防止 rolling 窗口被污染）：
     - 先剔除 is_halt=true 的行（或将停牌日 volume 设为 NaN）
     - 在剔除后的有效交易日序列上做 rolling
     - 算完后 merge 回完整日期序列
     口径依据：system-baseline.md §4「SMA20(Volume) 使用过去 20 个有效交易日（停牌日不计入窗口）」
  5. 均线（向量化 rolling，仅在有效交易日上计算）：
     ma5  = groupby(code)['adj_close'].rolling(5).mean()
     ma10 = groupby(code)['adj_close'].rolling(10).mean()
     ma20 = groupby(code)['adj_close'].rolling(20).mean()
     ma60 = groupby(code)['adj_close'].rolling(60).mean()
  6. 量均线（同样仅在有效交易日上计算）：
     volume_ma5  = groupby(code)['volume'].rolling(5).mean()
     volume_ma20 = groupby(code)['volume'].rolling(20).mean()
  7. 量比：volume_ratio = volume / volume_ma20
  8. bulk_upsert → l2_stock_adj_daily
```

**注意**：rolling 计算需要历史数据窗口。增量生成时，从 `start - 60 trading days` 开始读 L1，但只写 `[start, end]` 范围的结果到 L2，避免窗口不足导致 NaN。

### 5.3 clean_market_snapshot 计算逻辑

此表是 MSS 的直接输入，字段计算较复杂。优先用 DuckDB SQL 聚合：

```text
按日聚合 l1_stock_daily，每个字段的计算：

total_stocks          = COUNT(DISTINCT ts_code) WHERE NOT is_halt
rise_count            = COUNT(*) WHERE close > pre_close
fall_count            = COUNT(*) WHERE close < pre_close

strong_up_count       = 按板块涨跌停幅度分别计算（关键！不能统一用固定值）：
  主板(60/000):         pct_chg >= 0.05   (50% × 10%)
  创业板(300)/科创板(688): pct_chg >= 0.10   (50% × 20%)
  北交所(43/83):         pct_chg >= 0.15   (50% × 30%)
  ST:                   pct_chg >= 0.025  (50% × 5%)
  → 需 JOIN l1_stock_info 取 market, is_st

strong_down_count     = 对称（pct_chg <= -阈值）

limit_up_count        = COUNT(*) WHERE close >= up_limit × 0.998（容差）
limit_down_count      = COUNT(*) WHERE close <= down_limit × 1.002

touched_limit_up_count = COUNT(*) WHERE high >= up_limit × 0.998 AND close < up_limit × 0.998

new_100d_high_count   = 子查询：close >= MAX(close) OVER (PARTITION BY ts_code
                        ORDER BY date ROWS BETWEEN 100 PRECEDING AND 1 PRECEDING)
new_100d_low_count    = 对称

continuous_limit_up_2d     = 连续2天涨停的股票数（需窗口函数）
continuous_limit_up_3d_plus = 连续≥3天涨停
continuous_new_high_2d_plus = 连续≥2天创新高

high_open_low_close_count  = open 在日内区间上 1/3 且 close 在下 1/3：
  open  >= low + (high - low) × 2/3
  close <= low + (high - low) × 1/3

low_open_high_close_count  = 对称

pct_chg_std           = STDDEV(pct_chg) GROUP BY date
amount_volatility     = STDDEV(amount)  GROUP BY date
```

**strong_up/down 分板块计算 SQL 示例**：
```sql
-- 步骤 1：预先物化 stock_info 映射表（空间换时间，避免每行关联子查询）
-- 对每个 (ts_code, date) 对，取 effective_from <= date 的最新一行 market/is_st/industry
CREATE TEMP TABLE _tmp_stock_board AS
SELECT d.ts_code, d.date, i.market, i.is_st, i.industry
FROM l1_stock_daily d
ASOF JOIN l1_stock_info i
  ON d.ts_code = i.ts_code AND d.date >= i.effective_from;
-- 注：DuckDB 支持 ASOF JOIN，若不支持可改用窗口函数方案：
-- ROW_NUMBER() OVER (PARTITION BY ts_code, date ORDER BY effective_from DESC)

-- 步骤 2：分板块计算 strong_up_count
SELECT d.date,
       COUNT(*) FILTER (WHERE
           (b.market IN ('主板') AND NOT b.is_st AND d.pct_chg >= 0.05)
           OR (b.market IN ('创业板','科创板') AND NOT b.is_st AND d.pct_chg >= 0.10)
           OR (b.market IN ('北交所') AND NOT b.is_st AND d.pct_chg >= 0.15)
           OR (b.is_st AND d.pct_chg >= 0.025)
       ) AS strong_up_count
FROM l1_stock_daily d
JOIN _tmp_stock_board b ON d.ts_code = b.ts_code AND d.date = b.date
GROUP BY d.date
```

### 5.4 clean_industry_daily 计算逻辑

```sql
SELECT i.industry,
       d.date,
       AVG((d.close - d.pre_close) / NULLIF(d.pre_close, 0)) AS pct_chg,
       SUM(d.amount) AS amount,
       COUNT(DISTINCT d.ts_code) AS stock_count,
       COUNT(*) FILTER (WHERE d.close > d.pre_close) AS rise_count,
       COUNT(*) FILTER (WHERE d.close < d.pre_close) AS fall_count
FROM l1_stock_daily d
JOIN l1_stock_info i ON d.ts_code = i.ts_code
  AND i.effective_from = (
      SELECT MAX(effective_from) FROM l1_stock_info
      WHERE ts_code = d.ts_code AND effective_from <= d.date
  )
WHERE NOT d.is_halt
GROUP BY i.industry, d.date
```

### 5.5 股票代码转换

L1→L2 的代码转换在 cleaner 中一次性完成：

```python
def ts_code_to_code(ts_code: str) -> str:
    """000001.SZ → 000001"""
    return ts_code.split(".")[0]
```

L2+ 层全部使用 `code`（纯6位数字），系统内部统一。

---

## 6. builder.py — L2/L3/L4 生成工具

### 6.1 CLI 接口

```text
python main.py build --layers=l2              # 只生成 L2
python main.py build --layers=l2,l3           # L2 + L3
python main.py build --layers=all             # 全部重建
python main.py build --layers=l3 --start=2024-01-01 --end=2024-12-31
python main.py build --layers=l2 --force      # 强制全量重建
```

### 6.2 增量生成逻辑

```python
def build_layer(store: Store, layer: str, start: date = None,
                end: date = None, force: bool = False):
    """
    生成指定层级的数据。

    增量逻辑：
    - 不指定 start/end 且 force=False：从目标表 max(date)+1 到今天
    - 指定 start/end：只生成指定范围
    - force=True：清空目标表后全量重建
    """
    if force:
        store.conn.execute(f"DELETE FROM {target_table}")

    if start is None:
        last = store.get_max_date(target_table)
        start = next_trade_day(last) if last else config.HISTORY_START
    if end is None:
        end = today()

    if start > end:
        logger.info(f"{layer} 已是最新，跳过")
        return

    # 调用对应的清洗/计算函数
    if layer == "l2":
        clean_stock_adj_daily(store, start, end)
        clean_industry_daily(store, start, end)
        clean_market_snapshot(store, start, end)
    elif layer == "l3":
        # 调用各算法模块
        from selector.mss import compute_mss
        from selector.irs import compute_irs
        compute_mss(store, start, end)
        compute_irs(store, start, end)
        # l3_signals 由 strategy.generate_signals 在运行时按候选池上下文写入
        # （v0.01 不在 builder 中批量全市场生成信号）
```

### 6.3 层级依赖

```text
L2 依赖 L1（必须先 fetch）
L3 依赖 L2（必须先 build l2）
其中 l3_signals 由 strategy 运行时写入；builder 的 l3 仅构建 mss/irs（及后续 gene）
L4 由 broker/reporter 在运行时写入（不经过 builder）

builder 不自动级联：build --layers=l3 不会自动先 build l2
用户需显式指定 --layers=l2,l3 或 --layers=all
```

### 6.4 计算原则（通用）

1. **禁止逐行循环**：不用 `iterrows()`，用 pandas 向量化 / DuckDB SQL
2. **大块处理**：一次读一段日期的全市场数据，算完批量写入
3. **聚合用 SQL**：`l2_market_snapshot`、`l2_industry_daily` 直接 SQL 聚合
4. **滚动窗口用 pandas**：均线、量比等用 `rolling().mean()`
5. **写入一次性**：算完整块结果后 `bulk_upsert()`，不边算边写

---

## 7. 数据流总览

```text
TuShare API / AKShare API
    │
    ▼ fetcher.py（多线程拉取，主线程顺序写入）
    │
L1 Tables（l1_stock_daily, l1_index_daily, l1_stock_info, l1_trade_calendar）
    │
    ▼ cleaner.py（向量化计算，SQL 聚合）
    │
L2 Tables（l2_stock_adj_daily, l2_industry_daily, l2_market_snapshot）
    │
    ▼ mss.py / irs.py / gene.py（离线批处理） + strategy.py（运行时信号生成）
    │
L3 Tables（l3_mss_daily, l3_irs_daily, l3_signals, l3_stock_gene）
    │
    ▼ broker / reporter（运行时写入）
    │
L4 Tables（l4_orders, l4_trades, l4_stock_trust, l4_daily_report, l4_pattern_stats）
```

---

## 8. 错误处理与边界情况

### 8.1 数据缺失处理

| 场景 | 处理 |
|------|------|
| API 返回空 DataFrame | 跳过写入，不更新 fetch_progress，日志 warning |
| 某只股票某天停牌 | is_halt=true，L2 计算跳过该股当天（不影响均线连续性） |
| adj_factor 缺失 | 使用 1.0（等效未复权），日志 warning |
| 行业信息缺失 | industry='未知'，不参与 l2_industry_daily 聚合 |
| rolling 窗口不足 | 结果为 NaN，写入 L2 时保留 NULL，下游模块自行处理 |

### 8.2 幂等保证

- 所有表通过 PK 做 upsert：同一天重跑覆盖旧数据
- `_meta_fetch_progress` 只在成功后更新：失败不推进进度
- `_meta_runs` 记录每次运行状态：可追溯历史

### 8.3 磁盘空间估算

```text
全市场 ~5000 只股票 × 250 交易日/年 × 3 年 = ~3,750,000 行/L1表
DuckDB 列式压缩后预估：
  l1_stock_daily:       ~200 MB
  l2_stock_adj_daily:   ~300 MB（更多列）
  l2_market_snapshot:   ~0.3 MB（750 行）
  l2_industry_daily:    ~1.5 MB（31 × 750 行）
  L3 + L4:              ~50 MB
  总计:                  ~600 MB（3年数据）
```

