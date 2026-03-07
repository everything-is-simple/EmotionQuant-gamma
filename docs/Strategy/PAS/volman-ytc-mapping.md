# Bob Volman《外汇超短线交易》与 YTC 形态映射分析

> **文档版本**：v0.01 正式版（参考附录）  
> **文档状态**：Frozen（与 `system-baseline.md` 对齐）  
> **创建日期**：2026-03-01  
> **封版日期**：2026-03-03  
> **变更规则**：仅允许勘误与说明性修订；不改变 v0.01 触发口径。  
> **适配对象**：EmotionQuant-gamma PAS模块（A股日线T+1系统）

> **v0.01 口径说明**：本文件用于形态语义映射与增强参考，不作为 v0.01 的硬触发判定来源。  
> v0.01 的交易触发以 `strategy-design.md` 中 BOF 量化规则为准。
> 文中关于 `PAS_BPB`、Week2/Week4 的实现节奏均属历史研究草案，执行计划以 `system-baseline.md` 与 `docs/spec` 为准。

---

## 1. Volman 核心理论基础

### 1.1 跨周期原理（Volman 原话）
> "由于**价格行为原理非常普遍**，所以在其他具有相似波动率和较低交易成本的市场采用这个方法时，也**没必要进行太多的调整**。"  
> —— 原文第193-196行

**核心逻辑**：
1. **Trapped Traders理论**：被套交易者被迫止损→引发踩踏
2. **双重压力原理**：被困方止损订单 + 场外跟进方入场订单 = 同向叠加
3. **突破前压力**：压缩的弹簧效应（蓄力越久，突破越强）
4. **假突破识别**：无蓄力直冲边线 = 高概率陷阱

**时间尺度差异**：
- Volman：70tick（约30秒K线），日内超短线
- EmotionQuant：日线K线，T+1次日开盘执行
- **映射关键**：原理不变，信号蜡烛线从"3-7点波幅"→"日K实体占比>50%"

---

## 2. Volman 七种结构完整定义

### 2.1 DD结构（Double Doji）—— 双十字星突破

#### 定义
在20期EMA区域出现**2个（或3个）相等极值的十字星/小实体蜡烛线**（每根≤3点）

#### 触发条件
- 做多：突破双十字星的最高点
- 做空：突破双十字星的最低点

#### 技术特征
- 十字星收盘价≈开盘价，表示多空博弈达到临时平衡
- 必须在20EMA附近（视觉辅助，非强制触及）
- 两个极值必须相等（允许1点误差）

#### YTC映射
= **TST（Test of Support）** 的微观信号
- Volman的十字星 = YTC的"Hold Candle"（持有K线）
- 双十字星 = 支撑被测试2次后反弹
- **A股适配**：日K的十字星（实体≤1%），出现在ma20附近

---

### 2.2 FB结构（First Break）—— 首次突破

#### 定义
**趋势首次回撤**后在20EMA区域的反转突破

#### 3个必要条件（缺一不可）
1. **突然爆发的趋势**：单边强势波动，无显著回撤
2. **斜向有序回撤**：40-60%回撤深度，蜡烛线斜向下跌/上涨
3. **首次回撤**：如果是第2次或更多次回撤→无效，改用SB

#### 触发条件
回撤末端信号蜡烛线被突破（突破1个点即可）

#### 技术要点
- 信号蜡烛线长度≤7点（以便设10点止损）
- 20EMA作为回撤目标区域（不必精确触及）
- 回撤中大部分K线应为逆势颜色（上涨中回撤=黑体，下跌中回撤=白体）

#### YTC映射
= **BPB（Breakout Pullback）** 的完整版
- Volman的"40-60%回撤" = YTC的"Pullback深度判断"
- Volman的"首次回撤" = YTC的"BPB最佳入场时机"
- **A股适配**：
  ```python
  # PAS_BPB观测
  - pullback_depth = (high_Nd - close) / (high_Nd - low_Nd)  # 0.4~0.6为佳
  - ma20_distance = abs(close - ma20) / close  # <3%为接近ma20区域
  - is_first_pullback = True  # 需记录趋势启动点，判断是否首次
  ```

---

### 2.3 SB结构（Second Break）—— 二次突破

#### 定义
FB失败后，价格再次回到20EMA区域，**第2根信号蜡烛线**在趋势方向被突破

