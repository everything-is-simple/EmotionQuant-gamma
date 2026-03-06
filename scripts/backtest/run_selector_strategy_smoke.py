from __future__ import annotations

import argparse
from datetime import date, datetime
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.backtest.ablation import clear_runtime_tables
from src.config import get_settings
from src.contracts import StockCandidate
from src.data.builder import build_layers
from src.data.store import Store
from src.selector.selector import select_candidates_frame
from src.strategy.strategy import generate_signals


def _parse_date(text: str) -> date:
    return date.fromisoformat(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one selector -> strategy smoke chain and emit evidence")
    parser.add_argument("--calc-date", required=True, help="Signal date / calc date (YYYY-MM-DD)")
    parser.add_argument("--db-path", default=None, help="Execution DuckDB path override")
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path, default docs/spec/v0.01/evidence/v0.01-selector-strategy-smoke-YYYYMMDD.json",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cfg = get_settings().model_copy(deep=True)
    calc_date = _parse_date(args.calc_date)
    db_path = Path(args.db_path).expanduser().resolve() if args.db_path else cfg.db_path
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else REPO_ROOT / "docs" / "spec" / "v0.01" / "evidence" / f"v0.01-selector-strategy-smoke-{date.today():%Y%m%d}.json"
    )

    store = Store(db_path)
    try:
        clear_runtime_tables(store)
        build_rows = build_layers(store, cfg, layers=["l3"], start=calc_date, end=calc_date, force=False)
        candidates_df = select_candidates_frame(store, calc_date, cfg)
        candidates = [
            StockCandidate(code=str(row["code"]), industry=str(row["industry"]), score=float(row["score"]))
            for _, row in candidates_df.iterrows()
        ]
        signals = generate_signals(store, candidates, calc_date, cfg)

        payload = {
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "db_path": str(db_path),
            "calc_date": calc_date.isoformat(),
            "build_rows": int(build_rows),
            "candidates_count": int(len(candidates_df)),
            "signals_count": int(len(signals)),
            "sample_candidates": candidates_df.head(10).to_dict(orient="records"),
            "sample_signals": [signal.model_dump(mode="json") for signal in signals[:10]],
        }
    finally:
        store.close()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"selector_strategy_smoke={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
