from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.backtest.ablation import prepare_working_db
from src.config import get_settings
from src.data.store import Store
from src.selector.gene import (
    GENE_LOOKBACK_TRADE_DAYS,
    _lookback_trade_start,
    compute_gene,
    compute_gene_conditioning,
    compute_gene_mirror,
    compute_gene_validation,
)


def _parse_date(text: str) -> date:
    return date.fromisoformat(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run GX13 post-remediation G4/G5/G6 revalidation")
    parser.add_argument("--asof", default="2026-02-24", help="As-of trade date (YYYY-MM-DD)")
    parser.add_argument("--db-path", default=None, help="Source execution DuckDB path")
    parser.add_argument(
        "--working-db-path",
        default=None,
        help="Working copy DuckDB path; default uses TEMP_PATH/gene",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Evidence JSON output path; default uses TEMP_PATH/artifacts",
    )
    return parser


def _read_df_records(store: Store, sql: str, params: tuple[object, ...] = ()) -> list[dict[str, object]]:
    frame = store.read_df(sql, params)
    if frame.empty:
        return []
    records = frame.where(frame.notna(), None).to_dict(orient="records")
    normalized: list[dict[str, object]] = []
    for row in records:
        normalized_row: dict[str, object] = {}
        for key, value in row.items():
            if isinstance(value, date):
                normalized_row[key] = value.isoformat()
            else:
                normalized_row[key] = value
        normalized.append(normalized_row)
    return normalized


def _prepare_slim_gene_working_db(source_db: Path, working_db: Path, asof: date) -> Path:
    source_store = Store(source_db)
    try:
        start = _lookback_trade_start(source_store, asof, GENE_LOOKBACK_TRADE_DAYS)
    finally:
        source_store.close()

    if working_db.exists():
        working_db.unlink()
    working_store = Store(working_db)
    try:
        source_db_sql = str(source_db).replace("'", "''")
        working_store.conn.execute(f"ATTACH '{source_db_sql}' AS sourcedb")
        date_tables = [
            "l1_trade_calendar",
            "l2_stock_adj_daily",
            "l1_index_daily",
            "l2_industry_daily",
            "l2_industry_structure_daily",
            "l2_market_snapshot",
        ]
        for table in date_tables:
            working_store.conn.execute(f"DELETE FROM {table}")
        working_store.conn.execute(
            "INSERT INTO l1_trade_calendar SELECT * FROM sourcedb.l1_trade_calendar WHERE date BETWEEN ? AND ?",
            [start, asof],
        )
        working_store.conn.execute(
            "INSERT INTO l2_stock_adj_daily SELECT * FROM sourcedb.l2_stock_adj_daily WHERE date BETWEEN ? AND ?",
            [start, asof],
        )
        working_store.conn.execute(
            "INSERT INTO l1_index_daily SELECT * FROM sourcedb.l1_index_daily WHERE date BETWEEN ? AND ?",
            [start, asof],
        )
        working_store.conn.execute(
            "INSERT INTO l2_industry_daily SELECT * FROM sourcedb.l2_industry_daily WHERE date BETWEEN ? AND ?",
            [start, asof],
        )
        working_store.conn.execute(
            """
            INSERT INTO l2_industry_structure_daily
            SELECT *
            FROM sourcedb.l2_industry_structure_daily
            WHERE date BETWEEN ? AND ?
            """,
            [start, asof],
        )
        working_store.conn.execute(
            "INSERT INTO l2_market_snapshot SELECT * FROM sourcedb.l2_market_snapshot WHERE date BETWEEN ? AND ?",
            [start, asof],
        )
        working_store.conn.execute("DETACH sourcedb")
        return working_db
    finally:
        working_store.close()


def run_gx13_revalidation(
    *,
    source_db: Path,
    working_db: Path,
    asof: date,
) -> dict[str, object]:
    working_path = _prepare_slim_gene_working_db(source_db, working_db, asof)
    store = Store(working_path)
    try:
        compute_gene_rows = int(compute_gene(store, asof, asof))
        compute_gene_validation_rows = int(compute_gene_validation(store, asof))
        compute_gene_mirror_rows = int(compute_gene_mirror(store, asof))
        compute_gene_conditioning_rows = int(compute_gene_conditioning(store, asof))
        schema_version = int(store.get_schema_version().schema_version)

        g4_rows = _read_df_records(
            store,
            """
            SELECT
                metric_name,
                sample_size,
                monotonicity_score,
                avg_daily_rank_corr,
                positive_daily_rank_corr_rate,
                decision_tag
            FROM l3_gene_validation_eval
            WHERE calc_date = ?
              AND sample_scope = 'SELF_HISTORY_CURRENT_WAVE'
            ORDER BY CASE metric_name
                WHEN 'duration_percentile' THEN 1
                WHEN 'magnitude_percentile' THEN 2
                WHEN 'extreme_density_percentile' THEN 3
                WHEN 'gene_score' THEN 4
                ELSE 99
            END
            """,
            (asof,),
        )
        market_rows = _read_df_records(
            store,
            """
            SELECT
                entity_code,
                current_wave_direction,
                gene_score,
                primary_ruler_metric,
                primary_ruler_value,
                mirror_gene_rank,
                primary_ruler_rank,
                support_rise_ratio,
                support_strong_ratio,
                support_new_high_ratio,
                composite_decision_tag
            FROM l3_gene_mirror
            WHERE calc_date = ?
              AND entity_scope = 'MARKET'
            ORDER BY entity_code
            """,
            (asof,),
        )
        industry_by_mirror_rows = _read_df_records(
            store,
            """
            SELECT
                entity_code,
                current_wave_direction,
                gene_score,
                mirror_gene_rank,
                primary_ruler_rank
            FROM l3_gene_mirror
            WHERE calc_date = ?
              AND entity_scope = 'INDUSTRY'
            ORDER BY mirror_gene_rank, entity_code
            LIMIT 5
            """,
            (asof,),
        )
        industry_by_primary_rows = _read_df_records(
            store,
            """
            SELECT
                entity_code,
                current_wave_direction,
                primary_ruler_metric,
                primary_ruler_value,
                primary_ruler_rank,
                mirror_gene_rank
            FROM l3_gene_mirror
            WHERE calc_date = ?
              AND entity_scope = 'INDUSTRY'
            ORDER BY primary_ruler_rank, entity_code
            LIMIT 5
            """,
            (asof,),
        )
        g6_baseline_rows = _read_df_records(
            store,
            """
            SELECT
                signal_pattern,
                sample_size,
                hit_rate,
                avg_forward_return_pct
            FROM l3_gene_conditioning_eval
            WHERE calc_date = ?
              AND sample_scope = 'PAS_DETECTOR_TRIGGER'
              AND conditioning_key = 'ALL'
              AND conditioning_value = 'ALL'
            ORDER BY signal_pattern
            """,
            (asof,),
        )
        g6_better_rows = _read_df_records(
            store,
            """
            SELECT
                signal_pattern,
                conditioning_key,
                conditioning_value,
                payoff_delta_vs_pattern_baseline,
                edge_tag
            FROM l3_gene_conditioning_eval
            WHERE calc_date = ?
              AND sample_scope = 'PAS_DETECTOR_TRIGGER'
              AND edge_tag = 'BETTER'
            ORDER BY payoff_delta_vs_pattern_baseline DESC, signal_pattern, conditioning_key, conditioning_value
            LIMIT 10
            """,
            (asof,),
        )
        g6_worse_rows = _read_df_records(
            store,
            """
            SELECT
                signal_pattern,
                conditioning_key,
                conditioning_value,
                payoff_delta_vs_pattern_baseline,
                edge_tag
            FROM l3_gene_conditioning_eval
            WHERE calc_date = ?
              AND sample_scope = 'PAS_DETECTOR_TRIGGER'
              AND edge_tag = 'WORSE'
            ORDER BY payoff_delta_vs_pattern_baseline ASC, signal_pattern, conditioning_key, conditioning_value
            LIMIT 10
            """,
            (asof,),
        )
        return {
            "asof": asof.isoformat(),
            "source_db": str(source_db),
            "working_db": str(working_path),
            "schema_version": schema_version,
            "write_counts": {
                "compute_gene_rows": compute_gene_rows,
                "compute_gene_validation_rows": compute_gene_validation_rows,
                "compute_gene_mirror_rows": compute_gene_mirror_rows,
                "compute_gene_conditioning_rows": compute_gene_conditioning_rows,
            },
            "g4_validation": g4_rows,
            "g5_market": market_rows,
            "g5_industry_top_by_mirror_rank": industry_by_mirror_rows,
            "g5_industry_top_by_primary_rank": industry_by_primary_rows,
            "g6_baseline": g6_baseline_rows,
            "g6_better_examples": g6_better_rows,
            "g6_worse_examples": g6_worse_rows,
        }
    finally:
        store.close()


def main() -> int:
    args = build_parser().parse_args()
    cfg = get_settings()
    asof = _parse_date(args.asof)
    source_db = Path(args.db_path).expanduser().resolve() if args.db_path else cfg.db_path
    working_db = (
        Path(args.working_db_path).expanduser().resolve()
        if args.working_db_path
        else cfg.resolved_temp_path / "gene" / f"gx13-post-remediation-revalidation-{asof:%Y%m%d}.duckdb"
    )
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else cfg.resolved_temp_path / "artifacts" / f"gx13_post_remediation_revalidation_{asof:%Y%m%d}.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = run_gx13_revalidation(source_db=source_db, working_db=working_db, asof=asof)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
