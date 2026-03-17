# Phase 7 Data Provider Refactor Card

**状态**: `Active`  
**日期**: `2026-03-17`  
**对象**: `数据入口与原始库底座重构`

**上游锚点**:
1. `blueprint/03-execution/00-current-dev-data-baseline-20260311.md`
2. `docs/design-v2/02-modules/data-layer-design.md`
3. `scripts/data/bulk_download.py`
4. `scripts/data/import_tdx_vipdoc.py`
5. `scripts/data/import_tdx_static_assets.py`
6. `scripts/data/bulk_download_baostock.py`
7. `scripts/data/bulk_download_tushare.py`

---

## 1. 目标

把当前数据入口从：

`TuShare-first + old raw db reuse`

收束为：

`TDX local-first + BaoStock light incremental + TuShare emergency fallback`

其中本地通达信数据要正式拆成两部分：

1. `vipdoc`
负责历史主底座：
- `raw_daily`
- `raw_index_daily`
- `raw_trade_cal`

2. `T0002/hq_cache + mootdx`
负责本地静态/半静态资产：
- `raw_stock_basic`
- `raw_index_classify`
- `raw_index_member`

这张卡属于第一战场，因为它先改的是：

`raw -> L1 -> L2`

也就是全系统共享的数据入口与数据合同，而不是某一个研究战场的私有实现。

---

## 2. 当前正式判断

### 2.1 历史主底座

正式冻结为：

`历史主底座 = 本地通达信 vipdoc`

理由：
1. 覆盖全历史，且不受在线限速和接口波动影响。
2. 本地已经包含股票、主指数、板块/行业指数 `.day` 文件。
3. `mootdx.reader.daily()` 已验证可直接读取本地 `.day`。

### 2.2 静态资产主入口

正式冻结为：

`静态资产主入口 = T0002/hq_cache + mootdx`

使用口径：
1. `base.dbf` 负责当前股票快照底表。
2. `tdxhy.cfg + tdxzs.cfg` 负责本地行业/板块语义映射。
3. `block_zs.dat / block_gn.dat / block_fg.dat / 自定义板块` 负责当前板块成员快照。
4. `mootdx.reader.block()` / `block_new()` 负责读取本地板块文件。
5. `mootdx.quotes.stocks()` 只作为股票名称的可选兜底，不是主入口。

### 2.3 增量补数

正式冻结为：

`BaoStock 只做轻量增量`

承担：
1. 每日收盘后补最新交易日缺口。
2. 本地数据异常时补少量股票/指数日线。
3. 必要时补小窗口股票列表快照。

不承担：
1. 全历史全市场重拉。
2. 超大窗口暴力抓数。
3. 长期唯一主源。

### 2.4 保底入口

正式冻结为：

`TuShare = 过渡期保底`

承担：
1. BaoStock 不可用时的应急补数。
2. 过渡期 stock_basic 的兜底快照。

不再承担默认日常主入口职责。

### 2.5 行业与规则资产

正式冻结为：

`行业分类 + A股规则 = 本地静态资产`

来源：
1. 本地通达信板块/行业文件。
2. `SwClass` 本地文件。
3. A 股市场交易规则文档。
4. A 股涨跌停制度文档。

也就是说，行业和规则不再默认依赖在线下载。

---

## 3. 两阶段执行边界

### 3.1 Phase 7A = 工具层重构

这一阶段只动：
1. `scripts/data/audit_trade_date_coverage.py`
2. `scripts/data/bulk_download.py`
3. `scripts/data/bulk_download_baostock.py`
4. `scripts/data/bulk_download_tushare.py`
5. `scripts/data/bulk_download_vendor_common.py`
6. `scripts/data/import_tdx_vipdoc.py`
7. `scripts/data/import_tdx_static_assets.py`
8. `scripts/data/load_l1_from_raw_duckdb.py`
9. `scripts/data/repair_l1_partitions_from_raw_duckdb.py`

这一阶段的目标：
1. 打通 `vipdoc -> raw_daily/raw_index_daily/raw_trade_cal`。
2. 打通 `hq_cache -> raw_stock_basic/raw_index_classify/raw_index_member`。
3. 把 `BaoStock` 收缩成轻量增量工具。
4. 保留 `TuShare` 保底入口。
5. 保持旧 raw schema 兼容。

这一阶段不强制修改：
1. `src/data`
2. `tests`

### 3.2 Phase 7B = 正式数据层重构

这一阶段才允许进入：
1. `src/data/fetcher.py`
2. `src/data/cleaner.py`
3. `src/data/sw_industry.py`
4. `tests/unit/data/*`
5. selector / broker / backtest 相关测试

这一阶段的目标：
1. 把 `vipdoc + hq_cache + BaoStock` 升为正式主线数据口径。
2. 降级 `raw_daily_basic`。
3. 降级 `SW-specific chain`。
4. 把 `up_limit/down_limit` 改成基于本地规则推导。
5. 让 `L1 -> L2` 脱离 `TuShare-first` 老耦合。

---

## 4. 当前最小数据集

按当前默认主线，正式最小数据集冻结为：

1. `trade_calendar`
2. `stock_basic`
3. `stock_daily`
4. `price_limit_rules`
5. `optional market / industry reference`

说明：
1. `raw_daily_basic` 的估值类字段不是默认主线刚需。
2. `raw_limit_list` 可以退役。
3. `up_limit / down_limit` 保留，但优先改成规则推导。
4. 行业分类可以本地静态化，不再默认绑在线 `SW2021`。

---

## 5. mootdx 的正式地位

本卡正式记录：

`mootdx 是本地通达信数据接入层，不是边缘工具。`

它在系统中的职责分工是：
1. `reader.daily()` 读取本地 `.day` 历史日线。
2. `reader.block()` / `block_new()` 读取本地板块成员。
3. `quotes.stocks()` 作为股票名称与列表的轻量兜底。

也就是说，`mootdx` 进入了系统正式数据口径，而不是临时试验依赖。

---

## 6. 当前已完成

截至本卡当前进度，已经完成：
1. `import_tdx_vipdoc.py` 已落地。
2. 主 raw 库已用新 `vipdoc` 补到 `2026-03-17`。
3. `bulk_download_baostock.py` 已加安全模式。
4. `bulk_download_tushare.py` 已独立保留。
5. `import_tdx_static_assets.py` 已开工接入本地静态资产链。

---

## 7. 下一步顺序

当前固定顺序为：

1. 先完成 `Phase 7A` 工具层收口。
2. 把本地静态资产正式补进 raw 库。
3. 再跑 `L1` 刷新，确认 `stock_info` 链条恢复到最新快照。
4. 最后再进入 `Phase 7B`，改 `src/data` 与测试。

在 `Phase 7B` 之前，不允许口头假装系统已经完全切换成新数据合同。

---

## 8. Done 定义

### 7A Done

满足以下条件即算完成：
1. `vipdoc` 能导入 `raw_daily / raw_index_daily / raw_trade_cal`。
2. `hq_cache` 能导入 `raw_stock_basic / raw_index_classify / raw_index_member`。
3. `BaoStock` 能安全补小窗口缺口。
4. `TuShare` 保留保底入口。
5. 旧 raw schema 仍兼容。

### 7B Done

满足以下条件即算完成：
1. `src/data` 正式切到新口径。
2. 主线 `L1 -> L2` 可在无 `TuShare-first` 强依赖下跑通。
3. 本地行业/规则资产可替代在线行业/规则下载。
4. 相关测试通过。
5. `development-status` 与正式 record 同步完成。