#### 形态特征
- 看跌市场：**M型**（两个相等高点，中间一个低谷）
- 看涨市场：**W型**（两个相等低点，中间一个高峰）
- 两次突破之间间隔：通常1-4根K线（可更长，呈波浪状）

#### 心理逻辑（Volman原话第3349-3352行）
> "逆势交易者尝试了两次，并且两次都失败，然后士气低落或者惊慌失措地放弃逆势计划，逃离市场。"

**三阶段心理**：
1. 第一次突破失败 → **怀疑**（可能是假突破）
2. 价格再次回到EMA → **希望**（我的方向是对的）
3. 第二次被突破 → **恐惧/恐慌**（必须立即止损）

#### 触发条件
第2次回到20EMA区域时，信号蜡烛线被突破

#### YTC映射
= **CPB（Complex Pullback）** 或 **TST的二次测试**
- Volman的M/W形态 = YTC的"复杂回调结构"
- 两次失败尝试 = YTC的"Trapped Traders累积"
- **A股适配**：
  ```python
  # PAS_CPB观测（或作为pas_tst的强化信号）
  - first_break_failed = True  # 记录FB是否失败
  - second_test_at_ema = True  # 第2次触及ma20区域
  - m_or_w_pattern = detect_double_top_or_bottom()  # 形态识别
  ```

---

### 2.4 BB结构（Box Breakout）—— 箱体突破

#### 定义
价格在**狭窄箱体内蓄积压力**（通常≤5点），像压缩的弹簧

#### 3种出现位置
1. **回撤末端**：顺势交易，箱体在EMA区域形成
2. **强劲趋势中的水平回撤**：不是斜向回调，而是横盘震荡
3. **非趋势市场**：区间转折点、筑顶/筑底过程

#### 箱体特征
- **上边线**：由多个相等的蜡烛线最高点确定（允许1点误差）
- **下边线**：由多个相等的蜡烛线最低点确定
- **宽度**：通常≤5点（A股日线适配：≤3%振幅）
- **突破前压力**：箱体内出现小十字星（理想：双十字星）

#### 触发条件
突破箱体上边线或下边线，**最好有"挤压"过程**（多次测试边线）

#### YTC映射
= **所有5种形态的K线质量细化工具**
- Volman的箱体 = YTC的"价格密集区"
- 突破前压力 = YTC的"蓄力信号"
- **A股适配**：用于BPB/PB/TST的**信号强度加权**
  ```python
  # 增强signal_strength
  if has_box_pattern:  # 检测到箱体
      box_width = (high_box - low_box) / close
      if box_width < 0.03:  # 窄幅箱体
          strength_multiplier = 1.2  # 信号强度+20%
  ```

---

### 2.5 RB结构（Range Breakout）—— 区间突破

#### 定义
价格在**较宽区间**（通常20-40点）内拔河后突破边线

#### 关键要素
1. **区间边线**：由多个相等极值确定（≥3个点）
2. **"挤压"蓄力**：价格在20EMA与边线之间来回震荡
3. **避免捉弄式突破**（Teasing Breakout）：从中部直冲边线无蓄力

#### 假突破识别规则
| 特征 | 真突破 | 假突破（Fake） | 捉弄式突破（Teasing） |
|------|--------|----------------|----------------------|
| 起始位置 | 20EMA区域 | 区间顶部/底部 | 中部（无明确蓄力） |
| 蓄力过程 | 多次震荡 | 直线冲击 | 短暂停顿后冲击 |
| 跟进动作 | 1-2根K线内跟进 | 无跟进，价格回撤 | 跟进迟缓 |
| 成功率 | 高 | 低 | 中等 |

#### YTC映射
= **BOF（Breakout Failure）** 的反向
- Volman的真突破 = YTC的"有效BPB"
- Volman的假突破 = YTC的**BOF形态**（假突破反转入场）
- **A股适配**：
  ```python
  # PAS_BOF观测（v0.01可用，v0.03继续细化）
  - range_width = resistance_level - support_level
  - squeeze_count = count_tests_near_boundary()  # 边线测试次数
  - is_teasing = (squeeze_count < 2)  # 捉弄式突破标志
  if breakout_failed and not is_teasing:
      signal = "BOF_ENTRY"  # 假突破反转入场
  ```

---

### 2.6 IRB结构（Inside Range Breakout）—— 区间内突破 ⭐

