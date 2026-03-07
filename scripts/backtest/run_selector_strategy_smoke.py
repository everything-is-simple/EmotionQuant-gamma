from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.backtest.ablation import clear_runtime_tables, prepare_working_db
from src.config import get_settings
from src.contracts import StockCandidate
from src.data.builder import build_layers
from src.data.store import Store
from src.run_metadata import build_artifact_name, finish_run, start_run
from src.selector.selector import select_candidates_frame
from src.strategy.strategy import generate_signals


def _parse_date(text: str) -> date:
    return date.fromisoformat(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one selector -> strategy smoke chain and emit evidence")
    parser.add_argument("--calc-date", required=True, help="Signal date / calc date (YYYY-MM-DD)")
    parser.add_argument("--db-path", default=None, help="Execution DuckDB path override")
    parser.add_argument(
        "--working-db-path",
        default=None,
        help="Optional working copy DuckDB path; default uses a temp copy instead of mutating the live DB",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path, default docs/spec/v0.01-plus/evidence/<run_id>__selector_strategy_smoke.json",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cfg = get_settings().model_copy(deep=True)
    calc_date = _parse_date(args.calc_date)
    source_db_path = Path(args.db_path).expanduser().resolve() if args.db_path else cfg.db_path
    working_db_path = (
        Path(args.working_db_path).expanduser().resolve()
        if args.working_db_path
        else cfg.resolved_temp_path / "backtest" / f"selector-strategy-smoke-{date.today():%Y%m%d}.duckdb"
    )
    db_path = prepare_working_db(source_db_path, working_db_path)

    store = Store(db_path)
    output_root = REPO_ROOT / "docs" / "spec" / "v0.01-plus" / "evidence"
    run = start_run(
        store=store,
        scope="smoke",
        modules=["selector", "strategy"],
        config=cfg,
        runtime_env="script",
        artifact_root=str(output_root.resolve()),
        signal_date=calc_date,
    )
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else output_root / build_artifact_name(run.run_id, "selector_strategy_smoke", "json")
    )
    try:
        clear_runtime_tables(store)
        build_rows = build_layers(store, cfg, layers=["l3"], start=calc_date, end=calc_date, force=False)
        candidates_df = select_candidates_frame(store, calc_date, cfg)
        candidates = [
            StockCandidate(
                code=str(row["code"]),
                industry=str(row["industry"]),
                score=float(row["score"]),
                preselect_score=float(row["preselect_score"]) if "preselect_score" in row else float(row["score"]),
            )
            for _, row in candidates_df.iterrows()
        ]
        signals = generate_signals(store, candidates, calc_date, cfg, run_id=run.run_id)

        payload = {
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "run_id": run.run_id,
            "mode": run.mode,
            "variant": run.variant,
            "source_db_path": str(source_db_path),
            "db_path": str(db_path),
            "calc_date": calc_date.isoformat(),
            "build_rows": int(build_rows),
            "candidates_count": int(len(candidates_df)),
            "signals_count": int(len(signals)),
            "sample_candidates": candidates_df.head(10).to_dict(orient="records"),
            "sample_signals": [signal.model_dump(mode="json") for signal in signals[:10]],
        }
        finish_run(store, run.run_id, "SUCCESS")
    except Exception as exc:
        finish_run(store, run.run_id, "FAILED", str(exc))
        raise
    finally:
        store.close()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"selector_strategy_smoke={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
