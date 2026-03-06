from __future__ import annotations

from datetime import date

import pandas as pd


RAW_INDEX_CLASSIFY_COLUMNS = [
    "index_code",
    "industry_name",
    "level",
    "industry_code",
    "src",
    "trade_date",
    "is_pub",
    "parent_code",
]

RAW_INDEX_MEMBER_COLUMNS = [
    "index_code",
    "con_code",
    "in_date",
    "out_date",
    "trade_date",
    "ts_code",
    "stock_code",
    "is_new",
]

L1_SW_INDUSTRY_MEMBER_COLUMNS = [
    "industry_code",
    "industry_name",
    "ts_code",
    "in_date",
    "out_date",
    "is_new",
    "source_trade_date",
]


def _empty_df(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def _snapshot_yyyymmdd(snapshot_date: date | str) -> str:
    if isinstance(snapshot_date, date):
        return snapshot_date.strftime("%Y%m%d")
    return str(snapshot_date).strip()


def _clean_text(series: pd.Series | None) -> pd.Series:
    if series is None:
        return pd.Series(dtype="object")
    return series.fillna("").astype(str).str.strip()


def normalize_sw_l1_classify(classify: pd.DataFrame) -> pd.DataFrame:
    if classify is None or classify.empty:
        return _empty_df(["index_code", "industry_name", "industry_code"])

    df = classify.copy()
    if "src" in df.columns:
        df = df[df["src"].fillna("").astype(str).eq("SW2021")]
    if "level" in df.columns:
        df = df[df["level"].fillna("").astype(str).eq("L1")]

    df["index_code"] = _clean_text(df.get("index_code"))
    df["industry_name"] = _clean_text(df.get("industry_name"))
    if "industry_code" in df.columns:
        df["industry_code"] = _clean_text(df.get("industry_code"))
    else:
        df["industry_code"] = df["index_code"].str.replace(".SI", "", regex=False)

    if "trade_date" in df.columns:
        df["_trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d", errors="coerce")
    else:
        df["_trade_date"] = pd.NaT

    df = df[
        (df["index_code"] != "")
        & (df["industry_name"] != "")
        & (~df["industry_name"].str.startswith("行业"))
    ].copy()
    df = df.sort_values(["index_code", "_trade_date"], ascending=[True, False])
    df = df.drop_duplicates(subset=["index_code"], keep="first")
    return df[["index_code", "industry_name", "industry_code"]].reset_index(drop=True)


def normalize_sw_l1_member_history(member_frames: list[pd.DataFrame]) -> pd.DataFrame:
    chunks: list[pd.DataFrame] = []
    for frame in member_frames:
        if frame is None or frame.empty:
            continue
        df = frame.copy()
        index_code = _clean_text(df.get("l1_code"))
        if index_code.empty:
            index_code = _clean_text(df.get("index_code"))
        df["index_code"] = index_code
        ts_code = _clean_text(df.get("ts_code"))
        con_code = _clean_text(df.get("con_code"))
        df["ts_code"] = ts_code.where(ts_code != "", con_code)
        df["con_code"] = con_code.where(con_code != "", df["ts_code"])
        df["stock_code"] = _clean_text(df.get("stock_code"))
        df.loc[df["stock_code"] == "", "stock_code"] = df.loc[df["stock_code"] == "", "ts_code"].str[:6]
        df["in_date"] = _clean_text(df.get("in_date"))
        df["out_date"] = _clean_text(df.get("out_date"))
        df["is_new"] = _clean_text(df.get("is_new"))
        chunks.append(
            df[["index_code", "con_code", "in_date", "out_date", "ts_code", "stock_code", "is_new"]]
        )

    if not chunks:
        return _empty_df(["index_code", "con_code", "in_date", "out_date", "ts_code", "stock_code", "is_new"])

    members = pd.concat(chunks, ignore_index=True)
    members = members[
        (members["index_code"] != "") & (members["ts_code"] != "") & (members["in_date"] != "")
    ].copy()
    members["_out_date_dt"] = pd.to_datetime(
        members["out_date"].replace("", pd.NA),
        format="%Y%m%d",
        errors="coerce",
    )
    members["_has_out_date"] = members["out_date"] != ""
    members = members.sort_values(
        ["index_code", "ts_code", "in_date", "_has_out_date", "_out_date_dt"],
        ascending=[True, True, True, False, False],
    )
    # Tushare occasionally returns both an open row and a closed row for the same entry date.
    # v0.01 keeps one authoritative record per (industry_code, ts_code, in_date).
    members = members.drop_duplicates(
        subset=["index_code", "ts_code", "in_date"],
        keep="first",
    )
    return members.drop(columns=["_out_date_dt", "_has_out_date"]).reset_index(drop=True)


def build_sw_l1_classify_snapshot(classify: pd.DataFrame, snapshot_date: date | str) -> pd.DataFrame:
    normalized = normalize_sw_l1_classify(classify)
    if normalized.empty:
        return _empty_df(RAW_INDEX_CLASSIFY_COLUMNS)

    snapshot = normalized.copy()
    snapshot["level"] = "L1"
    snapshot["src"] = "SW2021"
    snapshot["trade_date"] = _snapshot_yyyymmdd(snapshot_date)
    snapshot["is_pub"] = None
    snapshot["parent_code"] = None
    return snapshot[RAW_INDEX_CLASSIFY_COLUMNS]


def build_sw_l1_member_snapshot(
    classify: pd.DataFrame,
    member_frames: list[pd.DataFrame],
    snapshot_date: date | str,
) -> pd.DataFrame:
    normalized_classify = normalize_sw_l1_classify(classify)
    if normalized_classify.empty:
        return _empty_df(RAW_INDEX_MEMBER_COLUMNS)

    members = normalize_sw_l1_member_history(member_frames)
    if members.empty:
        return _empty_df(RAW_INDEX_MEMBER_COLUMNS)

    allowed_codes = set(normalized_classify["index_code"].tolist())
    members = members[members["index_code"].isin(allowed_codes)].copy()
    members["trade_date"] = _snapshot_yyyymmdd(snapshot_date)
    return members[RAW_INDEX_MEMBER_COLUMNS].reset_index(drop=True)


def build_l1_sw_industry_member_rows(
    classify: pd.DataFrame,
    member_frames: list[pd.DataFrame],
    source_trade_date: date,
) -> pd.DataFrame:
    normalized_classify = normalize_sw_l1_classify(classify)
    if normalized_classify.empty:
        return _empty_df(L1_SW_INDUSTRY_MEMBER_COLUMNS)

    members = normalize_sw_l1_member_history(member_frames)
    if members.empty:
        return _empty_df(L1_SW_INDUSTRY_MEMBER_COLUMNS)

    classify_map = normalized_classify.set_index("index_code")["industry_name"].to_dict()
    allowed_codes = set(classify_map.keys())
    members = members[members["index_code"].isin(allowed_codes)].copy()
    members["industry_code"] = members["index_code"]
    members["industry_name"] = members["industry_code"].map(classify_map).fillna("")
    members["in_date"] = pd.to_datetime(members["in_date"], format="%Y%m%d", errors="coerce").dt.date
    members["out_date"] = pd.to_datetime(members["out_date"], format="%Y%m%d", errors="coerce").dt.date
    members["source_trade_date"] = source_trade_date
    members = members.dropna(subset=["in_date"])
    members = members[members["industry_name"] != ""].copy()
    members = members.drop_duplicates(
        subset=["industry_code", "ts_code", "in_date"],
        keep="first",
    )
    return members[L1_SW_INDUSTRY_MEMBER_COLUMNS].reset_index(drop=True)
