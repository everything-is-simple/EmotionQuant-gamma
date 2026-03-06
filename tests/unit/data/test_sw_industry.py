from __future__ import annotations

from datetime import date

import pandas as pd

from src.data.sw_industry import (
    build_l1_sw_industry_member_rows,
    build_sw_l1_classify_snapshot,
    build_sw_l1_member_snapshot,
    normalize_sw_l1_classify,
)


def test_normalize_sw_l1_classify_keeps_real_31_bucket_rows() -> None:
    classify = pd.DataFrame(
        [
            {
                "index_code": "801780.SI",
                "industry_name": "银行",
                "industry_code": "801780",
                "level": "L1",
                "src": "SW2021",
                "trade_date": "20260306",
            },
            {
                "index_code": "801100.SI",
                "industry_name": "行业1",
                "industry_code": "801100",
                "level": "L1",
                "src": "SW2021",
                "trade_date": "20260306",
            },
            {
                "index_code": "801780.SI",
                "industry_name": "银行旧快照",
                "industry_code": "801780",
                "level": "L1",
                "src": "SW2021",
                "trade_date": "20250306",
            },
        ]
    )

    normalized = normalize_sw_l1_classify(classify)

    assert normalized.to_dict(orient="records") == [
        {"index_code": "801780.SI", "industry_name": "银行", "industry_code": "801780"}
    ]


def test_sw_l1_snapshots_cover_active_and_removed_members() -> None:
    classify = pd.DataFrame(
        [
            {
                "index_code": "801780.SI",
                "industry_name": "银行",
                "industry_code": "801780",
                "level": "L1",
                "src": "SW2021",
            }
        ]
    )
    members = [
        pd.DataFrame(
            [
                {
                    "l1_code": "801780.SI",
                    "ts_code": "000001.SZ",
                    "in_date": "19910403",
                    "out_date": "",
                    "is_new": "Y",
                }
            ]
        ),
        pd.DataFrame(
            [
                {
                    "l1_code": "801780.SI",
                    "ts_code": "600001.SH",
                    "in_date": "20000101",
                    "out_date": "20100101",
                    "is_new": "N",
                }
            ]
        ),
    ]

    raw_classify = build_sw_l1_classify_snapshot(classify, snapshot_date="20260306")
    raw_member = build_sw_l1_member_snapshot(classify, members, snapshot_date="20260306")
    l1_member = build_l1_sw_industry_member_rows(classify, members, source_trade_date=date(2026, 3, 6))

    assert raw_classify["industry_name"].tolist() == ["银行"]
    assert set(raw_member["ts_code"]) == {"000001.SZ", "600001.SH"}
    assert set(raw_member["trade_date"]) == {"20260306"}
    assert l1_member.sort_values(["ts_code", "in_date"])["industry_name"].tolist() == ["银行", "银行"]
    assert l1_member.sort_values(["ts_code", "in_date"])["is_new"].tolist() == ["Y", "N"]


def test_sw_member_dedup_prefers_closed_row_when_same_in_date_conflicts() -> None:
    classify = pd.DataFrame(
        [
            {
                "index_code": "801180.SI",
                "industry_name": "房地产",
                "industry_code": "801180",
                "level": "L1",
                "src": "SW2021",
            }
        ]
    )
    members = [
        pd.DataFrame(
            [
                {
                    "l1_code": "801180.SI",
                    "ts_code": "600185.SH",
                    "in_date": "19990611",
                    "out_date": "",
                    "is_new": "Y",
                }
            ]
        ),
        pd.DataFrame(
            [
                {
                    "l1_code": "801180.SI",
                    "ts_code": "600185.SH",
                    "in_date": "19990611",
                    "out_date": "20260304",
                    "is_new": "N",
                }
            ]
        ),
    ]

    raw_member = build_sw_l1_member_snapshot(classify, members, snapshot_date="20260306")
    l1_member = build_l1_sw_industry_member_rows(classify, members, source_trade_date=date(2026, 3, 6))

    assert len(raw_member) == 1
    assert raw_member.iloc[0]["out_date"] == "20260304"
    assert len(l1_member) == 1
    assert l1_member.iloc[0]["out_date"] == date(2026, 3, 4)
