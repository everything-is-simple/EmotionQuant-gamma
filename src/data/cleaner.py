from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from src.data.store import Store


def ts_code_to_code(ts_code: str) -> str:
    return ts_code.split(".")[0]


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
    lookback_start = start - timedelta(days=180)
    raw = store.read_df(
        """
        SELECT ts_code, date, open, high, low, close, volume, amount, adj_factor, is_halt
        FROM l1_stock_daily
        WHERE date BETWEEN ? AND ?
        ORDER BY ts_code, date
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
            (
                SELECT i.industry
                FROM l1_stock_info i
                WHERE i.ts_code = d.ts_code AND i.effective_from <= d.date
                ORDER BY i.effective_from DESC
                LIMIT 1
            ) AS industry,
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
        WHERE d.date BETWEEN ? AND ?
        ORDER BY d.ts_code, d.date
        """,
        (start, end),
    )


def clean_industry_daily(store: Store, start: date, end: date) -> int:
    df = _stock_daily_with_info(store, start, end)
    if df.empty:
        return 0

    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    df = df[~df["is_halt"]].copy()
    df["industry"] = df["industry"].fillna("未知")
    df["ret"] = np.where(df["pre_close"] > 0, (df["close"] - df["pre_close"]) / df["pre_close"], np.nan)
    grouped = (
        df.groupby(["industry", "date"], as_index=False)
        .agg(
            pct_chg=("ret", "mean"),
            amount=("amount", "sum"),
            stock_count=("ts_code", "nunique"),
            rise_count=("ret", lambda s: int((s > 0).sum())),
            fall_count=("ret", lambda s: int((s < 0).sum())),
        )
        .sort_values(["industry", "date"])
    )
    return store.bulk_upsert("l2_industry_daily", grouped)


def _streak_lengths(flag: pd.Series) -> pd.Series:
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
    lookback_start = start - timedelta(days=220)
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
