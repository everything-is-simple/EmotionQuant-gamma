# PAS 算法设计

**版本**: v0.01 正式版  
**创建日期**: 2026-03-06  
**状态**: Active（算法级 SoT，执行语义仍受 `system-baseline.md` 冻结约束）  
**变更规则**: 允许在不改变 v0.01 执行语义前提下，对形态检测器框架与算法细案做受控纠偏。  
**对应模块**: `src/strategy/pattern_base.py`, `src/strategy/pas_bof.py`, `src/strategy/registry.py`, `src/strategy/strategy.py`  
**上游文档**: `system-baseline.md`, `strategy-design.md`, `architecture-master.md`

---

## 1. 定位

在当前系统里，PAS 的正式定义是：

`价格行为形态检测器框架`

它回答的问题只有一个：

`候选池中的这只股票，今天是否触发买入形态？`

它不是旧版研究中的“个股机会总分系统”。

---

## 2. 架构定义

### 2.1 detector 模式

每个形态一个 detector，统一接口：

```text
detect(code, asof_date, df) -> Signal | None
```

这保证了每个形态都可以：

- 单独回测
- 单独开关
- 单独写测试

### 2.2 registry 装配

`registry.py` 只负责：

- 注册 detector
- 按配置决定启用哪些 detector

它不负责形态计算。

### 2.3 strategy 汇总

`strategy.py` 负责：

1. 为候选票准备历史窗口
2. 调用活跃 detector
3. 合并 detector 结果
4. 幂等写入 `l3_signals`

它不负责具体 BOF/BPB/PB 的细节判定。

---

## 3. v0.01 正式口径

### 3.1 单形态

v0.01 只允许：

- `bof`

不允许多形态并行启用。

### 3.2 当前 BOF 定义

当前 BOF 的正式触发条件为：

1. `low < lower_bound * (1 - break_pct)`
2. `close >= lower_bound`
3. `close_pos >= 0.6`
4. `volume >= volume_ma20 * volume_mult`

满足即在 `T` 日收盘后生成 BUY 信号。

### 3.3 SELL 边界

PAS 只产生 `BUY`。

`SELL` 一律由 Broker 风控层生成。

这是当前系统的重要边界，不得回退。

---

## 4. 当前设计资产

PAS 是当前系统里设计最健康的一块。

原因不是它最复杂，而是它最清楚：

1. 算法定义和运行时装配分离
2. BUY 触发与 SELL 管理分离
3. 形态扩展路径清楚
4. 不把 MSS/IRS 分数塞进 detector 输入

这套 detector registry 架构应被视为当前系统的重要设计资产。

---

## 5. 当前开放点

### 5.1 生态未补齐

当前 registry 里真正在线的是：

- `bof`

其余形态仍处于预留状态：

- `bpb`
- `tst`
- `pb`
- `cpb`

### 5.2 组合模式已存在

当前 `strategy.py` 已支持：

- `ANY`
- `ALL`
- `VOTE`

但在 v0.01 中，只有一个在线 detector，因此正式口径仍是：

- `bof`
- `ANY`

---

## 6. v0.02+ 扩展方式

后续新增形态时，必须坚持：

1. 一形态一 detector
2. 先单形态独立回测
3. 通过后再注册进组合
4. 不把 MSS/IRS 分数塞进 detector 输入

这条扩展路径是正式设计约束，而不是建议。

---

## 7. 权威结论

PAS 的主问题不是架构，而是版本范围。

当前正式结论为：

- PAS 不是单一评分算法
- PAS 是形态触发器框架
- v0.01 只在线 BOF
- 后续形态按 detector 模式逐步接入

因此，PAS 的下一步不是重做，而是：

`保持 detector registry 架构不动，把它作为当前系统的算法主骨架。`
