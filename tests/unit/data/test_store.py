from __future__ import annotations

from datetime import date

import pandas as pd

from src.data.store import CURRENT_SCHEMA_VERSION, Store


def test_store_init_and_schema_version(tmp_path) -> None:
    db = tmp_path / "test.duckdb"
    store = Store(db)
    version = store.get_schema_version()
    assert version.schema_version == CURRENT_SCHEMA_VERSION
    store.close()


def test_store_crud_and_progress(tmp_path) -> None:
    db = tmp_path / "test.duckdb"
    store = Store(db)

    trade_cal = pd.DataFrame(
        [
            {"date": date(2026, 3, 3), "is_trade_day": True, "prev_trade_day": None, "next_trade_day": date(2026, 3, 4)},
            {"date": date(2026, 3, 4), "is_trade_day": True, "prev_trade_day": date(2026, 3, 3), "next_trade_day": None},
        ]
    )
    store.bulk_upsert("l1_trade_calendar", trade_cal)

    stock = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "date": date(2026, 3, 3),
                "open": 10.0,
                "high": 10.1,
                "low": 9.9,
                "close": 10.0,
                "pre_close": 9.8,
                "volume": 1000.0,
                "amount": 10000.0,
                "pct_chg": 0.02,
                "adj_factor": 1.0,
                "is_halt": False,
                "up_limit": 10.78,
                "down_limit": 8.82,
                "total_mv": 100000.0,
                "circ_mv": 80000.0,
            }
        ]
    )
    store.bulk_upsert("l1_stock_daily", stock)

    close = store.read_scalar(
        "SELECT close FROM l1_stock_daily WHERE ts_code = ? AND date = ?",
        ("000001.SZ", date(2026, 3, 3)),
    )
    assert close == 10.0

    asof = store.read_table_asof("l1_stock_daily", asof_date=date(2026, 3, 4), code_col="ts_code", codes=["000001.SZ"])
    assert len(asof) == 1

    store.update_fetch_progress("stock_daily", date(2026, 3, 4), status="OK")
    assert store.get_fetch_progress("stock_daily") == date(2026, 3, 4)
    assert store.next_trade_date(date(2026, 3, 3)) == date(2026, 3, 4)
    store.close()


def test_store_applies_memory_limit_from_env(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DUCKDB_MEMORY_LIMIT", "512MB")
    db = tmp_path / "test_memory.duckdb"
    store = Store(db)
    try:
        current = store.read_scalar("SELECT current_setting('memory_limit')")
        text = str(current).upper()
        value = float(text.split()[0])
        assert 400.0 <= value <= 600.0
        assert text.endswith("MIB") or text.endswith("MB")
    finally:
        store.close()


def test_bulk_upsert_mirrors_pattern_strength_for_legacy_rank_table(tmp_path) -> None:
    db = tmp_path / "legacy_rank.duckdb"
    store = Store(db)
    try:
        store.conn.execute("DROP TABLE l3_signal_rank_exp")
        store.conn.execute(
            """
            CREATE TABLE l3_signal_rank_exp (
                run_id       VARCHAR NOT NULL,
                signal_id    VARCHAR NOT NULL,
                signal_date  DATE    NOT NULL,
                code         VARCHAR NOT NULL,
                industry     VARCHAR,
                variant      VARCHAR NOT NULL,
                bof_strength DOUBLE NOT NULL,
                irs_score    DOUBLE NOT NULL,
                mss_score    DOUBLE NOT NULL,
                final_score  DOUBLE NOT NULL,
                final_rank   INTEGER NOT NULL,
                selected     BOOLEAN NOT NULL,
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (run_id, signal_id)
            )
            """
        )
        frame = pd.DataFrame(
            [
                {
                    "run_id": "run-1",
                    "signal_id": "000001_2026-03-03_bof",
                    "signal_date": date(2026, 3, 3),
                    "code": "000001",
                    "industry": "银行",
                    "variant": "v0_01_dtt_pattern_plus_irs_score",
                    "pattern_strength": 82.5,
                    "irs_score": 61.0,
                    "mss_score": 50.0,
                    "final_score": 74.0,
                    "final_rank": 1,
                    "selected": True,
                }
            ]
        )

        inserted = store.bulk_upsert("l3_signal_rank_exp", frame)

        row = store.read_df(
            """
            SELECT run_id, signal_id, bof_strength, irs_score, final_score
            FROM l3_signal_rank_exp
            """
        ).iloc[0]
        assert inserted == 1
        assert row["run_id"] == "run-1"
        assert row["signal_id"] == "000001_2026-03-03_bof"
        assert float(row["bof_strength"]) == 82.5
        assert float(row["irs_score"]) == 61.0
        assert float(row["final_score"]) == 74.0
    finally:
        store.close()