#### 定义
在**区间内部形成小箱体**（BB结构），**提前**突破小箱体来抢跑区间边线突破

#### 3种交易方式
1. **区间边线反弹交易**（最安全）
   - 在区间上边线或下边线附近的BB突破
   - 典型：价格测试边线后形成小箱体，突破小箱体即入场

2. **区间中部交易**（需强力技术支持）
   - 在较宽区间（>20点）中部的BB突破
   - 风险：可能被区间边线反弹打止损

3. **突破交易**
   - IRB突破后继续突破区间边线
   - 享受"真空效应"（价格被快速吸向下一整数位）

#### "杯柄形态"（Cup & Handle）—— Volman重点强调
**原文第8100-8122行完整描述**：

> "这个形态是由两个'U'形构成——大的'U'形是茶杯，旁边较小的'U'形是茶杯的手柄。连接茶杯和手柄的中间点是一个局点，并且一旦这个高点被突破，市场会在突破的方向上做出强烈的反应。"

**杯柄结构**：
- **茶杯（大U）**：区间内的回调波动，形成圆弧底
- **手柄（小u）**：茶杯右侧的小型回调/盘整，形成小箱体
- **中间点（Cup Handle Junction）**：茶杯最高点，手柄起始点
- **突破点**：手柄顶点被突破 = 入场信号

**手柄特征**（关键）：
- 长度：通常3-7点（A股适配：1-2日K线）
- 形态：小型双底/升高底部/十字星聚集
- 位置：在20EMA区域找到支撑
- 止损：手柄底部下方1点（手柄越短，止损越经济）

#### YTC映射
= **BPB/PB的K线质量强化 + 回调触发细节**

| Volman IRB | YTC形态 | 具体映射 |
|-----------|---------|---------|
| 杯柄形态 | BPB回调结构 | 茶杯=大回调，手柄=小盘整，突破手柄=BPB入场 |
| 区间边线反弹 | PB触发细节 | 测试support_level后反弹=PB信号 |
| 真空效应 | 无阻力上涨 | 突破后快速吸向整数位=YTC的"smooth move" |

#### A股适配示例
```python
# 在pas_bpb.py中增强信号识别
def detect_cup_handle(df, signal_date, lookback=20):
    """
    检测杯柄形态（IRB结构）
    返回：(is_valid, handle_bottom, handle_top)
    """
    recent = df.tail(lookback)
    
    # 1. 检测茶杯（大U形）：先跌后涨
    cup_low = recent['adj_low'].min()
    cup_left = recent.iloc[:len(recent)//2]['adj_close'].mean()
    cup_right = recent.iloc[-5:]['adj_close'].mean()
    is_cup = (cup_right > cup_low * 1.02) and (cup_left > cup_low * 1.02)
    
    # 2. 检测手柄（小u形）：最后3-5根K线的小幅回调
    handle = recent.tail(5)
    handle_high = handle['adj_high'].max()
    handle_low = handle['adj_low'].min()
    handle_width = (handle_high - handle_low) / handle_low
    is_handle = handle_width < 0.03  # 手柄宽度<3%
    
    # 3. 手柄在ma20附近
    near_ma20 = abs(handle_low - handle['ma20'].iloc[-1]) / handle_low < 0.02
    
    if is_cup and is_handle and near_ma20:
        return True, handle_low, handle_high
    return False, None, None

# 在BPB检测中调用
has_cup_handle, h_low, h_top = detect_cup_handle(df, signal_date)
if has_cup_handle:
    strength *= 1.3  # 杯柄形态加权+30%
```

---

### 2.7 ARB结构（Advanced Range Breakout）—— 高级区间突破

#### 定义
结合**多个技术形态**的复杂区间突破（第13章内容）

#### 特点
- 包含假突破、捉弄式突破、双重压力、头肩底等经典形态
- 需要综合评估整体市场力量：
  - **底部抬高** = 多头控盘（Higher Lows）
  - **顶部降低** = 空头控盘（Lower Highs）
  - 交替出现 = 力量均衡（区间震荡）

#### 技术分析要点（Volman强调）
> "底部越来越高比顶部越来越低更显著，就说明当前的市场力量是向上的。"  
> —— 原文第4584-4595行

#### YTC映射
= **CPB的高级版本** + **多层次结构确认**
- ARB的头肩底 = YTC的"复杂形态"
- 底部排列分析 = YTC的"趋势强度判断"
- **A股适配**：作为**pas_cpb的形态识别增强**

