# Spec 03: Strategy

> **版本**: v0.01 | **状态**: Active | **基线**: `docs/design-v2/rebuild-v0.01.md` | **评审标准**: `docs/design-v2/sandbox-review-standard.md`

## 需求摘要
对候选池中每只股票判断买卖时机。PAS 形态检测器架构：每个形态一个检测器，签名统一，可独立回测，config 驱动装配。v0.01 只实现 BOF（假突破反杀）并单形态跑通。

**设计文档**: `docs/design-v2/strategy-design.md`, `docs/design-v2/volman-ytc-mapping.md`, `docs/design-v2/architecture-master.md` §4.3

## 交付文件

| 文件 | 职责 |
|------|------|
| `src/strategy/__init__.py` | 包初始化 |
| `src/strategy/pattern_base.py` | PatternDetector ABC |
| `src/strategy/pas_bof.py` | BOF 假突破检测器（v0.01核心） |
| `src/strategy/registry.py` | 形态注册表 + get_active_detectors |
| `src/strategy/strategy.py` | 信号汇总 + 组合模式 |

## 设计要点

### PatternDetector ABC
```python
class PatternDetector(ABC):
    name: str  # 形态唯一标识
    @abstractmethod
    def detect(self, df: pd.DataFrame, code: str, signal_date: date) -> Optional[Signal]
```
- df = 该股票 l2_stock_adj_daily 历史（至少 signal_date 前 60 天 + 当天）
- 只读 OHLCV + 均线 + 量比，**不访问 MSS/IRS**
- signal.action 只产出 BUY（SELL 由 broker 止损触发）

### BOF 检测算法（v0.01）
1. 定位区间边界（lower bound = min(adj_low[t-20, t-1])）
2. Spring 触发：`low < lower*(1-1%)` 且 `close >= lower`
3. 收盘位置确认：`close_pos >= 0.6`
4. 量能确认：`volume >= volume_ma20*1.2`
5. 触发即生成 BUY Signal（`signal_date=T`），不存在入场前的延续确认
6. 失效退出由 Broker 风控层执行（次日不延续 / 收盘跌回结构内）

### registry.py
- ALL_DETECTORS: dict[str, type[PatternDetector]]，五形态在册（tst/bof/bpb/pb/cpb）
- `get_active_detectors(config)` → 根据 PAS_PATTERNS 返回实例列表
- 新增形态：写 py → 注册 → 加入 PAS_PATTERNS → 独立回测 → 加入组合

### strategy.py
- `generate_signals(store, candidates, signal_date, config)` → list[Signal]
- 对每只候选股准备 df（lookback 60天），遍历活跃检测器
- 组合模式：ANY(取最强) / ALL(全触发才出) / VOTE(加权阈值)
- v0.01 只启用 bof，默认 ANY
- 信号写入 l3_signals

## 实现任务

### pattern_base.py
- [ ] 定义 PatternDetector ABC（name + detect 抽象方法）
- [ ] 定义 df 输入规范注释（列要求 + 行排序要求）

### pas_bof.py
- [ ] 实现 BofDetector 类（name="bof"，含 config 参数）
- [ ] Spring 触发判定（4条件全满足即产出 BUY Signal，无延续确认期）
- [ ] strength 计算（收盘位置 + 量比 + 反转K线实体占比）
- [ ] 边界保护（窗口不足20天 / 分母为零 / 一字涨跌停 → return None）
- [ ] 单测：构造假破位数据，验证触发/不触发/边界保护
- 注：失效退出（次日不延续/跌回结构）由 Broker 风控层执行，不在 detector 内实现

### registry.py
- [ ] 实现 ALL_DETECTORS（五形态在册，v0.01 仅启用 bof）
- [ ] 实现 `get_active_detectors(config)`（按 PAS_PATTERNS 过滤+实例化）
- [ ] 预留第2/3迭代检测器注释位
- [ ] v0.01 验收时强校验：`len(PAS_PATTERNS) == 1 and PAS_PATTERNS[0] == \"bof\"`

### strategy.py
- [ ] 实现 `generate_signals`（遍历候选 × 检测器）
- [ ] 实现 `_combine_signals`（ANY/ALL/VOTE 三种模式）
- [ ] 写入 l3_signals（**bulk_upsert**，signal_id 确定性幂等键，重跑覆盖而非追加，D7/H17控制点）
- [ ] 单测：mock 多信号输入，验证三种组合模式

### config 配置
- [ ] PAS_PATTERNS = ["bof"]
- [ ] PAS_COMBINATION = "ANY"
- [ ] PAS_LOOKBACK_DAYS = 60
- [ ] PAS_MIN_HISTORY_DAYS = 30
- [ ] PAS_BOF_BREAK_PCT = 0.01
- [ ] PAS_BOF_VOLUME_MULT = 1.2

## 验收标准
1. BofDetector 对构造的假破位数据输出 BUY 信号（4条件满足即触发，无延续确认期）
2. close < lower_bound → 不触发信号（收盘未收回结构上方）
3. 分母为零/数据不足/窗口不足20天 → return None（不崩溃）
4. `generate_signals` 对空候选池返回空列表
5. 单形态回测命令可执行：`python main.py backtest --patterns=bof`
6. v0.01 禁止并行启用多个 PAS 形态
7. 失效退出（次日不延续/跌回结构）由 Broker spec-04 覆盖验证

## 已知风险与偏差

| 级别 | 问题 | Owner | 截止日期 | 状态 |
|------|------|-------|----------|------|
| — | 当前无已知 S2+ 偏差 | — | — | — |

