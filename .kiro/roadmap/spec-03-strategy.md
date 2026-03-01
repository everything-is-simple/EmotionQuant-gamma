# Spec 03: Strategy

## 需求摘要
对候选池中每只股票判断买卖时机。PAS 形态检测器架构：每个形态一个检测器，签名统一，可独立回测，config 驱动装配。第1迭代只实现 BPB（突破回踩）+ Volman 增强。

**设计文档**: `docs/design-v2/strategy-design.md`, `docs/design-v2/volman-ytc-mapping.md`, `docs/design-v2/architecture-master.md` §4.3

## 交付文件

| 文件 | 职责 |
|------|------|
| `src/strategy/__init__.py` | 包初始化 |
| `src/strategy/pattern_base.py` | PatternDetector ABC |
| `src/strategy/pas_bpb.py` | BPB 突破回踩检测器（第1迭代核心） |
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

### BPB 检测算法（7 步）
1. 计算三核心观测：price_position, volume_ratio, breakout_strength
2. 基础触发：price_position>0.8 AND volume_ratio>1.5 AND breakout_strength>0
3. 回调深度检查 + near_ma20
4. Volman FB 首次回撤检测（穿越 ma20 次数 ≤1）
5. Volman IRB 杯柄形态检测（大U + 小箱体 + ma20附近）
6. 不利条件评估（score < -1 放弃）：前方阻力、冲击效应、整数价位
7. strength = base(0.4×突破强度 + 0.3×量比 + 0.3×实体占比) × multiplier

Multiplier: 首次回撤 ×1.2, 杯柄 ×1.3, 理想回调深度 ×1.1, 有利条件 ×1.1

### registry.py
- ALL_DETECTORS: dict[str, type[PatternDetector]]，第1迭代只有 "bpb"
- `get_active_detectors(config)` → 根据 PAS_PATTERNS 返回实例列表
- 新增形态：写 py → 注册 → 加入 PAS_PATTERNS → 独立回测 → 加入组合

### strategy.py
- `generate_signals(store, candidates, signal_date, config)` → list[Signal]
- 对每只候选股准备 df（lookback 60天），遍历活跃检测器
- 组合模式：ANY(取最强) / ALL(全触发才出) / VOTE(加权阈值)
- 第1迭代只有1个形态，默认 ANY
- 信号写入 l3_signals

## 实现任务

### pattern_base.py
- [ ] 定义 PatternDetector ABC（name + detect 抽象方法）
- [ ] 定义 df 输入规范注释（列要求 + 行排序要求）

### pas_bpb.py
- [ ] 实现 BpbDetector 类（name="bpb"，含 config 参数）
- [ ] Step 1-2: 三核心观测 + 基础触发条件
- [ ] Step 3: 回调深度检查 + near_ma20
- [ ] Step 4: `_check_first_pullback`（FB 首次回撤，穿越 ma20 计数）
- [ ] Step 5: `_detect_cup_handle`（IRB 杯柄：大U + 手柄<3% + ma20附近）
- [ ] Step 6: `_evaluate_market_conditions`（底部抬高/前方阻力/冲击效应/整数价位）
- [ ] Step 7: strength 计算（base + multiplier，cap at 1.0）
- [ ] `_normalize(value, low, high)` 线性归一化辅助
- [ ] 分母为零保护（high_Nd==low_Nd → return None, volume_ma20==0 → skip）
- [ ] 单测：构造突破回踩 mock K线，验证信号触发和 strength 范围
- [ ] 单测：数据不足 / 未突破 / 不利条件 → return None

### registry.py
- [ ] 实现 ALL_DETECTORS（第1迭代只注册 bpb）
- [ ] 实现 `get_active_detectors(config)`（按 PAS_PATTERNS 过滤+实例化）
- [ ] 预留第2/3迭代检测器注释位

### strategy.py
- [ ] 实现 `generate_signals`（遍历候选 × 检测器）
- [ ] 实现 `_combine_signals`（ANY/ALL/VOTE 三种模式）
- [ ] 写入 l3_signals（bulk_insert）
- [ ] 单测：mock 多信号输入，验证三种组合模式

### config 配置
- [ ] PAS_PATTERNS = ["bpb"]
- [ ] PAS_COMBINATION = "ANY"
- [ ] PAS_LOOKBACK_DAYS = 60
- [ ] PAS_MIN_HISTORY_DAYS = 30
- [ ] PAS_BPB_LOOKBACK = 20

## 验收标准
1. BpbDetector 对构造的突破回踩数据输出 BUY 信号，strength ∈ (0, 1]
2. lookback 不足 20 天 → return None
3. high_Nd == low_Nd → return None（不崩溃）
4. market_score < -1 → 放弃交易
5. `generate_signals` 对空候选池返回空列表
6. 单形态回测命令可执行：`python main.py backtest --patterns=bpb`
