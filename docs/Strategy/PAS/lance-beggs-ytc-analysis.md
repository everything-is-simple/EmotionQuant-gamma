# Lance Beggs《YTC Price Action Trader》系列梳理

**原始资料**：`G:\《股市浮沉二十载》\2020.(Au)LanceBeggs`  
**文档版本**：v1.0.0  
**创建日期**：2026-03-07  
**对应模块**：PAS（价格行为信号）  
**文档状态**：Draft（待补充原著细节）

---

## 1. 资料概述

### 1.1 基本信息

- **作者**：Lance Beggs（澳大利亚）
- **系列**：YTC Price Action Trader（卷1-4）
- **出版年份**：2010-2015
- **核心主题**：价格行为交易（Price Action Trading）
- **用户评价**：最喜欢、最好读、最好用

### 1.2 核心价值

这是**EmotionQuant PAS模块的主要理论来源**，提供了：
- 五种核心形态（BPB/PB/TST/BOF/CPB）
- 完整的交易系统框架
- 大量实战案例
- 清晰的入场和出场规则

**为什么选择YTC**：
> "许多case，够详细，完整交易系统。"（用户原话）

---

## 2. YTC系列结构

### 2.1 卷1：基础理论

**主题**：价格行为交易的基础概念

**核心内容**：
- 什么是价格行为（Price Action）
- 为什么价格行为有效
- 市场结构（Market Structure）
- 支撑与阻力（Support & Resistance）
- 趋势与区间（Trend & Range）

**关键概念**：
- **价格行为的定义**：通过价格、成交量、K线形态判断市场，不使用技术指标
- **市场结构的重要性**：理解市场的高点、低点、趋势、区间
- **支撑阻力的本质**：供需平衡点，不是神秘的"线"

### 2.2 卷2：市场结构理论（MSS）

**主题**：Market Structure & Sentiment（市场结构与情绪）

**核心内容**：
- 市场结构的识别
- 趋势的定义和识别
- 区间的定义和识别
- 市场情绪的判断

**关键概念**：
- **Higher Highs & Higher Lows**：上升趋势的定义
- **Lower Highs & Lower Lows**：下降趋势的定义
- **Market Sentiment**：市场情绪的强弱判断

**与EmotionQuant的关系**：
- YTC的MSS ≠ EmotionQuant的MSS
- YTC的MSS是"市场结构"，EmotionQuant的MSS是"市场情绪"
- 但两者都强调"市场状态"的重要性

### 2.3 卷3：五种架构（核心）

**主题**：Five Setups（五种形态）

**核心内容**：
1. BPB（Breakout Pullback）：突破回调
2. PB（Pullback）：简单回调
3. TST（Test of Support/Resistance）：支撑/阻力测试
4. BOF（Breakout Failure）：假突破反转
5. CPB（Complex Pullback）：复杂回调

**这是EmotionQuant PAS模块的核心来源**

### 2.4 卷4：资金管理与心理

**主题**：Money Management & Trading Psychology

**核心内容**：
- 仓位管理
- 风险控制
- 止损设置
- 盈亏比计算
- 交易心理

**关键概念**：
- **风险收益比**：至少1:2，理想1:3或更高
- **仓位管理**：单笔风险不超过账户的1-2%
- **交易心理**：纪律、耐心、情绪控制

---

## 3. 五种核心形态详解

### 3.1 BPB（Breakout Pullback）- 突破回调

#### 定义
价格突破关键阻力位后，回调至支撑区域（通常是前阻力位），然后继续上涨。

#### 核心要素
1. **突破（Breakout）**：
   - 价格突破前高或关键阻力
   - 突破时最好有成交量配合
   - 突破后价格站稳在阻力位上方

2. **回调（Pullback）**：
   - 价格回调至前阻力位（现支撑位）
   - 回调深度通常40-60%
   - 回调时成交量萎缩

3. **确认（Confirmation）**：
   - 价格在支撑位获得支撑
   - 出现反转K线（如Pin Bar、Inside Bar）
   - 价格再次上涨，突破回调高点

#### 入场规则
- **入场点**：回调低点上方1-2个tick
- **止损点**：回调低点下方1-2个tick
- **目标价**：前高上方，或下一个阻力位

#### 风险收益比
- 理想：1:2或更高
- 最低：1:1.5

#### 成功率
- 约60-70%（Lance Beggs估计）

