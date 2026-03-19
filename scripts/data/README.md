# scripts/data

**状态**: `Active`  
**日期**: `2026-03-18`  
**当前数据底座**: `TDX local-first`

## 每日主流程

如果你每天收盘后要增量更新自己的本地数据库，真正要用的是这 3 个：

1. `import_tdx_vipdoc.py`
2. `import_tdx_static_assets.py`
3. `repair_l1_partitions_from_raw_duckdb.py`

推荐顺序：

```powershell
python scripts/data/import_tdx_vipdoc.py --start 20260318 --end 20260318 --vipdoc-root G:\new-tdx\new-tdx\vipdoc --db-path G:\EmotionQuant_data\duckdb\emotionquant.duckdb
python scripts/data/import_tdx_static_assets.py --tdx-root G:\new-tdx\new-tdx --snapshot-date 20260318 --db-path G:\EmotionQuant_data\duckdb\emotionquant.duckdb
python scripts/data/repair_l1_partitions_from_raw_duckdb.py --source-db G:\EmotionQuant_data\duckdb\emotionquant.duckdb --target-db G:\EmotionQuant_data\emotionquant.duckdb --start 2026-03-18 --end 2026-03-18
```

如果想更稳一点，把最后一步的修复窗口放大到最近 5 个交易日。

## 这些脚本各自干什么

### 每日主流程

- `import_tdx_vipdoc.py`
  把本地通达信 `vipdoc` 的个股/指数日线导入 raw 库
- `import_tdx_static_assets.py`
  把本地 `T0002/hq_cache` 的股票列表、行业分类、行业成员快照导入 raw 库
- `repair_l1_partitions_from_raw_duckdb.py`
  把最近窗口的 raw 数据修复进执行库 `L1`

### 低频或初始化

- `load_l1_from_raw_duckdb.py`
  从 raw 库全量或大窗口重建 L1，适合初次建库或大范围重刷

### 在线补洞和保底

- `bulk_download_baostock.py`
  BaoStock 轻量补洞，不适合全历史暴力重拉
- `bulk_download_tushare.py`
  TuShare 保底入口
- `bulk_download.py`
  老的 TuShare-first 批量引擎，当前只建议作为遗留 fallback

### 工具和诊断

- `bulk_download_vendor_common.py`
  公共工具模块，不直接运行
- `audit_trade_date_coverage.py`
  覆盖率审计脚本，诊断用，不是日更入口
- `run_gene_incremental_builder.py`
  Gene 增量 builder，按脏窗口扫描受影响 code，再只重建这些 code 的 `l3_stock_gene / l3_stock_lifespan_surface / l3_gene_wave / l3_gene_event`，并可选刷新 market surface

## 当前结论：哪些算过时

这批里没有必须立刻删除的脚本，但有两个已经不该再当每日主流程：

1. `bulk_download.py`
2. `bulk_download_tushare.py`

它们不是错误，而是“遗留 fallback”。当前正式日更链已经切成：

`import_tdx_vipdoc.py + import_tdx_static_assets.py + repair_l1_partitions_from_raw_duckdb.py`
