# PAS 算法设计

**版本**: `v0.01 正式版`  
**状态**: `Active`（算法级 SoT，执行语义仍受 `system-baseline.md` 冻结约束）  
**封版日期**: `不适用（Active SoT）`  
**变更规则**: `允许在不改变 v0.01 执行语义前提下，对形态检测器框架与算法细案做受控纠偏。`  
**上游文档**: `docs/design-v2/01-system/system-baseline.md`, `docs/design-v2/02-modules/strategy-design.md`, `docs/design-v2/01-system/architecture-master.md`  
**创建日期**: `2026-03-06`  
**最后更新**: `2026-03-07`  
**对应模块**: `src/strategy/pattern_base.py`, `src/strategy/pas_bof.py`, `src/strategy/registry.py`, `src/strategy/strategy.py`  
**理论来源**: `docs/Strategy/PAS/`

---

## 1. 定位与理论基础

### 1.1 系统定位

在当前系统里，PAS 的正式定义是：

`价格行为形态检测器框架（Price Action Signals）`

它回答的问题只有一个：

`候选池中的这只股票，今天是否触发买入形态？`

它不是旧版研究中的"个股机会总分系统"。

### 1.2 理论来源

PAS 的核心理论来自五位价格行为交易大师的方法论：

1. **Lance Beggs《YTC Price Action Trader》系列**（`docs/Strategy/PAS/lance-beggs-ytc-analysis.md`）
   - 五种核心形态：BPB/PB/TST/BOF/CPB
   - 完整交易系统框架
   - 大量实战案例
   - **EmotionQuant PAS 模块的主要理论来源**

2. **许佳冲《裸K线交易法》**（`docs/Strategy/PAS/xu-jiachong-naked-kline-analysis.md`）
   - BOF 详解（Spring/Upthrust）
   - Pin Bar 识别
   - A股炸板形态
   - **BOF 形态的详细实现参考**

3. **Bob Volman《外汇超短线交易》**（`docs/Strategy/PAS/volman-ytc-mapping.md`）
   - 七种结构与 YTC 五形态的映射
   - 临界点技术
   - 进攻与防守策略
   - **形态识别的精细化参考**

4. **Al Brooks《Price Action》系列**（待补充）
   - PAS 宗师级理论
   - 如何处理失败形态
   - 一根根讲 K 线
   - **失败处理和细节分析参考**

5. **立花义正方法论**（`docs/Strategy/PAS/tachibana-yoshimasa-analysis.md`）
   - 逆向思维
   - 极端情绪交易
   - **与 PAS 的关系：补充极端情况处理**

**核心设计原则**：
- 形态优先于指标（Price Action > Indicators）
- 结构优先于预测（Structure > Prediction）
- 失效优先于止盈（Failure Exit > Profit Target）
- 一形态一检测器（Modular Design）

### 1.3 五形态理论映射

| 形态 | 理论来源 | 核心逻辑 | v0.01 状态 |
|------|---------|---------|-----------|
| BOF | Lance Beggs + 许佳冲 | 假突破反转（Spring/Upthrust） | ✅ 已实现 |
| BPB | Lance Beggs | 突破回调（Breakout Pullback） | ⏳ v0.02 |
| TST | Lance Beggs | 支撑/阻力测试（Test） | ⏳ v0.03 |
| PB | Lance Beggs | 简单回调（Pullback） | ⏳ v0.03 |
| CPB | Lance Beggs | 复杂回调（Complex Pullback） | ⏳ v0.04 |

---

## 2. 架构定义

### 2.1 detector 模式

每个形态一个 detector，统一接口：

```python
def detect(code: str, asof_date: date, df: pd.DataFrame) -> Signal | None:
    """
    形态检测统一接口
    
    参数：
    - code: 股票代码
    - asof_date: 检测日期（T 日）
    - df: 历史数据（至少包含 asof_date 及之前 N 日）
    
    返回：
    - Signal: 触发则返回信号对象
    - None: 未触发则返回 None
    """
```

这保证了每个形态都可以：

- 单独回测
- 单独开关
- 单独写测试
- 单独调参

### 2.2 registry 装配

`registry.py` 只负责：

- 注册 detector
- 按配置决定启用哪些 detector
- 提供统一的 `get_active_detectors()` 接口

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

### 3.1 单形态约束

v0.01 只允许：

- `bof`（BOF - Breakout Failure）

不允许多形态并行启用。

### 3.2 当前 BOF 定义

当前 BOF 的正式触发条件为：

1. `low < lower_bound * (1 - break_pct)`（假突破向下）
2. `close >= lower_bound`（收盘回到结构内）
3. `close_pos >= 0.6`（收盘位置在当日振幅上部）
4. `volume >= volume_ma20 * volume_mult`（成交量放大）

