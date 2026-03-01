# A股交易规则

本文件定义 A 股特有的交易制度约束，影响 data/broker/selector 三个模块的实现。

## T+1 执行语义（统一口径）

| 要素 | 规则 |
|------|------|
| signal_date | T 日（T日收盘后产生信号） |
| execute_date | next_trade_date(T)（依赖 l1_trade_calendar） |
| 成交价 | T+1 日开盘价（adj_open） |
| 当日买入 | 次日才能卖出（T+1 约束） |
| T 日 Close 成交 | **禁止**（未来函数） |
| 停牌日 | 订单 REJECTED (HALTED) |
| 一字涨停（买入时） | open >= up_limit × 0.998 → REJECTED (LIMIT_UP) |
| 一字跌停（卖出时） | open <= down_limit × 1.002 → REJECTED (LIMIT_DOWN) |

## 交易基础约束

- **交易时段**：9:30-11:30, 13:00-15:00（沪深交易所）
- **最小交易单位**：100 股（1 手），仓位计算向下取整到 100
- **行业分类**：申万一级（31 个行业），TuShare 原生支持

## 板块涨跌停幅度

| 板块 | 涨跌停幅度 | 强势股阈值（50%×涨停幅度） |
|------|-----------|------------------------|
| 主板 | ±10% | ±5% |
| 创业板 | ±20% | ±10% |
| 科创板 | ±20% | ±10% |
| ST | ±5% | ±2.5% |

**strong_up_count / strong_down_count 必须按板块分别计算**，不允许全市场统一用 ±5%。需 JOIN l1_stock_info 取 market 和 is_st 字段。

## 手续费（A股标准费率）

```
佣金:   max(成交额 × 0.0003, 5元)    # 万三，最低5元
印花税: 成交额 × 0.001                # 千一，仅卖出
过户费: 成交额 × 0.00002              # 万0.2，买卖双边

总费用 = 佣金 + 印花税(仅卖) + 过户费(双边)
```

config.py 中对应常量：
- `COMMISSION_RATE = 0.0003`
- `MIN_COMMISSION = 5.0`
- `STAMP_DUTY_RATE = 0.001`
- `TRANSFER_FEE_RATE = 0.00002`

## 基础过滤规则（selector）

| 过滤项 | 规则 | 依赖字段 |
|--------|------|---------|
| 排除 ST | is_st = true → 排除 | l1_stock_info.is_st |
| 排除次新股 | 上市不足 60 个交易日 → 排除 | l1_stock_info.list_date |
| 流动性过滤 | 日成交额 < MIN_DAILY_AMOUNT → 排除 | l2_stock_adj_daily.amount |
| 市值过滤（可选） | total_mv < MIN_MARKET_CAP → 排除 | l1_stock_daily.total_mv |

## 风控中的A股约束

- **日内浮亏即走**：T+1买入后，T+1收盘价 < 买入价 → T+2开盘强制卖出（受T+1限制当天不能卖）
- **涨跌停不追**：买入时若开盘一字涨停 → REJECTED
- **移动止盈用 high 追踪**：max_price = max(每日 adj_high)，不是 close

## 涨停判定（容差）

```
涨停: close >= up_limit × 0.998
跌停: close <= down_limit × 1.002
曾触涨停: high >= up_limit × 0.998 AND close < up_limit × 0.998（炸板）
```
