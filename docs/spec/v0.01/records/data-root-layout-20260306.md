# 数据根目录说明（2026-03-06）

**数据根目录**: `G:\EmotionQuant_data`

本文件只解释目录职责，不定义系统交易语义。若与 `v0.01-data-storage-decision-20260306.md` 冲突，以后者为准。

---

## 1. 当前目录布局

```text
G:\EmotionQuant_data
├─ emotionquant.duckdb          # 唯一执行库
├─ duckdb\
│  └─ emotionquant.duckdb       # raw 历史源库
├─ parquet\
│  └─ l1\...                    # 遗留 raw Parquet 冷备
├─ logs\                        # 运行日志
└─ cache\                       # 临时缓存
```

---

## 2. 各目录用途

### 2.1 `emotionquant.duckdb`

系统执行主库。

包含：

1. `l1_*`
2. `l2_*`
3. `l3_*`
4. `l4_*`
5. `_meta_*`

### 2.2 `duckdb\emotionquant.duckdb`

raw 历史源库。

主要承载：

1. `raw_daily`
2. `raw_daily_basic`
3. `raw_index_daily`
4. `raw_trade_cal`
5. `raw_stock_basic`
6. 其他 raw 辅助表

### 2.3 `parquet\`

遗留 Parquet 冷备目录。

当前预期：

1. 可保留历史 raw 数据文件。
2. 不作为 `main.py` 默认数据源。
3. 不参与 v0.01 在线执行闭环。

### 2.4 `logs\`

日志目录。

用于：

1. CLI 运行日志
2. 错误排障日志
3. 必要的运行留痕

### 2.5 `cache\`

临时缓存目录。

用于：

1. 一次性下载中间物
2. 探针文件
3. 可丢弃的临时导出

---

## 3. 运维原则

1. 恢复运行优先看执行库 `emotionquant.duckdb` 是否完整。
2. 需要历史回填或重建时，再使用 raw 源库 `duckdb\emotionquant.duckdb`。
3. `parquet` 丢失不应影响 v0.01 主流程运行。
4. `cache` 应视为可清空目录。
5. `logs` 可轮转归档，但不应承载业务状态。
