from __future__ import annotations

from datetime import date

import pandas as pd

from src.config import Settings
from src.data.store import Store
from src.selector.selector import _persist_selector_candidate_trace


def test_selector_trace_persist_tolerates_missing_preselect_score_column(tmp_path) -> None:
    db = tmp_path / "selector_trace_preselect_missing.duckdb"
    store = Store(db)
    calc_date = date(2026, 1, 10)

    annotated = pd.DataFrame(
        [
            {
                "code": "000001",
                "industry": "银行",
                "amount": 3e8,
                "volume_ratio": 1.2,
                "filters_passed": "LIST_STATUS;HALT;ST;LIST_DAYS;AMOUNT",
                "reject_reason": "",
                "liquidity_tag": "HIGH",
                "score": 12.34,
            }
        ]
    )
    ranked_all = pd.DataFrame([{"code": "000001", "score": 12.34}])
    ranked_top_n = pd.DataFrame([{"code": "000001", "score": 12.34}])

    _persist_selector_candidate_trace(
        store=store,
        calc_date=calc_date,
        cfg=Settings(PIPELINE_MODE="dtt"),
        run_id="selector_trace_preselect_missing",
        annotated=annotated,
        ranked_all=ranked_all,
        ranked_top_n=ranked_top_n,
    )

    trace = store.get_selector_candidate_trace("selector_trace_preselect_missing", calc_date, "000001")
    assert trace is not None
    assert pd.isna(trace["preselect_score"])
    assert float(trace["final_score"]) == 12.34
    assert bool(trace["selected"]) is True
    store.close()
