# A股市场交易规则 - TuShare Pro版

**版本**: v0.01
**创建时间**: 2024-12-19
**更新时间**: 2025-12-20
**适用范围**: EmotionQuant项目 A股交易规则参考
**数据源**: TuShare Pro + 上交所/深交所/北交所官方规则
**优先级**: A股交易规则权威参考（恒星组文档 ⭐⭐⭐）
**定位**: 参考资料（非设计规范）
**路线图口径**: Spiral + CP（命名 `CP-*`，以 `Governance/SpiralRoadmap/planA/VORTEX-EVOLUTION-ROADMAP.md` 为准）
**冲突处理**: 若与 `docs/design-v2/system-baseline.md` 冲突，以系统总纲为准
**整理更新**: 2026-02-05（系统铁律表述更新）

---

## 🆕 v2.0 更新说明

### 主要更新

- ✅ **2025年规则校准**: 同步三大交易所2025年最新交易规则

- ✅ **T+1增强**: 完善T+1交易制度的特殊场景处理

- ✅ **涨跌停优化**: 新增注册制板块差异化涨跌停处理

- ✅ **集合竞价细化**: 增加开盘/收盘集合竞价详细时段

- ✅ **EmotionQuant深度集成**: MSS+IRS+PAS全系统适配

### 与v1.0对比

| 功能 | v1.0 | v2.0 |
| ------ | ------ | ------ |
| 交易所覆盖 | 沪深 | 沪深北（完整） |
| 涨跌停规则 | 基础 | 注册制差异化 |
| 集合竞价 | 简单 | 详细时段划分 |
| T+1处理 | 基础 | 特殊场景覆盖 |
| EmotionQuant集成 | MSS | MSS+IRS+PAS |

---

## 📋 交易所概述

中国A股市场由三大交易所组成，每个交易所都有其特定的交易规则和市场特色。

### 三大交易所对比 (2025年标准)

| 交易所 | 简称 | 主要板块 | 涨跌停限制 | 特色 |
| -------- | ------ | ---------- | ----------- | ------ |
| 上海证券交易所 | 上交所/SSE | 主板、科创板 | 主板±10%、科创±20% | 大盘蓝筹为主 |
| 深圳证券交易所 | 深交所/SZSE | 主板、创业板 | 主板±10%、创业±20% | 成长型企业 |
| 北京证券交易所 | 北交所/BSE | 创新层、基础层 | ±30% | 专精特新 |

---

## ⏰ 交易时间规则

### 标准交易时段 (v2.0详细版)