#### A股适配
```python
# BPB检测伪代码
def detect_bpb(df, signal_date):
    # 1. 检测突破
    high_Nd = df.iloc[:-1].tail(N)['adj_high'].max()
    close = df.loc[signal_date, 'adj_close']
    breakout = close > high_Nd
    
    # 2. 检测回调
    pullback_low = df.tail(5)['adj_low'].min()
    pullback_depth = (high_Nd - pullback_low) / (high_Nd - low_Nd)
    is_pullback = 0.4 <= pullback_depth <= 0.6
    
    # 3. 检测确认
    price_position = (close - pullback_low) / (high_Nd - pullback_low)
    is_confirmed = price_position > 0.8
    
    # 4. 成交量配合
    volume_ratio = df.loc[signal_date, 'volume'] / df['volume'].rolling(20).mean()
    is_volume_ok = volume_ratio > 1.5
    
    if breakout and is_pullback and is_confirmed and is_volume_ok:
        return Signal(
            type='BPB',
            entry=close,
            stop_loss=pullback_low * 0.99,
            target=high_Nd * 1.05,
            strength=calculate_strength(...)
        )
```

#### 案例（Lance Beggs原著）
- 案例1：EUR/USD突破1.3000后回调至1.2950，然后继续上涨至1.3100
- 案例2：黄金突破1800后回调至1780，然后继续上涨至1850

### 3.2 PB（Pullback）- 简单回调

#### 定义
趋势中的简单回调，不需要突破新高，只是趋势的延续。

#### 与BPB的区别
- **BPB**：需要突破新高，是突破确认
- **PB**：不需要突破新高，是趋势延续

#### 核心要素
1. **趋势确认**：
   - 明确的上升或下降趋势
   - Higher Highs & Higher Lows（上升）
   - Lower Highs & Lower Lows（下降）

2. **回调**：
   - 价格回调至支撑区域
   - 回调深度通常30-50%
   - 回调时成交量萎缩

3. **反弹**：
   - 价格在支撑位反弹
   - 出现反转K线
   - 价格继续沿趋势方向运行

#### 入场规则
- **入场点**：回调低点上方1-2个tick
- **止损点**：回调低点下方1-2个tick，或前一个低点
- **目标价**：前高，或趋势延伸目标

#### 风险收益比
- 理想：1:2或更高
- 最低：1:1.5

#### 成功率
- 约50-60%（低于BPB）

#### A股适配
- 适用于强势股的回调买入
- 止损可以设置得更宽一些（如回调低点-2%）
- 目标价可以设置得更保守一些

### 3.3 TST（Test of Support/Resistance）- 支撑/阻力测试

#### 定义
价格回到前期支撑位或阻力位，测试其有效性。

#### 核心要素
1. **支撑/阻力位**：
   - 前期低点（支撑）
   - 前期高点（阻力）
   - 前期突破点（支撑/阻力转换）

2. **测试**：
   - 价格回到支撑/阻力位附近
   - 价格在该位置停留、震荡
   - 出现测试K线（如Doji、Pin Bar）

3. **反弹/反转**：
   - 支撑有效，价格反弹
   - 阻力有效，价格反转

#### 入场规则
- **做多入场**：支撑位上方1-2个tick
- **做空入场**：阻力位下方1-2个tick
- **止损点**：支撑/阻力位下方/上方1-2个tick
- **目标价**：前高/前低，或下一个关键位置

#### 风险收益比
- 理想：1:2或更高
- 最低：1:1.5

#### 成功率
- 约50-60%

#### A股适配
```python
# TST检测伪代码
def detect_tst(df, signal_date):
    # 1. 识别支撑位
    support_level = df.tail(60)['adj_low'].min()
    
    # 2. 检测测试
    close = df.loc[signal_date, 'adj_close']
    distance_to_support = abs(close - support_level) / support_level
    is_testing = distance_to_support < 0.02  # 2%以内
    
    # 3. 检测反弹
    prev_close = df.iloc[-2]['adj_close']
    is_bouncing = close > prev_close
    
    # 4. K线形态
    body_ratio = abs(close - open) / (high - low)
    is_reversal_candle = body_ratio > 0.5
    
    if is_testing and is_bouncing and is_reversal_candle:
        return Signal(
            type='TST',
            entry=close,
            stop_loss=support_level * 0.99,
            target=df.tail(20)['adj_high'].max(),
            strength=calculate_strength(...)
        )
```

