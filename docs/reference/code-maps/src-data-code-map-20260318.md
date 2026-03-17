# src/data 代码地图

**状态**: `Active`  
**日期**: `2026-03-18`  
**对象**: `src/data`  
**当前数据口径**: `TDX local-first + BaoStock light incremental + TuShare emergency fallback`

---

## 1. 这层回答什么

`src/data` 现在负责三件事：

1. 把原始事实装进执行库
2. 把执行库的 `L1` 清洗成策略消费的 `L2`
3. 给上层 `selector / broker / backtest` 提供稳定数据合同

一句话：

`scripts/data` 负责把数据搬进 raw 库，`src/data` 负责把 raw/L1/L2 做成主线可消费的事实层。`

---

## 2. 当前总走线

```text
本地通达信 vipdoc
-> raw_daily / raw_index_daily / raw_trade_cal

本地通达信 T0002/hq_cache
-> raw_stock_basic / raw_index_classify / raw_index_member

BaoStock / TuShare
-> 小窗口补洞 / 保底

raw DuckDB
-> fetcher.bootstrap_l1_from_raw_duckdb()
-> l1_trade_calendar
-> l1_stock_daily
-> l1_index_daily
-> l1_stock_info
-> l1_industry_member

L1
-> cleaner.clean_stock_adj_daily()
-> l2_stock_adj_daily

L1
-> cleaner.clean_industry_daily()
-> l2_industry_daily

L1
-> cleaner.clean_industry_structure_daily()
-> l2_industry_structure_daily

L1
-> cleaner.clean_market_snapshot()
-> l2_market_snapshot