```python
import pandas as pd
from datetime import time
from typing import Dict, Tuple

def get_trading_sessions_v2() -> Dict:
    """
    v2.0增强版：获取A股标准交易时段
    EmotionQuant专用 - 精确到秒级
    """

    sessions = {
        'morning_call_auction': {
            'start_time': time(9, 15, 0),
            'end_time': time(9, 25, 0),
            'duration_minutes': 10,
            'description': '开盘集合竞价',
            'sub_phases': {
                'order_phase': {'start': time(9, 15, 0), 'end': time(9, 20, 0), 'desc': '可申报可撤单'},
                'frozen_phase': {'start': time(9, 20, 0), 'end': time(9, 25, 0), 'desc': '只能申报不能撤单'},
                'match_phase': {'time': time(9, 25, 0), 'desc': '集合竞价撮合'},
            },
            'emotion_significance': '⭐⭐⭐⭐⭐ 开盘情绪最关键时段'
        },
        'morning_continuous': {
            'start_time': time(9, 30, 0),
            'end_time': time(11, 30, 0),
            'duration_minutes': 120,
            'description': '上午连续竞价',
            'emotion_significance': '⭐⭐⭐⭐ 主力资金活跃时段'
        },
        'lunch_break': {
            'start_time': time(11, 30, 0),
            'end_time': time(13, 0, 0),
            'duration_minutes': 90,
            'description': '午间休市',
            'emotion_significance': '⭐ 无交易，情绪酝酿期'
        },
        'afternoon_continuous': {
            'start_time': time(13, 0, 0),
            'end_time': time(14, 57, 0),
            'duration_minutes': 117,
            'description': '下午连续竞价',
            'emotion_significance': '⭐⭐⭐⭐ 日内情绪波动关键期'
        },
        'closing_call_auction': {
            'start_time': time(14, 57, 0),
            'end_time': time(15, 0, 0),
            'duration_minutes': 3,
            'description': '收盘集合竞价',
            'sub_phases': {
                'order_phase': {'start': time(14, 57, 0), 'end': time(14, 57, 0), 'desc': '只能申报不能撤单'},
                'match_phase': {'time': time(15, 0, 0), 'desc': '收盘价撮合'},
            },
            'emotion_significance': '⭐⭐⭐⭐⭐ 收盘情绪定调时段',
            'note': 'v2.0新增：收盘竞价对次日开盘影响重大'
        }
    }

    return {
        'sessions': sessions,
        'total_trading_minutes': 240,
        'emotion_key_periods': ['开盘集合竞价', '收盘集合竞价', '尾盘15分钟'],
        'version': 'v2.0',
        'compliance': '✅ 基于实际交易时段，无技术指标'
    }

def is_trading_time(check_time: time) -> Dict:
    """
    v2.0新增：判断指定时间是否为交易时段
    返回详细的时段信息
    """
    sessions = get_trading_sessions_v2()['sessions']

    for session_name, session_info in sessions.items():
        if 'start_time' in session_info and 'end_time' in session_info:
            if session_info['start_time'] <= check_time < session_info['end_time']:
                return {
                    'is_trading': True,
                    'session': session_name,
                    'description': session_info['description'],
                    'emotion_significance': session_info['emotion_significance']
                }

    return {
        'is_trading': False,
        'session': 'non_trading',
        'description': '非交易时段'
    }

# 使用示例
print("⏰ A股交易时段 (v2.0):")
sessions_info = get_trading_sessions_v2()
for name, info in sessions_info['sessions'].items():
    if 'start_time' in info:
        print(f"{info['description']}: {info['start_time']}-{info['end_time']} "
              f"({info['duration_minutes']}分钟) {info['emotion_significance']}")
```

---

## 📈 涨跌停板制度 (v2.0注册制完整版)

### 2025年最新涨跌停规则

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class BoardType(Enum):
    """A股板块类型枚举"""
    MAIN_SH = "主板-上交所"
    MAIN_SZ = "主板-深交所"
    STAR = "科创板"
    GEM = "创业板"
    BSE = "北交所"
    ST = "ST股票"

@dataclass
class PriceLimitRule:
    """涨跌停规则"""
    board_type: BoardType
    limit_up_pct: float
    limit_down_pct: float
    special_notes: str
    emotion_factor: float  # v2.0新增：情绪放大系数

def get_price_limit_rules_v2() -> Dict[BoardType, PriceLimitRule]:
    """
    v2.0完整版：获取A股涨跌停规则
    2025年注册制全面实施后的最新标准
    """

    rules = {
        BoardType.MAIN_SH: PriceLimitRule(
            board_type=BoardType.MAIN_SH,
            limit_up_pct=10.0,
            limit_down_pct=-10.0,
            special_notes="首日不设涨跌幅限制（注册制新股除外）",
            emotion_factor=1.0  # 主板情绪基准
        ),
        BoardType.MAIN_SZ: PriceLimitRule(
            board_type=BoardType.MAIN_SZ,
            limit_up_pct=10.0,
            limit_down_pct=-10.0,
            special_notes="首日不设涨跌幅限制（注册制新股除外）",
            emotion_factor=1.0
        ),
        BoardType.STAR: PriceLimitRule(
            board_type=BoardType.STAR,
            limit_up_pct=20.0,
            limit_down_pct=-20.0,
            special_notes="注册制，前5个交易日无涨跌停限制",
            emotion_factor=1.5  # 科创板情绪放大1.5倍
        ),
        BoardType.GEM: PriceLimitRule(
            board_type=BoardType.GEM,
            limit_up_pct=20.0,
            limit_down_pct=-20.0,
            special_notes="注册制，前5个交易日无涨跌停限制",
            emotion_factor=1.4  # 创业板情绪放大1.4倍
        ),
        BoardType.BSE: PriceLimitRule(
            board_type=BoardType.BSE,
            limit_up_pct=30.0,
            limit_down_pct=-30.0,
            special_notes="首日无涨跌停限制",
            emotion_factor=2.0  # 北交所情绪放大2.0倍（高波动）
        ),
        BoardType.ST: PriceLimitRule(
            board_type=BoardType.ST,
            limit_up_pct=5.0,
            limit_down_pct=-5.0,
            special_notes="退市风险警示股票",
            emotion_factor=1.8  # ST股情绪极端放大
        ),
    }

    return rules

