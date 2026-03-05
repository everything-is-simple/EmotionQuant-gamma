from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import duckdb


@dataclass(frozen=True)
class CoverageStats:
    total_rows: int
    hit_rows: int
    miss_rows: int
    hit_rate: float
    avg_lag_days: float | None
    p50_lag_days: float | None
    p95_lag_days: float | None
    max_lag_days: int | None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build G6 as-of coverage evidence")
    parser.add_argument("--target-db", default=r"G:\EmotionQuant_data\emotionquant.duckdb")
    parser.add_argument("--source-db", default=r"G:\EmotionQuant_data\duckdb\emotionquant.duckdb")
    parser.add_argument("--start", default="2023-01-01")
    parser.add_argument("--end", default="2026-02-24")
    parser.add_argument(
        "--output",
        default="docs/spec/v0.01/v0.01-g6-asof-evidence-20260305.json",
        help="Evidence JSON output path",
    )
    return parser


def _to_float(value) -> float | None:
    if value is None:
        return None
    return float(value)


def _to_int(value) -> int | None:
    if value is None:
        return None
    return int(value)


def _fetch_source_boundary(con: duckdb.DuckDBPyConnection) -> dict:
    # 源快照频率边界：trade_date 不是日更，存在长间隔，这会传导到 as-of 新鲜度。
    all_stats = con.execute(
        """
        SELECT
          MIN(STRPTIME(trade_date, '%Y%m%d')::DATE) AS min_date,
          MAX(STRPTIME(trade_date, '%Y%m%d')::DATE) AS max_date,
          COUNT(*) AS rows,
          COUNT(DISTINCT trade_date) AS snapshot_days
        FROM rawdb.raw_stock_basic
        """
    ).fetchone()

    gap_stats = con.execute(
        """
        WITH d AS (
          SELECT DISTINCT STRPTIME(trade_date, '%Y%m%d')::DATE AS d
          FROM rawdb.raw_stock_basic
          WHERE trade_date IS NOT NULL
        ),
        g AS (
          SELECT d, LAG(d) OVER (ORDER BY d) AS prev_d
          FROM d
        )
        SELECT
          AVG(CASE WHEN prev_d IS NOT NULL THEN DATE_DIFF('day', prev_d, d) END) AS avg_gap,
          MEDIAN(CASE WHEN prev_d IS NOT NULL THEN DATE_DIFF('day', prev_d, d) END) AS p50_gap,
          QUANTILE_CONT(CASE WHEN prev_d IS NOT NULL THEN DATE_DIFF('day', prev_d, d) END, 0.95) AS p95_gap,
          MAX(CASE WHEN prev_d IS NOT NULL THEN DATE_DIFF('day', prev_d, d) END) AS max_gap
        FROM g
        """
    ).fetchone()

    by_status = con.execute(
        """
        SELECT
          list_status,
          MIN(STRPTIME(trade_date, '%Y%m%d')::DATE) AS min_date,
          MAX(STRPTIME(trade_date, '%Y%m%d')::DATE) AS max_date,
          COUNT(*) AS rows,
          COUNT(DISTINCT trade_date) AS snapshot_days
        FROM rawdb.raw_stock_basic
        GROUP BY 1
        ORDER BY 1
        """
    ).fetchall()

    return {
        "all": {
            "min_date": all_stats[0].isoformat() if all_stats[0] else None,
            "max_date": all_stats[1].isoformat() if all_stats[1] else None,
            "rows": int(all_stats[2] or 0),
            "snapshot_days": int(all_stats[3] or 0),
            "avg_gap_days": _to_float(gap_stats[0]),
            "p50_gap_days": _to_float(gap_stats[1]),
            "p95_gap_days": _to_float(gap_stats[2]),
            "max_gap_days": _to_int(gap_stats[3]),
        },
        "by_list_status": [
            {
                "list_status": row[0],
                "min_date": row[1].isoformat() if row[1] else None,
                "max_date": row[2].isoformat() if row[2] else None,
                "rows": int(row[3] or 0),
                "snapshot_days": int(row[4] or 0),
            }
            for row in by_status
        ],
    }