满足即在 `T` 日收盘后生成 BUY 信号。

**理论依据**：
- Lance Beggs: BOF 是"假突破后的反转"，需要价格回到结构内
- 许佳冲: Spring 形态要求"向下假突破 + 快速收回 + 量能配合"
- 执行语义: T 日触发 → T+1 开盘成交

### 3.3 SELL 边界

PAS 只产生 `BUY`。

`SELL` 一律由 Broker 风控层生成。

这是当前系统的重要边界，不得回退。

**理论依据**：
- Lance Beggs: 入场由形态决定，出场由风控决定
- 许佳冲: 止损优先于止盈
- 系统设计: 形态检测与风险管理分离

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

- `bpb`（v0.02）
- `tst`（v0.03）
- `pb`（v0.03）
- `cpb`（v0.04）

### 5.2 组合模式已存在

当前 `strategy.py` 已支持：

- `ANY`（任一形态触发即生成信号）
- `ALL`（所有形态同时触发才生成信号）
- `VOTE`（多数形态触发才生成信号）

但在 v0.01 中，只有一个在线 detector，因此正式口径仍是：

- `bof`
- `ANY`

---

## 6. 版本演进路径（v0.01-v0.06）

### 6.1 v0.01：BOF 单形态闭环

**当前状态**：
- 仅 BOF 形态（Spring/Upthrust）
- 四条件触发（假突破 + 收回 + 位置 + 量能）
- detector 模式架构
- 单形态回测验证

**理论依据**：
- Lance Beggs: BOF 是最可靠的反转形态
- 许佳冲: Spring 是 A 股最常见的做多机会
- 系统设计: 先做一个形态的闭环，再扩展

**验收标准**：
- BOF 单形态回测通过（EV >= 0, PF >= 1.05, MDD <= 25%）
- trade_count >= 60
- 形态识别准确率 >= 60%

### 6.2 v0.02：BPB 形态接入

**计划改进**：
- 新增 BPB detector（突破回调）
- BPB 单形态回测
- BOF + BPB 组合回测（ANY 模式）
- 形态优先级排序

**理论依据**：
- Lance Beggs: BPB 是趋势延续的最佳入场点
- Bob Volman: RB（Range Break）对应 BPB
- 系统设计: 反转（BOF）+ 延续（BPB）覆盖两大场景

**BPB 触发条件**（草案）：
1. 突破前高/前低（breakout）
2. 回调至突破点附近（pullback）
3. 回调幅度 <= 50%（浅回调）
4. 量能配合（volume >= volume_ma20 * 1.2）

**验收标准**：
- BPB 单形态回测通过
- BOF + BPB 组合改善 baseline
- 两形态互补性验证（不同市场环境表现）

### 6.3 v0.03：TST/PB 形态接入

**计划改进**：
- 新增 TST detector（支撑/阻力测试）
- 新增 PB detector（简单回调）
- 四形态组合回测（BOF/BPB/TST/PB）
- 形态失效率统计

**理论依据**：
- Lance Beggs: TST 是趋势中的低风险入场
- Lance Beggs: PB 是最简单的趋势跟随
- Bob Volman: BB（Bounce Back）对应 TST

**TST 触发条件**（草案）：
1. 价格触及支撑/阻力（test）
2. 快速反弹（rejection）
3. 未跌破/突破关键位（hold）
4. 量能萎缩（volume < volume_ma20）

**PB 触发条件**（草案）：
1. 明确趋势（连续 N 日同向）
2. 回调至均线附近（pullback）
3. 回调幅度 <= 38.2%（斐波那契）
4. 量能配合

**验收标准**：
- TST/PB 单形态回测通过
- 四形态组合改善 baseline
- 形态失效率 <= 40%

### 6.4 v0.04：CPB 形态接入 + 失败处理

**计划改进**：
- 新增 CPB detector（复杂回调）
- 五形态完整生态
- 失败形态识别（Al Brooks 理论）
- 失败后的反向信号

**理论依据**：
- Lance Beggs: CPB 是高级形态，需要更多确认
- Al Brooks: 失败的 BOF 可能是反向的 BPB
- 系统设计: 失败处理是成熟系统的标志

**CPB 触发条件**（草案）：
1. 多次回调（complex）
2. 回调幅度 > 50%（深回调）
3. 最终突破（breakout）
4. 量能持续放大

**失败处理**（草案）：
- BOF 失败 → 可能是反向 BPB
- BPB 失败 → 可能是反向 BOF
- TST 失败 → 趋势反转信号
- 失败后冷却期（不再触发同形态）

**验收标准**：
- CPB 单形态回测通过
- 五形态组合改善 baseline
- 失败处理减少亏损 >= 20%

### 6.5 v0.05：形态强度评分