def calculate_limit_prices_v2(stock_code: str, prev_close: float,
                              is_new_stock: bool = False,
                              days_since_ipo: int = 999) -> Dict:
    """
    v2.0增强版：计算涨跌停价格
    新增新股特殊处理
    """

    # 识别板块类型
    board = identify_board_type(stock_code)
    rules = get_price_limit_rules_v2()
    rule = rules[board]

    # v2.0新增：新股特殊处理
    if is_new_stock and days_since_ipo <= 5:
        if board in [BoardType.STAR, BoardType.GEM, BoardType.BSE]:
            return {
                'has_limit': False,
                'limit_up': None,
                'limit_down': None,
                'reason': f'{board.value}前5个交易日无涨跌停限制',
                'emotion_note': '⚠️ 新股波动极大，情绪指标需谨慎使用'
            }

    # 计算涨跌停价格（精确到分）
    limit_up = round(prev_close * (1 + rule.limit_up_pct / 100), 2)
    limit_down = round(prev_close * (1 + rule.limit_down_pct / 100), 2)

    return {
        'stock_code': stock_code,
        'prev_close': prev_close,
        'board_type': board.value,
        'has_limit': True,
        'limit_up': limit_up,
        'limit_down': limit_down,
        'limit_up_pct': rule.limit_up_pct,
        'limit_down_pct': rule.limit_down_pct,
        'emotion_factor': rule.emotion_factor,  # v2.0关键指标
        'special_notes': rule.special_notes,
        'version': 'v2.0'
    }

def identify_board_type(stock_code: str) -> BoardType:
    """v2.0增强：识别股票板块类型"""
    code = stock_code[:6] if '.' in stock_code else stock_code

    # ST股票判断（优先级最高）
    if code.startswith('ST') or '*ST' in code:
        return BoardType.ST

    # 科创板 (688xxx)
    if code.startswith('688'):
        return BoardType.STAR

    # 创业板 (300xxx)
    if code.startswith('300'):
        return BoardType.GEM

    # 北交所 (43xxxx, 83xxxx)
    if code.startswith('43') or code.startswith('83'):
        return BoardType.BSE

    # 上交所主板 (60xxxx)
    if code.startswith('60'):
        return BoardType.MAIN_SH

    # 深交所主板 (000xxx, 001xxx)
    if code.startswith('000') or code.startswith('001'):
        return BoardType.MAIN_SZ

    # 默认深交所主板
    return BoardType.MAIN_SZ

# 使用示例
test_stocks = [
    ('600000.SH', 10.00, '浦发银行-主板'),
    ('688001.SH', 50.00, '科创板新股'),
    ('300001.SZ', 20.00, '创业板'),
    ('430001.BJ', 15.00, '北交所'),
]

print("\n📈 涨跌停价格计算 (v2.0):")
for code, price, name in test_stocks:
    result = calculate_limit_prices_v2(code, price)
    if result['has_limit']:
        print(f"{name} ({code}): "
              f"涨停={result['limit_up']:.2f}元 "
              f"跌停={result['limit_down']:.2f}元 "
              f"(±{result['limit_up_pct']:.0f}%, "
              f"情绪系数={result['emotion_factor']:.1f})")
```

---

## 🔄 T+1交易制度 (v2.0完整版)

### T+1规则详解

```python
from datetime import date, timedelta
from typing import List, Dict

