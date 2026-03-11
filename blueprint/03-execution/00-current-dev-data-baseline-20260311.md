# Current Dev/Data Baseline

**状态**: `Active`  
**日期**: `2026-03-11`  
**对象**: `当前主线固定执行前提`  
**定位**: `非 phase 卡，但所有 phase 开工前必须继承的本地环境 / 数据源 / 路径基线`

---

## 1. 定位

本文不重写算法正文，也不替代 phase card。

本文只冻结当前主线执行时必须时刻记住的 5 件事：

1. 三目录的固定职责。
2. 当前执行库与旧库候选的默认区分。
3. 本地旧库优先、TuShare 补缺的取数顺序。
4. 双 TuShare key 的角色分工。
5. 当前 `blueprint` 的正式开工顺序。

一句话说：

`后续所有实现都默认继承这份本地执行前提，不再每次开工时重新口头解释。`

---

## 2. 三目录固定职责

当前本地目录纪律固定为：

1. `G:\EmotionQuant-gamma`
   - 只放代码、文档、配置与必要脚本。
   - 不放运行时缓存、临时 DuckDB、测试临时目录。
2. `G:\EmotionQuant_data`
   - 只放本地数据库、日志与长期数据产物。
   - 默认是正式 `DATA_PATH`。
3. `G:\EmotionQuant-temp`
   - 只放临时文件、运行副本、实验缓存、中间产物、pytest/backtest 工作副本。
   - 默认是正式 `TEMP_PATH`。

当前 `.env` 的最小路径口径应保持为：

```dotenv
DATA_PATH=G:\EmotionQuant_data
TEMP_PATH=G:\EmotionQuant-temp
```

若未显式覆写：

1. `LOG_PATH` 允许按当前代码默认规则回落。
2. 临时 DuckDB、pytest cache、backtest working db 一律放 `G:\EmotionQuant-temp`。

---

## 3. 当前数据库默认口径

截至 `2026-03-11`，本地已知有两份 DuckDB 候选：

1. `G:\EmotionQuant_data\emotionquant.duckdb`
2. `G:\EmotionQuant_data\duckdb\emotionquant.duckdb`

当前主线默认固定为：

1. `G:\EmotionQuant_data\emotionquant.duckdb`
   - 视为当前正式执行库。
   - `config.py` 在 `DATA_PATH=G:\EmotionQuant_data` 下默认解析到这里。
2. `G:\EmotionQuant_data\duckdb\emotionquant.duckdb`
   - 视为旧库 / 历史库候选。
   - 默认只作为迁移源、审计源或补数参考，不作为当前主线默认写入目标。

没有明确变更前，不允许：

1. 把 `G:\EmotionQuant_data\duckdb\emotionquant.duckdb` 误当正式执行库写入。
2. 因为旧库数据更全，就绕过当前执行库和当前 schema 直接把旧库当主线真相源。

---

## 4. 数据补齐顺序

当前数据补齐顺序固定为：

1. 先从本地旧库提取能直接复用的数据。
2. 当前执行库缺的数据，再从 TuShare 补齐。
3. 迁移 / 补数 / 工作副本产生的中间产物，一律放到 `G:\EmotionQuant-temp`。

当前代码允许的本地旧库入口固定为：

1. `.env` 中的 `RAW_DB_PATH`
2. `main.py fetch --from-raw-db <path>`

这意味着：

1. 旧库优先承担“已有数据复用”。
2. TuShare 优先承担“缺口补齐”。
3. 本地旧库与当前执行库的角色必须分开，不能混成“哪个文件大就写哪个”。

---

## 5. TuShare 双通道固定口径

当前 TuShare 口径固定为双通道：

1. 主通道：`TUSHARE_PRIMARY_*`
   - 对应 `10000` 积分网关号。
2. 兜底通道：`TUSHARE_FALLBACK_*`
   - 对应 `5000` 积分官方号。

当前固定角色分工为：

1. 主通道优先承担 L1 原始接口采集。
2. 主通道失败时，自动或受控切换到兜底通道。
3. 不再把单一 `TUSHARE_TOKEN` 视为唯一长期口径；它只保留兼容角色。

当前默认参考接口范围为：

`daily / daily_basic / limit_list_d / index_daily / index_member / index_classify / stock_basic / trade_cal`

双 key 可用性基线命令固定优先使用：

```powershell
python scripts/data/check_tushare_dual_tokens.py --env-file .env --channels both
```

---

## 6. Blueprint 正式开工顺序

当前主线的正式阅读 / 开工顺序固定为：

1. `blueprint/README.md`
2. `blueprint/01-full-design/01-09`
3. `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`
4. `blueprint/03-execution/00-current-dev-data-baseline-20260311.md`
5. `blueprint/03-execution/01-current-mainline-execution-breakdown-20260308.md`
6. 当前 phase card

截至 `2026-03-11` 的执行状态固定为：

1. `Phase 0` 已完成。
2. `Phase 1` 已完成。
3. `Phase 1.5` 已完成。
4. `Phase 2` 已完成。
5. 当前正式开工卡为 `Phase 3 / MSS`。
6. `Phase 4 / Gate` 已 ready，但执行仍依赖 `Phase 3` 交付物。

---

## 7. 固定禁止项

当前主线默认禁止：

1. 跳过 `blueprint`，直接按旧 `docs` 或旧仓库口头经验实现。
2. 在仓库根目录写运行时 DuckDB、pytest 临时目录或实验缓存。
3. 把 `MSS / IRS / PAS` 三条主线同时并行乱改，绕过当前 phase 顺序。
4. 在未区分当前执行库与旧库候选前直接做补数或回测。
5. 在未明确主备角色前混用两个 TuShare key。

---

## 8. 当前一句话基线

当前主线的本地执行基线可以压缩成一句话：

`以 G:\EmotionQuant_data\emotionquant.duckdb 为当前执行库，以 G:\EmotionQuant_data\duckdb\emotionquant.duckdb 为旧库候选，先复用本地旧库、再用双通道 TuShare 补缺，所有实现一律按 blueprint 当前卡从 Phase 3 -> Phase 4 推进。`