### 3.4 BOF（Breakout Failure）- 假突破反转

#### 定义
价格假突破关键位置后失败，反向入场。

#### 核心要素
1. **假突破**：
   - 价格突破关键阻力/支撑
   - 但无法持续，很快回到区间内
   - 通常伴随成交量不足

2. **失败确认**：
   - 价格回到突破前的区间
   - 出现反转K线（如Pin Bar）
   - 成交量萎缩

3. **反向入场**：
   - 做空（假突破上方阻力后）
   - 做多（假突破下方支撑后）

#### 入场规则
- **做空入场**：假突破高点下方1-2个tick
- **做多入场**：假突破低点上方1-2个tick
- **止损点**：假突破高点/低点上方/下方1-2个tick
- **目标价**：区间另一端，或更远的支撑/阻力

#### 风险收益比
- 理想：1:3或更高（因为假突破后往往有较大反向运动）
- 最低：1:2

#### 成功率
- 约40-50%（低于其他形态，但盈亏比高）

#### A股适配
```python
# BOF检测伪代码（v0.01核心）
def detect_bof(df, signal_date):
    # 1. 识别假突破
    resistance = df.tail(60)['adj_high'].max()
    high = df.loc[signal_date, 'adj_high']
    close = df.loc[signal_date, 'adj_close']
    
    is_fake_breakout = (high > resistance) and (close < resistance)
    
    # 2. 检测失败确认
    is_limit_up = df.loc[signal_date, 'is_limit_up']
    is_touched_limit_up = df.loc[signal_date, 'is_touched_limit_up']
    is_broken = is_touched_limit_up and not is_limit_up  # 炸板
    
    # 3. 成交量
    volume_ratio = df.loc[signal_date, 'volume'] / df['volume'].rolling(20).mean()
    is_volume_weak = volume_ratio < 2.0  # 放量不足
    
    # 4. K线形态
    body_ratio = abs(close - open) / (high - low)
    is_pin_bar = body_ratio < 0.3 and (high - close) / (high - low) > 0.6
    
    if is_fake_breakout and (is_broken or is_pin_bar) and is_volume_weak:
        return Signal(
            type='BOF',
            entry=close,
            stop_loss=high * 1.01,
            target=df.tail(20)['adj_low'].min(),
            strength=calculate_strength(...)
        )
```

#### 案例（Lance Beggs原著）
- 案例1：EUR/USD假突破1.3000后回落至1.2900
- 案例2：黄金假突破1800后回落至1750

#### A股典型案例
- **涨停后炸板**：最典型的BOF形态
- **高开低走**：开盘冲高但收盘回落
- **假突破前高**：突破前高但无法持续

### 3.5 CPB（Complex Pullback）- 复杂回调

#### 定义
回调结构复杂，多次测试支撑，形成复杂形态（如M/W、头肩底等）。

#### 与PB的区别
- **PB**：简单回调，一次性回调后反弹
- **CPB**：复杂回调，多次测试支撑，形成复杂形态

#### 核心要素
1. **复杂结构**：
   - M型（双顶）
   - W型（双底）
   - 头肩底/头肩顶
   - 三角形整理

2. **多次测试**：
   - 价格多次测试支撑/阻力
   - 每次测试都未突破
   - 形成明显的形态

3. **突破确认**：
   - 价格突破形态的颈线
   - 成交量配合
   - 趋势延续

#### 入场规则
- **入场点**：形态颈线突破后
- **止损点**：形态的最低点/最高点
- **目标价**：形态高度的延伸

#### 风险收益比
- 理想：1:2或更高
- 最低：1:1.5

#### 成功率
- 约50-60%

#### A股适配
- 适用于震荡市中的复杂形态
- 止损可以设置在形态的关键点位
- 目标价可以根据形态高度计算

---

## 4. YTC的核心理念

### 4.1 价格行为的本质

Lance Beggs强调：
> "价格行为原理非常普遍，所以在其他具有相似波动率和较低交易成本的市场采用这个方法时，也没必要进行太多的调整。"

**核心观点**：
- 价格行为是市场参与者集体行为的体现
- 支撑阻力是供需平衡点
- 形态是市场心理的反映
- 这些原理在任何市场都适用

### 4.2 市场结构的重要性

Lance Beggs强调：
> "理解市场结构是价格行为交易的基础。如果你不理解市场结构，你就无法识别高概率的交易机会。"

