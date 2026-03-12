from __future__ import annotations

from datetime import date

import pandas as pd

from src.backtest.normandy_tachibana_alpha import (
    _generate_normandy_tachibana_signals,
    _load_tachibana_candidate_histories_batch,
    build_normandy_tachibana_alpha_digest,
    build_normandy_tachibana_alpha_scenarios,
)
from src.config import Settings
from src.contracts import StockCandidate


def test_build_normandy_tachibana_alpha_scenarios_returns_control_and_candidate() -> None:
    scenarios = build_normandy_tachibana_alpha_scenarios(Settings())
    assert [scenario.label for scenario in scenarios] == [
        "BOF_CONTROL",
        "TACHI_CROWD_FAILURE",
    ]
    assert scenarios[0].control is True
    assert scenarios[1].signal_pattern == "tachi_crowd_failure"


def test_build_normandy_tachibana_alpha_digest_marks_contrary_candidate() -> None:
    matrix_payload = {
        "summary_run_id": "normandy_tachibana_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20240101_20241231_t000001",
        "start": "2024-01-01",
        "end": "2024-12-31",
        "dtt_variant": "v0_01_dtt_pattern_only",
        "matrix_status": "completed",
        "results": [
            {
                "label": "BOF_CONTROL",
                "family": "BOF_CONTROL",
                "trade_count": 80,
                "expected_value": 0.02,
                "profit_factor": 1.40,
                "max_drawdown": 0.18,
                "participation_rate": 0.30,
                "overlap_rate_vs_bof_control": 1.0,
                "incremental_buy_trades_vs_bof_control": 0,
            },
            {
                "label": "TACHI_CROWD_FAILURE",
                "family": "TACHIBANA_CONTRARY",
                "trade_count": 42,
                "expected_value": 0.05,
                "profit_factor": 1.30,
                "max_drawdown": 0.22,
                "participation_rate": 0.14,
                "overlap_rate_vs_bof_control": 0.45,
                "incremental_buy_trades_vs_bof_control": 27,
            },
        ],
    }

    digest = build_normandy_tachibana_alpha_digest(matrix_payload)

    assert digest["provenance_leader"] == "TACHI_CROWD_FAILURE"
    assert digest["contrary_alpha_candidates"] == ["TACHI_CROWD_FAILURE"]
    assert digest["scorecard"][0]["label"] == "TACHI_CROWD_FAILURE"
    assert "TACHI_CROWD_FAILURE" in digest["conclusion"]


def test_build_normandy_tachibana_alpha_digest_keeps_unqualified_candidate_as_observation() -> None:
    matrix_payload = {
        "summary_run_id": "normandy_tachibana_alpha_matrix_dtt_v0_01_dtt_pattern_only_w20240101_20241231_t000002",
        "start": "2024-01-01",
        "end": "2024-12-31",
        "dtt_variant": "v0_01_dtt_pattern_only",
        "matrix_status": "completed",
        "results": [
            {
                "label": "BOF_CONTROL",
                "family": "BOF_CONTROL",
                "trade_count": 80,
                "expected_value": 0.02,
                "profit_factor": 1.40,
                "max_drawdown": 0.18,
                "participation_rate": 0.30,
                "overlap_rate_vs_bof_control": 1.0,
                "incremental_buy_trades_vs_bof_control": 0,
            },
            {
                "label": "TACHI_CROWD_FAILURE",
                "family": "TACHIBANA_CONTRARY",
                "trade_count": 11,
                "expected_value": -0.01,
                "profit_factor": 0.80,
                "max_drawdown": 0.16,
                "participation_rate": 0.03,
                "overlap_rate_vs_bof_control": 0.90,
                "incremental_buy_trades_vs_bof_control": 6,
            },
        ],
    }

    digest = build_normandy_tachibana_alpha_digest(matrix_payload)

    assert digest["contrary_alpha_candidates"] == []
    assert digest["provenance_leader"] == "TACHI_CROWD_FAILURE"
    assert "观测对象" in digest["conclusion"]


