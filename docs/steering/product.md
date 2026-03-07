# EmotionQuant 产品铁律

**版本**: `v0.01 正式版`  
**状态**: `Frozen`  
**封版日期**: `2026-03-03`  
**变更规则**: `仅允许勘误、链接修复与说明性澄清；若治理口径调整，必须先修订上游 baseline。`  
**上游文档**: `docs/design-v2/01-system/system-baseline.md`

## 冻结区与冲突处理

1. 本文档属于冻结区；默认只允许勘误、链接修复与说明性澄清。若涉及执行语义、模块边界或口径调整，必须进入后续版本处理。
2. 若本文档与 `docs/design-v2/01-system/system-baseline.md` 冲突，以 baseline 为准，并应同步回写本文档。
3. 当前治理状态与是否恢复实现，以 `docs/spec/common/records/development-status.md` 为准。
4. 版本证据、回归结果与阶段记录，统一归档到 `docs/spec/<version>/`。

## 系统定位
A股量化选股+交易信号系统。6个模块、3套因子（MSS/IRS/PAS）、L1-L4数据分层、DuckDB单库。

## 12 条铁律（全体必须遵守）

1. **v0.01 实盘口径 = BOF 单形态闭环**；MSS/IRS 为可开关漏斗，必须先通过消融验证。
2. **MSS 只看市场级**，不碰行业和个股。
3. **IRS 只看行业级**，不碰市场温度和个股形态。
4. **PAS 为框架概念，v0.01 实现仅 BOF**；不把 MSS/IRS 分数当形态输入，只看价格和量。
5. **同一原始观测只归属一个因子**，禁止跨因子重复计分。
6. **模块间只传"结果契约"**（pydantic 对象），不传内部中间特征。
7. **pydantic 只校验模块边界对象**，不逐行校验 DataFrame。
8. **每个模块可独立单测**，不依赖其他模块启动。
9. **Backtest 和纸上交易共用同一个 broker 内核**，保证回测/实盘语义一致。
10. **执行语义固定为 T+1 Open**：signal_date=T（T日收盘后生成信号），execute_date=T+1，成交价=T+1 开盘价。禁止 T 日收盘价成交（未来函数）。
11. **v0.01 单形态先行**：PAS 五形态在册，但仅启用 BOF；禁止并行多形态同时开工。
12. **低频非拥挤优先**：先保证可复现正期望与生存能力，再追求收益扩张。

## v0.01 验证铁律

- MSS/IRS 必须按 `BOF baseline -> BOF+MSS -> BOF+MSS+IRS` 做消融对照，未验证不得宣称有效。
- `ENABLE_GENE_FILTER` 在 v0.01 必须关闭；gene 只允许做事后样本反推。

## 6 模块职责（不可越界）

| 模块 | 回答的问题 | 硬边界 |
|------|-----------|--------|
| Data（fetcher/cleaner/builder/store） | 数据拉取、清洗、派生、存储 | 零业务逻辑，不做策略判断 |
| Selector（mss/irs/gene/selector） | 从~5000股中选50-100只候选 | 不输出交易动作 |
| Strategy（pas_*/registry/strategy） | 候选池中哪只今天买？ | 不把MSS/IRS当输入 |
| Broker（risk/matcher） | 风控+撮合 | 回测和纸上交易共用内核 |
| Backtest（engine） | 历史回测 | 只用backtrader，调broker内核 |
| Report（reporter） | 统计+预警 | 只读数据，不触发交易 |

## 三套因子系统

- **MSS**（时机维度）：今天该不该做？→ 开关
- **IRS**（空间维度）：做哪些行业？→ 缩小范围
- **PAS**（触发维度）：这只股票现在买不买？→ 信号

跨系统唯一性保证：MSS=全市场聚合、IRS=行业聚合、PAS=个股级，计算粒度完全不同，不存在重复计分。

## 禁止事项

- 禁止 Strategy 读取 MSS/IRS 分数
- 禁止跨模块直接调用（通过 DuckDB 表交互）
- 禁止 T 日收盘价成交（未来函数）
- 禁止逐行 DataFrame 校验（pydantic 只在模块边界）
- 禁止全市场统一用 ±5% 计算强势股（必须按板块分别计算阈值）