def _fetch_l1_info_boundary(con: duckdb.DuckDBPyConnection) -> dict:
    row = con.execute(
        """
        SELECT
          MIN(effective_from),
          MAX(effective_from),
          COUNT(*) AS rows,
          COUNT(DISTINCT effective_from) AS effective_days,
          COUNT(DISTINCT ts_code) AS codes
        FROM l1_stock_info
        """
    ).fetchone()
    distribution = con.execute(
        """
        SELECT effective_from, COUNT(*) AS rows
        FROM l1_stock_info
        GROUP BY 1
        ORDER BY 1
        """
    ).fetchall()
    return {
        "min_effective_from": row[0].isoformat() if row[0] else None,
        "max_effective_from": row[1].isoformat() if row[1] else None,
        "rows": int(row[2] or 0),
        "effective_days": int(row[3] or 0),
        "codes": int(row[4] or 0),
        "effective_from_distribution": [
            {"effective_from": item[0].isoformat(), "rows": int(item[1])} for item in distribution
        ],
    }


def _fetch_daily_asof_coverage(
    con: duckdb.DuckDBPyConnection, start: str, end: str
) -> CoverageStats:
    row = con.execute(
        """
        WITH d AS (
          SELECT ts_code, date
          FROM l1_stock_daily
          WHERE date BETWEEN ? AND ?
        ),
        a AS (
          SELECT
            d.ts_code,
            d.date,
            (
              SELECT MAX(s.effective_from)
              FROM l1_stock_info s
              WHERE s.ts_code = d.ts_code AND s.effective_from <= d.date
            ) AS asof_effective_from
          FROM d
        )
        SELECT
          COUNT(*) AS total_rows,
          SUM(CASE WHEN asof_effective_from IS NOT NULL THEN 1 ELSE 0 END) AS hit_rows,
          SUM(CASE WHEN asof_effective_from IS NULL THEN 1 ELSE 0 END) AS miss_rows,
          1.0 * SUM(CASE WHEN asof_effective_from IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) AS hit_rate,
          AVG(CASE WHEN asof_effective_from IS NOT NULL THEN DATE_DIFF('day', asof_effective_from, date) END) AS avg_lag_days,
          MEDIAN(CASE WHEN asof_effective_from IS NOT NULL THEN DATE_DIFF('day', asof_effective_from, date) END) AS p50_lag_days,
          QUANTILE_CONT(
            CASE WHEN asof_effective_from IS NOT NULL THEN DATE_DIFF('day', asof_effective_from, date) END,
            0.95
          ) AS p95_lag_days,
          MAX(CASE WHEN asof_effective_from IS NOT NULL THEN DATE_DIFF('day', asof_effective_from, date) END) AS max_lag_days
        FROM a
        """,
        [start, end],
    ).fetchone()
    return CoverageStats(
        total_rows=int(row[0] or 0),
        hit_rows=int(row[1] or 0),
        miss_rows=int(row[2] or 0),
        hit_rate=float(row[3] or 0.0),
        avg_lag_days=_to_float(row[4]),
        p50_lag_days=_to_float(row[5]),
        p95_lag_days=_to_float(row[6]),
        max_lag_days=_to_int(row[7]),
    )


def _fetch_signal_asof_coverage(
    con: duckdb.DuckDBPyConnection, start: str, end: str
) -> CoverageStats:
    row = con.execute(
        """
        WITH s AS (
          SELECT code, signal_date AS date
          FROM l3_signals
          WHERE signal_date BETWEEN ? AND ?
        ),
        a AS (
          SELECT
            s.code,
            s.date,
            (
              SELECT MAX(i.effective_from)
              FROM l1_stock_info i
              WHERE SPLIT_PART(i.ts_code, '.', 1) = s.code AND i.effective_from <= s.date
            ) AS asof_effective_from
          FROM s
        )
        SELECT
          COUNT(*) AS total_rows,
          SUM(CASE WHEN asof_effective_from IS NOT NULL THEN 1 ELSE 0 END) AS hit_rows,
          SUM(CASE WHEN asof_effective_from IS NULL THEN 1 ELSE 0 END) AS miss_rows,
          1.0 * SUM(CASE WHEN asof_effective_from IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*) AS hit_rate,
          AVG(CASE WHEN asof_effective_from IS NOT NULL THEN DATE_DIFF('day', asof_effective_from, date) END) AS avg_lag_days,
          MEDIAN(CASE WHEN asof_effective_from IS NOT NULL THEN DATE_DIFF('day', asof_effective_from, date) END) AS p50_lag_days,
          QUANTILE_CONT(
            CASE WHEN asof_effective_from IS NOT NULL THEN DATE_DIFF('day', asof_effective_from, date) END,
            0.95
          ) AS p95_lag_days,
          MAX(CASE WHEN asof_effective_from IS NOT NULL THEN DATE_DIFF('day', asof_effective_from, date) END) AS max_lag_days
        FROM a
        """,
        [start, end],
    ).fetchone()
    return CoverageStats(
        total_rows=int(row[0] or 0),
        hit_rows=int(row[1] or 0),
        miss_rows=int(row[2] or 0),
        hit_rate=float(row[3] or 0.0),
        avg_lag_days=_to_float(row[4]),
        p50_lag_days=_to_float(row[5]),
        p95_lag_days=_to_float(row[6]),
        max_lag_days=_to_int(row[7]),
    )


