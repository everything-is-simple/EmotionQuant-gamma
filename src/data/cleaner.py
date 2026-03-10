from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from src.data.store import Store


def ts_code_to_code(ts_code: str) -> str:
    return ts_code.split(".")[0]


def _clear_date_range(store: Store, table: str, start: date, end: date, date_col: str = "date") -> None:
    # 局部重建必须先清目标分区，否则 source 缩小后会残留旧行，破坏幂等。
    store.conn.execute(f"DELETE FROM {table} WHERE {date_col} BETWEEN ? AND ?", [start, end])


def _rolling_on_valid_days(
    df: pd.DataFrame, value_col: str, window: int, halt_col: str = "is_halt"
) -> pd.Series:
    # v0.01 口径：rolling 仅在有效交易日上计算，停牌日不进入窗口。
    valid = df.loc[~df[halt_col], ["ts_code", "date", value_col]].copy()
    valid = valid.sort_values(["ts_code", "date"])
    valid[f"_r_{window}"] = (
        valid.groupby("ts_code")[value_col]
        .transform(lambda s: s.rolling(window, min_periods=window).mean())
        .astype(float)
    )
    merged = df[["ts_code", "date"]].merge(
        valid[["ts_code", "date", f"_r_{window}"]], on=["ts_code", "date"], how="left"
    )
    return merged[f"_r_{window}"]


def clean_stock_adj_daily(store: Store, start: date, end: date) -> int:
    _clear_date_range(store, "l2_stock_adj_daily", start, end)
    lookback_start = start - timedelta(days=180)
    raw = store.read_df(
        """
        SELECT d.ts_code, d.date, d.open, d.high, d.low, d.close, d.volume, d.amount, d.adj_factor, d.is_halt
        FROM l1_stock_daily d
        INNER JOIN l1_trade_calendar cal
            ON cal.date = d.date AND cal.is_trade_day = TRUE
        WHERE d.date BETWEEN ? AND ?
        ORDER BY d.ts_code, d.date
        """,
        (lookback_start, end),
    )
    if raw.empty:
        return 0

    df = raw.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    # 复权口径冻结：adj = raw * adj_factor；adj_factor 缺失按 1.0 兜底。
    df["adj_factor"] = df["adj_factor"].fillna(1.0)
    df["code"] = df["ts_code"].map(ts_code_to_code)
    df["adj_open"] = df["open"] * df["adj_factor"]
    df["adj_high"] = df["high"] * df["adj_factor"]
    df["adj_low"] = df["low"] * df["adj_factor"]
    df["adj_close"] = df["close"] * df["adj_factor"]
    df = df.sort_values(["code", "date"])
    df["pct_chg"] = df.groupby("code")["adj_close"].pct_change()
    df["ma5"] = _rolling_on_valid_days(df, "adj_close", 5)
    df["ma10"] = _rolling_on_valid_days(df, "adj_close", 10)
    df["ma20"] = _rolling_on_valid_days(df, "adj_close", 20)
    df["ma60"] = _rolling_on_valid_days(df, "adj_close", 60)
    df["volume_ma5"] = _rolling_on_valid_days(df, "volume", 5)
    df["volume_ma20"] = _rolling_on_valid_days(df, "volume", 20)
    # 避免分母为 0 导致脏值扩散到下游策略。
    df["volume_ratio"] = np.where(df["volume_ma20"] > 0, df["volume"] / df["volume_ma20"], np.nan)

    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    out = df.loc[
        (df["date"] >= start_ts) & (df["date"] <= end_ts),
        [
            "code",
            "date",
            "adj_open",
            "adj_high",
            "adj_low",
            "adj_close",
            "volume",
            "amount",
            "pct_chg",
            "ma5",
            "ma10",
            "ma20",
            "ma60",
            "volume_ma5",
            "volume_ma20",
            "volume_ratio",
        ],
    ].copy()
    return store.bulk_upsert("l2_stock_adj_daily", out)