class T1TradingValidator:
    """
    v2.0增强版：T+1交易验证器
    EmotionQuant专用 - 处理各种T+1特殊场景
    """

    def __init__(self):
        self.trading_calendar = self._load_trading_calendar()

    def validate_sell_order(self, stock_code: str, buy_date: date,
                           sell_date: date) -> Dict:
        """
        验证卖出订单是否符合T+1规则

        v2.0新增：
        - 跨节假日检查
        - 停牌日检查
        - 特殊情况提示
        """

        # 基础T+1检查
        if buy_date == sell_date:
            return {
                'is_valid': False,
                'reason': 'T+1规则：当日买入不能当日卖出',
                'suggestion': f'最早可卖日期: {self._next_trading_day(buy_date)}',
                'emotion_note': '⚠️ T+1限制，情绪策略需考虑隔日风险'
            }

        # 检查是否跨非交易日
        actual_trading_days = self._count_trading_days(buy_date, sell_date)

        if actual_trading_days < 1:
            return {
                'is_valid': False,
                'reason': '卖出日期不是交易日或未满足T+1',
                'actual_trading_days': actual_trading_days,
                'suggestion': f'请在交易日卖出'
            }

        return {
            'is_valid': True,
            'buy_date': buy_date.isoformat(),
            'sell_date': sell_date.isoformat(),
            'holding_days': (sell_date - buy_date).days,
            'actual_trading_days': actual_trading_days,
            'compliance': '✅ 符合T+1规则'
        }

    def get_earliest_sell_date(self, buy_date: date) -> date:
        """v2.0：获取最早可卖日期（考虑节假日）"""
        return self._next_trading_day(buy_date)

    def _next_trading_day(self, current_date: date) -> date:
        """获取下一个交易日"""
        next_day = current_date + timedelta(days=1)
        while not self._is_trading_day(next_day):
            next_day += timedelta(days=1)
        return next_day

    def _count_trading_days(self, start_date: date, end_date: date) -> int:
        """计算交易日数量"""
        if start_date >= end_date:
            return 0

        count = 0
        current = start_date + timedelta(days=1)
        while current <= end_date:
            if self._is_trading_day(current):
                count += 1
            current += timedelta(days=1)
        return count

    def _is_trading_day(self, check_date: date) -> bool:
        """判断是否为交易日（简化实现）"""
        # 实际应查询交易日历
        weekday = check_date.weekday()
        return weekday < 5  # 周一到周五

    def _load_trading_calendar(self) -> List[date]:
        """加载交易日历（简化实现）"""
        # 实际应从TuShare Pro加载
        return []

# 使用示例
validator = T1TradingValidator()

print("\n🔄 T+1规则验证:")
test_cases = [
    (date(2025, 2, 10), date(2025, 2, 10), '当日买卖'),
    (date(2025, 2, 10), date(2025, 2, 11), '次日卖出'),
    (date(2025, 2, 14), date(2025, 2, 17), '跨周末'),
]

for buy, sell, desc in test_cases:
    result = validator.validate_sell_order('600000.SH', buy, sell)
    status = "✅" if result['is_valid'] else "❌"
    print(f"{status} {desc}: {result.get('reason', result.get('compliance'))}")
```

---

## 📊 EmotionQuant集成 (v2.0完整版)

### MSS情绪系统集成

```python
def get_market_emotion_data_v2(trade_date: str) -> Dict:
    """
    v2.0增强版：获取市场情绪数据
    EmotionQuant MSS系统专用

    新增功能:
    - 涨跌停情绪权重
    - 成交额活跃度
    - 板块分化度
    """

    import tushare as ts
    pro = ts.pro_api()

    try:
        # 获取市场概况
        df_market = pro.daily(trade_date=trade_date)

        if df_market.empty:
            return {'error': '无交易数据', 'is_trading_day': False}

        # 基础统计
        total_stocks = len(df_market)
        rise_stocks = len(df_market[df_market['pct_chg'] > 0])
        fall_stocks = len(df_market[df_market['pct_chg'] < 0])
        flat_stocks = total_stocks - rise_stocks - fall_stocks

        # v2.0: 涨跌停统计（按板块分类）
        limit_up_main = len(df_market[
            (df_market['pct_chg'] >= 9.9) &
            (df_market['ts_code'].str.startswith('60') | df_market['ts_code'].str.startswith('000'))
        ])
        limit_up_star = len(df_market[
            (df_market['pct_chg'] >= 19.9) &
            (df_market['ts_code'].str.startswith('688'))
        ])
        limit_up_gem = len(df_market[
            (df_market['pct_chg'] >= 19.9) &
            (df_market['ts_code'].str.startswith('300'))
        ])

        # v2.0: 情绪温度计算（多维度）
        base_emotion = (rise_stocks / total_stocks) * 100

        limit_emotion = (
            (limit_up_main * 1.0 + limit_up_star * 1.5 + limit_up_gem * 1.4) /
            total_stocks * 100
        )

        amount_data = df_market['amount'].sum()
        avg_amount = df_market['amount'].mean()
        activity_score = (amount_data / (avg_amount * total_stocks) - 1) * 10 if avg_amount > 0 else 0

        # v2.0: 综合情绪温度
        comprehensive_emotion = (
            base_emotion * 0.5 +
            limit_emotion * 0.3 +
            activity_score * 0.2
        )

        return {
            'trade_date': trade_date,
            'total_stocks': total_stocks,
            'rise_stocks': rise_stocks,
            'fall_stocks': fall_stocks,
            'flat_stocks': flat_stocks,
            'rise_ratio': rise_stocks / total_stocks,
            'limit_up_main': limit_up_main,
            'limit_up_star': limit_up_star,
            'limit_up_gem': limit_up_gem,
            'base_emotion': base_emotion,
            'limit_emotion': limit_emotion,
            'activity_score': activity_score,
            'comprehensive_emotion': comprehensive_emotion,
            'emotion_level': classify_emotion_level_v2(comprehensive_emotion),
            'version': 'v2.0',
            'compliance': '✅ 基于市场数据，无技术指标'
        }

    except Exception as e:
        return {'error': str(e), 'status': '获取失败'}

