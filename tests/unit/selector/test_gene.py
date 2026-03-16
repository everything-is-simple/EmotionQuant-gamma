from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from src.data.store import Store
from src.selector.gene import compute_gene


def _trade_calendar(start: date, days: int) -> pd.DataFrame:
    rows = []
    for index in range(days):
        day = start + timedelta(days=index)
        rows.append(
            {
                "date": day,
                "is_trade_day": True,
                "prev_trade_day": start + timedelta(days=index - 1) if index > 0 else None,
                "next_trade_day": start + timedelta(days=index + 1) if index < days - 1 else None,
            }
        )
    return pd.DataFrame(rows)


def _adj_daily_rows(base: date, code: str, closes: list[float]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, close in enumerate(closes):
        day = base + timedelta(days=index)
        rows.append(
            {
                "code": code,
                "date": day,
                "adj_open": close - 0.1,
                "adj_high": close + 0.2,
                "adj_low": close - 0.2,
                "adj_close": close,
                "volume": 1_000.0 + index * 10.0,
                "amount": close * 10_000.0,
                "pct_chg": 0.0,
            }
        )
    return rows


def test_compute_gene_writes_wave_event_and_snapshot_tables(tmp_path) -> None:
    db = tmp_path / "gene_wave_ruler.duckdb"
    store = Store(db)
    try:
        base = date(2026, 1, 5)
        closes_a = [10.0, 11.0, 13.0, 12.0, 9.0, 10.0, 12.0, 11.0, 13.0, 12.0, 14.0, 15.0]
        closes_b = [8.0, 8.5, 9.2, 8.9, 7.8, 8.1, 8.8, 8.4, 9.0, 8.8, 9.1, 9.3]

        store.bulk_upsert("l1_trade_calendar", _trade_calendar(base, len(closes_a)))
        store.bulk_upsert(
            "l2_stock_adj_daily",
            pd.DataFrame(_adj_daily_rows(base, "AAA", closes_a) + _adj_daily_rows(base, "BBB", closes_b)),
        )

        written = compute_gene(store, base, base + timedelta(days=len(closes_a) - 1))

        schema = store.read_df("PRAGMA table_info('l3_stock_gene')")
        snapshots = store.read_df(
            """
            SELECT
                code,
                calc_date,
                current_wave_direction,
                current_wave_magnitude_pct,
                current_wave_magnitude_percentile,
                current_wave_magnitude_band,
                current_wave_age_band,
                cross_section_magnitude_rank,
                cross_section_magnitude_percentile
            FROM l3_stock_gene
            WHERE calc_date = ?
            ORDER BY cross_section_magnitude_rank, code
            """,
            (base + timedelta(days=len(closes_a) - 1),),
        )
        waves = store.read_df(
            """
            SELECT
                code,
                direction,
                magnitude_pct,
                duration_trade_days,
                wave_role,
                reversal_tag,
                magnitude_percentile,
                magnitude_band,
                wave_age_band
            FROM l3_gene_wave
            ORDER BY code, end_date
            """
        )
        events = store.read_df(
            """
            SELECT
                code,
                wave_id,
                event_type,
                event_seq,
                is_two_b_failure
            FROM l3_gene_event
            ORDER BY code, event_date, event_seq
            """
        )
        factor_eval = store.read_df(
            """
            SELECT
                calc_date,
                factor_name,
                sample_scope,
                direction_scope,
                forward_horizon_trade_days,
                bin_label,
                sample_size,
                monotonicity_score
            FROM l3_gene_factor_eval
            ORDER BY factor_name, bin_label
            """
        )
        distribution_eval = store.read_df(
            """
            SELECT
                code,
                calc_date,
                metric_name,
                band_label,
                threshold_p65,
                threshold_p95,
                band_sample_size
            FROM l3_gene_distribution_eval
            ORDER BY code, metric_name
            """
        )

        assert written > 0
        assert "current_wave_direction" in schema["name"].tolist()
        assert "cross_section_magnitude_rank" in schema["name"].tolist()
        assert "current_wave_magnitude_band" in schema["name"].tolist()
        assert "current_wave_age_band" in schema["name"].tolist()
        assert "latest_confirmed_turn_type" in schema["name"].tolist()
        assert "latest_two_b_confirm_type" in schema["name"].tolist()
        assert not snapshots.empty
        assert not waves.empty
        assert not events.empty
        assert not factor_eval.empty
        assert not distribution_eval.empty
        assert snapshots["current_wave_direction"].tolist() == ["UP", "UP"]
        assert snapshots["code"].tolist() == ["AAA", "BBB"]
        assert snapshots["cross_section_magnitude_rank"].tolist() == [1, 2]
        assert float(snapshots.iloc[0]["current_wave_magnitude_pct"]) > float(
            snapshots.iloc[1]["current_wave_magnitude_pct"]
        )
        assert snapshots["current_wave_magnitude_percentile"].notna().all()
        assert snapshots["current_wave_magnitude_band"].isin(["NORMAL", "STRONG", "EXTREME", "UNSCALED"]).all()
        assert snapshots["current_wave_age_band"].isin(["NORMAL", "STRONG", "EXTREME", "UNSCALED"]).all()
        assert waves["magnitude_percentile"].notna().all()
        assert waves["magnitude_band"].isin(["NORMAL", "STRONG", "EXTREME", "UNSCALED"]).all()
        assert waves["wave_age_band"].isin(["NORMAL", "STRONG", "EXTREME", "UNSCALED"]).all()
        assert events["event_seq"].min() == 1
        assert set(factor_eval.loc[factor_eval["bin_label"] == "ALL", "factor_name"].tolist()) == {
            "magnitude",
            "duration",
            "extreme_density",
        }
        assert factor_eval["sample_scope"].eq("SELF_HISTORY_PERCENTILE").all()
        assert factor_eval["direction_scope"].eq("ALL").all()
        assert factor_eval["forward_horizon_trade_days"].eq(10).all()
        assert set(distribution_eval["metric_name"].tolist()) == {"duration_trade_days", "magnitude_pct"}
        assert distribution_eval["band_label"].isin(["NORMAL", "STRONG", "EXTREME", "UNSCALED"]).all()
    finally:
        store.close()


def test_compute_gene_writes_g3_structure_labels(tmp_path) -> None:
    db = tmp_path / "gene_structure_labels.duckdb"
    store = Store(db)
    try:
        base = date(2026, 1, 5)
        closes_turn_up = [14.0, 13.0, 12.0, 13.0, 14.0, 13.4, 12.6, 13.2, 14.5, 15.0, 14.6, 14.2]
        closes_turn_down = [13.0, 14.0, 15.0, 14.0, 13.0, 13.6, 14.4, 13.8, 12.5, 12.0, 12.4, 12.8]

        store.bulk_upsert("l1_trade_calendar", _trade_calendar(base, len(closes_turn_up)))
        store.bulk_upsert(
            "l2_stock_adj_daily",
            pd.DataFrame(
                _adj_daily_rows(base, "AAA", closes_turn_up) + _adj_daily_rows(base, "BBB", closes_turn_down)
            ),
        )

        compute_gene(store, base, base + timedelta(days=len(closes_turn_up) - 1))

        structure_waves = store.read_df(
            """
            SELECT
                code,
                end_date,
                turn_confirm_type,
                turn_step1_date,
                turn_step2_date,
                turn_step3_date,
                two_b_confirm_type
            FROM l3_gene_wave
            WHERE turn_confirm_type <> 'NONE' OR two_b_confirm_type <> 'NONE'
            ORDER BY code, end_date
            """
        )
        structure_events = store.read_df(
            """
            SELECT
                code,
                wave_id,
                event_type,
                event_family,
                structure_direction,
                anchor_wave_id
            FROM l3_gene_event
            WHERE event_family = 'STRUCTURE'
            ORDER BY code, event_date, event_seq
            """
        )
        snapshots = store.read_df(
            """
            SELECT
                code,
                latest_confirmed_turn_type,
                latest_two_b_confirm_type
            FROM l3_stock_gene
            WHERE calc_date = ?
            ORDER BY code
            """,
            (base + timedelta(days=len(closes_turn_up) - 1),),
        )

        assert not structure_waves.empty
        assert not structure_events.empty
        assert set(structure_events["event_type"].tolist()) >= {
            "123_STEP1",
            "123_STEP2",
            "123_STEP3",
            "2B_BOTTOM",
            "2B_TOP",
        }

        up_turn = structure_waves.loc[structure_waves["code"] == "AAA"].reset_index(drop=True)
        assert "CONFIRMED_TURN_UP" in up_turn["turn_confirm_type"].tolist()
        up_confirm = up_turn.loc[up_turn["turn_confirm_type"] == "CONFIRMED_TURN_UP"].iloc[0]
        assert up_confirm["turn_step1_date"] < up_confirm["turn_step2_date"] < up_confirm["turn_step3_date"]
        assert "2B_BOTTOM" in up_turn["two_b_confirm_type"].tolist()

        down_turn = structure_waves.loc[structure_waves["code"] == "BBB"].reset_index(drop=True)
        assert "CONFIRMED_TURN_DOWN" in down_turn["turn_confirm_type"].tolist()
        down_confirm = down_turn.loc[down_turn["turn_confirm_type"] == "CONFIRMED_TURN_DOWN"].iloc[0]
        assert down_confirm["turn_step1_date"] < down_confirm["turn_step2_date"] < down_confirm["turn_step3_date"]
        assert "2B_TOP" in down_turn["two_b_confirm_type"].tolist()

        assert snapshots["latest_confirmed_turn_type"].tolist() == ["CONFIRMED_TURN_UP", "CONFIRMED_TURN_DOWN"]
        assert snapshots["latest_two_b_confirm_type"].tolist() == ["2B_BOTTOM", "2B_TOP"]
        assert set(structure_events.loc[structure_events["code"] == "AAA", "structure_direction"].tolist()) == {"UP"}
        assert set(structure_events.loc[structure_events["code"] == "BBB", "structure_direction"].tolist()) == {
            "DOWN"
        }
    finally:
        store.close()