def _stock_daily_with_info(store: Store, start: date, end: date) -> pd.DataFrame:
    return store.read_df(
        """
        SELECT
            d.ts_code, d.date, d.open, d.high, d.low, d.close, d.pre_close, d.volume, d.amount,
            d.pct_chg, d.is_halt, d.up_limit, d.down_limit,
            COALESCE((
                SELECT m.industry_name
                FROM l1_sw_industry_member m
                WHERE m.ts_code = d.ts_code
                  AND m.in_date <= d.date
                  AND (m.out_date IS NULL OR m.out_date >= d.date)
                ORDER BY m.in_date DESC, m.industry_code ASC
                LIMIT 1
            ), '未知') AS industry,
            (
                SELECT i.market
                FROM l1_stock_info i
                WHERE i.ts_code = d.ts_code AND i.effective_from <= d.date
                ORDER BY i.effective_from DESC
                LIMIT 1
            ) AS market,
            COALESCE((
                SELECT i.is_st
                FROM l1_stock_info i
                WHERE i.ts_code = d.ts_code AND i.effective_from <= d.date
                ORDER BY i.effective_from DESC
                LIMIT 1
            ), FALSE) AS is_st
        FROM l1_stock_daily d
        INNER JOIN l1_trade_calendar cal
            ON cal.date = d.date AND cal.is_trade_day = TRUE
        WHERE d.date BETWEEN ? AND ?
        ORDER BY d.ts_code, d.date
        """,
        (start, end),
    )


def clean_industry_daily(store: Store, start: date, end: date) -> int:
    _clear_date_range(store, "l2_industry_daily", start, end)
    # P2-A 第一批输入扩展只保留行业级中间态：
    # 先在 DuckDB 聚合到 industry/day，再补 20 日均额与 5/20 日收益，
    # 避免把整段个股明细和行业宽表都长期留在 pandas 内存里。
    lookback_start = start - timedelta(days=60)
    grouped = store.read_df(
        """
        WITH stock_base AS (
            SELECT
                COALESCE((
                    SELECT m.industry_name
                    FROM l1_sw_industry_member m
                    WHERE m.ts_code = d.ts_code
                      AND m.in_date <= d.date
                      AND (m.out_date IS NULL OR m.out_date >= d.date)
                    ORDER BY m.in_date DESC, m.industry_code ASC
                    LIMIT 1
                ), '未知') AS industry,
                d.date,
                CASE
                    WHEN d.pre_close > 0 THEN (d.close - d.pre_close) / d.pre_close
                    ELSE NULL
                END AS ret,
                d.amount,
                d.ts_code
            FROM l1_stock_daily d
            INNER JOIN l1_trade_calendar cal
                ON cal.date = d.date AND cal.is_trade_day = TRUE
            WHERE d.date BETWEEN ? AND ?
              AND COALESCE(d.is_halt, FALSE) = FALSE
        ),
        daily AS (
            SELECT
                industry,
                date,
                AVG(ret) AS pct_chg,
                SUM(amount) AS amount,
                COUNT(DISTINCT ts_code) AS stock_count,
                SUM(CASE WHEN ret > 0 THEN 1 ELSE 0 END) AS rise_count,
                SUM(CASE WHEN ret < 0 THEN 1 ELSE 0 END) AS fall_count
            FROM stock_base
            GROUP BY industry, date
        ),
        enriched AS (
            SELECT
                industry,
                date,
                pct_chg,
                amount,
                stock_count,
                rise_count,
                fall_count,
                ROW_NUMBER() OVER (
                    PARTITION BY industry
                    ORDER BY date
                ) AS rn,
                AVG(amount) OVER (
                    PARTITION BY industry
                    ORDER BY date
                    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                ) AS amount_ma20_raw,
                EXP(SUM(LN(1.0 + COALESCE(pct_chg, 0.0))) OVER (
                    PARTITION BY industry
                    ORDER BY date
                    ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
                )) - 1.0 AS return_5d_raw,
                EXP(SUM(LN(1.0 + COALESCE(pct_chg, 0.0))) OVER (
                    PARTITION BY industry
                    ORDER BY date
                    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                )) - 1.0 AS return_20d_raw
            FROM daily
        )
        SELECT
            industry,
            date,
            pct_chg,
            amount,
            stock_count,
            rise_count,
            fall_count,
            CASE WHEN rn >= 20 THEN amount_ma20_raw ELSE NULL END AS amount_ma20,
            CASE WHEN rn >= 5 THEN return_5d_raw ELSE NULL END AS return_5d,
            CASE WHEN rn >= 20 THEN return_20d_raw ELSE NULL END AS return_20d
        FROM enriched
        WHERE date BETWEEN ? AND ?
        ORDER BY industry, date
        """,
        (lookback_start, end, start, end),
    )
    if grouped.empty:
        return 0
    return store.bulk_upsert("l2_industry_daily", grouped)


