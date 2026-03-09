# A股涨跌停制度与板块差异参考

**文档版本**：`sealed-reference v1`  
**文档状态**：`Reference`  
**标准来源**：沪深北交易所官方规则  
**定位**：外部规则参考，不直接定义当前系统执行口径  
**整理更新**：`2026-03-09`

---

## 当前定位

本文是：

1. A 股涨跌停制度参考
2. 主板 / 创业板 / 科创板 / 北交所 / ST 差异参考
3. 板块边界与价格限制校验参考

本文不是：

1. 当前系统的情绪因子定义
2. 当前 MSS / IRS / PAS 的算法正文
3. 当前 Broker 的执行实现方案

当前权威入口：

1. 当前主线设计：`blueprint/`
2. 当前实现与状态：`docs/spec/common/records/development-status.md`
3. 历史冻结基线：`docs/design-v2/01-system/system-baseline.md`

冲突处理：

1. 若本文与仓库当前设计冲突，以 `blueprint/`、`design-v2` 和当前代码为准。
2. 若本文与交易所官方规则冲突，以官方规则为准。

---

## 使用说明

本文回答的是：

1. 不同板块的涨跌停幅度
2. 新股、ST 等特殊情形的差异
3. 涨跌停价格校验的基础思路

本文不直接回答：

1. 当前系统如何把涨跌停映射成情绪分数
2. 当前系统如何把板块波动性映射成权重
3. 当前 Broker 如何在执行层处理所有涨跌停边界

这些内容应查看当前设计正文和实现代码，而不是以本文旧样例代替。

---

## 制度总览

常见板块规则参考如下：

| 板块 | 涨停幅度 | 跌停幅度 | 新股前若干日限制 | 说明 |
|---|---|---|---|---|
| 主板 | `+10%` | `-10%` | 以当期官方规则为准 | 常见基准板块 |
| 科创板 | `+20%` | `-20%` | 常见为前 5 日无涨跌停 | 注册制板块 |
| 创业板 | `+20%` | `-20%` | 常见为前 5 日无涨跌停 | 注册制板块 |
| 北交所 | `+30%` | `-30%` | 常见为首日无涨跌停 | 高波动板块 |
| ST | `+5%` | `-5%` | 依具体规则执行 | 风险警示股票 |

说明：

1. 上表用于仓库做规则识别与边界校验参考。
2. 具体新股首日 / 前若干日规则以交易所最新口径为准。

---

## 通用计算参考

下面的示例只演示“板块识别 + 涨跌停价格计算”的基础思路，不代表当前系统正式实现。

```python
from dataclasses import dataclass


@dataclass
class PriceLimitResult:
    stock_code: str
    has_limit: bool
    limit_up: float | None
    limit_down: float | None
    note: str


def calculate_limit_prices(board: str, prev_close: float, is_new_stock: bool = False) -> PriceLimitResult:
    no_limit_days_boards = {"STAR", "GEM", "BSE"}

    if is_new_stock and board in no_limit_days_boards:
        return PriceLimitResult(
            stock_code=board,
            has_limit=False,
            limit_up=None,
            limit_down=None,
            note="新股特殊阶段无涨跌停限制，具体以官方规则为准",
        )

    limit_map = {
        "MAIN": 0.10,
        "STAR": 0.20,
        "GEM": 0.20,
        "BSE": 0.30,
        "ST": 0.05,
    }

    pct = limit_map[board]
    return PriceLimitResult(
        stock_code=board,
        has_limit=True,
        limit_up=round(prev_close * (1 + pct), 2),
        limit_down=round(prev_close * (1 - pct), 2),
        note=f"{board} 涨跌停按 {pct:.0%} 计算",
    )
```

---

## 仓库使用边界

本文在仓库内主要承担 3 类参考职责：

1. 板块差异与涨跌停制度参考
2. 价格上下限校验参考
3. 停牌 / 一字板等执行边界的外部制度背景说明

本文不再承担：

1. `EmotionQuant` 情绪系数定义
2. MSS / IRS / PAS 的板块权重逻辑
3. 当前系统对涨跌停的因子级消费说明

历史上把涨跌停制度直接扩写为 `EmotionQuant` 情绪系数应用的段落，现统一视为旧草稿，不再保留在正文中。

---

## 相关文档

- `blueprint/README.md`
- `blueprint/01-full-design/05-broker-risk-contract-annex-20260308.md`
- `docs/design-v2/01-system/system-baseline.md`
- `docs/spec/common/records/development-status.md`
- `docs/reference/a-stock-rules/A股市场交易规则-tushare版.md`

---

## 参考资料

- [上海证券交易所](http://www.sse.com.cn/)
- [深圳证券交易所](http://www.szse.cn/)
- [北京证券交易所](http://www.bse.cn/)

---

**封印说明**：

1. 本文保留“涨跌停制度与板块差异参考”价值。
2. 旧版 `EmotionQuant` 情绪系数、板块情绪权重等内容已从正文移除。
3. 如需回看旧草稿，请查 Git 历史，而不要把旧草稿当成当前主线设计的一部分。
