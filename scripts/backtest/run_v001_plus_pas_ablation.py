from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.backtest.pas_ablation import run_pas_ablation, write_pas_ablation_evidence
from src.config import get_settings
from src.run_metadata import build_artifact_name, build_run_id, sanitize_label


def _parse_date(text: str) -> date:
    return date.fromisoformat(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run v0.01-plus PAS registry ablation")
    parser.add_argument("--start", required=True, help="Backtest start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="Backtest end date (YYYY-MM-DD)")
    parser.add_argument(
        "--dtt-variant",
        default=None,
        help="DTT variant to keep fixed during PAS ablation; default uses current config.dtt_variant",
    )
    parser.add_argument("--cash", type=float, default=None, help="Initial cash override")
    parser.add_argument("--db-path", default=None, help="Execution DuckDB path override")
    parser.add_argument(
        "--skip-rebuild-l3",
        action="store_true",
        help="Reuse existing l3_mss_daily/l3_irs_daily in the working DB instead of rebuilding them",
    )
    parser.add_argument(
        "--working-db-path",
        default=None,
        help="Optional working copy DuckDB path; default uses TEMP_PATH/backtest",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path, default docs/spec/v0.01-plus/evidence/<run_id>__pas_ablation.json",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cfg = get_settings().model_copy(deep=True)
    start = _parse_date(args.start)
    end = _parse_date(args.end)
    dtt_variant = sanitize_label(args.dtt_variant or cfg.dtt_variant)
    db_path = Path(args.db_path).expanduser().resolve() if args.db_path else cfg.db_path
    working_db_path = (
        Path(args.working_db_path).expanduser().resolve()
        if args.working_db_path
        else cfg.resolved_temp_path / "backtest" / f"pas-ablation-{date.today():%Y%m%d}.duckdb"
    )
    output_root = REPO_ROOT / "docs" / "spec" / "v0.01-plus" / "evidence"
    summary_run_id = build_run_id(
        scope="pas_ablation",
        mode="dtt",
        variant=f"{dtt_variant}_pas_registry_matrix",
        start=start,
        end=end,
    )
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else output_root / build_artifact_name(summary_run_id, "pas_ablation", "json")
    )

    payload = run_pas_ablation(
        db_path=db_path,
        config=cfg,
        start=start,
        end=end,
        dtt_variant=dtt_variant,
        initial_cash=args.cash,
        rebuild_l3=not args.skip_rebuild_l3,
        working_db_path=working_db_path,
        artifact_root=cfg.resolved_temp_path / "artifacts",
    )
    payload["summary_run_id"] = summary_run_id
    path = write_pas_ablation_evidence(output_path, payload)
    print(f"pas_ablation={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