def clean_industry_structure_daily(store: Store, start: date, end: date) -> int:
    _clear_date_range(store, "l2_industry_structure_daily", start, end)
    lookback_start = start - timedelta(days=220)
    follow_end = store.next_trade_date(end) or end
    # 结构表是 P2 给 IRS 提供的“行业内部广度/龙头/跟随”输入层：
    # 仍然严格停留在 L2，只允许消费 L1 明细，不反向读取 PAS/L3 结果。
    grouped = store.read_df(
        """
        WITH stock_base AS (
            SELECT
                COALESCE((
                    SELECT m.industry_name
                    FROM l1_sw_industry_member m
                    WHERE m.ts_code = d.ts_code
                      AND m.in_date <= d.date
                      AND (m.out_date IS NULL OR m.out_date >= d.date)
                    ORDER BY m.in_date DESC, m.industry_code ASC
                    LIMIT 1
                ), '未知') AS industry,
                d.ts_code,
                d.date,
                d.close,
                d.pre_close,
                d.amount,
                d.up_limit,
                CASE
                    WHEN d.pre_close > 0 THEN (d.close - d.pre_close) / d.pre_close
                    ELSE NULL
                END AS ret,
                CASE
                    WHEN COALESCE((
                        SELECT i.is_st
                        FROM l1_stock_info i
                        WHERE i.ts_code = d.ts_code AND i.effective_from <= d.date
                        ORDER BY i.effective_from DESC
                        LIMIT 1
                    ), FALSE) THEN 0.025
                    WHEN (
                        SELECT i.market
                        FROM l1_stock_info i
                        WHERE i.ts_code = d.ts_code AND i.effective_from <= d.date
                        ORDER BY i.effective_from DESC
                        LIMIT 1
                    ) IN ('创业板', '科创板') THEN 0.10
                    WHEN (
                        SELECT i.market
                        FROM l1_stock_info i
                        WHERE i.ts_code = d.ts_code AND i.effective_from <= d.date
                        ORDER BY i.effective_from DESC
                        LIMIT 1
                    ) = '北交所' THEN 0.15
                    ELSE 0.05
                END AS strong_up_threshold
            FROM l1_stock_daily d
            INNER JOIN l1_trade_calendar cal
                ON cal.date = d.date AND cal.is_trade_day = TRUE
            WHERE d.date BETWEEN ? AND ?
              AND COALESCE(d.is_halt, FALSE) = FALSE
        ),
        flagged AS (
            SELECT
                industry,
                ts_code,
                date,
                close,
                amount,
                ret,
                strong_up_threshold,
                (ret >= strong_up_threshold) AS strong_up,
                (
                    MAX(close) OVER (
                        PARTITION BY ts_code
                        ORDER BY date
                        ROWS BETWEEN 100 PRECEDING AND 1 PRECEDING
                    )
                ) AS prev_high_100,
                (up_limit IS NOT NULL AND close >= up_limit * 0.998) AS limit_up,
                LEAD(ret) OVER (PARTITION BY ts_code ORDER BY date) AS next_ret
            FROM stock_base
        ),
        scored AS (
            SELECT
                industry,
                date,
                amount,
                strong_up,
                (prev_high_100 IS NOT NULL AND close >= prev_high_100) AS new_100d_high,
                limit_up,
                next_ret,
                (
                    strong_up
                    OR (prev_high_100 IS NOT NULL AND close >= prev_high_100)
                    OR limit_up
                ) AS leader_flag,
                CASE
                    WHEN (
                        strong_up
                        OR (prev_high_100 IS NOT NULL AND close >= prev_high_100)
                        OR limit_up
                    ) THEN LEAST(
                        1.0,
                        GREATEST(
                            0.0,
                            0.50 * LEAST(COALESCE(ret, 0.0) / NULLIF(strong_up_threshold, 0.0), 1.0)
                            + 0.30 * CASE WHEN prev_high_100 IS NOT NULL AND close >= prev_high_100 THEN 1.0 ELSE 0.0 END
                            + 0.20 * CASE WHEN limit_up THEN 1.0 ELSE 0.0 END
                        )
                    )
                    ELSE 0.0
                END AS leader_score
            FROM flagged
        )
        SELECT
            industry,
            date,
            SUM(CASE WHEN strong_up THEN 1 ELSE 0 END) AS strong_up_count,
            SUM(CASE WHEN new_100d_high THEN 1 ELSE 0 END) AS new_high_count,
            SUM(CASE WHEN leader_flag THEN 1 ELSE 0 END) AS leader_count,
            COALESCE(AVG(CASE WHEN leader_flag THEN leader_score END), 0.0) AS leader_strength,
            COALESCE(AVG(CASE WHEN leader_flag THEN 1.0 ELSE 0.0 END), 0.0) AS strong_stock_ratio,
            COALESCE(
                SUM(CASE WHEN leader_flag THEN amount ELSE 0.0 END) / NULLIF(SUM(amount), 0.0),
                0.0
            ) AS strong_stock_amount_share,
            COALESCE(
                AVG(
                    CASE
                        WHEN leader_flag AND next_ret IS NOT NULL THEN CASE WHEN next_ret > 0 THEN 1.0 ELSE 0.0 END
                    END
                ),
                0.0
            ) AS leader_follow_through,
            -- P2-B 当前保持层级纪律：L2 不反向读取 PAS/L3。
            -- 因此先显式落受控占位值，后续若引入 BOF 密度，只能通过独立预聚合结果接入。
            0.0 AS bof_hit_density_5d
        FROM scored
        WHERE date BETWEEN ? AND ?
        GROUP BY industry, date
        ORDER BY industry, date
        """,
        (lookback_start, follow_end, start, end),
    )
    if grouped.empty:
        return 0
    return store.bulk_upsert("l2_industry_structure_daily", grouped)


