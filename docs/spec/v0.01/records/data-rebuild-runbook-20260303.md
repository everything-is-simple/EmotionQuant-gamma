# 数据重建运行记录（2026-03-03）

**版本**: v0.01 正式版运维记录  
**执行时间**: 2026-03-03  
**数据根目录**: `G:\EmotionQuant_data`  
**结论**: 保留 L1，清空 L2/L3/L4，按链路重建。

---

## 1. 当前盘点结果（执行后）

### 1.1 可继续使用（L1）

`parquet/l1` 保留，覆盖度如下：

| 数据集 | 文件数 | 起始日期 | 结束日期 |
|---|---:|---:|---:|
| raw_daily | 6342 | 20000104 | 20260224 |
| raw_daily_basic | 6338 | 20000104 | 20260224 |
| raw_index_daily | 6338 | 20000104 | 20260224 |
| raw_trade_cal | 9553 | 20000101 | 20260225 |
| raw_limit_list | 1516 | 20191128 | 20260224 |
| raw_stock_basic | 68 | 20100101 | 20260201 |
| raw_index_classify | 12 | 20190101 | 20260201 |
| raw_index_member | 54 | 20190102 | 20260201 |

DuckDB（`emotionquant.duckdb`）保留的 L1 相关表：

- `raw_daily`
- `raw_daily_basic`
- `raw_index_daily`
- `raw_trade_cal`
- `raw_limit_list`
- `raw_stock_basic`
- `raw_index_classify`
- `raw_index_member`
- 以及探针/配置表：`__rw_probe`、`_storage_probe`、`system_config`

### 1.2 已删除（L2/L3/L4）

- 已删除目录：`parquet/l2`、`parquet/l3`（`parquet/l4` 原本不存在）。
- DuckDB 中所有非 L1 派生表已删除（24 张），仅保留 `raw_*` 和探针/配置表。

---

## 2. 哪些需要新增（L1补采建议）

以下不是阻塞项，但为了长窗回测和 IRS 稳定性，建议后续补齐：

1. `raw_index_classify` 与 `raw_index_member` 的更早历史（目前起点 2019）。
2. `raw_stock_basic` 历史快照起点可再前探（目前起点 2010）。
3. 对 `raw_limit_list` 的早期历史（目前起点 2019）建立替代方案或明确策略起算窗口。

---

## 3. 重建链路与执行顺序

1. `L1 -> L2`：从 `raw_*` 统一生成标准化行情/截面特征。
2. `L2 -> L3`：基于 L2 计算 MSS/IRS/PAS 输出（v0.01 仅 BOF 触发器）。
3. `L3 -> L4`：回测/纸上交易写入订单、成交、报告与归因。

---

## 4. 性能口径（必须执行）

1. **向量化优先**：尽量使用 DuckDB SQL（窗口函数、分组聚合、批量 join），避免 Python 行级循环。
2. **增量构建优先**：默认从目标表 `max(date)+1` 续算；仅在公式变更时 `--force` 全量重建。
3. **分层物化**：L2 物化公共特征，避免 L3 重复计算同一指标（空间换时间）。
4. **批量 I/O**：统一 `bulk_upsert`，禁止逐行写入。
5. **日期分块执行**：按交易日分片处理，减少单次内存峰值。

---

## 5. 记录落点（你问的“写在哪些文件”）

1. **口径与架构规则**：`docs/design-v2/02-modules/data-layer-design.md`
2. **系统级执行约束**：`docs/design-v2/01-system/system-baseline.md`
3. **每次真实清理/重建证据**：本文件（按日期滚动新增）