def test_generate_normandy_tachibana_signals_loads_histories_in_batches(monkeypatch) -> None:
    scenario = build_normandy_tachibana_alpha_scenarios(Settings())[1]
    config = Settings(PAS_EVAL_BATCH_SIZE=2, ENABLE_DTT_MODE=False, PIPELINE_MODE="legacy")
    candidates = [
        StockCandidate(
            code="000001",
            industry="BANK",
            score=1.0,
            trade_date=date(2024, 1, 31),
            preselect_score=1.0,
            candidate_rank=1,
        ),
        StockCandidate(
            code="000002",
            industry="BANK",
            score=1.0,
            trade_date=date(2024, 1, 31),
            preselect_score=1.0,
            candidate_rank=2,
        ),
        StockCandidate(
            code="000003",
            industry="BANK",
            score=1.0,
            trade_date=date(2024, 1, 31),
            preselect_score=1.0,
            candidate_rank=3,
        ),
    ]
    load_batches: list[list[str]] = []

    def fake_load_candidate_histories_batch(store, codes, asof_date, lookback_days):
        load_batches.append(list(codes))
        rows: list[dict[str, object]] = []
        for code in codes:
            for offset in range(31):
                rows.append(
                    {
                        "code": code,
                        "date": date(2024, 1, 1),
                        "adj_low": 1.0,
                        "adj_close": 1.0,
                        "adj_open": 1.0,
                        "adj_high": 1.0,
                        "volume": 1.0,
                        "volume_ma20": 1.0,
                        "ma20": 1.0,
                        "volume_ratio": 1.0,
                    }
                )
        return pd.DataFrame(rows)

    class FakeDetector:
        required_window = 31

        def evaluate(self, code, asof_date, history):
            return None, {"detected": False, "detect_reason": "TEST"}

    class FakeStore:
        db_path = "test.duckdb"

        def bulk_upsert(self, table_name, frame):
            return None

    class FakeHistoryConn:
        def close(self):
            return None

    monkeypatch.setattr(
        "src.backtest.normandy_tachibana_alpha._load_tachibana_candidate_histories_batch",
        fake_load_candidate_histories_batch,
    )
    monkeypatch.setattr(
        "src.backtest.normandy_tachibana_alpha._build_detector",
        lambda _config, _scenario: FakeDetector(),
    )
    monkeypatch.setattr(
        "src.backtest.normandy_tachibana_alpha.duckdb.connect",
        lambda *_args, **_kwargs: FakeHistoryConn(),
    )

    signals = _generate_normandy_tachibana_signals(
        store=FakeStore(),
        candidates=candidates,
        asof_date=date(2024, 1, 31),
        scenario=scenario,
        config=config,
        run_id="test-run",
    )

    assert signals == []
    assert load_batches == [["000001", "000002"], ["000003"]]


def test_load_tachibana_candidate_histories_batch_falls_back_for_missing_codes(monkeypatch) -> None:
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeConn:
        def execute(self, sql, params):
            calls.append(("execute", tuple(params)))

            class FakeResult:
                def df(self_nonlocal):
                    if "000002" in params and "000001" not in params:
                        return pd.DataFrame(
                            [
                                {
                                    "code": "000002",
                                    "date": date(2024, 1, 29),
                                    "adj_low": 2.0,
                                    "adj_close": 2.0,
                                    "adj_open": 2.0,
                                    "adj_high": 2.0,
                                    "volume": 2.0,
                                    "volume_ma20": 2.0,
                                    "ma20": 2.0,
                                    "volume_ratio": 2.0,
                                },
                                {
                                    "code": "000002",
                                    "date": date(2024, 1, 30),
                                    "adj_low": 2.0,
                                    "adj_close": 2.0,
                                    "adj_open": 2.0,
                                    "adj_high": 2.0,
                                    "volume": 2.0,
                                    "volume_ma20": 2.0,
                                    "ma20": 2.0,
                                    "volume_ratio": 2.0,
                                },
                            ]
                        )
                    return pd.DataFrame(
                        [
                            {
                                "code": "000001",
                                "date": date(2024, 1, 29),
                                "adj_low": 1.0,
                                "adj_close": 1.0,
                                "adj_open": 1.0,
                                "adj_high": 1.0,
                                "volume": 1.0,
                                "volume_ma20": 1.0,
                                "ma20": 1.0,
                                "volume_ratio": 1.0,
                            },
                            {
                                "code": "000001",
                                "date": date(2024, 1, 30),
                                "adj_low": 1.0,
                                "adj_close": 1.0,
                                "adj_open": 1.0,
                                "adj_high": 1.0,
                                "volume": 1.0,
                                "volume_ma20": 1.0,
                                "ma20": 1.0,
                                "volume_ratio": 1.0,
                            },
                        ]
                    )

            return FakeResult()

    class FakeStore:
        conn = FakeConn()

        def read_df(self, sql, params):
            return self.conn.execute(sql, params).df()

    frame = _load_tachibana_candidate_histories_batch(
        reader=FakeStore(),
        codes=["000001", "000002"],
        asof_date=date(2024, 1, 31),
        lookback_days=2,
    )

    assert sorted(frame["code"].unique().tolist()) == ["000001", "000002"]
    execute_params = calls[0][1]
    assert execute_params[-3] == date(2023, 8, 4)
    assert execute_params[-2] == date(2024, 1, 31)
    assert execute_params[-1] == 2