---

## 3. 临界点技术（Critical Point Technique）—— 核心风险管理

### 3.1 核心定义（Volman第14章）

> "临界点构成了我们出场策略的核心，因此属于适当交易管理中最基础的部分。"  
> —— 原文第10018-10019行

**临界点（Critical Point）**：
- 定义：交易有效性的最后防线，**突破1个点即止损**
- 特征：始终位于关键技术点位（支撑/阻力、结构极值）
- 作用：保护交易，避免"明显已经变糟糕的头寸"继续亏损

### 3.2 移动止损规则（动态临界点）

#### 黄金法则
1. **目标价格永远不变**（10点，对应A股的固定盈亏比）
2. **止损只能朝目标方向移动**（减小风险），决不能反向扩大
3. **移动前提**：新临界点必须经过**技术确认**

#### 技术确认流程（必须等待突破）
```
入场后价格回撤 → 形成新的极值点（最低点/最高点）
→ 等待下一根K线突破这个极值（确认反转）
→ 将临界点移到回撤极值处

❌ 错误：回撤出现最低点，立即移动止损 → 容易被"洗出"
✅ 正确：等最低点被向上突破，确认反转后再移动
```

#### 示例（做多交易）
```
入场价：100元
初始临界点：95元（信号K线最低点-1元）

情况1：价格涨到105元后回撤到102元
→ 等待：下一根K线突破102元的最高点
→ 确认后：临界点移至102元（锁定利润）

情况2：回撤到102元后继续跌破102元
→ 不移动临界点，保持95元
→ 原因：回撤未被确认反转，可能继续下跌
```

### 3.3 特殊情况：±1点的技术保障

**何时增加1点保障**：
- 临界点位于重大技术点位**1点之下/之上**
- 目的：避免在关键价位附近被"震出"

**示例**（Volman原文第10378-10400行）：
```
BB结构最低点：100.01元
DD结构最低点：100.00元（更关键的技术点位）

方案1（激进）：临界点 = 100.00元（止损6点）
方案2（保守）：临界点 = 99.99元（止损7点，增加1点保障）

选择方案2的理由：
- 100.00是所有短期走势图都能看到的关键点
- 大量多头止损设在100.00下方
- 增加1点容错，提高成功率
```

### 3.4 常见错误

#### 错误1：过早止损
**表现**：临界点刚被触及（未突破）就立即出场

**后果**：
- 错失价格在临界点反弹的机会
- 关键支撑位常能守住（场外多头愿意在此入场）

**正确做法**（Volman第10441-10467行）：
> "在价格刚刚触及临界点的时候就按下出场键，是交易者可以做得最糟糕的事情。正确的出场时机是在市场真正跌破了这个临界点（X）。"

#### 错误2：盈亏平衡出场
**定义**：价格回到入场价附近就出场，"保本"心态

**问题**：
- 入场价通常是关键技术点位（突破点）
- 聪明的多头会在此价位买入，而非卖出
- 过早出场 = 放弃了高概率盈利机会

**识别盈亏平衡陷阱**：
- BB结构信号线 = 不应设为临界点（这是支撑位）
- 区间边线 = 不应设为临界点（可能被测试）

### 3.5 临界点与20EMA的关系

**黄金法则**（Volman第10889-10900行）：
> "低于20期EMA的价格顶部（做空情况下）和高于20期EMA的价格底部（做多情况下），都应该密切留意它们的显著性，这是一个黄金法则，但绝不是一条铁律。"

**实践建议**：
- 做多：很少在20EMA**上方**止损（除非有其他技术理由）
- 做空：很少在20EMA**下方**止损
- 原因：EMA区域是回撤目标区，不是止损区

### 3.6 A股T+1适配方案

由于A股T+1无法日内止损，EmotionQuant的临界点技术需要适配为：

#### 方案1：预设止损价（在Broker模块）
```python
# broker/risk.py
class PositionRisk:
    def calculate_stop_loss(self, entry_price, signal_type):
        """
        根据信号类型预设止损价
        """
        if signal_type == "PAS_BPB":
            # BPB：止损在回调低点-1%
            stop_loss = entry_price * 0.94  # 假设6%止损
        elif signal_type == "PAS_TST":
            # TST：止损在support_level-1%
            stop_loss = self.support_level * 0.99
        
        return stop_loss
    
    def update_stop_loss(self, current_price, position):
        """
        收盘后更新止损价（模拟临界点移动）
        """
        if current_price > position.entry_price * 1.05:  # 盈利>5%
            # 移动止损到盈亏平衡点上方
            new_stop = position.entry_price * 1.02
            position.stop_loss = max(position.stop_loss, new_stop)
```