def _fetch_miss_breakdown(con: duckdb.DuckDBPyConnection, start: str, end: str) -> dict:
    unique_counts = con.execute(
        """
        WITH d AS (
          SELECT DISTINCT ts_code
          FROM l1_stock_daily
          WHERE date BETWEEN ? AND ?
        ),
        i AS (
          SELECT DISTINCT ts_code
          FROM l1_stock_info
        )
        SELECT
          (SELECT COUNT(*) FROM d) AS daily_codes,
          (SELECT COUNT(*) FROM i) AS info_codes,
          (
            SELECT COUNT(*)
            FROM d LEFT JOIN i USING(ts_code)
            WHERE i.ts_code IS NULL
          ) AS missing_codes
        """,
        [start, end],
    ).fetchone()

    missing_status = con.execute(
        """
        WITH missing AS (
          SELECT DISTINCT d.ts_code
          FROM l1_stock_daily d
          LEFT JOIN (SELECT DISTINCT ts_code FROM l1_stock_info) i USING(ts_code)
          WHERE d.date BETWEEN ? AND ?
            AND i.ts_code IS NULL
        ),
        stat AS (
          SELECT m.ts_code, r.list_status
          FROM missing m
          LEFT JOIN rawdb.raw_stock_basic r ON r.ts_code = m.ts_code
        )
        SELECT list_status, COUNT(DISTINCT ts_code) AS codes
        FROM stat
        GROUP BY 1
        ORDER BY codes DESC
        """,
        [start, end],
    ).fetchall()

    no_raw_info_count = con.execute(
        """
        WITH missing AS (
          SELECT DISTINCT d.ts_code
          FROM l1_stock_daily d
          LEFT JOIN (SELECT DISTINCT ts_code FROM l1_stock_info) i USING(ts_code)
          WHERE d.date BETWEEN ? AND ?
            AND i.ts_code IS NULL
        ),
        stat AS (
          SELECT m.ts_code, MAX(r.trade_date) AS any_trade_date
          FROM missing m
          LEFT JOIN rawdb.raw_stock_basic r ON r.ts_code = m.ts_code
          GROUP BY 1
        )
        SELECT COUNT(*)
        FROM stat
        WHERE any_trade_date IS NULL
        """,
        [start, end],
    ).fetchone()[0]

    return {
        "daily_codes": int(unique_counts[0] or 0),
        "info_codes": int(unique_counts[1] or 0),
        "missing_codes": int(unique_counts[2] or 0),
        "missing_codes_status_breakdown": [
            {"list_status": row[0], "codes": int(row[1])} for row in missing_status
        ],
        "missing_codes_without_raw_stock_basic": int(no_raw_info_count or 0),
    }


def main() -> int:
    args = build_parser().parse_args()
    target_db = Path(args.target_db).expanduser().resolve()
    source_db = Path(args.source_db).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(target_db))
    try:
        con.execute(f"ATTACH '{source_db.as_posix()}' AS rawdb")

        source_boundary = _fetch_source_boundary(con)
        l1_info_boundary = _fetch_l1_info_boundary(con)
        daily_coverage = _fetch_daily_asof_coverage(con, args.start, args.end)
        signal_coverage = _fetch_signal_asof_coverage(con, args.start, args.end)
        miss_breakdown = _fetch_miss_breakdown(con, args.start, args.end)

        result = {
            "window": {"start": args.start, "end": args.end},
            "source_raw_stock_basic_boundary": source_boundary,
            "l1_stock_info_boundary": l1_info_boundary,
            "asof_coverage_l1_stock_daily": asdict(daily_coverage),
            "asof_coverage_l3_signals": asdict(signal_coverage),
            "miss_breakdown": miss_breakdown,
        }
    finally:
        con.close()

    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
