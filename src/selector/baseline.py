from __future__ import annotations

"""Selector 研究线共享的冻结基线锚点。

这个文件只存“已经校准好的常数”，不存阈值含义，也不存主线治理决策。
这样当有人改这里时，可以明确知道自己改的是数学基线，而不是运行语义。
"""

# MSS 冻结基线：
# 这里只保存“原始因子 -> [0, 100] 解释分数”的归一化锚点，不负责解释阈值语义，
# 也不负责决定 Broker 应该如何放大/缩小风险。
# 这样做的目的是把“数学刻度”与“交易治理”拆开，避免后来有人只改了均值/方差，
# 却误以为自己同时改掉了 MSS 的运行边界。
MSS_BASELINE = {
    "market_coefficient_mean": 0.4773860533555573,
    "market_coefficient_std": 0.23364959561646687,
    "profit_effect_mean": 0.02001627879301641,
    "profit_effect_std": 0.02405607273268048,
    "loss_effect_mean": 0.01498781726283301,
    "loss_effect_std": 0.030001566738781904,
    "continuity_mean": 0.1929883692056652,
    "continuity_std": 0.09005146213678802,
    "extreme_mean": 0.41160185981493663,
    "extreme_std": 0.13036907349337296,
    "volatility_mean": 0.18112868209847394,
    "volatility_std": 0.05756783616858019,
}

# IRS 冻结基线：
# 当前 IRS 主线已收口为以横截面排序为主，所以默认锚点保持中性。
# 真正的因子取舍、权重、fallback 语义在 irs.py 和治理文档中定义，
# 这里仅提供一个“没有单独校准文件时也能稳定运行”的最低公共基线。
IRS_BASELINE = {
    "rs_score_mean": 0.0,
    "rs_score_std": 1.0,
    "cf_score_mean": 0.0,
    "cf_score_std": 1.0,
}