**计划改进**：
- 形态强度量化（0-1 分）
- 基于历史成功率动态调整
- 形态优先级排序
- 弱形态过滤

**理论依据**：
- Lance Beggs: 不是所有形态都值得交易
- Bob Volman: 临界点的质量决定成功率
- 系统设计: 形态强度是后置评分的基础

**强度评分因子**（草案）：
- 结构清晰度（structure_clarity）
- 量能配合度（volume_confirmation）
- 位置优势（position_advantage）
- 历史成功率（historical_win_rate）

**验收标准**：
- 强度评分与实际收益相关性 >= 0.3
- 弱形态过滤改善胜率 >= 5%
- 强度排序与优先级一致

### 6.6 v0.06：自适应参数

**计划改进**：
- 形态参数不再固定，基于市场环境动态调整
- 不同市场环境（牛/熊/震荡）使用不同参数
- 引入机器学习优化参数
- 形态组合策略

**理论依据**：
- Lance Beggs: 市场环境变化，形态参数也应调整
- 系统设计: 自适应是系统成熟的标志

**自适应参数**（草案）：
- 牛市: 放宽 BOF 条件，收紧 BPB 条件
- 熊市: 收紧 BOF 条件，放宽 TST 条件
- 震荡: 均衡参数，增加 PB 权重

**验收标准**：
- 自适应参数相对固定参数改善 EV >= 15%
- 不同环境参数差异显著
- 参数调整逻辑可解释

---

## 7. v0.02+ 扩展方式

后续新增形态时，必须坚持：

1. 一形态一 detector
2. 先单形态独立回测
3. 通过后再注册进组合
4. 不把 MSS/IRS 分数塞进 detector 输入

这条扩展路径是正式设计约束，而不是建议。

**理论依据**：
- Lance Beggs: 每个形态都应该能独立盈利
- 系统设计: 模块化是可维护性的基础

---

## 8. 形态检测器接口规范

### 8.1 标准接口

```python
class PatternDetector(ABC):
    """形态检测器基类"""
    
    @abstractmethod
    def detect(self, code: str, asof_date: date, df: pd.DataFrame) -> Signal | None:
        """
        形态检测
        
        参数：
        - code: 股票代码（6位）
        - asof_date: 检测日期（T 日）
        - df: 历史数据（包含 asof_date 及之前至少 20 日）
        
        返回：
        - Signal: 触发则返回信号对象（含 bof_strength）
        - None: 未触发则返回 None
        """
        pass
    
    @abstractmethod
    def get_required_window(self) -> int:
        """返回所需历史窗口长度（交易日）"""
        pass
    
    @abstractmethod
    def get_pattern_name(self) -> str:
        """返回形态名称（小写，如 'bof'）"""
        pass
```

### 8.2 Signal 输出规范

```python
class Signal(BaseModel):
    signal_id: str              # 幂等键: f"{code}_{signal_date}_{pattern}"
    code: str                   # 股票代码（6位）
    signal_date: date           # 信号日期（T 日）
    action: str                 # 固定为 "BUY"
    pattern: str                # 形态名称（如 "bof"）
    reason_code: str            # 触发原因（如 "BOF_SPRING"）
    bof_strength: float         # 形态强度（0-1）
    
    # v0.02+ 新增字段
    irs_score: float = 0.0      # 行业评分（后置）
    mss_score: float = 0.0      # 市场温度（后置）
    final_score: float = 0.0    # 综合评分（后置）
```

---

## 9. 权威结论

PAS 的主问题不是架构，而是版本范围。

当前正式结论为：

- PAS 不是单一评分算法
- PAS 是形态触发器框架
- v0.01 只在线 BOF
- 后续形态按 detector 模式逐步接入
- 理论基础清晰（五位大师方法论）
- 扩展路径明确（v0.01-v0.06）

因此，PAS 的下一步不是重做，而是：

`保持 detector registry 架构不动，把它作为当前系统的算法主骨架，按版本计划逐步接入 BPB/TST/PB/CPB。`

---

## 10. 参考文献

1. `docs/Strategy/PAS/lance-beggs-ytc-analysis.md` - 五形态理论来源
2. `docs/Strategy/PAS/xu-jiachong-naked-kline-analysis.md` - BOF 详细实现
3. `docs/Strategy/PAS/volman-ytc-mapping.md` - 形态映射关系
4. `docs/Strategy/PAS/tachibana-yoshimasa-analysis.md` - 极端情况处理
5. `docs/design-v2/01-system/system-baseline.md` - 执行语义
6. `docs/design-v2/02-modules/strategy-design.md` - Strategy 模块设计
7. `docs/design-v2/03-algorithms/core-algorithms/down-to-top-integration.md` - v0.02 软评分模式

