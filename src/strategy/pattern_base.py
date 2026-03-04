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
        """
        raise NotImplementedError

