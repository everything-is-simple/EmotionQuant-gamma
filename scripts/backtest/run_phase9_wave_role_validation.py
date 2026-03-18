from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.backtest.phase9_wave_role_validation import (
    PHASE9_WAVE_ROLE_VALIDATION_SCOPE,
    run_phase9_wave_role_validation,
    write_phase9_wave_role_validation_evidence,
)
from src.config import get_settings
from src.run_metadata import build_artifact_name, build_run_id, sanitize_label


def _parse_date(text: str) -> date:
    return date.fromisoformat(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Phase 9B wave_role isolated validation")
    parser.add_argument("--start", required=True, help="Validation start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="Validation end date (YYYY-MM-DD)")
    parser.add_argument(
        "--blocked-role",
        default="COUNTERTREND",
        help="Wave role to block as the isolated negative filter",
    )
    parser.add_argument("--cash", type=float, default=None, help="Initial cash override")
    parser.add_argument("--db-path", default=None, help="Execution DuckDB path override")
    parser.add_argument(
        "--skip-rebuild-l3",
        action="store_true",
        help="Reuse existing l3_* tables in the working DB instead of rebuilding them",
    )
    parser.add_argument(
        "--working-db-path",
        default=None,
        help="Optional working copy DuckDB path; default uses TEMP_PATH/backtest",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path; default docs/spec/v0.01-plus/evidence/<run_id>__phase9_wave_role_validation.json",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cfg = get_settings().model_copy(deep=True)
    start = _parse_date(args.start)
    end = _parse_date(args.end)
    blocked_role = str(args.blocked_role).strip().upper()
    initial_cash = float(args.cash if args.cash is not None else cfg.backtest_initial_cash)
    db_path = Path(args.db_path).expanduser().resolve() if args.db_path else cfg.db_path
    working_db_path = (
        Path(args.working_db_path).expanduser().resolve()
        if args.working_db_path
        else cfg.resolved_temp_path / "backtest" / f"phase9-wave-role-validation-{date.today():%Y%m%d}.duckdb"
    )
    output_root = REPO_ROOT / "docs" / "spec" / "v0.01-plus" / "evidence"
    variant_slug = sanitize_label(f"wave_role_negative_filter_{blocked_role.lower()}")
    summary_run_id = build_run_id(
        scope=PHASE9_WAVE_ROLE_VALIDATION_SCOPE,
        mode="legacy",
        variant=variant_slug,
        start=start,
        end=end,
    )
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else output_root / build_artifact_name(summary_run_id, "phase9_wave_role_validation", "json")
    )

    payload = run_phase9_wave_role_validation(
        db_path=db_path,
        config=cfg,
        start=start,
        end=end,
        blocked_role=blocked_role,
        initial_cash=initial_cash,
        rebuild_l3=not args.skip_rebuild_l3,
        working_db_path=working_db_path,
        artifact_root=cfg.resolved_temp_path / "artifacts",
    )
    payload["summary_run_id"] = summary_run_id
    path = write_phase9_wave_role_validation_evidence(output_path, payload)
    print(f"phase9_wave_role_validation={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
