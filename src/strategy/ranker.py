from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from src.config import Settings
from src.contracts import Signal, StockCandidate
from src.data.store import Store


@dataclass(frozen=True)
class DttVariantSpec:
    label: str
    uses_irs: bool
    uses_mss: bool


DTT_VARIANTS: dict[str, DttVariantSpec] = {
    "v0_01_dtt_bof_only": DttVariantSpec(
        label="v0_01_dtt_bof_only",
        uses_irs=False,
        uses_mss=False,
    ),
    "v0_01_dtt_bof_plus_irs_score": DttVariantSpec(
        label="v0_01_dtt_bof_plus_irs_score",
        uses_irs=True,
        uses_mss=False,
    ),
    "v0_01_dtt_bof_plus_irs_mss_score": DttVariantSpec(
        label="v0_01_dtt_bof_plus_irs_mss_score",
        uses_irs=True,
        uses_mss=True,
    ),
}


def resolve_dtt_variant(label: str) -> DttVariantSpec:
    normalized = label.strip().lower()
    variant = DTT_VARIANTS.get(normalized)
    if variant is None:
        raise ValueError(f"Unsupported DTT variant: {label}")
    return variant


def _load_irs_score_map(store: Store, asof_date: date) -> dict[str, float]:
    rows = store.read_df(
        """
        SELECT industry, rank
        FROM l3_irs_daily
        WHERE date = ?
        ORDER BY rank ASC
        """,
        (asof_date,),
    )
    if rows.empty:
        return {}
    total = max(int(len(rows)), 1)
    score_map: dict[str, float] = {}
    for _, row in rows.iterrows():
        rank = int(row["rank"])
        if total == 1:
            score_map[str(row["industry"])] = 100.0
            continue
        # DTT 当前用稳定线性映射，把行业名次转成 0-100 的后置增强分。
        score_map[str(row["industry"])] = 100.0 * (1.0 - (rank - 1) / (total - 1))
    return score_map


def _load_mss_score(store: Store, asof_date: date) -> float | None:
    value = store.read_scalar("SELECT score FROM l3_mss_daily WHERE date = ?", (asof_date,))
    if value is None:
        return None
    return float(value)


def _compute_final_score(
    cfg: Settings,
    variant: DttVariantSpec,
    bof_strength: float,
    irs_score: float,
    mss_score: float,
) -> float:
    bof_score = bof_strength * 100.0 if bof_strength <= 1.0 else bof_strength
    total_weight = cfg.dtt_bof_weight
    score = cfg.dtt_bof_weight * bof_score
    if variant.uses_irs:
        score += cfg.dtt_irs_weight * irs_score
        total_weight += cfg.dtt_irs_weight
    if variant.uses_mss:
        score += cfg.dtt_mss_weight * mss_score
        total_weight += cfg.dtt_mss_weight
    if total_weight <= 0:
        return bof_score
    return score / total_weight


def build_dtt_score_frame(
    store: Store,
    signals: list[Signal],
    candidates: list[StockCandidate],
    asof_date: date,
    run_id: str,
    config: Settings,
) -> pd.DataFrame:
    if not signals:
        return pd.DataFrame(
            columns=[
                "run_id",
                "signal_id",
                "signal_date",
                "code",
                "industry",
                "variant",
                "bof_strength",
                "irs_score",
                "mss_score",
                "final_score",
            ]
        )

    variant = resolve_dtt_variant(config.dtt_variant)
    candidate_map = {candidate.code: candidate for candidate in candidates}
    irs_score_map = _load_irs_score_map(store, asof_date) if variant.uses_irs else {}
    market_score = _load_mss_score(store, asof_date) if variant.uses_mss else None
    fill_score = float(config.dtt_score_fill)

    rows: list[dict[str, object]] = []
    for signal in signals:
        candidate = candidate_map.get(signal.code)
        industry = candidate.industry if candidate is not None else "未知"
        bof_strength = float(signal.bof_strength if signal.bof_strength is not None else signal.strength)
        irs_score = float(irs_score_map.get(industry, fill_score)) if variant.uses_irs else fill_score
        mss_score = float(market_score if market_score is not None else fill_score)
        if not variant.uses_mss:
            mss_score = fill_score
        final_score = _compute_final_score(config, variant, bof_strength, irs_score, mss_score)
        rows.append(
            {
                "run_id": run_id,
                "signal_id": signal.signal_id,
                "signal_date": signal.signal_date,
                "code": signal.code,
                "industry": industry,
                "variant": variant.label,
                "bof_strength": bof_strength,
                "irs_score": irs_score,
                "mss_score": mss_score,
                "final_score": final_score,
            }
        )

    return pd.DataFrame(rows)


def finalize_dtt_rank_frame(score_frame: pd.DataFrame, top_n: int) -> pd.DataFrame:
    if score_frame.empty:
        return pd.DataFrame(
            columns=[
                "run_id",
                "signal_id",
                "signal_date",
                "code",
                "industry",
                "variant",
                "bof_strength",
                "irs_score",
                "mss_score",
                "final_score",
                "final_rank",
                "selected",
            ]
        )

    ranked = score_frame.sort_values(
        ["final_score", "signal_id"], ascending=[False, True]
    ).reset_index(drop=True)
    ranked["final_rank"] = range(1, len(ranked) + 1)
    ranked["selected"] = ranked["final_rank"] <= max(1, int(top_n))
    return ranked


def build_dtt_rank_frame(
    store: Store,
    signals: list[Signal],
    candidates: list[StockCandidate],
    asof_date: date,
    run_id: str,
    config: Settings,
) -> pd.DataFrame:
    score_frame = build_dtt_score_frame(store, signals, candidates, asof_date, run_id, config)
    return finalize_dtt_rank_frame(score_frame, config.dtt_top_n)


def materialize_ranked_signals(signals: list[Signal], rank_frame: pd.DataFrame) -> list[Signal]:
    if not signals or rank_frame.empty:
        return []
    rank_map = {
        str(row["signal_id"]): row
        for _, row in rank_frame.iterrows()
        if bool(row.get("selected", False))
    }
    ranked_signals: list[Signal] = []
    for signal in signals:
        row = rank_map.get(signal.signal_id)
        if row is None:
            continue
        ranked_signals.append(
            signal.model_copy(
                update={
                    "bof_strength": float(row["bof_strength"]),
                    "irs_score": float(row["irs_score"]),
                    "mss_score": float(row["mss_score"]),
                    "final_score": float(row["final_score"]),
                    "final_rank": int(row["final_rank"]),
                    "variant": str(row["variant"]),
                }
            )
        )
    return sorted(
        ranked_signals,
        key=lambda item: int(item.final_rank or 0),
    )
