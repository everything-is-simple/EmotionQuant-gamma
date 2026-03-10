from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

import pandas as pd

from src.contracts import Signal


class PatternDetector(ABC):
    """形态检测器抽象接口。"""

    name: str

    @abstractmethod
    def detect(self, code: str, asof_date: date, df: pd.DataFrame) -> Signal | None:
        """
        输入:
        - code: 6 位股票代码
        - asof_date: 信号日（T 日收盘后）
        - df: 历史窗口数据，必须按 date 升序

        约束:
        - detector 只回答“这个形态今天是否触发”
        - 不负责 IRS 排序、MSS 风控或 Broker 执行
        """
        raise NotImplementedError

