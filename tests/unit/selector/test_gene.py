from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from src.data.store import Store
from src.selector.gene import compute_gene, compute_gene_conditioning, compute_gene_mirror


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


def _adj_daily_rows_from_specs(base: date, code: str, specs: list[dict[str, float]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    previous_close = float(specs[0]["close"])
    for index, spec in enumerate(specs):
        day = base + timedelta(days=index)
        close = float(spec["close"])
        open_price = float(spec.get("open", close if index == 0 else previous_close))
        high_price = float(spec.get("high", max(open_price, close) + 0.15))
        low_price = float(spec.get("low", min(open_price, close) - 0.15))
        volume = float(spec.get("volume", 1_000.0))
        volume_ma20 = float(spec.get("volume_ma20", 900.0))
        rows.append(
            {
                "code": code,
                "date": day,
                "adj_open": open_price,
                "adj_high": high_price,
                "adj_low": low_price,
                "adj_close": close,
                "volume": volume,
                "volume_ma20": volume_ma20,
                "amount": close * volume,
                "pct_chg": ((close - previous_close) / previous_close) * 100.0 if index > 0 else 0.0,
            }
        )
        previous_close = close
    return rows


def _index_daily_rows(base: date, ts_code: str, closes: list[float]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    previous_close = closes[0]
    for index, close in enumerate(closes):
        day = base + timedelta(days=index)
        rows.append(
            {
                "ts_code": ts_code,
                "date": day,
                "open": previous_close,
                "high": max(previous_close, close) + 0.3,
                "low": min(previous_close, close) - 0.3,
                "close": close,
                "pre_close": previous_close,
                "pct_chg": ((close - previous_close) / previous_close) * 100.0 if previous_close else 0.0,
                "volume": 10_000.0 + index * 100.0,
                "amount": close * 1_000_000.0,
            }
        )
        previous_close = close
    return rows


def _industry_daily_rows(base: date, industry: str, pct_changes: list[float], amount_base: float) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    rolling_return = 0.0
    for index, pct_chg in enumerate(pct_changes):
        day = base + timedelta(days=index)
        rolling_return += pct_chg
        stock_count = 20 + index
        rise_ratio = 0.45 if pct_chg < 0 else 0.65
        rise_count = int(stock_count * rise_ratio)
        rows.append(
            {
                "industry": industry,
                "date": day,
                "pct_chg": pct_chg,
                "amount": amount_base + index * 1_000_000.0,
                "stock_count": stock_count,
                "rise_count": rise_count,
                "fall_count": stock_count - rise_count,
                "amount_ma20": max(amount_base * 0.85, 1.0),
                "return_5d": rolling_return,
                "return_20d": rolling_return,
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
                trend_level,
                current_wave_direction,
                current_context_trend_level,
                current_context_trend_direction,
                current_context_view_scope,
                current_context_view_level,
                current_context_parent_trend_level,
                current_context_parent_trend_direction,
                current_wave_role_basis,
                reversal_state,
                reversal_state_family,
                reversal_state_is_confirmed_turn,
                reversal_state_is_two_b_watch,
                reversal_state_is_countertrend_watch,
                current_two_b_window_bars,
                current_two_b_window_basis,
                current_wave_magnitude_pct,
                current_wave_magnitude_percentile,
                current_wave_magnitude_band,
                current_wave_history_reference_trade_days,
                current_wave_history_span_trade_days,
                current_wave_age_band,
                current_wave_duration_band,
                current_wave_age_band_basis,
                current_wave_lifespan_joint_percentile,
                current_wave_lifespan_joint_band,
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
                trend_level,
                context_trend_level,
                context_trend_direction_after,
                magnitude_pct,
                duration_trade_days,
                wave_role,
                wave_role_basis,
                two_b_window_bars,
                two_b_window_basis,
                reversal_tag,
                history_reference_trade_days,
                history_span_trade_days,
                magnitude_percentile,
                magnitude_band,
                wave_age_band,
                wave_age_band_basis,
                lifespan_joint_percentile,
                lifespan_joint_band,
                prior_mainstream_magnitude_pct,
                retracement_vs_prior_mainstream_pct
            FROM l3_gene_wave
            WHERE trend_level = 'INTERMEDIATE'
            ORDER BY code, end_date
            """
        )
        countertrend_snapshots = store.read_df(
            """
            SELECT
                code,
                calc_date,
                current_wave_role,
                current_wave_prior_mainstream_wave_id,
                current_wave_prior_mainstream_magnitude_pct,
                current_wave_retracement_vs_prior_mainstream_pct
            FROM l3_stock_gene
            WHERE current_wave_role = 'COUNTERTREND'
            ORDER BY code, calc_date
            """
        )
        events = store.read_df(
            """
            SELECT
                code,
                wave_id,
                event_type,
                event_seq,
                is_two_b_failure,
                confirmation_window_bars,
                confirmation_window_basis
            FROM l3_gene_event
            WHERE wave_id LIKE '%::INTERMEDIATE::%'
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
        validation_eval = store.read_df(
            """
            SELECT
                calc_date,
                metric_name,
                sample_scope,
                forward_horizon_trade_days,
                sample_size,
                decision_tag
            FROM l3_gene_validation_eval
            ORDER BY metric_name
            """
        )

        assert written > 0
        assert "current_wave_direction" in schema["name"].tolist()
        assert "trend_level" in schema["name"].tolist()
        assert "current_context_trend_level" in schema["name"].tolist()
        assert "current_context_trend_direction" in schema["name"].tolist()
        assert "current_context_view_scope" in schema["name"].tolist()
        assert "current_context_parent_trend_level" in schema["name"].tolist()
        assert "current_wave_role_basis" in schema["name"].tolist()
        assert "current_two_b_window_bars" in schema["name"].tolist()
        assert "current_two_b_window_basis" in schema["name"].tolist()
        assert "current_short_wave_role_basis" in schema["name"].tolist()
        assert "current_intermediate_wave_role_basis" in schema["name"].tolist()
        assert "current_long_wave_role_basis" in schema["name"].tolist()
        assert "cross_section_magnitude_rank" in schema["name"].tolist()
        assert "current_wave_magnitude_band" in schema["name"].tolist()
        assert "current_wave_age_band" in schema["name"].tolist()
        assert "current_wave_age_band_basis" in schema["name"].tolist()
        assert "current_wave_history_reference_trade_days" in schema["name"].tolist()
        assert "current_wave_history_span_trade_days" in schema["name"].tolist()
        assert "current_wave_lifespan_joint_percentile" in schema["name"].tolist()
        assert "current_wave_lifespan_joint_band" in schema["name"].tolist()
        assert "current_wave_retracement_vs_prior_mainstream_pct" in schema["name"].tolist()
        assert "latest_confirmed_turn_type" in schema["name"].tolist()
        assert "latest_two_b_confirm_type" in schema["name"].tolist()
        assert not snapshots.empty
        assert not waves.empty
        assert not countertrend_snapshots.empty
        assert not events.empty
        assert not factor_eval.empty
        assert not distribution_eval.empty
        assert snapshots["current_wave_direction"].tolist() == ["UP", "UP"]
        assert snapshots["trend_level"].tolist() == ["INTERMEDIATE", "INTERMEDIATE"]
        assert snapshots["current_context_trend_level"].tolist() == ["INTERMEDIATE", "INTERMEDIATE"]
        assert snapshots["current_context_trend_direction"].isin(["UP", "DOWN"]).all()
        assert snapshots["current_context_view_scope"].eq("CANONICAL_INTERMEDIATE_VIEW").all()
        assert snapshots["current_context_view_level"].eq("INTERMEDIATE").all()
        assert snapshots["current_context_parent_trend_level"].eq("LONG").all()
        assert (snapshots["current_context_parent_trend_direction"] == snapshots["current_context_trend_direction"]).all()
        assert snapshots["current_wave_role_basis"].tolist() == [
            "INTERMEDIATE_PARENT_CONTEXT_DIRECTION",
            "INTERMEDIATE_PARENT_CONTEXT_DIRECTION",
        ]
        assert snapshots["reversal_state"].isin(
            ["NONE", "TWO_B_WATCH", "COUNTERTREND_WATCH", "CONFIRMED_TURN_UP", "CONFIRMED_TURN_DOWN"]
        ).all()
        assert snapshots["reversal_state_family"].isin(
            ["NONE", "CONFIRMED_TURN", "TWO_B_WATCH", "COUNTERTREND_WATCH"]
        ).all()
        assert snapshots.loc[
            snapshots["reversal_state_family"] == "CONFIRMED_TURN", "reversal_state_is_confirmed_turn"
        ].all()
        assert snapshots.loc[
            snapshots["reversal_state_family"] == "TWO_B_WATCH", "reversal_state_is_two_b_watch"
        ].all()
        assert snapshots.loc[
            snapshots["reversal_state_family"] == "COUNTERTREND_WATCH", "reversal_state_is_countertrend_watch"
        ].all()
        assert snapshots["current_two_b_window_bars"].tolist() == [5, 5]
        assert snapshots["current_two_b_window_basis"].tolist() == [
            "INTERMEDIATE_WITHIN_3_TO_5_BARS",
            "INTERMEDIATE_WITHIN_3_TO_5_BARS",
        ]
        assert snapshots["code"].tolist() == ["AAA", "BBB"]
        assert snapshots["cross_section_magnitude_rank"].tolist() == [1, 2]
        assert float(snapshots.iloc[0]["current_wave_magnitude_pct"]) > float(
            snapshots.iloc[1]["current_wave_magnitude_pct"]
        )
        assert snapshots["current_wave_magnitude_percentile"].notna().all()
        assert snapshots["current_wave_magnitude_band"].isin(["NORMAL", "STRONG", "EXTREME", "UNSCALED"]).all()
        assert snapshots["current_wave_history_reference_trade_days"].eq(1260).all()
        assert snapshots["current_wave_history_span_trade_days"].gt(0).all()
        assert (snapshots["current_wave_age_band"] == snapshots["current_wave_duration_band"]).all()
        assert snapshots["current_wave_age_band_basis"].eq("DURATION_BAND_ALIAS").all()
        assert snapshots["current_wave_age_band"].isin(["NORMAL", "STRONG", "EXTREME", "UNSCALED"]).all()
        assert snapshots["current_wave_lifespan_joint_percentile"].between(0.0, 100.0).all()
        assert snapshots["current_wave_lifespan_joint_band"].isin(["NORMAL", "STRONG", "EXTREME", "UNSCALED"]).all()
        assert waves["trend_level"].eq("INTERMEDIATE").all()
        assert waves["context_trend_level"].eq("LONG").all()
        assert waves["wave_role_basis"].eq("INTERMEDIATE_PARENT_CONTEXT_DIRECTION").all()
        assert waves["two_b_window_bars"].eq(5).all()
        assert waves["two_b_window_basis"].eq("INTERMEDIATE_WITHIN_3_TO_5_BARS").all()
        assert set(waves["wave_role"].tolist()) == {"MAINSTREAM", "COUNTERTREND"}
        assert waves["context_trend_direction_after"].isin(["UP", "DOWN"]).all()
        assert waves["history_reference_trade_days"].eq(1260).all()
        assert waves["history_span_trade_days"].ge(0).all()
        extreme_events = events.loc[events["event_type"].isin(["NEW_HIGH", "NEW_LOW"])].reset_index(drop=True)
        assert not extreme_events.empty
        assert extreme_events["confirmation_window_bars"].eq(5).all()
        assert extreme_events["confirmation_window_basis"].eq("INTERMEDIATE_WITHIN_3_TO_5_BARS").all()
        assert waves["magnitude_percentile"].notna().all()
        assert waves["magnitude_band"].isin(["NORMAL", "STRONG", "EXTREME", "UNSCALED"]).all()
        assert waves["wave_age_band_basis"].eq("DURATION_BAND_ALIAS").all()
        assert waves["wave_age_band"].isin(["NORMAL", "STRONG", "EXTREME", "UNSCALED"]).all()
        assert waves["lifespan_joint_percentile"].between(0.0, 100.0).all()
        assert waves["lifespan_joint_band"].isin(["NORMAL", "STRONG", "EXTREME", "UNSCALED"]).all()
        assert waves["retracement_vs_prior_mainstream_pct"].dropna().ge(0.0).all()
        assert countertrend_snapshots["current_wave_prior_mainstream_wave_id"].notna().any()
        assert countertrend_snapshots["current_wave_prior_mainstream_magnitude_pct"].notna().any()
        assert countertrend_snapshots["current_wave_retracement_vs_prior_mainstream_pct"].notna().any()
        assert countertrend_snapshots["current_wave_retracement_vs_prior_mainstream_pct"].dropna().ge(0.0).all()
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
        assert not validation_eval.empty
        assert set(validation_eval["metric_name"].tolist()) == {
            "duration_percentile",
            "extreme_density_percentile",
            "gene_score",
            "magnitude_percentile",
        }
        assert validation_eval["sample_scope"].eq("SELF_HISTORY_CURRENT_WAVE").all()
        assert validation_eval["forward_horizon_trade_days"].eq(10).all()
        assert validation_eval["sample_size"].gt(0).all()
        assert validation_eval["decision_tag"].ne("").all()
    finally:
        store.close()


def test_compute_gene_writes_gx8_three_level_hierarchy(tmp_path) -> None:
    db = tmp_path / "gene_gx8_hierarchy.duckdb"
    store = Store(db)
    try:
        base = date(2026, 1, 5)
        closes = [
            10.0, 11.0, 13.0, 15.0, 14.0, 12.0, 10.0, 9.0, 11.0, 13.0, 16.0, 18.0,
            17.0, 15.0, 13.0, 11.0, 10.0, 12.0, 14.0, 17.0, 19.0, 18.0, 16.0, 14.0,
            12.0, 11.0, 13.0, 15.0, 18.0, 20.0, 19.0, 17.0, 15.0, 13.0, 12.0, 14.0,
            16.0, 19.0, 21.0, 20.0, 18.0, 16.0,
        ]
        end = base + timedelta(days=len(closes) - 1)

        store.bulk_upsert("l1_trade_calendar", _trade_calendar(base, len(closes)))
        store.bulk_upsert("l2_stock_adj_daily", pd.DataFrame(_adj_daily_rows(base, "AAA", closes)))

        compute_gene(store, base, end)

        waves = store.read_df(
            """
            SELECT trend_level, context_trend_level, wave_role_basis, two_b_window_bars, two_b_window_basis
            FROM l3_gene_wave
            ORDER BY trend_level, end_date
            """
        )
        snapshot = store.read_df(
            """
            SELECT
                trend_level,
                current_context_trend_level,
                current_context_view_scope,
                current_context_view_level,
                current_context_parent_trend_level,
                current_short_trend_level,
                current_short_context_trend_level,
                current_short_wave_role_basis,
                current_short_two_b_window_bars,
                current_short_two_b_window_basis,
                current_intermediate_trend_level,
                current_intermediate_context_trend_level,
                current_intermediate_wave_role_basis,
                current_intermediate_two_b_window_bars,
                current_intermediate_two_b_window_basis,
                current_long_trend_level,
                current_long_context_trend_level,
                current_long_wave_role_basis,
                current_long_two_b_window_bars,
                current_long_two_b_window_basis
            FROM l3_stock_gene
            WHERE calc_date = ?
            """,
            (end,),
        )

        assert set(waves["trend_level"].tolist()) == {"SHORT", "INTERMEDIATE", "LONG"}
        assert set(
            waves.loc[waves["trend_level"] == "SHORT", "context_trend_level"].tolist()
        ) == {"INTERMEDIATE"}
        assert set(
            waves.loc[waves["trend_level"] == "INTERMEDIATE", "context_trend_level"].tolist()
        ) == {"LONG"}
        assert set(waves.loc[waves["trend_level"] == "LONG", "context_trend_level"].tolist()) == {"LONG"}
        assert set(
            waves.loc[waves["trend_level"] == "SHORT", "wave_role_basis"].tolist()
        ) == {"SHORT_PARENT_CONTEXT_DIRECTION"}
        assert set(
            waves.loc[waves["trend_level"] == "INTERMEDIATE", "wave_role_basis"].tolist()
        ) == {"INTERMEDIATE_PARENT_CONTEXT_DIRECTION"}
        assert set(waves.loc[waves["trend_level"] == "LONG", "wave_role_basis"].tolist()) == {
            "LONG_SELF_DIRECTION_BOOTSTRAP"
        }
        assert set(waves.loc[waves["trend_level"] == "SHORT", "two_b_window_bars"].tolist()) == {1}
        assert set(waves.loc[waves["trend_level"] == "INTERMEDIATE", "two_b_window_bars"].tolist()) == {5}
        assert set(waves.loc[waves["trend_level"] == "LONG", "two_b_window_bars"].tolist()) == {10}
        assert set(waves.loc[waves["trend_level"] == "SHORT", "two_b_window_basis"].tolist()) == {
            "SHORT_WITHIN_1_BAR"
        }
        assert set(waves.loc[waves["trend_level"] == "INTERMEDIATE", "two_b_window_basis"].tolist()) == {
            "INTERMEDIATE_WITHIN_3_TO_5_BARS"
        }
        assert set(waves.loc[waves["trend_level"] == "LONG", "two_b_window_basis"].tolist()) == {
            "LONG_WITHIN_7_TO_10_BARS"
        }

        assert len(snapshot) == 1
        row = snapshot.iloc[0]
        assert row["trend_level"] == "INTERMEDIATE"
        assert row["current_context_trend_level"] == "INTERMEDIATE"
        assert row["current_context_view_scope"] == "CANONICAL_INTERMEDIATE_VIEW"
        assert row["current_context_view_level"] == "INTERMEDIATE"
        assert row["current_context_parent_trend_level"] == "LONG"
        assert row["current_short_trend_level"] == "SHORT"
        assert row["current_short_context_trend_level"] == "INTERMEDIATE"
        assert row["current_short_wave_role_basis"] == "SHORT_PARENT_CONTEXT_DIRECTION"
        assert row["current_short_two_b_window_bars"] == 1
        assert row["current_short_two_b_window_basis"] == "SHORT_WITHIN_1_BAR"
        assert row["current_intermediate_trend_level"] == "INTERMEDIATE"
        assert row["current_intermediate_context_trend_level"] == "LONG"
        assert row["current_intermediate_wave_role_basis"] == "INTERMEDIATE_PARENT_CONTEXT_DIRECTION"
        assert row["current_intermediate_two_b_window_bars"] == 5
        assert row["current_intermediate_two_b_window_basis"] == "INTERMEDIATE_WITHIN_3_TO_5_BARS"
        assert row["current_long_trend_level"] == "LONG"
        assert row["current_long_context_trend_level"] == "LONG"
        assert row["current_long_wave_role_basis"] == "LONG_SELF_DIRECTION_BOOTSTRAP"
        assert row["current_long_two_b_window_bars"] == 10
        assert row["current_long_two_b_window_basis"] == "LONG_WITHIN_7_TO_10_BARS"
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
                trend_level,
                end_date,
                turn_confirm_type,
                turn_step1_date,
                turn_step2_date,
                turn_step3_date,
                turn_step1_condition,
                turn_step2_condition,
                turn_step3_condition,
                two_b_confirm_type,
                two_b_window_bars,
                two_b_window_basis
            FROM l3_gene_wave
            WHERE trend_level = 'INTERMEDIATE'
              AND (turn_confirm_type <> 'NONE' OR two_b_confirm_type <> 'NONE')
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
                anchor_wave_id,
                structure_condition,
                confirmation_window_bars,
                confirmation_window_basis
            FROM l3_gene_event
            WHERE event_family = 'STRUCTURE'
              AND anchor_wave_id LIKE '%::INTERMEDIATE::%'
            ORDER BY code, event_date, event_seq
            """
        )
        snapshots = store.read_df(
            """
            SELECT
                code,
                latest_confirmed_turn_type,
                latest_two_b_confirm_type,
                current_two_b_window_bars,
                current_two_b_window_basis
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
        assert up_confirm["turn_step1_condition"] == "trendline_break"
        assert up_confirm["turn_step2_condition"] == "failed_extreme_test"
        assert up_confirm["turn_step3_condition"] == "prior_pivot_breach"
        assert "2B_BOTTOM" in up_turn["two_b_confirm_type"].tolist()
        assert up_turn["two_b_window_bars"].eq(5).all()
        assert up_turn["two_b_window_basis"].eq("INTERMEDIATE_WITHIN_3_TO_5_BARS").all()

        down_turn = structure_waves.loc[structure_waves["code"] == "BBB"].reset_index(drop=True)
        assert "CONFIRMED_TURN_DOWN" in down_turn["turn_confirm_type"].tolist()
        down_confirm = down_turn.loc[down_turn["turn_confirm_type"] == "CONFIRMED_TURN_DOWN"].iloc[0]
        assert down_confirm["turn_step1_date"] < down_confirm["turn_step2_date"] < down_confirm["turn_step3_date"]
        assert down_confirm["turn_step1_condition"] == "trendline_break"
        assert down_confirm["turn_step2_condition"] == "failed_extreme_test"
        assert down_confirm["turn_step3_condition"] == "prior_pivot_breach"
        assert "2B_TOP" in down_turn["two_b_confirm_type"].tolist()
        assert down_turn["two_b_window_bars"].eq(5).all()
        assert down_turn["two_b_window_basis"].eq("INTERMEDIATE_WITHIN_3_TO_5_BARS").all()

        assert snapshots["latest_confirmed_turn_type"].tolist() == ["CONFIRMED_TURN_UP", "CONFIRMED_TURN_DOWN"]
        assert snapshots["latest_two_b_confirm_type"].tolist() == ["2B_BOTTOM", "2B_TOP"]
        assert snapshots["current_two_b_window_bars"].tolist() == [5, 5]
        assert snapshots["current_two_b_window_basis"].tolist() == [
            "INTERMEDIATE_WITHIN_3_TO_5_BARS",
            "INTERMEDIATE_WITHIN_3_TO_5_BARS",
        ]
        assert set(structure_events.loc[structure_events["code"] == "AAA", "structure_direction"].tolist()) == {"UP"}
        assert set(structure_events.loc[structure_events["code"] == "BBB", "structure_direction"].tolist()) == {
            "DOWN"
        }
        two_b_structure = structure_events.loc[
            structure_events["event_type"].isin(["2B_BOTTOM", "2B_TOP"])
        ].reset_index(drop=True)
        assert not two_b_structure.empty
        assert two_b_structure["confirmation_window_bars"].eq(5).all()
        assert two_b_structure["confirmation_window_basis"].eq("INTERMEDIATE_WITHIN_3_TO_5_BARS").all()
        turn_steps = structure_events.loc[
            structure_events["event_type"].isin(["123_STEP1", "123_STEP2", "123_STEP3"])
        ].reset_index(drop=True)
        assert not turn_steps.empty
        assert set(turn_steps["structure_condition"].tolist()) == {
            "trendline_break",
            "failed_extreme_test",
            "prior_pivot_breach",
        }
    finally:
        store.close()


def test_compute_gene_mirror_writes_market_and_industry_rows(tmp_path) -> None:
    db = tmp_path / "gene_mirror.duckdb"
    store = Store(db)
    try:
        base = date(2026, 1, 5)
        closes_a = [10.0, 11.0, 13.0, 12.0, 9.0, 10.0, 12.0, 11.0, 13.0, 12.0, 14.0, 15.0, 14.5, 14.8]
        closes_b = [8.0, 8.4, 8.9, 8.6, 7.9, 8.0, 8.5, 8.3, 8.9, 8.7, 9.0, 9.2, 9.1, 9.4]
        index_closes = [3200.0, 3210.0, 3235.0, 3220.0, 3190.0, 3205.0, 3230.0, 3225.0, 3240.0, 3230.0, 3255.0, 3270.0, 3265.0, 3278.0]
        industry_a = [1.5, 1.1, -0.5, 1.2, 0.8, 0.6, 1.4, -0.2, 1.0, 0.9, 1.3, 0.7, 0.4, 0.6]
        industry_b = [-0.8, 0.3, -1.1, -0.4, 0.2, -0.3, 0.4, -0.7, 0.1, -0.2, 0.2, -0.1, 0.3, -0.4]
        end = base + timedelta(days=len(closes_a) - 1)

        store.bulk_upsert("l1_trade_calendar", _trade_calendar(base, len(closes_a)))
        store.bulk_upsert(
            "l2_stock_adj_daily",
            pd.DataFrame(_adj_daily_rows(base, "AAA", closes_a) + _adj_daily_rows(base, "BBB", closes_b)),
        )
        store.bulk_upsert("l1_index_daily", pd.DataFrame(_index_daily_rows(base, "000001.SH", index_closes)))
        store.bulk_upsert(
            "l2_industry_daily",
            pd.DataFrame(
                _industry_daily_rows(base, "科技", industry_a, 50_000_000.0)
                + _industry_daily_rows(base, "周期", industry_b, 35_000_000.0)
            ),
        )
        store.bulk_upsert(
            "l2_industry_structure_daily",
            pd.DataFrame(
                [
                    {
                        "industry": "科技",
                        "date": end,
                        "strong_up_count": 8,
                        "new_high_count": 5,
                        "leader_count": 3,
                        "leader_strength": 0.8,
                        "strong_stock_ratio": 0.42,
                        "strong_stock_amount_share": 0.5,
                        "leader_follow_through": 0.65,
                        "bof_hit_density_5d": 0.3,
                    },
                    {
                        "industry": "周期",
                        "date": end,
                        "strong_up_count": 3,
                        "new_high_count": 1,
                        "leader_count": 1,
                        "leader_strength": 0.3,
                        "strong_stock_ratio": 0.18,
                        "strong_stock_amount_share": 0.2,
                        "leader_follow_through": 0.25,
                        "bof_hit_density_5d": 0.1,
                    },
                ]
            ),
        )
        store.bulk_upsert(
            "l2_market_snapshot",
            pd.DataFrame(
                [
                    {
                        "date": end,
                        "total_stocks": 5000,
                        "rise_count": 3200,
                        "fall_count": 1700,
                        "strong_up_count": 420,
                        "strong_down_count": 80,
                        "limit_up_count": 0,
                        "limit_down_count": 0,
                        "touched_limit_up_count": 0,
                        "new_100d_high_count": 260,
                        "new_100d_low_count": 40,
                        "continuous_limit_up_2d": 0,
                        "continuous_limit_up_3d_plus": 0,
                        "continuous_new_high_2d_plus": 80,
                        "high_open_low_close_count": 1200,
                        "low_open_high_close_count": 900,
                        "pct_chg_std": 0.03,
                        "amount_volatility": 500_000.0,
                    }
                ]
            ),
        )

        compute_gene(store, base, end)
        written = compute_gene_mirror(store, end)

        mirror_rows = store.read_df(
            """
            SELECT
                entity_scope,
                entity_code,
                source_table,
                price_source_kind,
                primary_ruler_metric,
                composite_decision_tag,
                mirror_gene_rank,
                primary_ruler_rank,
                support_rise_ratio,
                support_amount_vs_ma20,
                support_follow_through
            FROM l3_gene_mirror
            WHERE calc_date = ?
            ORDER BY entity_scope, mirror_gene_rank, entity_code
            """,
            (end,),
        )

        assert written == 3
        assert mirror_rows["entity_scope"].tolist().count("MARKET") == 1
        assert mirror_rows["entity_scope"].tolist().count("INDUSTRY") == 2
        assert set(mirror_rows["source_table"].tolist()) == {"l1_index_daily", "l2_industry_daily"}
        assert set(mirror_rows["price_source_kind"].tolist()) == {"OHLC_NATIVE", "SYNTHETIC_CLOSE_ONLY"}
        assert mirror_rows["primary_ruler_metric"].isin(
            ["duration_percentile", "magnitude_percentile", "extreme_density_percentile", "gene_score"]
        ).all()
        assert mirror_rows["composite_decision_tag"].ne("").all()

        market_row = mirror_rows.loc[mirror_rows["entity_scope"] == "MARKET"].iloc[0]
        assert float(market_row["support_rise_ratio"]) > 0.6

        industry_rows = mirror_rows.loc[mirror_rows["entity_scope"] == "INDUSTRY"].reset_index(drop=True)
        assert set(industry_rows["mirror_gene_rank"].tolist()) == {1, 2}
        assert industry_rows["support_amount_vs_ma20"].notna().all()
        assert industry_rows["support_follow_through"].notna().all()
    finally:
        store.close()


def test_compute_gene_conditioning_writes_pattern_conditioning_rows(tmp_path) -> None:
    db = tmp_path / "gene_conditioning.duckdb"
    store = Store(db)
    try:
        base = date(2026, 1, 5)

        def bof_specs() -> list[dict[str, float]]:
            specs: list[dict[str, float]] = []
            for _ in range(20):
                specs.append(
                    {
                        "open": 9.95,
                        "high": 10.4,
                        "low": 9.8,
                        "close": 10.0,
                        "volume": 1_000.0,
                        "volume_ma20": 900.0,
                    }
                )
            specs.append(
                {
                    "open": 9.7,
                    "high": 10.5,
                    "low": 9.5,
                    "close": 10.3,
                    "volume": 1_300.0,
                    "volume_ma20": 900.0,
                }
            )
            for close in [10.5, 10.7, 10.9, 11.1, 11.0, 11.3, 11.5, 11.7, 11.8, 12.0, 12.2, 12.1]:
                specs.append({"close": close, "volume": 1_100.0, "volume_ma20": 900.0})
            return specs

        def pb_specs() -> list[dict[str, float]]:
            specs: list[dict[str, float]] = []
            for index in range(20):
                close = 10.0 + index * 0.25
                specs.append(
                    {
                        "close": close,
                        "open": close - 0.08,
                        "high": close + 0.18,
                        "low": close - 0.18,
                        "volume": 1_000.0,
                        "volume_ma20": 900.0,
                    }
                )
            for index in range(15):
                close = 15.2 + index * 0.32
                specs.append(
                    {
                        "close": close,
                        "open": close - 0.08,
                        "high": close + 0.2,
                        "low": close - 0.18,
                        "volume": 1_030.0,
                        "volume_ma20": 900.0,
                    }
                )
            for close in [19.0, 18.5, 18.0, 17.5, 18.8]:
                specs.append(
                    {
                        "close": close,
                        "open": close - 0.08,
                        "high": close + 0.18,
                        "low": close - 0.18,
                        "volume": 980.0,
                        "volume_ma20": 900.0,
                    }
                )
            specs.append(
                {
                    "open": 18.9,
                    "high": 19.8,
                    "low": 18.7,
                    "close": 19.6,
                    "volume": 1_200.0,
                    "volume_ma20": 900.0,
                }
            )
            for close in [19.8, 20.0, 20.2, 20.5, 20.3, 20.6, 20.8, 21.0, 21.2, 21.5, 21.3, 21.4]:
                specs.append({"close": close, "volume": 1_050.0, "volume_ma20": 900.0})
            return specs

        def bpb_specs() -> list[dict[str, float]]:
            specs: list[dict[str, float]] = []
            for close in [
                10.0,
                10.05,
                10.1,
                10.15,
                10.2,
                10.25,
                10.2,
                10.15,
                10.1,
                10.05,
                10.0,
                10.08,
                10.12,
                10.16,
                10.2,
                10.24,
                10.18,
                10.12,
                10.08,
                10.14,
            ]:
                specs.append(
                    {
                        "open": close - 0.05,
                        "high": close + 0.12,
                        "low": close - 0.12,
                        "close": close,
                        "volume": 1_000.0,
                        "volume_ma20": 900.0,
                    }
                )
            specs.extend(
                [
                    {
                        "open": 10.48,
                        "high": 10.7,
                        "low": 10.56,
                        "close": 10.65,
                        "volume": 1_300.0,
                        "volume_ma20": 900.0,
                    },
                    {
                        "open": 10.72,
                        "high": 10.88,
                        "low": 10.7,
                        "close": 10.82,
                        "volume": 1_280.0,
                        "volume_ma20": 900.0,
                    },
                    {
                        "open": 10.78,
                        "high": 10.75,
                        "low": 10.55,
                        "close": 10.62,
                        "volume": 980.0,
                        "volume_ma20": 900.0,
                    },
                    {
                        "open": 10.64,
                        "high": 10.7,
                        "low": 10.52,
                        "close": 10.58,
                        "volume": 970.0,
                        "volume_ma20": 900.0,
                    },
                    {
                        "open": 10.6,
                        "high": 10.72,
                        "low": 10.56,
                        "close": 10.64,
                        "volume": 960.0,
                        "volume_ma20": 900.0,
                    },
                ]
            )
            specs.append(
                {
                    "open": 10.7,
                    "high": 11.05,
                    "low": 10.66,
                    "close": 11.0,
                    "volume": 1_250.0,
                    "volume_ma20": 900.0,
                }
            )
            for close in [11.05, 11.12, 11.2, 11.18, 11.26, 11.3, 11.36, 11.42, 11.48, 11.52, 11.58, 11.6]:
                specs.append({"close": close, "volume": 1_040.0, "volume_ma20": 900.0})
            return specs

        def tst_specs() -> list[dict[str, float]]:
            specs: list[dict[str, float]] = []
            for index in range(55):
                close = 10.35 + (index % 5) * 0.08 + (index // 20) * 0.03
                low = 10.0 if index in (3, 17, 31) else close - 0.18
                specs.append(
                    {
                        "open": close - 0.06,
                        "high": close + 0.18,
                        "low": low,
                        "close": close,
                        "volume": 1_000.0,
                        "volume_ma20": 900.0,
                    }
                )
            for close in [10.18, 10.12, 10.16, 10.1, 10.2]:
                specs.append(
                    {
                        "open": close + 0.02,
                        "high": close + 0.16,
                        "low": 10.05,
                        "close": close,
                        "volume": 980.0,
                        "volume_ma20": 900.0,
                    }
                )
            specs.append(
                {
                    "open": 10.22,
                    "high": 10.55,
                    "low": 10.0,
                    "close": 10.48,
                    "volume": 1_100.0,
                    "volume_ma20": 900.0,
                }
            )
            for close in [10.52, 10.56, 10.6, 10.64, 10.68, 10.72, 10.76, 10.8, 10.84, 10.88, 10.92, 10.96]:
                specs.append({"close": close, "volume": 1_020.0, "volume_ma20": 900.0})
            return specs

        def cpb_specs() -> list[dict[str, float]]:
            specs: list[dict[str, float]] = []
            for close in [
                10.1,
                10.2,
                10.15,
                10.25,
                10.2,
                10.18,
                10.22,
                10.16,
                10.24,
                10.19,
                10.23,
                10.17,
                10.25,
                10.2,
                10.24,
                10.18,
                10.26,
                10.21,
                10.25,
                10.2,
            ]:
                specs.append(
                    {
                        "open": close - 0.05,
                        "high": close + 0.15,
                        "low": close - 0.15,
                        "close": close,
                        "volume": 1_000.0,
                        "volume_ma20": 900.0,
                    }
                )
            for index in range(20):
                close = 10.2 + (index % 3) * 0.03
                specs.append(
                    {
                        "open": close - 0.05,
                        "high": close + 0.12,
                        "low": close - 0.12,
                        "close": close,
                        "volume": 1_020.0,
                        "volume_ma20": 900.0,
                    }
                )
            specs.append(
                {
                    "open": 10.4,
                    "high": 10.8,
                    "low": 10.35,
                    "close": 10.75,
                    "volume": 1_300.0,
                    "volume_ma20": 900.0,
                }
            )
            for close in [10.82, 10.88, 10.95, 11.0, 10.98, 11.05, 11.12, 11.2, 11.18, 11.26, 11.3, 11.28]:
                specs.append({"close": close, "volume": 1_040.0, "volume_ma20": 900.0})
            return specs

        spec_map = {
            "BOF": bof_specs(),
            "BPB": bpb_specs(),
            "PB": pb_specs(),
            "TST": tst_specs(),
            "CPB": cpb_specs(),
        }
        max_len = max(len(specs) for specs in spec_map.values())
        for specs in spec_map.values():
            while len(specs) < max_len:
                specs.append(
                    {
                        "close": float(specs[-1]["close"]) + 0.05,
                        "volume": 1_040.0,
                        "volume_ma20": 900.0,
                    }
                )
        end = base + timedelta(days=max_len - 1)

        store.bulk_upsert("l1_trade_calendar", _trade_calendar(base, max_len))
        stock_rows: list[dict[str, object]] = []
        for code, specs in spec_map.items():
            stock_rows.extend(_adj_daily_rows_from_specs(base, code, specs))
        store.bulk_upsert("l2_stock_adj_daily", pd.DataFrame(stock_rows))

        compute_gene(store, base, end)
        written = compute_gene_conditioning(store, end)

        conditioning_rows = store.read_df(
            """
            SELECT
                signal_pattern,
                sample_scope,
                conditioning_key,
                conditioning_value,
                sample_size,
                hit_rate,
                avg_forward_return_pct,
                edge_tag
            FROM l3_gene_conditioning_eval
            WHERE calc_date = ?
            ORDER BY signal_pattern, conditioning_key, conditioning_value
            """,
            (end,),
        )
        baseline_rows = conditioning_rows.loc[conditioning_rows["conditioning_key"] == "ALL"].reset_index(drop=True)

        assert written > 0
        assert not conditioning_rows.empty
        assert set(conditioning_rows["signal_pattern"].tolist()) == {"bof", "bpb", "pb", "tst", "cpb"}
        assert conditioning_rows["sample_scope"].eq("PAS_DETECTOR_TRIGGER").all()
        assert set(conditioning_rows["conditioning_key"].tolist()) >= {
            "ALL",
            "current_wave_age_band",
            "current_wave_direction",
            "current_wave_magnitude_band",
            "latest_confirmed_turn_type",
            "latest_two_b_confirm_type",
            "streak_bucket",
        }
        assert len(baseline_rows) == 5
        assert baseline_rows["conditioning_value"].eq("ALL").all()
        assert baseline_rows["edge_tag"].eq("BASELINE").all()
        assert baseline_rows["sample_size"].gt(0).all()
        assert conditioning_rows["hit_rate"].between(0.0, 1.0).all()
        assert conditioning_rows["avg_forward_return_pct"].notna().all()
    finally:
        store.close()