#### 方案2：策略退化检测（在Report模块）
```python
# reporter/warnings.py
def check_critical_point_breach(positions):
    """
    检测是否突破临界点（次日开盘检查）
    """
    warnings = []
    for pos in positions:
        if pos.current_price < pos.stop_loss:
            warnings.append({
                'type': 'CRITICAL_BREACH',
                'code': pos.code,
                'action': 'CLOSE_ASAP',  # 开盘立即平仓
                'reason': f'Price breached critical point: {pos.stop_loss}'
            })
    return warnings
```

---

## 4. 不利市场条件识别（第15章）

### 4.1 核心原则（Volman第11621-11632行）

> "要想巧妙地进行超短线交易，我们可能必须在90%的时间里都采取旁观者的立场，只有在我们经过评估后认为当前的市场力量对我们的交易有利，才能交易。这不仅意味着我们的结构要符合整体价格行为，还意味着**在通往目标价格的路上没有明显的支撑位或阻力位**。"

### 4.2 不利条件检查清单

#### 1. 前方阻力位/支撑位
| 类型 | 识别方法 | 风险等级 |
|------|---------|---------|
| **整数位** | 价格接近X.00/X.50（如1.3150） | 高 |
| **聚集K线** | 前期密集成交区（3根以上K线重叠） | 高 |
| **双顶/双底** | 两个相等极值点 | 中 |
| **三重顶/底** | 三个相等极值点 | 极高 |
| **前高/前低** | N日内的最高点/最低点 | 中 |

#### 2. 冲击效应（Momentum Effect）
**定义**：价格从底部/顶部快速暴涨/暴跌，突破所有阻力

**识别特征**：
- 单边长蜡烛线连续出现（3根以上）
- 突破幅度>10%（A股）或>20点（外汇）
- 没有明显回撤（直线冲击）

**风险**：
- 大玩家可能精确抓顶/抓底，设置陷阱
- 逆势交易者会在极值点激进入场
- 回撤概率极高

**应对**：放弃冲击后的**第一次回撤**，等待40-60%回撤后再考虑

#### 3. 真空效应（Vacuum Effect）
**定义**：价格突破区间边线后，**未测试**前一个整数位，留下"真空地带"

**识别**：
```
当前价格：1.3170
前一个整数位：1.3100（未被测试）
→ 真空地带：1.3100-1.3170
```

**风险**：
- 缺乏"跟进动作"（场外多头等待更低价位）
- 价格容易被吸回真空区
- 做多信号强度打折扣

**应对**：等待价格回测整数位后再入场

#### 4. 不利的结构位置
| 情况 | 描述 | 风险评估 |
|------|------|---------|
| DD在阻力位下方 | 双十字星触发点接近前高 | 放弃或等待更强蓄力 |
| FB冲击后首次回撤 | 暴涨后立即回调 | 放弃，等第2次回撤（SB） |
| BB箱体过小 | 箱体宽度<2点（A股<1%） | 蓄力不足，放弃 |
| RB捉弄式突破 | 从中部冲击边线，无挤压 | 假突破概率高，放弃 |

### 4.3 市场力量评估矩阵

#### 整体市场状况评分（-3到+3）
```python
def evaluate_market_conditions(df, direction='long'):
    """
    评估市场条件是否有利
    返回：score (-3到+3), details
    """
    score = 0
    details = []
    
    # 1. 底部/顶部排列 (+2/-2)
    recent_lows = get_recent_lows(df, n=5)
    if direction == 'long':
        if is_higher_lows(recent_lows):
            score += 2
            details.append("Higher Lows: 底部抬高 +2")
        elif is_lower_lows(recent_lows):
            score -= 2
            details.append("Lower Lows: 底部降低 -2")
    
    # 2. 前方阻力/支撑 (-1 to -3)
    resistance_distance = get_resistance_distance(df, direction)
    if resistance_distance < 0.03:  # 3%以内
        if resistance_strength == 'strong':  # 三重顶等
            score -= 3
            details.append("Strong Resistance nearby -3")
        else:
            score -= 1
            details.append("Resistance nearby -1")
    
    # 3. 真空效应 (-1)
    if has_vacuum_below(df) and direction == 'long':
        score -= 1
        details.append("Vacuum Effect below -1")
    
    # 4. 冲击效应 (-2)
    if recent_momentum_spike(df):
        score -= 2
        details.append("Recent Momentum Spike -2")
    
    # 5. EMA位置 (+1/-1)
    if direction == 'long' and df['close'].iloc[-1] > df['ma20'].iloc[-1]:
        score += 1
        details.append("Above MA20 +1")
    
    return score, details

# 使用
score, details = evaluate_market_conditions(df, direction='long')
if score < 0:
    print("不利市场条件，放弃交易")
    print("\n".join(details))
```

