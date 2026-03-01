# Spec 01: Data Layer

## 需求摘要
搭建系统地基：从 TuShare 拉取 A 股数据、清洗加工、存入 DuckDB、定义模块间契约。零业务逻辑。

**设计文档**: `docs/design-v2/data-layer-design.md`, `docs/design-v2/architecture-master.md` §4.1

## 交付文件

| 文件 | 职责 |
|------|------|
| `src/config.py` | 全局配置（环境变量、开关、常量） |
| `src/contracts.py` | pydantic 模块边界契约（6个类） |
| `src/data/store.py` | DuckDB 统一存取层（建表、upsert、查询） |
| `src/data/fetcher.py` | L1 数据下载（TuShare主 + AKShare备） |
| `src/data/cleaner.py` | L1→L2 清洗加工（复权、均线、聚合） |
| `src/data/builder.py` | L2/L3/L4 增量生成调度 |

## 设计要点

### store.py
- Store 类持有唯一 DuckDB 连接，启用 WAL
- `bulk_upsert(table, df)`: 注册 df 为临时视图 → INSERT OR REPLACE
- `read_df(sql, params)`: 统一查询入口
- `get_fetch_progress` / `update_fetch_progress`: 断点续传元数据
- main.py 创建 Store 实例，参数传递给各模块（不用全局单例，测试时注入 `:memory:`）

### fetcher.py
- DataFetcher(ABC) → TuShareFetcher / AKShareFetcher 多态
- `fetch_stock_daily`: 按月分批，daily() + daily_basic() 按 (ts_code, date) 合并
- 降级粒度为整次运行（不在单次 API 调用级别切换）
- 多线程并行：4种数据类型（stock_daily/index_daily/stock_info/trade_cal）并行拉取，主线程顺序写入
- tenacity 重试 3 次，API 调用间 sleep 0.3s

### cleaner.py
- `clean_stock_adj_daily`: 前复权(adj_factor) → pct_chg → MA5/10/20/60 → 量比
- `clean_market_snapshot`: 全市场截面统计（strong_up/down 按板块分别计算阈值！）
- `clean_industry_daily`: 按申万一级聚合（等权平均涨跌幅）
- 增量生成时从 start-60 天读 L1（滚动窗口），只写 [start, end] 到 L2

### contracts.py
- 6 个 pydantic BaseModel: MarketScore, IndustryScore, StockCandidate, Signal, Order, Trade
- id 字段: `Field(default_factory=lambda: uuid4().hex[:12])`

## 实现任务

### 基础框架
- [ ] 创建 `src/` 目录结构和 `__init__.py`
- [ ] 实现 `src/config.py`（DATA_PATH、TuShare token、全部开关和常量）
- [ ] 实现 `src/contracts.py`（6 个契约类）
- [ ] 更新 `pyproject.toml` 依赖

### store.py
- [ ] 实现 Store.__init__（连接 DuckDB、启用 WAL、执行全部 DDL）
- [ ] 实现全部 L1-L4 建表 DDL（含 _meta_fetch_progress, _meta_runs）
- [ ] 实现 bulk_upsert / bulk_insert / read_df / read_table
- [ ] 实现 get_fetch_progress / update_fetch_progress / get_max_date
- [ ] 单测：`:memory:` 库上验证 CRUD

### fetcher.py
- [ ] 实现 DataFetcher ABC（4 个抽象方法）
- [ ] 实现 TuShareFetcher（fetch_stock_daily 含 daily+daily_basic 合并）
- [ ] 实现 AKShareFetcher 骨架（字段映射到 TuShare 格式）
- [ ] 实现 create_fetcher 工厂函数（探活 → 降级）
- [ ] 实现 fetch_incremental（断点续传）
- [ ] 实现多线程并行拉取（ThreadPoolExecutor + 队列 + 主线程顺序写入）
- [ ] 单测：mock API 返回，验证合并逻辑和断点续传

### cleaner.py
- [ ] 实现 clean_stock_adj_daily（前复权 + pct_chg + MA + 量比，向量化）
- [ ] 实现 clean_market_snapshot（17 个字段，strong_up/down 按板块 JOIN l1_stock_info）
- [ ] 实现 clean_industry_daily（按申万一级聚合）
- [ ] 实现 ts_code_to_code 转换
- [ ] 单测：构造 mock L1 数据，验证 L2 输出正确性

### builder.py
- [ ] 实现 CLI 接口（--layers, --start, --end, --force）
- [ ] 实现增量生成逻辑（检查 max(date)，只算新日期）
- [ ] 实现强制全量重建（--force）

### 集成验证
- [ ] 端到端：fetch → clean → build，拉取近 3 年数据写入 DuckDB
- [ ] 验证 L1 表行数合理（~5000股 × ~750天 ≈ 375万行）
- [ ] 验证 L2 表 MA/量比无异常 NaN（窗口不足的首 60 天除外）

## 验收标准
1. `python main.py fetch` 能拉取并存储 3 年历史数据
2. `python main.py build --layers=l2` 能生成全部 L2 表
3. L2 表的 strong_up_count 按板块分别计算（不是统一 ±5%）
4. contracts.py 全部类型可实例化和序列化
5. Store 单测在 `:memory:` 库上通过
