# EmotionQuant

EmotionQuant 是一套面向中国 A 股的交易系统，当前已经按“四个战场”收成统一骨架：

1. `blueprint/`：第一战场，主线治理、默认运行口径、正式执行卡。
2. `normandy/`：第二战场，alpha truth、入场/出场伤害诊断。
3. `positioning/`：第三战场，仓位、退出、执行纪律。
4. `gene/`：第四战场，历史趋势/波段/寿命/环境解释。

## 当前一页总览

如果现在只想先看一页，把系统怎么用、四个目录各放什么、Gene 平均寿命框架怎么读弄清楚，直接看：

- [`docs/reference/operations/current-system-usage-map-20260319.md`](docs/reference/operations/current-system-usage-map-20260319.md)

## 当前默认运行口径

当前治理层写死的默认运行链是：

`Selector preselection -> BOF baseline entry -> FIXED_NOTIONAL_CONTROL -> FULL_EXIT_CONTROL -> Broker execution`

当前边界也要分清：

1. `Gene` 现在是 `context sidecar / attribution layer`，不是 runtime hard gate。
2. 旧 `IRS/MSS` 已不再是默认执行主骨架。
3. `scripts/backtest/` 是证据 runner 层，不是系统默认入口。

## 当前数据底座

这一轮之后，数据层已经切成：

`TDX local-first -> raw 库 -> L1 -> L2 -> selector / broker / backtest`

主底座：

1. 本地通达信 `vipdoc` 提供个股/指数历史日线。
2. 本地 `T0002/hq_cache` 提供股票列表、行业成员快照等静态资产。
3. 本地规则推导 `up_limit / down_limit`。

补洞与保底：

1. `BaoStock` 只做小窗口缺口补数。
2. `TuShare` 只做应急保底。

相关入口：

- [`scripts/data/README.md`](scripts/data/README.md)
- [`docs/reference/code-maps/src-data-code-map-20260318.md`](docs/reference/code-maps/src-data-code-map-20260318.md)
- 历史 baseline：[`docs/design-v2/01-system/system-baseline.md`](docs/design-v2/01-system/system-baseline.md)

## 设计与治理入口

- 四战场集成图：[`docs/spec/common/records/four-battlefields-integrated-system-map-20260316.md`](docs/spec/common/records/four-battlefields-integrated-system-map-20260316.md)
- 当前主线权威层：[`blueprint/README.md`](blueprint/README.md)
- 文档书架：[`docs/navigation/four-battlefields-document-shelf/README.md`](docs/navigation/four-battlefields-document-shelf/README.md)
- 治理状态账本：[`docs/spec/common/records/development-status.md`](docs/spec/common/records/development-status.md)
- 历史基线权威层：[`docs/design-v2/01-system/system-baseline.md`](docs/design-v2/01-system/system-baseline.md)

## 每日维护流程

收盘后，推荐固定这样维护本地数据库：

1. 先用通达信把本地数据下载到最新。
2. 运行 `scripts/data/import_tdx_vipdoc.py`。
3. 运行 `scripts/data/import_tdx_static_assets.py`。
4. 运行 `scripts/data/repair_l1_partitions_from_raw_duckdb.py`。

具体命令和说明见：
[`scripts/data/README.md`](scripts/data/README.md)

## 快速开始

### 推荐目录结构

```text
G:\
├─ EmotionQuant-gamma\   # 代码 + 文档 + formal evidence / record
├─ EmotionQuant_data\    # 正式数据库 + 长期数据产物
├─ EmotionQuant-temp\    # working DB + 临时缓存 + 中间产物
└─ EmotionQuant-report\  # 导出报表 + 人读长报告
```

### 环境准备

1. 复制 `.env.example` 为 `.env`
2. 填写 `DATA_PATH`、`TEMP_PATH`
3. 需要时填写 `RAW_DB_PATH`
4. 安装依赖

### 安装

```bash
pip install -e .
pip install -e ".[dev]"
```

### 常用命令

```bash
python main.py fetch --from-raw-db G:\EmotionQuant_data\duckdb\emotionquant.duckdb --start 2026-03-01 --end 2026-03-18
python main.py build --layers l2,l3 --start 2026-03-01 --end 2026-03-18
python main.py backtest --start 2024-01-01 --end 2024-12-31 --patterns bof
```

## 相关入口

- [`docs/README.md`](docs/README.md)
- [`scripts/data/README.md`](scripts/data/README.md)
- [`scripts/backtest/README.md`](scripts/backtest/README.md)
- [`scripts/ops/README.md`](scripts/ops/README.md)
- [`scripts/report/README.md`](scripts/report/README.md)
- [`docs/reference/operations/current-mainline-operating-runbook-20260317.md`](docs/reference/operations/current-mainline-operating-runbook-20260317.md)

## License

MIT，见 [`LICENSE`](LICENSE)。