### 4.4 A股特殊考虑

#### 涨跌停限制
- **接近涨停**（>9%）：极高风险，放弃做多
- **接近跌停**（<-9%）：极高风险，放弃做空
- 原因：T+1无法止损，涨跌停次日可能开盘一字板

#### 整数心理价位（A股特有）
- 10元、20元、50元、100元 = 强力支撑/阻力
- 9.99元、19.99元 = 心理关口
- 优先级高于Volman的"20点整数位"

---

## 5. 与YTC五形态的完整映射表

| YTC形态 | Volman结构 | 映射关系 | 优先级 | 实现阶段 |
|---------|-----------|---------|--------|---------|
| **BPB** | FB + IRB杯柄 | FB=首次回调突破<br>杯柄=K线质量细节 | MVP | Week 2 |
| **PB** | FB（非首次）+ IRB | 简单回调=FB变种<br>边线反弹=IRB | 2nd | Week 3 |
| **TST** | DD + SB | 双十字星=测试信号<br>二次突破=二次测试 | 3rd | Week 4 |
| **BOF** | RB假突破 | 假突破识别=BOF入场 | 3rd | Week 4 |
| **CPB** | SB + ARB | M/W形态=复杂回调<br>头肩底=高级形态 | 3rd | Week 4 |

---

## 6. EmotionQuant 具体适配方案

### 6.1 在PAS模块中增强信号识别

