# EmotionQuant 产品铁律

**版本**: `v0.01-plus 主线替代版`  
**状态**: `Active`  
**封版日期**: `不适用（Active SoT）`  
**变更规则**: `允许在不改变 v0.01 Frozen 历史基线的前提下，按当前主开发线设计与 Gate 结果受控修订。`  
**上游文档**: `docs/design-migration-boundary.md`, `blueprint/README.md`, `blueprint/02-implementation-spec/01-current-mainline-implementation-spec-20260308.md`

## 当前主线口径

1. `v0.01 Frozen` 是历史基线，只用于对照、回退与回归验证。
2. `v0.01-plus` 是当前主开发线。
3. 当前主线执行链路固定为：`Selector 初选 -> BOF 触发 -> IRS 排序 -> MSS 控仓位 -> Broker 执行`。
4. 如与 `v0.01 Frozen` 历史口径冲突，以 `docs/spec/v0.01-plus/` 与当前设计 SoT 为准；历史基线只用于说明旧系统曾如何运行。

## 系统定位

A股量化选股+交易信号系统。6个模块、3套因子（MSS/IRS/PAS）、L1-L4数据分层、DuckDB单库。

## 当前主线铁律

1. **Selector 只做基础过滤与规模控制**；不得再承担 `MSS gate / IRS filter` 交易决策。
2. **BOF 是当前唯一主触发器**；先独立触发，再进入后置排序。
3. **IRS 是唯一后置横截面增强因子**；用于区分同日多信号优先级。
4. **MSS 是市场级风险调节因子**；用于调节仓位、持仓上限和风险暴露，不进入个股横截面排序。
5. **模块间只传结果契约**（pydantic 对象），不传内部中间特征。
6. **Backtest 和纸上交易共用同一个 broker 内核**，保证回测/实盘语义一致。
7. **执行语义固定为 T+1 Open**：`signal_date=T`，`execute_date=T+1`，成交价=`T+1` 开盘价。禁止未来函数。
8. **低频非拥挤优先**：先保证可复现正期望与生存能力，再追求收益扩张。

## 6 模块职责（不可越界）

| 模块 | 回答的问题 | 硬边界 |
|------|-----------|--------|
| Data（fetcher/cleaner/builder/store） | 数据拉取、清洗、派生、存储 | 零业务逻辑，不做策略判断 |
| Selector（selector） | 从全市场中挑出可供 BOF 扫描的候选池 | 不输出交易动作，不读 `MSS/IRS` 做硬过滤 |
| Strategy（pas_*/registry/strategy/ranker） | 哪些候选触发 BOF，谁更值得排前 | 不做市场级控仓位 |
| Broker（broker/risk/matcher） | 风控+撮合+执行截断 | 当前主线唯一 `MSS` 消费者 |
| Backtest（engine） | 历史回测 | 只用 backtrader 推时钟，交易内核调用 broker |
| Report（reporter） | 统计+预警+归因 | 只读数据，不触发交易 |

## 三套因子系统

- **MSS**（时机维度）：市场风险调节，不再前置停手。
- **IRS**（空间维度）：行业横截面增强，只做后置排序。
- **PAS/BOF**（触发维度）：个股形态触发。

跨系统唯一性保证：MSS=全市场聚合、IRS=行业聚合、PAS=个股级，计算粒度完全不同，不存在重复计分。

## 禁止事项

- 禁止 Selector 继续消费 `MSS/IRS` 作为前置交易门控。
- 禁止把 `MSS` 再写回个股横截面主排序公式，除非后续有单独立项和新证据支持。
- 禁止 Strategy 直接决定最终下单数量与仓位控制。
- 禁止跨模块直接调用内部实现（通过 DuckDB 表或契约对象交互）。
- 禁止 T 日收盘价成交（未来函数）。