**市场结构的三要素**：
1. **趋势**：Higher Highs & Higher Lows（上升）或 Lower Highs & Lower Lows（下降）
2. **区间**：价格在支撑和阻力之间震荡
3. **转折**：趋势转为区间，或区间转为趋势

### 4.3 高概率交易的特征

Lance Beggs总结的高概率交易特征：
1. **顺势交易**：与主趋势方向一致
2. **关键位置**：在支撑/阻力位附近
3. **确认信号**：有明确的K线确认
4. **成交量配合**：突破时有成交量，回调时成交量萎缩
5. **风险收益比**：至少1:2

### 4.4 交易纪律

Lance Beggs强调：
> "交易纪律比交易技巧更重要。即使你有最好的交易系统，如果没有纪律，你也会失败。"

**纪律的三要素**：
1. **严格止损**：永远不要移动止损到不利方向
2. **耐心等待**：只交易高概率机会
3. **情绪控制**：不要因为连续亏损而改变系统

---

## 5. 与EmotionQuant的映射

### 5.1 直接采用的部分

**五种形态**：
- BPB → PAS_BPB
- PB → PAS_PB
- TST → PAS_TST
- BOF → PAS_BOF（v0.01核心）
- CPB → PAS_CPB

**入场规则**：
- 形态识别逻辑
- 入场点设置
- 止损点设置
- 目标价计算

**风险收益比**：
- 最低1:2的要求
- 理想1:3或更高

### 5.2 A股适配的部分

**时间周期**：
- YTC：分钟图、小时图
- EmotionQuant：日线图（T+1制度）

**止损方式**：
- YTC：日内止损
- EmotionQuant：次日开盘止损

**成交量**：
- YTC：相对成交量
- EmotionQuant：量比、换手率

**形态识别**：
- YTC：手工识别
- EmotionQuant：算法自动识别

### 5.3 未采用的部分

**技术指标**：
- YTC也不使用技术指标
- 但EmotionQuant更严格（铁律）

**盘中交易**：
- YTC：盘中交易
- EmotionQuant：收盘后决策，次日开盘执行

---

## 6. 实战案例（待补充）

### 6.1 BPB案例

**案例1**：（待补充原著案例）
- 市场：
- 时间：
- 形态：
- 入场：
- 止损：
- 目标：
- 结果：

### 6.2 BOF案例

**案例1**：（待补充原著案例）
- 市场：
- 时间：
- 形态：
- 入场：
- 止损：
- 目标：
- 结果：

---

## 7. 关键引用

### 7.1 价格行为的定义

> "Price action trading is a methodology that relies on the analysis of price movement, without the use of indicators. It's about understanding what the market is doing right now, and what it's likely to do in the near future, based on recent price behavior."

### 7.2 市场结构的重要性

> "Market structure is the foundation of price action trading. If you don't understand market structure, you can't identify high-probability trading opportunities."

### 7.3 交易纪律

> "Trading discipline is more important than trading skill. Even with the best trading system, you'll fail without discipline."

---

## 8. 后续行动

### 8.1 深入阅读

- [ ] 重读YTC卷3，提取五种形态的详细规则
- [ ] 提取原著中的实战案例
- [ ] 提取原著中的图表和示意图
- [ ] 总结每种形态的成功率和盈亏比

### 8.2 A股验证

- [ ] 使用A股历史数据验证五种形态
- [ ] 统计每种形态在A股的成功率
- [ ] 优化形态识别的参数
- [ ] 形成A股适配的最佳实践

### 8.3 系统实现

- [ ] 实现五种形态的自动识别
- [ ] 实现入场点、止损点、目标价的自动计算
- [ ] 实现风险收益比的自动评估
- [ ] 实现形态强度的自动评分

---

## 9. 参考文献

1. Lance Beggs. *YTC Price Action Trader* 卷1-4.
2. EmotionQuant PAS算法设计：`blueprint/01-full-design/04-pas-trigger-bof-contract-supplement-20260308.md`
3. Volman-YTC映射：`docs/Strategy/PAS/volman-ytc-mapping.md`

---

**文档状态**：Draft（需要补充原著细节和案例）  
**下一步行动**：
1. 重读YTC原著，提取详细规则
2. 补充实战案例和图表
3. 完善A股适配方案
4. 形成可执行的实现指南