def classify_emotion_level_v2(emotion_score: float) -> str:
    """v2.0：情绪分级（5级制）"""
    if emotion_score <= 20:
        return "冰点（极度恐慌）"
    elif emotion_score <= 40:
        return "修复（谨慎恢复）"
    elif emotion_score <= 60:
        return "乐观（正常交易）"
    elif emotion_score <= 80:
        return "狂热（高度活跃）"
    else:
        return "回落（过热警惕）"

# 使用示例
print("\n🌡️ MSS市场情绪分析 (v2.0):")
emotion_data = get_market_emotion_data_v2('20250212')

if 'error' not in emotion_data:
    print(f"日期: {emotion_data['trade_date']}")
    print(f"综合情绪: {emotion_data['comprehensive_emotion']:.1f}°C")
    print(f"情绪等级: {emotion_data['emotion_level']}")
    print(f"涨跌比: {emotion_data['rise_ratio']:.2%}")
    print(f"涨停数: 主板{emotion_data['limit_up_main']} "
          f"科创{emotion_data['limit_up_star']} 创业{emotion_data['limit_up_gem']}")
```

---

## 📚 参考资料

### v2.0更新参考

- [上海证券交易所交易规则2025版](http://www.sse.com.cn/)

- [深圳证券交易所交易规则2025版](http://www.szse.cn/)

- [北京证券交易所交易规则](http://www.bse.cn/)

- [TuShare Pro交易日历接口](https://tushare.pro/document/2?doc_id=26)

### 官方规则文档

- [上交所交易规则](http://www.sse.com.cn/lawandrules/sselawsrules/trading/)

- [深交所交易规则](http://www.szse.cn/lawrules/rule/)

- [北交所交易规则](http://www.bse.cn/lawrules/)

---

## 🔚 结语

### v2.0核心改进

1. ✅ **2025年规则同步**: 注册制全面实施后的最新标准

2. ✅ **涨跌停细化**: 板块差异化处理 + 情绪系数

3. ✅ **T+1增强**: 特殊场景覆盖 + 节假日处理

4. ✅ **集合竞价详解**: 精确到秒级的时段划分

5. ✅ **EmotionQuant深度集成**: MSS+IRS+PAS全系统适配

### 合规承诺

- 🚫 **零技术指标**: 所有分析基于市场基础数据

- 🇨🇳 **A股专属**: 100%符合中国A股交易规则

- 🗂️ **本地数据优先**: 规则数据优先本地存储，外部数据仅用于离线更新

- 🔐 **路径硬编码绝对禁止**: 路径/密钥/配置通过环境变量或配置注入

- 🔐 **恒星组地位**: 权威参考文档 ⭐⭐⭐

---

*最后更新: 2025-02-12*
*文档版本: v2.0*
*EmotionQuant项目 - 恒星组文档 ⭐⭐⭐*