#### pas_bpb.py 增强
```python
from typing import Optional, Tuple
import pandas as pd
from datetime import date

class BpbDetector(PatternDetector):
    name = "bpb"
    
    def detect(self, df: pd.DataFrame, code: str, signal_date: date) -> Optional[Signal]:
        """
        BPB检测，融合Volman的FB+IRB思想
        """
        # === 原有BPB观测 ===
        close = df.loc[signal_date, 'adj_close']
        high_Nd = df.iloc[:-1].tail(config.PAS_BPB_LOOKBACK)['adj_high'].max()
        low_Nd = df.iloc[:-1].tail(config.PAS_BPB_LOOKBACK)['adj_low'].min()
        
        price_position = (close - low_Nd) / (high_Nd - low_Nd)
        volume_ratio = df.loc[signal_date, 'volume'] / df.loc[signal_date, 'volume_ma20']
        breakout_strength = (close - high_Nd) / high_Nd
        
        # === Volman增强 ===
        # 1. FB首次回撤检测
        is_first_pullback = self._check_first_pullback(df, signal_date)
        
        # 2. IRB杯柄形态检测
        has_cup_handle, handle_strength = self._detect_cup_handle(df, signal_date)
        
        # 3. 市场条件评估
        market_score, _ = self._evaluate_market_conditions(df, direction='long')
        
        # === 触发条件（Volman的40-60%回撤） ===
        pullback_depth = 1 - price_position  # 0.4~0.6为佳
        
        if not (price_position > 0.8 and volume_ratio > 1.5 and breakout_strength > 0):
            return None
        
        # 放弃不利市场条件
        if market_score < -1:
            return None
        
        # === strength计算（融合Volman的K线质量） ===
        # 原始strength
        base_strength = (
            0.4 * self._normalize(breakout_strength, 0, 0.1) +
            0.3 * self._normalize(volume_ratio, 1.0, 3.0) +
            0.3 * self._body_ratio(df, signal_date)
        )
        
        # Volman增强系数
        multiplier = 1.0
        if is_first_pullback:
            multiplier *= 1.2  # 首次回撤+20%
        if has_cup_handle:
            multiplier *= 1.3  # 杯柄形态+30%
        if 0.4 <= pullback_depth <= 0.6:
            multiplier *= 1.1  # 理想回撤深度+10%
        if market_score > 1:
            multiplier *= 1.1  # 有利市场条件+10%
        
        final_strength = min(base_strength * multiplier, 1.0)
        
        return Signal(
            code=code,
            date=signal_date,
            direction='BUY',
            reason_code='PAS_BPB',
            strength=final_strength,
            observations={
                'price_position': price_position,
                'volume_ratio': volume_ratio,
                'breakout_strength': breakout_strength,
                'pullback_depth': pullback_depth,
                'is_first_pullback': is_first_pullback,
                'has_cup_handle': has_cup_handle,
                'market_score': market_score
            }
        )
    
    def _check_first_pullback(self, df, signal_date) -> bool:
        """检测是否首次回撤（Volman FB条件3）"""
        # 简化版：检查前20日是否有过ma20下方→上方的穿越
        recent = df.tail(20)
        crossovers = (recent['adj_close'] > recent['ma20']).diff()
        return crossovers.sum() <= 1  # 只有1次穿越=首次回撤
    
    def _detect_cup_handle(self, df, signal_date) -> Tuple[bool, float]:
        """检测杯柄形态（Volman IRB核心）"""
        recent = df.tail(20)
        
        # 茶杯：先跌后涨
        cup_low = recent['adj_low'].min()
        cup_left = recent.iloc[:10]['adj_close'].mean()
        cup_right = recent.iloc[-5:]['adj_close'].mean()
        is_cup = (cup_right > cup_low * 1.02) and (cup_left > cup_low * 1.02)
        
        # 手柄：最后3-5根K线的窄幅震荡
        handle = recent.tail(5)
        handle_width = (handle['adj_high'].max() - handle['adj_low'].min()) / handle['adj_low'].min()
        is_handle = handle_width < 0.03
        
        # 手柄在ma20附近
        near_ma20 = abs(handle['adj_close'].iloc[-1] - handle['ma20'].iloc[-1]) / handle['ma20'].iloc[-1] < 0.02
        
        if is_cup and is_handle and near_ma20:
            return True, 0.3  # 返回强度加成
        return False, 0.0
    
    def _evaluate_market_conditions(self, df, direction) -> Tuple[int, list]:
        """评估市场条件（Volman第15章）"""
        score = 0
        details = []
        
        recent = df.tail(10)
        lows = recent['adj_low'].values
        
        # 底部抬高检测
        if all(lows[i] >= lows[i-1] * 0.99 for i in range(1, len(lows))):
            score += 2
            details.append("Higher Lows +2")
        
        # 前方阻力检测（简化：检查前高）
        current = df['adj_close'].iloc[-1]
        prev_high = df.iloc[-20:-1]['adj_high'].max()
        if current > prev_high * 0.97:  # 接近前高
            score -= 2
            details.append("Near Resistance -2")
        
        return score, details
```

### 6.2 在Broker模块实现临界点管理

#### broker/risk.py
```python
class CriticalPointManager:
    """
    临界点管理器（Volman第14章适配）
    由于A股T+1，只能在收盘后更新，次日开盘执行
    """
    
    def __init__(self):
        self.positions = {}  # {code: PositionInfo}
    
    def set_initial_critical_point(self, position):
        """
        设置初始临界点（入场时）
        """
        if position.signal_type == 'PAS_BPB':
            # BPB：临界点在回调低点-1%
            lookback_low = position.entry_data['pullback_low']
            position.critical_point = lookback_low * 0.99
        
        elif position.signal_type == 'PAS_TST':
            # TST：临界点在support_level-1%
            position.critical_point = position.entry_data['support_level'] * 0.99
        
        position.initial_stop_loss = position.critical_point
        return position.critical_point
    
    def update_critical_point(self, position, latest_bar):
        """
        更新临界点（收盘后每日执行）
        Volman规则：只能朝盈利方向移动
        """
        if position.direction == 'LONG':
            current_price = latest_bar['adj_close']
            
            # 规则1：价格回撤后反弹，形成更高低点
            if current_price > position.entry_price * 1.05:  # 盈利>5%
                recent_low = self._get_recent_pullback_low(position, latest_bar)
                
                if recent_low and recent_low > position.critical_point:
                    # 等待反弹确认（Volman技术确认）
                    if self._confirm_reversal(position, latest_bar):
                        old_cp = position.critical_point
                        position.critical_point = recent_low * 0.99  # 低点-1%
                        
                        logging.info(
                            f"临界点移动: {position.code} "
                            f"{old_cp:.2f} -> {position.critical_point:.2f}"
                        )
        
        return position.critical_point
    
    def check_breach(self, position, current_price) -> bool:
        """
        检测是否突破临界点（次日开盘检查）
        """
        if position.direction == 'LONG':
            return current_price < position.critical_point
        else:
            return current_price > position.critical_point
    
    def _confirm_reversal(self, position, latest_bar) -> bool:
        """
        确认反转（Volman规则：回撤低点必须被向上突破）
        """
        # 简化版：检查最新K线是否突破前一根K线高点
        prev_high = position.price_history[-2]['adj_high']
        current_close = latest_bar['adj_close']
        return current_close > prev_high
```

