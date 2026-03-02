# EnvBucket 实现清单（v0.01）

**状态**: Draft  
**日期**: 2026-03-02  
**适用范围**: BOF 单形态（v0.01），日线，T+1 Open 执行  
**对应文档**: `rebuild-v0.01.md`、`data-layer-design.md`、`strategy-design.md`、`broker-design.md`、`backtest-report-design.md`

---

## 1. 目标

在不改动 PAS 触发逻辑前提下，为 BOF 增加环境分桶统计能力，回答两件事：

1. BOF 在什么环境下有效。
2. 哪些环境应关闭或降仓（先给建议，不自动执行）。

---

## 2. v0.01 边界（强约束）

1. 分桶只用基准指数公开变量（Baseline 桶）。
2. 不把分桶变量作为 BOF detector 输入条件。
3. 先做统计与报表，不做自动参数优化。
4. v0.01 不引入自定义 MSS/IRS 交叉桶（留到 v0.02）。

---

## 3. 分桶定义（固定口径）

基准指数默认：`000300.SH`（可配置）。

1. `mss_bucket`
   - `BULL`: close > ma50 且 ma20 上行
   - `BEAR`: close < ma50 且 ma20 下行
   - `NEU`: 其他
2. `liq_bucket`
   - `EXPAND`: amount_sma20 / amount_sma60 >= 1.05
   - `NEU`: 0.95 <= ratio < 1.05
   - `CONTRACT`: ratio < 0.95
3. `vol_bucket`
   - `LOW`: vol_pct <= rolling_q33
   - `MID`: rolling_q33 < vol_pct <= rolling_q66
   - `HIGH`: vol_pct > rolling_q66
   - `vol_pct = atr20 / close`

---

## 4. Data Layer TODO（`data-layer`）

## 4.1 新增 L3 表

新增表：`l3_env_index_daily`

字段：

1. `date DATE`
2. `index_code VARCHAR`
3. `close DOUBLE`
4. `amount DOUBLE`
5. `ma20 DOUBLE`
6. `ma50 DOUBLE`
7. `atr20 DOUBLE`
8. `amount_sma20 DOUBLE`
9. `amount_sma60 DOUBLE`
10. `liq_ratio DOUBLE`
11. `vol_pct DOUBLE`
12. `mss_bucket VARCHAR`
13. `liq_bucket VARCHAR`
14. `vol_bucket VARCHAR`
15. `created_at TIMESTAMP`

索引：

1. `(date, index_code)` 唯一索引

## 4.2 扩展现有表字段

给 `l3_signals` 增加：

1. `index_code`
2. `mss_bucket`
3. `liq_bucket`
4. `vol_bucket`

给 `l4_trades` 增加：

1. `index_code`
2. `mss_bucket`
3. `liq_bucket`
4. `vol_bucket`

## 4.3 Builder 任务

新增函数：`build_env_index_daily(calc_date)`

职责：

1. 读取 `l1_index_daily`（基准指数）
2. 计算 MA/ATR/成交额均值
3. 生成三桶标签
4. upsert 到 `l3_env_index_daily`

完成标准：

1. 任一交易日可查到 1 行环境记录
2. 重跑同日不重复写脏数据

---

## 5. Strategy TODO（`strategy`）

1. 在 `generate_signals()` 阶段读取当日 `l3_env_index_daily`
2. 将 `index_code/mss_bucket/liq_bucket/vol_bucket` 写入 Signal（或 `meta`）
3. 明确禁止 detector 读取这些字段参与触发判定

完成标准：

1. BOF 触发结果与未加分桶前保持一致（信号数量误差应为 0）
2. 信号记录带完整分桶标签

---

## 6. Broker TODO（`broker`）

1. 订单创建时透传信号环境标签
2. 成交写入 `l4_trades` 时保留环境标签
3. 暂不做自动开关，仅做可追溯记录

完成标准：

1. 任一交易可追溯到其环境桶
2. 不改变现有 T+1 执行语义

---

## 7. Backtest/Report TODO（`backtest-report`）

## 7.1 新增统计输出（至少 CSV）

1. `bof_funnel_stats`
   - 维度：`mss_bucket, liq_bucket, vol_bucket`
   - 指标：`trigger_count, confirm_count, confirm_rate, trade_count, avg_strength`
2. `bof_env_performance`
   - 维度：`mss_bucket, liq_bucket, vol_bucket`
   - 指标：`trade_count, win_rate, avg_return, median_return, avg_win, avg_loss, expectancy, max_drawdown, hold_days_avg, consecutive_loss_p95`

## 7.2 建议门控规则（报告输出建议，不自动执行）

1. `mss=BEAR and liq=CONTRACT` -> 建议关闭 BOF
2. `mss=NEU and liq=CONTRACT` -> 建议只做 HOT 层
3. `vol=HIGH` -> 建议降仓

完成标准：

1. 报告能直接列出负期望环境桶
2. 报告包含中位数而非只看均值

---

## 8. 配置项 TODO

新增配置：

1. `ENV_INDEX_CODE = "000300.SH"`
2. `ENV_LIQ_EXPAND_THRESHOLD = 1.05`
3. `ENV_LIQ_CONTRACT_THRESHOLD = 0.95`
4. `ENV_VOL_QUANTILE_WINDOW = 750`  # 约 3 年交易日

---

## 9. 验收清单（DoD）

1. 跑一次 BOF 回测，能生成 `l3_env_index_daily`
2. `l3_signals` 与 `l4_trades` 都带环境标签
3. 能输出 `bof_funnel_stats` 与 `bof_env_performance`
4. 统计结果可回答：
   - 哪些桶 confirm_rate 高
   - 哪些桶 expectancy 为负
   - 哪些桶连亏风险高（P95）

---

## 10. 实施顺序（建议）

1. Data schema + builder
2. Strategy 标签透传
3. Broker 持久化透传
4. Report 聚合输出
5. 再做策略门控（v0.02）

