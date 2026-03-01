# EmotionQuant 路线图

## 迭代总览

| 迭代 | 周期 | 核心交付 | 状态 |
|------|------|---------|------|
| 第1迭代（MVP） | Week 1-4 | 6模块跑通 + BPB单形态 + 完整回测 | 🔵 进行中 |
| 第2迭代 | Week 5-7 | PB形态 + 牛股基因库 + IRS扩展因子 | ⚪ 未开始 |
| 第3迭代 | Week 8-10 | TST/BOF/CPB形态 + 临界点管理 + BB箱体增强 | ⚪ 未开始 |

---

## 第1迭代：最小可用系统（Week 1-4）

### Week 1 — Data + 基础框架
- **spec**: `spec-01-data-layer.md`
- **交付**: fetcher.py, store.py, cleaner.py, builder.py, contracts.py, config.py
- **验收**: 能拉取并存储近3年历史数据，L1→L2清洗通过，contracts类型校验通过
- **前置依赖**: 无

### Week 2 — Selector + Strategy
- **spec**: `spec-02-selector.md`, `spec-03-strategy.md`
- **交付**: mss.py, irs.py, selector.py, pas_bpb.py, registry.py, strategy.py
- **验收**: 全市场运行一次选股+信号生成，每个模块可独立单测
- **前置依赖**: Week 1（L2表必须可用）

### Week 3 — Broker + Backtest
- **spec**: `spec-04-broker.md`
- **交付**: risk.py, matcher.py, engine.py
- **验收**: 跑通第一次完整回测（BPB单策略），收益/回撤/夏普数据合理
- **前置依赖**: Week 2（L3信号必须可用）

### Week 4 — Report + 纸上交易 + 联调
- **spec**: `spec-05-backtest-report.md`
- **交付**: reporter.py, 纸上交易模式, 全链路联调
- **验收**: 每日能自动跑一遍完整流程 data→selector→strategy→broker→report
- **前置依赖**: Week 3（broker内核必须可用）

### 模块依赖图

```
Week 1          Week 2              Week 3          Week 4
────────        ────────            ────────        ────────
contracts ─┐
config    ─┤
store     ─┤    mss ──┐
fetcher   ─┤    irs ──┼─ selector ─┐
cleaner   ─┤    gene* ┘           │
builder   ─┘                      ├─ strategy ─── broker ─── report
            pas_bpb ──┐           │               │
            registry ─┼───────────┘               │
            strategy ─┘                           engine ────┘

* gene = 第2迭代，第1迭代只建表占位
```

---

## 第2迭代：扩展形态+基因库（Week 5-7）

| 交付物 | 说明 |
|--------|------|
| pas_pb.py | PB回调形态检测器（YTC五形态之二） |
| gene.py 实现 | 五牛五衰基因计算，250日滚动窗口 |
| ENABLE_GENE_FILTER = True | 基因库漏斗开启 |
| IRS 扩展因子 | 连续性 + 估值（从2因子扩展到4因子） |
| BB箱体增强 | 所有形态的信号强度加权 |
| PAS_COMBINATION 生效 | ANY/ALL/VOTE三种组合模式 |

---

## 第3迭代：完整YTC五形态（Week 8-10）

| 交付物 | 说明 |
|--------|------|
| pas_tst.py | TST支撑测试（DD双十字星+SB二次突破） |
| pas_bof.py | BOF假突破（RB假突破识别，A股反向应用） |
| pas_cpb.py | CPB复杂回调（SB+ARB，M/W形态+头肩底） |
| CriticalPointManager | 临界点动态管理（Volman第14章适配） |
| IRS 龙头+基因库因子 | 从4因子扩展到6因子 |
| 不利条件预警 | Volman第15章：阻力位/冲击效应/真空效应 |

---

## 关键决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| 回测引擎 | backtrader 单引擎 | 旧版三引擎都没实现，只留一套做到底 |
| 存储 | DuckDB 单库 | 替代旧版L1-L4四层门禁架构 |
| 数据源 | TuShare主 + AKShare备 | 简化旧版双TuShare通道 |
| 执行策略 | YTC/Volman形态检测 | 替代旧版打板/短线战法 |
| IRS 第1迭代 | 2因子（相对强度+资金流向） | 信号最强的2个，其余后续加回 |
| GUI | 延后 | 第1迭代命令行足够 |
