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

L1_INDUSTRY_MEMBER_COLUMNS = [
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
    return series.fillna("").astype(str).str.replace("\x00", "", regex=False).str.strip()


def _stock_only_mask(ts_codes: pd.Series) -> pd.Series:
    cleaned = _clean_text(ts_codes).str.upper()
    return (
        cleaned.str.match(r"^(600|601|603|605|688|689|900)\d{3}\.SH$")
        | cleaned.str.match(r"^(000|001|002|003|200|300|301)\d{3}\.SZ$")
        | cleaned.str.match(r"^(4|8)\d{5}\.BJ$")
    )


def normalize_l1_industry_classify(classify: pd.DataFrame) -> pd.DataFrame:
    if classify is None or classify.empty:
        return _empty_df(["index_code", "industry_name", "industry_code", "src", "level", "trade_date"])

    df = classify.copy()
    df["index_code"] = _clean_text(df.get("index_code"))
    df["industry_name"] = _clean_text(df.get("industry_name"))
    if "industry_code" in df.columns:
        df["industry_code"] = _clean_text(df.get("industry_code"))
    else:
        df["industry_code"] = df["index_code"]
    df["src"] = _clean_text(df.get("src"))
    df["level"] = _clean_text(df.get("level"))
    df["trade_date"] = _clean_text(df.get("trade_date"))
    df["_trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d", errors="coerce")

    df = df[(df["index_code"] != "") & (df["industry_name"] != "")].copy()
    df = df[~df["industry_name"].str.startswith("行业")].copy()
    df = df.sort_values(["index_code", "_trade_date"], ascending=[True, False])
    df = df.drop_duplicates(subset=["index_code"], keep="first")
    return df[["index_code", "industry_name", "industry_code", "src", "level", "trade_date"]].reset_index(drop=True)


def normalize_sw_l1_classify(classify: pd.DataFrame) -> pd.DataFrame:
    if classify is None or classify.empty:
        return _empty_df(["index_code", "industry_name", "industry_code"])

    df = classify.copy()
    if "src" in df.columns:
        df = df[df["src"].fillna("").astype(str).eq("SW2021")]
    if "level" in df.columns:
        df = df[df["level"].fillna("").astype(str).eq("L1")]
    normalized = normalize_l1_industry_classify(df)
    return normalized[["index_code", "industry_name", "industry_code"]]


def normalize_l1_industry_member_history(member_frames: pd.DataFrame | list[pd.DataFrame]) -> pd.DataFrame:
    if isinstance(member_frames, pd.DataFrame):
        frames = [member_frames]
    else:
        frames = member_frames

    chunks: list[pd.DataFrame] = []
    for frame in frames:
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
        df["trade_date"] = _clean_text(df.get("trade_date"))
        chunks.append(
            df[["index_code", "con_code", "in_date", "out_date", "ts_code", "stock_code", "is_new", "trade_date"]]
        )

    if not chunks:
        return _empty_df(
            ["index_code", "con_code", "in_date", "out_date", "ts_code", "stock_code", "is_new", "trade_date"]
        )

    members = pd.concat(chunks, ignore_index=True)
    members = members[
        (members["index_code"] != "") & (members["ts_code"] != "") & (members["in_date"] != "")
    ].copy()
    members["_trade_date_dt"] = pd.to_datetime(
        members["trade_date"].replace("", pd.NA),
        format="%Y%m%d",
        errors="coerce",
    )
    members["_out_date_dt"] = pd.to_datetime(
        members["out_date"].replace("", pd.NA),
        format="%Y%m%d",
        errors="coerce",
    )
    members["_has_out_date"] = members["out_date"] != ""
    members = members.sort_values(
        ["index_code", "ts_code", "in_date", "_has_out_date", "_out_date_dt", "_trade_date_dt"],
        ascending=[True, True, True, False, False, False],
    )
    members = members.drop_duplicates(
        subset=["index_code", "ts_code", "in_date"],
        keep="first",
    )
    return members.drop(columns=["_trade_date_dt", "_out_date_dt", "_has_out_date"]).reset_index(drop=True)


def normalize_sw_l1_member_history(member_frames: list[pd.DataFrame]) -> pd.DataFrame:
    return normalize_l1_industry_member_history(member_frames)


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


def build_l1_industry_member_rows(
    classify: pd.DataFrame,
    member_frames: pd.DataFrame | list[pd.DataFrame],
    source_trade_date: date,
    stock_only: bool = True,
) -> pd.DataFrame:
    normalized_classify = normalize_l1_industry_classify(classify)
    if normalized_classify.empty:
        return _empty_df(L1_INDUSTRY_MEMBER_COLUMNS)

    members = normalize_l1_industry_member_history(member_frames)
    if members.empty:
        return _empty_df(L1_INDUSTRY_MEMBER_COLUMNS)

    classify_map = normalized_classify.set_index("index_code")["industry_name"].to_dict()
    allowed_codes = set(classify_map.keys())
    members = members[members["index_code"].isin(allowed_codes)].copy()
    if stock_only:
        members = members[_stock_only_mask(members["ts_code"])].copy()
    if members.empty:
        return _empty_df(L1_INDUSTRY_MEMBER_COLUMNS)

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
    return members[L1_INDUSTRY_MEMBER_COLUMNS].reset_index(drop=True)


def build_l1_sw_industry_member_rows(
    classify: pd.DataFrame,
    member_frames: list[pd.DataFrame],
    source_trade_date: date,
) -> pd.DataFrame:
    """Legacy SW2021-only wrapper kept for historical specs and old callers."""
    sw_classify = classify.copy()
    if "src" in sw_classify.columns:
        sw_classify = sw_classify[sw_classify["src"].fillna("").astype(str).eq("SW2021")]
    if "level" in sw_classify.columns:
        sw_classify = sw_classify[sw_classify["level"].fillna("").astype(str).eq("L1")]
    return build_l1_industry_member_rows(sw_classify, member_frames, source_trade_date, stock_only=True)