def _streak_lengths(flag: pd.Series) -> pd.Series:
    # streak 需要逐元素状态转移，用一个很短的 Python 循环反而比来回构造
    # 多个中间列更直观；上游已经把窗口限制在 220 天 lookback 内。
    values = flag.fillna(False).astype(bool).to_numpy()
    out = np.zeros(len(values), dtype=int)
    run = 0
    for i, v in enumerate(values):
        if v:
            run += 1
        else:
            run = 0
        out[i] = run
    return pd.Series(out, index=flag.index)


def clean_market_snapshot(store: Store, start: date, end: date) -> int:
    _clear_date_range(store, "l2_market_snapshot", start, end)
    lookback_start = start - timedelta(days=220)
    # MSS 需要一段更长的历史来判断新高/新低、连板和波动率，
    # 这里一次性读 220 天后再压成“日级市场截面”，避免把个股长窗口结果长期留在 L3。
    df = _stock_daily_with_info(store, lookback_start, end)
    if df.empty:
        return 0

    df = df.sort_values(["ts_code", "date"]).copy()
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    df["ret"] = np.where(df["pre_close"] > 0, (df["close"] - df["pre_close"]) / df["pre_close"], np.nan)
    market = df["market"].fillna("")
    is_st = df["is_st"].fillna(False)
    # 分板块强弱阈值（Frozen）：主板5%，创/科10%，北交15%，ST 2.5%。
    threshold = np.select(
        [
            is_st,
            market.isin(["创业板", "科创板"]),
            market.eq("北交所"),
        ],
        [0.025, 0.10, 0.15],
        default=0.05,
    )
    df["strong_up"] = df["ret"] >= threshold
    df["strong_down"] = df["ret"] <= -threshold
    df["limit_up"] = (df["close"] >= df["up_limit"] * 0.998) & df["up_limit"].notna()
    df["limit_down"] = (df["close"] <= df["down_limit"] * 1.002) & df["down_limit"].notna()
    df["touched_limit_up"] = (
        (df["high"] >= df["up_limit"] * 0.998)
        & (df["close"] < df["up_limit"] * 0.998)
        & df["up_limit"].notna()
    )
    daily_range = (df["high"] - df["low"]).replace(0, np.nan)
    df["high_open_low_close"] = (df["open"] >= df["low"] + daily_range * (2 / 3)) & (
        df["close"] <= df["low"] + daily_range * (1 / 3)
    )
    df["low_open_high_close"] = (df["open"] <= df["low"] + daily_range * (1 / 3)) & (
        df["close"] >= df["low"] + daily_range * (2 / 3)
    )

    prev_high_100 = (
        df.groupby("ts_code")["close"]
        .transform(lambda s: s.shift(1).rolling(100, min_periods=100).max())
        .astype(float)
    )
    prev_low_100 = (
        df.groupby("ts_code")["close"]
        .transform(lambda s: s.shift(1).rolling(100, min_periods=100).min())
        .astype(float)
    )
    df["new_100d_high"] = df["close"] >= prev_high_100
    df["new_100d_low"] = df["close"] <= prev_low_100
    # 连板/新高连续性用于 MSS 输入，必须按个股时序计算 streak。
    df["limit_up_streak"] = df.groupby("ts_code", group_keys=False)["limit_up"].apply(_streak_lengths)
    df["new_high_streak"] = df.groupby("ts_code", group_keys=False)["new_100d_high"].apply(_streak_lengths)

    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    effective = df[(df["date"] >= start_ts) & (df["date"] <= end_ts)].copy()
    agg = (
        effective.groupby("date", as_index=False)
        .agg(
            total_stocks=("ts_code", lambda s: int(effective.loc[s.index, "is_halt"].eq(False).sum())),
            rise_count=("ret", lambda s: int((s > 0).sum())),
            fall_count=("ret", lambda s: int((s < 0).sum())),
            strong_up_count=("strong_up", "sum"),
            strong_down_count=("strong_down", "sum"),
            limit_up_count=("limit_up", "sum"),
            limit_down_count=("limit_down", "sum"),
            touched_limit_up_count=("touched_limit_up", "sum"),
            new_100d_high_count=("new_100d_high", "sum"),
            new_100d_low_count=("new_100d_low", "sum"),
            continuous_limit_up_2d=("limit_up_streak", lambda s: int((s >= 2).sum())),
            continuous_limit_up_3d_plus=("limit_up_streak", lambda s: int((s >= 3).sum())),
            continuous_new_high_2d_plus=("new_high_streak", lambda s: int((s >= 2).sum())),
            high_open_low_close_count=("high_open_low_close", "sum"),
            low_open_high_close_count=("low_open_high_close", "sum"),
            pct_chg_std=("ret", "std"),
            amount_volatility=("amount", "std"),
        )
        .sort_values("date")
    )
    int_cols = [
        "total_stocks",
        "rise_count",
        "fall_count",
        "strong_up_count",
        "strong_down_count",
        "limit_up_count",
        "limit_down_count",
        "touched_limit_up_count",
        "new_100d_high_count",
        "new_100d_low_count",
        "continuous_limit_up_2d",
        "continuous_limit_up_3d_plus",
        "continuous_new_high_2d_plus",
        "high_open_low_close_count",
        "low_open_high_close_count",
    ]
    for col in int_cols:
        agg[col] = agg[col].fillna(0).astype(int)
    return store.bulk_upsert("l2_market_snapshot", agg)
