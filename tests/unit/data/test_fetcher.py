from __future__ import annotations

import sys
import types

import pandas as pd

from src.data.fetcher import TuShareFetcher


class _FakePro:
    def __init__(self) -> None:
        self._DataApi__token = ""
        self._DataApi__http_url = ""

    def stock_basic(self, exchange: str, list_status: str, fields: str) -> pd.DataFrame:
        assert exchange == ""
        assert "list_status" in fields
        rows = {
            "L": [
                {
                    "ts_code": "000001.SZ",
                    "name": "平安银行",
                    "industry": "银行",
                    "market": "主板",
                    "list_status": "L",
                    "list_date": "19910403",
                }
            ],
            "D": [
                {
                    "ts_code": "000002.SZ",
                    "name": "样本退市股",
                    "industry": "制造",
                    "market": "主板",
                    "list_status": "D",
                    "list_date": "20000101",
                }
            ],
            "P": [],
        }
        return pd.DataFrame(rows[list_status])


def test_fetch_stock_info_keeps_list_status(monkeypatch) -> None:
    fake_ts = types.SimpleNamespace(pro_api=lambda token: _FakePro())
    monkeypatch.setitem(sys.modules, "tushare", fake_ts)

    fetcher = TuShareFetcher(token="dummy-token")
    df = fetcher.fetch_stock_info()

    assert set(df["list_status"]) == {"L", "D"}
    assert "effective_from" in df.columns
