# Normandy Dev/Data Baseline Inheritance

**状态**: `Active`  
**日期**: `2026-03-11`  
**对象**: `第二战场固定继承前提`

---

## 1. 定位

本文不重写 `blueprint/03-execution/00-current-dev-data-baseline-20260311.md`。

本文只声明：

`第二战场默认无条件继承当前主线已经冻结的 dev/data baseline。`

---

## 2. 默认继承项

第二战场默认继承以下固定规则：

1. 三目录固定职责。
2. 当前执行库与旧库候选的默认区分。
3. 本地旧库优先、TuShare 补缺的取数顺序。
4. 双 TuShare key 的角色分工。
5. `T+1 Open` 执行语义。

当前继承源固定为：

`blueprint/03-execution/00-current-dev-data-baseline-20260311.md`

---

## 3. 三目录纪律

第二战场当前必须继续遵守：

1. `G:\EmotionQuant-gamma`
   - 只放代码、文档、配置与必要脚本。
   - 不放运行时缓存、临时 DuckDB、测试临时目录。
2. `G:\EmotionQuant_data`
   - 只放本地数据库、日志与长期数据产物。
   - 默认是正式 `DATA_PATH`。
3. `G:\EmotionQuant-temp`
   - 只放临时文件、运行副本、实验缓存、中间产物、pytest/backtest 工作副本。
   - 默认是正式 `TEMP_PATH`。

---

## 4. 当前数据库与旧库优先

第二战场当前继续固定：

1. `G:\EmotionQuant_data\emotionquant.duckdb`
   - 视为当前正式执行库。
2. `G:\EmotionQuant_data\duckdb\emotionquant.duckdb`
   - 视为旧库 / 历史库候选。

数据补齐顺序继续固定为：

1. 先从本地旧库提取能直接复用的数据。
2. 当前执行库缺的数据，再从 TuShare 补齐。
3. 工作副本、中间产物一律放 `G:\EmotionQuant-temp`。

当前允许的本地旧库入口继续固定为：

1. `.env` 中的 `RAW_DB_PATH`
2. `main.py fetch --from-raw-db <path>`

---

## 5. 双 TuShare key 继承口径

第二战场当前继续固定：

1. 主通道：`TUSHARE_PRIMARY_*`
2. 兜底通道：`TUSHARE_FALLBACK_*`

角色分工继续保持：

1. 主通道优先承担 L1 原始接口采集。
2. 主通道失败时，再切换到兜底通道。
3. 不把单一 `TUSHARE_TOKEN` 视为唯一长期口径。

---

## 6. 第二战场当前一句话基线

第二战场当前一句话基线固定为：

`继续以 G:\EmotionQuant_data\emotionquant.duckdb 为执行库、以 G:\EmotionQuant_data\duckdb\emotionquant.duckdb 为旧库候选，先复用 RAW_DB_PATH 指向的本地旧库、再用双通道 TuShare 补缺，所有 working db 与中间产物一律落在 G:\EmotionQuant-temp。`