### 6.3 在Reporter模块增加不利条件预警

#### reporter/warnings.py
```python
def generate_adverse_condition_warnings(positions, market_data):
    """
    生成不利市场条件预警（Volman第15章）
    """
    warnings = []
    
    for pos in positions:
        df = market_data[pos.code]
        current_price = df['adj_close'].iloc[-1]
        
        # 1. 前方阻力位预警
        resistance = find_nearest_resistance(df, current_price)
        if resistance and (resistance - current_price) / current_price < 0.03:
            warnings.append({
                'level': 'WARNING',
                'code': pos.code,
                'type': 'RESISTANCE_AHEAD',
                'message': f'接近阻力位 {resistance:.2f}，距离 {(resistance/current_price-1)*100:.1f}%',
                'action': 'CONSIDER_TAKE_PROFIT'
            })
        
        # 2. 冲击效应预警（连续大阳线后）
        momentum_spike = detect_momentum_spike(df)
        if momentum_spike and pos.holding_days < 3:
            warnings.append({
                'level': 'CAUTION',
                'code': pos.code,
                'type': 'MOMENTUM_SPIKE',
                'message': '入场前存在冲击效应，回撤风险高',
                'action': 'TIGHTEN_STOP_LOSS'
            })
        
        # 3. 真空效应预警
        if has_vacuum_below(df, current_price):
            warnings.append({
                'level': 'INFO',
                'code': pos.code,
                'type': 'VACUUM_EFFECT',
                'message': '下方存在未测试整数位，缺乏支撑',
                'action': 'MONITOR_CLOSELY'
            })
    
    return warnings
```

---

## 7. 实施优先级与时间表

### MVP阶段（Week 2）：PAS_BPB + Volman核心
- [x] FB结构逻辑（首次回撤判断）
- [x] IRB杯柄形态检测（基础版）
- [x] 市场条件评估（简化版：阻力位+底部排列）
- [ ] strength加权系数

### 2nd迭代（Week 3）：PAS_PB + BB增强
- [ ] FB变种（非首次回撤）
- [ ] BB箱体检测（用于所有形态的信号强化）
- [ ] 不利条件预警（阻力位、冲击效应）

### 3rd迭代（Week 4）：TST/BOF/CPB + 临界点技术
- [ ] DD结构（双十字星识别）
- [ ] SB结构（M/W形态检测）
- [ ] RB假突破识别（BOF入场）
- [ ] 临界点动态管理（在Broker模块）
- [ ] ARB高级形态（头肩底等）

---

## 8. 参考文献

1. **Bob Volman**. *Forex Price Action Scalping*（外汇超短线交易：技术、结构和价格行为原理）. 山西人民出版社, 2017.
   - 第7-13章：7种结构完整定义
   - 第14章：临界点技术
   - 第15章：不利市场条件识别

2. **Lance Beggs**. *YTC Price Action Trader* 卷2-4.
   - 卷2：市场结构理论（MSS）
   - 卷3：五种架构（TST/BOF/BPB/PB/CPB）
   - 卷4：资金管理

3. **EmotionQuant-gamma 设计文档**:
   - `docs/design-v2/01-system/architecture-master.md` §4.3 PAS模块
   - `plans/7f7d1b26-e7b6-444d-a6f2-607720c2488c` PAS+Strategy实现计划

---

**文档状态**：已完成  
**下一步行动**：将此映射关系写入 `architecture-master.md` §4.3.8

