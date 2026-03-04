from __future__ import annotations

from datetime import date

from src.data.store import Store


def compute_gene(store: Store, start: date, end: date) -> int:
    """
    v0.01 保留函数签名：
    Gene 仅用于事后分析，不进入实时漏斗。
    """
    _ = (store, start, end)
    return 0

