from __future__ import annotations

import argparse
from pathlib import Path

import duckdb


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Load L1 tables from local raw DuckDB (snapshot-safe)")
    p.add_argument("--target-db", default=r"G:\EmotionQuant_data\emotionquant.duckdb")
    p.add_argument("--source-db", default=r"G:\EmotionQuant_data\duckdb\emotionquant.duckdb")
    p.add_argument("--start", default="2023-01-01")
    p.add_argument("--end", default="2026-03-04")
    p.add_argument("--refresh-stock-info-only", action="store_true", default=False)
    return p


def main() -> int:
    args = build_parser().parse_args()

    target = Path(args.target_db).expanduser().resolve()
    source = Path(args.source_db).expanduser().resolve()

    con = duckdb.connect(str(target))
    con.execute(f"ATTACH '{source.as_posix()}' AS rawdb")
    # 兼容旧库：为 stock_info 补齐 list_status 列，避免快照导入失败。
    con.execute("ALTER TABLE l1_stock_info ADD COLUMN IF NOT EXISTS list_status VARCHAR DEFAULT 'L'")

    if args.refresh_stock_info_only:
        con.execute("DELETE FROM l1_stock_info")
    else:
        for t in [
            'l1_trade_calendar',
            'l1_stock_daily',
            'l1_index_daily',
            'l1_stock_info',
        ]:
            con.execute(f"DELETE FROM {t}")

        # trade calendar
        con.execute(
            """
            INSERT INTO l1_trade_calendar(date, is_trade_day, prev_trade_day, next_trade_day)
            WITH cal AS (
              SELECT
                STRPTIME(cal_date, '%Y%m%d')::DATE AS date,
                (is_open = 1) AS is_trade_day
              FROM rawdb.raw_trade_cal
              WHERE STRPTIME(cal_date, '%Y%m%d')::DATE BETWEEN ? AND ?
            ),
            td AS (
              SELECT date FROM cal WHERE is_trade_day = TRUE ORDER BY date
            ),
            td_link AS (
              SELECT
                date,
                LAG(date) OVER (ORDER BY date) AS prev_trade_day,
                LEAD(date) OVER (ORDER BY date) AS next_trade_day
              FROM td
            )
            SELECT c.date, c.is_trade_day, l.prev_trade_day, l.next_trade_day
            FROM cal c LEFT JOIN td_link l USING(date)
            ORDER BY c.date
            """,
            [args.start, args.end],
        )

        # index daily (SSE Composite)
        con.execute(
            """
            INSERT INTO l1_index_daily(ts_code, date, open, high, low, close, pre_close, pct_chg, volume, amount)
            SELECT
              ts_code,
              STRPTIME(trade_date, '%Y%m%d')::DATE AS date,
              open, high, low, close, pre_close, pct_chg,
              vol AS volume,
              amount
            FROM rawdb.raw_index_daily
            WHERE ts_code = '000001.SH'
              AND STRPTIME(trade_date, '%Y%m%d')::DATE BETWEEN ? AND ?
            """,
            [args.start, args.end],
        )

        # stock daily + daily_basic
        con.execute(
            """
            INSERT INTO l1_stock_daily(
              ts_code, date, open, high, low, close, pre_close, volume, amount, pct_chg,
              adj_factor, is_halt, up_limit, down_limit, total_mv, circ_mv
            )
            SELECT
              d.ts_code,
              STRPTIME(d.trade_date, '%Y%m%d')::DATE AS date,
              d.open, d.high, d.low, d.close, d.pre_close,
              d.vol AS volume,
              d.amount,
              d.pct_chg,
              1.0 AS adj_factor,
              (COALESCE(d.vol, 0) = 0) AS is_halt,
              NULL::DOUBLE AS up_limit,
              NULL::DOUBLE AS down_limit,
              b.total_mv,
              b.circ_mv
            FROM rawdb.raw_daily d
            LEFT JOIN rawdb.raw_daily_basic b
              ON d.ts_code = b.ts_code AND d.trade_date = b.trade_date
            WHERE STRPTIME(d.trade_date, '%Y%m%d')::DATE BETWEEN ? AND ?
            """,
            [args.start, args.end],
        )

    # stock_info snapshot strategy:
    # keep a row when attrs change by effective date, not only latest one.
    con.execute(
        """
        INSERT INTO l1_stock_info(
          ts_code, name, industry, market, list_status, is_st, list_date, effective_from
        )
        WITH base AS (
          SELECT
            ts_code,
            name,
            industry,
            market,
            COALESCE(list_status, 'L') AS list_status,
            list_date,
            STRPTIME(trade_date, '%Y%m%d')::DATE AS effective_from
          FROM rawdb.raw_stock_basic
          WHERE STRPTIME(trade_date, '%Y%m%d')::DATE BETWEEN ? AND ?
        ),
        dedup_day AS (
          SELECT *,
                 ROW_NUMBER() OVER (
                   PARTITION BY ts_code, effective_from
                   ORDER BY effective_from DESC
                 ) AS rn
          FROM base
        ),
        clean AS (
          SELECT ts_code, name, industry, market, list_status, list_date, effective_from
          FROM dedup_day
          WHERE rn = 1
        ),
        with_prev AS (
          SELECT
            *,
            LAG(name) OVER (PARTITION BY ts_code ORDER BY effective_from) AS prev_name,
            LAG(industry) OVER (PARTITION BY ts_code ORDER BY effective_from) AS prev_industry,
            LAG(market) OVER (PARTITION BY ts_code ORDER BY effective_from) AS prev_market,
            LAG(list_status) OVER (PARTITION BY ts_code ORDER BY effective_from) AS prev_list_status,
            LAG(list_date) OVER (PARTITION BY ts_code ORDER BY effective_from) AS prev_list_date
          FROM clean
        ),
        changed AS (
          SELECT *
          FROM with_prev
          WHERE prev_name IS NULL
             OR COALESCE(name, '') <> COALESCE(prev_name, '')
             OR COALESCE(industry, '') <> COALESCE(prev_industry, '')
             OR COALESCE(market, '') <> COALESCE(prev_market, '')
             OR COALESCE(list_status, '') <> COALESCE(prev_list_status, '')
             OR COALESCE(list_date, '') <> COALESCE(prev_list_date, '')
        )
        SELECT
          ts_code,
          name,
          industry,
          market,
          list_status,
          (name LIKE '%ST%') AS is_st,
          STRPTIME(list_date, '%Y%m%d')::DATE AS list_date,
          effective_from
        FROM changed
        """,
        [args.start, args.end],
    )

    for t in ["l1_trade_calendar", "l1_stock_daily", "l1_index_daily", "l1_stock_info"]:
        if t == "l1_stock_info" and not args.refresh_stock_info_only:
            # already filled above
            pass
        cnt = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"{t}={cnt}")

    if con.execute("SELECT COUNT(*) FROM l1_stock_info").fetchone()[0] > 0:
        mn, mx = con.execute(
            "SELECT MIN(effective_from), MAX(effective_from) FROM l1_stock_info"
        ).fetchone()
        print(f"l1_stock_info_effective_range={mn}..{mx}")

    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
