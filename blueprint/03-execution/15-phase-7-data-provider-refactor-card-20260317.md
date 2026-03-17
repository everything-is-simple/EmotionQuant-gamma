# Phase 7 Data Provider Refactor Card

**状态**: `Active`
**日期**: `2026-03-17`
**对象**: `数据层供应商与历史底座重构`

**上游锚点**:
1. `blueprint/03-execution/00-current-dev-data-baseline-20260311.md`
2. `docs/design-v2/02-modules/data-layer-design.md`
3. `scripts/data/bulk_download.py`
4. `scripts/data/bulk_download_baostock.py`
5. `scripts/data/bulk_download_tushare.py`
6. `scripts/data/import_tdx_vipdoc.py`

---

## 1. 目标

把当前数据入口从：

`TuShare-first + old raw db reuse`

收束为：

`vipdoc historical base + BaoStock light incremental + TuShare emergency fallback`

这张卡属于第一战场，不属于 `gene / normandy / positioning`。  
因为它先改的是：

`raw -> L1 -> L2`

也就是全系统共享的数据入口与数据合同。

---

## 2. 当前正式判断

### 2.1 历史主底座

正式冻结为：

`历史主底座应该切到本地通达信 vipdoc`

理由：
1. 本地 `vipdoc` 已确认覆盖沪深京日线
2. 本地 `vipdoc` 已确认包含主指数、板块指数、行业/概念指数 `.day`
3. `mootdx` 已实测能直接读取本地 `.day`
4. 历史底座不再受在线限速、接口变更、供应商停摆影响

### 2.2 增量补数

正式冻结为：

`BaoStock 只做轻量增量`

承担：
1. 每日收盘后补最新交易日
2. 补股票列表 / 基础信息
3. 必要时补少量主指数缺口
4. 必要时补粗行业桶

不承担：
1. 全历史全市场重拉
2. 超大窗口暴力抓数
3. 未来唯一长期主源

### 2.3 保底入口

正式冻结为：

`TuShare = 三个月保底入口`

承担：
1. BaoStock 不可用时的应急补洞
2. 某些静态资产初始化时的兜底

不再承担默认日常主入口职责。

### 2.4 行业与规则资产

正式冻结为：

`行业分类 + A股规则 = 本地静态资产`

来源：
1. `SwClass` 本地文件
2. `A股市场交易规则`
3. `A股涨跌停板制度`
4. 本地行业指数 / 板块指数日线

---

## 3. 两阶段执行边界

### 3.1 Phase 7A = 工具层重构

这一步只动：
1. `scripts/data/audit_trade_date_coverage.py`
2. `scripts/data/bulk_download.py`
3. `scripts/data/bulk_download_baostock.py`
4. `scripts/data/bulk_download_tushare.py`
5. `scripts/data/bulk_download_vendor_common.py`
6. `scripts/data/import_tdx_vipdoc.py`
7. `scripts/data/load_l1_from_raw_duckdb.py`
8. `scripts/data/repair_l1_partitions_from_raw_duckdb.py`

这一阶段的目标：
1. 建好 `vipdoc` 导入入口
2. 建好 `BaoStock` 轻量增量入口
3. 保留 `TuShare` 兜底入口
4. 删除 `AKShare`
5. 保持旧 raw schema 兼容

这一阶段不强制改：
1. `src/data`
2. `tests`

### 3.2 Phase 7B = 正式数据层重构

这一步才允许进入：
1. `src/data/fetcher.py`
2. `src/data/cleaner.py`
3. `src/data/sw_industry.py`
4. 配套 `tests/unit/data/*`
5. 配套 selector / broker / backtest 相关测试

这一阶段的目标：
1. 把 `vipdoc + BaoStock` 升成主线默认数据口径
2. 降级 `raw_daily_basic`
3. 降级 `SW-specific chain`
4. 把 `up_limit/down_limit` 改成本地规则推导
5. 让 `L1 -> L2` 脱离 `TuShare-first` 老耦合

---

## 4. 系统最小数据集

按当前默认主线，正式最小数据集冻结为：

1. `trade_calendar`
2. `stock_basic`
3. `stock_daily`
4. `price_limit_rules`
5. `optional market / industry reference`

说明：
1. `raw_daily_basic` 的估值字段不是默认主线刚需
2. `raw_limit_list` 可以退役
3. `up_limit / down_limit` 保留，但优先改成本地推导
4. `SW-specific chain` 不再视为默认硬依赖

---

## 5. 当前已完成

截至本卡开启时，已完成：
1. `BaoStock` 独立下载器已落地
2. `BaoStock` 安全模式已落地，默认阻止大窗口全量抓取
3. `TuShare` 独立入口已落地
4. `vipdoc` 导入器已落地
5. `AKShare` 已退出当前方案
6. `mootdx` 已实测可读本地 `vipdoc`

---

## 6. 下一步顺序

当前固定顺序为：

1. 先完成 `Phase 7A` 脚本层收口
2. 再跑一次 `vipdoc -> raw` 全历史导入验证
3. 再设计本地静态行业/规则资产导入
4. 最后才开启 `Phase 7B`，修改 `src/data` 与测试

在 `Phase 7B` 之前，不允许口头假装已经切换系统默认数据口径。

---

## 7. Done 定义

### 7A Done

满足以下条件即算完成：
1. `vipdoc` 能导入 `raw_daily / raw_index_daily / raw_trade_cal`
2. `BaoStock` 能安全补最新缺口
3. `TuShare` 保留保底入口
4. `AKShare` 已退出工具层
5. 旧 raw schema 仍兼容

### 7B Done

满足以下条件即算完成：
1. `src/data` 正式切换到新口径
2. 主线 `L1 -> L2` 可在无 `TuShare-first` 强依赖下跑通
3. 本地行业/规则资产可替代在线行业/规则下载
4. 相关测试通过
5. `development-status` 和正式 record 完成同步