L2
-> builder.build_l2()
-> builder.build_l3()
-> selector / broker / backtest
```

---

## 3. 文件地图

### 3.1 `src/data/store.py`

角色：
- DuckDB 统一存储网关
- schema 版本与迁移入口
- 表 DDL、bulk upsert、fetch progress 的统一门面

主要读写：
- 读写所有 `l1/l2/l3/l4` 表
- 读写 `_meta_schema_version`
- 读写 `_meta_fetch_progress`

本轮最关键的语义：
- `schema v12`
- `l1_sw_industry_member -> l1_industry_member` 迁移
- `sw_industry_member -> industry_member` 进度键兼容

什么时候先看它：
- 你在追“某张表到底长什么样”
- 你在追“为什么老库能升级”
- 你在追“fetch progress 为什么记成这样”

### 3.2 `src/data/fetcher.py`

角色：
- provider 统一抓取接口
- `raw -> L1` 装载入口
- 增量抓取和局部修复入口

主要读：
- 远端 provider 返回的 DataFrame
- raw 库：
  - `raw_trade_cal`
  - `raw_daily`
  - `raw_daily_basic`
  - `raw_index_daily`
  - `raw_stock_basic`
  - `raw_index_classify`
  - `raw_index_member`

主要写：
- `l1_trade_calendar`
- `l1_stock_daily`
- `l1_index_daily`
- `l1_stock_info`
- `l1_industry_member`
- `_meta_fetch_progress`

关键函数：
- `bootstrap_l1_from_raw_duckdb()`
  这是离线主底座的核心装载函数
- `repair_l1_partitions_from_raw_duckdb()`
  这是按日期局部修复 L1 的入口
- `_apply_local_price_limits()`
  这是本地推导 `up_limit/down_limit` 的地方
- `fetch_incremental()`
  这是在线/补洞增量入口

什么时候先看它：
- 你在追“raw 怎么进 L1”
- 你在追“涨跌停价是哪里算出来的”
- 你在追“为什么现在是 TDX local-first”

### 3.3 `src/data/cleaner.py`

角色：
- `L1 -> L2` 清洗与聚合层

主要读：
- `l1_trade_calendar`
- `l1_stock_daily`
- `l1_index_daily`
- `l1_stock_info`
- `l1_industry_member`

主要写：
- `l2_stock_adj_daily`
- `l2_industry_daily`
- `l2_industry_structure_daily`
- `l2_market_snapshot`

关键函数：
- `clean_stock_adj_daily()`
  个股复权主表
- `clean_industry_daily()`
  行业日快照
- `clean_industry_structure_daily()`
  行业内宽度/龙头/强势结构
- `clean_market_snapshot()`
  市场快照

什么时候先看它：
- 你在追“上层策略吃到的特征表是怎么来的”
- 你在追“行业字段优先级”
- 你在追“某个 L2 指标在哪算的”

### 3.4 `src/data/builder.py`

角色：
- `L2/L3` 调度器

主要读：
- `Store`
- `Settings`
- `cleaner` 系列函数
- `selector` 下的 `compute_irs / compute_gene / compute_mss_variant`

主要写：
- 不直接造业务字段
- 通过调度 `cleaner/selector` 间接更新 `l2_* / l3_*`

关键函数：
- `build_l2()`
- `build_l3()`
- `build_layers()`

什么时候先看它：
- 你在追“系统一次 build 到底跑了哪几步”
- 你在追“force rebuild 会清哪些表”

### 3.5 `src/data/sw_industry.py`

角色：
- 行业分类与成员关系的标准化工具层

主要读：
- `raw_index_classify`
- `raw_index_member`
- 远端 `index_classify/index_member_all` 返回的 DataFrame

主要写：
- 不直接写库
- 产出标准化 DataFrame 给 `fetcher` 或脚本落库

关键函数：
- `normalize_l1_industry_classify()`
- `normalize_l1_industry_member_history()`
- `build_l1_industry_member_rows()`

兼容壳：
- `build_l1_sw_industry_member_rows()`
  只给历史规格和旧调用留后门，不再是主合同

什么时候先看它：
- 你在追“行业成员 DataFrame 到底是怎么清洗出来的”
- 你在追“为什么现在叫 generic bucket，不再死守 SW 专用链”

### 3.6 `src/data/__init__.py`

角色：
- 包入口

当前价值：
- 很小，基本不承载业务逻辑

---

## 4. 表地图

### 4.1 raw 层

当前真正关键的是：

| 表名 | 当前主来源 | 说明 |
|---|---|---|
| `raw_daily` | `vipdoc` | 个股日线原始事实 |
| `raw_index_daily` | `vipdoc` | 指数/板块日线原始事实 |
| `raw_trade_cal` | `vipdoc` | 交易日历 |
| `raw_stock_basic` | `T0002/hq_cache` | 当前快照版股票基础信息 |
| `raw_index_classify` | `T0002/hq_cache` | 当前快照版行业/板块分类 |
| `raw_index_member` | `T0002/hq_cache` | 当前快照版行业/板块成员 |
| `raw_daily_basic` | 历史遗留/兼容 | 现在不是主底座重点 |

### 4.2 L1 层

| 表名 | 谁生成 | 谁消费 |
|---|---|---|
| `l1_trade_calendar` | `fetcher.bootstrap_*` | `fetcher/cleaner/broker/backtest` |
| `l1_stock_daily` | `fetcher.bootstrap_*` | `cleaner/selector/broker` |
| `l1_index_daily` | `fetcher.bootstrap_*` | `cleaner/irs/gene` |
| `l1_stock_info` | `fetcher.bootstrap_*` | `cleaner/fetcher/broker` |
| `l1_industry_member` | `fetcher.bootstrap_*` | `cleaner/selector/irs` |

### 4.3 L2 层

| 表名 | 谁生成 | 谁消费 |
|---|---|---|
| `l2_stock_adj_daily` | `cleaner.clean_stock_adj_daily()` | `strategy/selector/gene/backtest` |
| `l2_industry_daily` | `cleaner.clean_industry_daily()` | `irs/gene` |
| `l2_industry_structure_daily` | `cleaner.clean_industry_structure_daily()` | `irs` |
| `l2_market_snapshot` | `cleaner.clean_market_snapshot()` | `mss/gene` |

---

## 5. 当前最关键的 4 条数据合同

1. `l1_stock_daily.up_limit/down_limit` 已经本地化  
不再把在线 `stk_limit` 当硬依赖。

2. `l1_industry_member` 已经是活跃合同  
旧 `l1_sw_industry_member` 只剩迁移兼容和历史痕迹。

3. `industry` 现在是 generic bucket 语义  
不是必须等同于 `SW2021` 才能跑主线。

4. `raw 底座` 已经转成 `TDX local-first`  
在线源只负责轻量补洞和保底。

---

## 6. 这一层和其他核心目录的关系

`src/data` 不直接回答交易问题，它回答的是“事实怎样稳定供给”。

对应关系是：

- `src/data`
  负责把事实准备好
- `src/selector`
  负责解释这些事实
- `src/strategy`
  负责在事实之上组织 trigger/setup
- `src/broker`
  负责按事实边界执行
- `src/backtest`
  负责把前面四层串起来复盘

---

## 7. 阅读顺序建议

如果你要从头顺着读 `src/data`，最推荐顺序是：

1. `src/data/store.py`
2. `src/data/fetcher.py`
3. `src/data/cleaner.py`
4. `src/data/builder.py`
5. `src/data/sw_industry.py`
6. `scripts/data/import_tdx_vipdoc.py`
7. `scripts/data/import_tdx_static_assets.py`

---

## 8. 当前结论

`src/data` 这层现在最重要的变化，不是“多了几个脚本”，而是数据主权变了。`

以前更像：
`在线 provider first`

现在更像：
`TDX local-first -> raw -> L1 -> L2 -> selector/broker/backtest`

这就是当前系统数据底座的真实代码地图。
