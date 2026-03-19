from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd

from src.data.store import Store

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURFACE_ORDER = (
    "BULL_MAINSTREAM",
    "BULL_COUNTERTREND",
    "BEAR_MAINSTREAM",
    "BEAR_COUNTERTREND",
)

QUARTILE_TICKS = [0.0, 25.0, 50.0, 75.0, 100.0]


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def _safe_int(value: Any) -> int | None:
    parsed = _safe_float(value)
    if parsed is None:
        return None
    return int(parsed)


def _metric_label(metric_name: str) -> str:
    return "retracement %" if metric_name == "retracement_vs_prior_mainstream_pct" else "magnitude %"


def _surface_theme(surface_label: str, *, odds_mode: bool) -> tuple[list[str], str]:
    if odds_mode:
        colors = ["#f2f2f2", "#d9d9d9", "#a6a6a6", "#595959"]
    elif surface_label.startswith("BULL"):
        colors = ["#e6f4ea", "#cde9d5", "#a8d6b8", "#6fb387"]
    else:
        colors = ["#fbe9e7", "#f5c8c2", "#eea79d", "#d96c5f"]
    edge = "#2f3b2f" if surface_label.startswith("BULL") else "#4a2c2a"
    return colors, edge


def _book_style_label(surface_label: str) -> str:
    if surface_label.endswith("COUNTERTREND"):
        return "Figure 26-1 style"
    return "Figure 11-1 style"


def _surface_current_percentile(row: pd.Series) -> float | None:
    joint = _safe_float(row.get("current_wave_joint_percentile"))
    if joint is not None:
        return joint
    amplitude = _safe_float(row.get("current_wave_amplitude_percentile"))
    duration = _safe_float(row.get("current_wave_duration_percentile"))
    values = [value for value in [amplitude, duration] if value is not None]
    if not values:
        return None
    return float(sum(values) / len(values))


def _axis_labels(row: pd.Series, prefix: str) -> list[str]:
    labels: list[str] = []
    for name in ["min", "q25", "q50", "q75", "max"]:
        value = _safe_float(row.get(f"{prefix}_{name}"))
        labels.append("-" if value is None else f"{value:.1f}")
    return labels


def _surface_summary(row: pd.Series) -> dict[str, object]:
    return {
        "surface_label": str(row["surface_label"]),
        "market_regime_label": str(row["market_regime_label"]),
        "wave_role": str(row["wave_role"]),
        "amplitude_metric_name": str(row["amplitude_metric_name"]),
        "sample_size": _safe_int(row.get("sample_size")) or 0,
        "history_reference_trade_days": _safe_int(row.get("history_reference_trade_days")),
        "sample_first_wave_start_date": (
            pd.Timestamp(row["sample_first_wave_start_date"]).date().isoformat()
            if pd.notna(row.get("sample_first_wave_start_date"))
            else None
        ),
        "sample_last_wave_end_date": (
            pd.Timestamp(row["sample_last_wave_end_date"]).date().isoformat()
            if pd.notna(row.get("sample_last_wave_end_date"))
            else None
        ),
        "amplitude_axis_labels": _axis_labels(row, "amplitude"),
        "duration_axis_labels": _axis_labels(row, "duration"),
        "current_wave_matches_surface": bool(row.get("current_wave_matches_surface") or False),
        "current_wave_percentile": _surface_current_percentile(row),
        "current_wave_average_remaining_prob": _safe_float(row.get("current_wave_average_remaining_prob")),
        "current_wave_average_aged_prob": _safe_float(row.get("current_wave_average_aged_prob")),
        "current_wave_remaining_vs_aged_odds": _safe_float(row.get("current_wave_remaining_vs_aged_odds")),
        "current_wave_aged_vs_remaining_odds": _safe_float(row.get("current_wave_aged_vs_remaining_odds")),
    }


def load_market_lifespan_surface_frame(
    store: Store,
    *,
    calc_date: date | None = None,
    entity_scope: str = "MARKET",
    entity_code: str | None = None,
) -> tuple[date, str, pd.DataFrame]:
    selected_date = calc_date
    if selected_date is None:
        selected_date_raw = store.read_scalar(
            """
            SELECT MAX(calc_date)
            FROM l3_gene_market_lifespan_surface
            WHERE entity_scope = ?
            """,
            (entity_scope,),
        )
        if selected_date_raw is None:
            raise ValueError(
                "No market lifespan surface rows found. Materialize l3_gene_market_lifespan_surface first "
                "(for example by running compute_gene_mirror on a target calc_date)."
            )
        selected_date = pd.Timestamp(selected_date_raw).date()

    resolved_entity_code = entity_code
    if resolved_entity_code is None:
        entity_frame = store.read_df(
            """
            SELECT DISTINCT entity_code
            FROM l3_gene_market_lifespan_surface
            WHERE entity_scope = ?
              AND calc_date = ?
            ORDER BY entity_code
            """,
            (entity_scope, selected_date),
        )
        if entity_frame.empty:
            raise ValueError(
                f"No market lifespan surface rows found for {selected_date.isoformat()}. "
                "Materialize l3_gene_market_lifespan_surface for that date first."
            )
        resolved_entity_code = str(entity_frame.iloc[0]["entity_code"])

    frame = store.read_df(
        """
        SELECT
            entity_scope,
            entity_code,
            entity_name,
            source_table,
            price_source_kind,
            calc_date,
            market_regime_direction,
            market_regime_label,
            wave_role,
            surface_label,
            amplitude_metric_name,
            history_reference_trade_days,
            sample_size,
            sample_first_wave_start_date,
            sample_last_wave_end_date,
            amplitude_min,
            amplitude_q25,
            amplitude_q50,
            amplitude_q75,
            amplitude_max,
            duration_min,
            duration_q25,
            duration_q50,
            duration_q75,
            duration_max,
            current_wave_matches_surface,
            current_wave_amplitude_percentile,
            current_wave_duration_percentile,
            current_wave_joint_percentile,
            current_wave_average_remaining_prob,
            current_wave_average_aged_prob,
            current_wave_remaining_vs_aged_odds,
            current_wave_aged_vs_remaining_odds
        FROM l3_gene_market_lifespan_surface
        WHERE entity_scope = ?
          AND entity_code = ?
          AND calc_date = ?
        ORDER BY surface_label
        """,
        (entity_scope, resolved_entity_code, selected_date),
    )
    if frame.empty:
        raise ValueError(
            f"No market lifespan surface rows found for {entity_scope}/{resolved_entity_code} on "
            f"{selected_date.isoformat()}. Materialize l3_gene_market_lifespan_surface first."
        )
    return selected_date, resolved_entity_code, frame


def build_market_lifespan_report_payload(
    frame: pd.DataFrame,
    *,
    calc_date: date,
    entity_scope: str,
    entity_code: str,
) -> dict[str, object]:
    normalized = frame.copy()
    normalized["surface_label"] = normalized["surface_label"].astype(str)
    normalized = normalized.set_index("surface_label", drop=False)

    surfaces: list[dict[str, object]] = []
    for surface_label in SURFACE_ORDER:
        if surface_label not in normalized.index:
            continue
        surfaces.append(_surface_summary(normalized.loc[surface_label]))

    if not surfaces:
        raise ValueError("No canonical market lifespan surfaces found in input frame.")

    entity_name = str(normalized.iloc[0].get("entity_name") or entity_code)
    return {
        "calc_date": calc_date.isoformat(),
        "entity_scope": entity_scope,
        "entity_code": entity_code,
        "entity_name": entity_name,
        "surface_count": len(surfaces),
        "surfaces": surfaces,
        "directory_contract": {
            "repo_root": r"G:\EmotionQuant-gamma",
            "data_root": r"G:\EmotionQuant_data",
            "temp_root": r"G:\EmotionQuant-temp",
            "report_root": r"G:\EmotionQuant-report",
        },
    }


def _render_surface_panel(ax: plt.Axes, surface: dict[str, object], *, odds_mode: bool) -> None:
    x = np.linspace(0.0, 100.0, 600)
    y = np.exp(-0.5 * ((x - 50.0) / 18.0) ** 2)
    y = y / y.max()
    colors, edge = _surface_theme(str(surface["surface_label"]), odds_mode=odds_mode)
    quartiles = [(0.0, 25.0), (25.0, 50.0), (50.0, 75.0), (75.0, 100.0)]

    for index, (left, right) in enumerate(quartiles):
        mask = (x >= left) & (x <= right)
        alpha = 0.55 if odds_mode else 0.40
        ax.fill_between(x[mask], y[mask], color=colors[index], alpha=alpha)

    ax.plot(x, y, color=edge, linewidth=2.0)
    for boundary in [25.0, 50.0, 75.0]:
        ax.axvline(boundary, color="#8a8a8a", linestyle="--", linewidth=0.8)

    ax.set_xlim(0.0, 100.0)
    ax.set_ylim(0.0, 1.15)
    ax.set_yticks([])
    ax.set_xticks(QUARTILE_TICKS)
    ax.set_xticklabels(surface["amplitude_axis_labels"], fontsize=8)
    ax.set_xlabel(_metric_label(str(surface["amplitude_metric_name"])), fontsize=9)
    ax.set_title(
        f'{surface["surface_label"]} | n={surface["sample_size"]}',
        fontsize=11,
        pad=8,
    )
    ax.text(
        0.01,
        1.03,
        _book_style_label(str(surface["surface_label"])),
        transform=ax.transAxes,
        fontsize=8,
        color="#555555",
    )

    duration_axis = ax.secondary_xaxis("top")
    duration_axis.set_xticks(QUARTILE_TICKS)
    duration_axis.set_xticklabels(surface["duration_axis_labels"], fontsize=8)
    duration_axis.set_xlabel("duration days", fontsize=9)

    current_percentile = _safe_float(surface.get("current_wave_percentile"))
    aged_prob = _safe_float(surface.get("current_wave_average_aged_prob"))
    odds = _safe_float(surface.get("current_wave_remaining_vs_aged_odds"))
    sample_size = int(surface.get("sample_size") or 0)
    if sample_size <= 0:
        message = "UNSCALED\ninsufficient history"
        bbox = dict(boxstyle="round,pad=0.3", facecolor="#fff4cc", edgecolor="#c9a227")
        ax.text(74.0, 0.78, message, fontsize=8, bbox=bbox)
        return

    if current_percentile is not None:
        current_y = math.exp(-0.5 * ((current_percentile - 50.0) / 18.0) ** 2)
        ax.scatter([current_percentile], [current_y], color="#1f77b4", s=38, zorder=3)
        if odds_mode:
            message = (
                f"current p={current_percentile:.1f}\n"
                f"aged={aged_prob:.2f}\n"
                f"remain/aged odds={odds:.2f}"
                if aged_prob is not None and odds is not None
                else f"current p={current_percentile:.1f}\naged/odds unavailable"
            )
        else:
            message = (
                f"current p={current_percentile:.1f}\n"
                f"aged={aged_prob:.2f}"
                if aged_prob is not None
                else f"current p={current_percentile:.1f}"
            )
        ax.text(
            min(max(current_percentile + 4.0, 3.0), 72.0),
            min(current_y + 0.10, 1.0),
            message,
            fontsize=8,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#ffffff", edgecolor="#7a7a7a"),
        )


def render_market_lifespan_panels(
    output_path: Path,
    payload: dict[str, object],
    *,
    odds_mode: bool,
) -> Path:
    surfaces = list(payload["surfaces"])
    figure, axes = plt.subplots(2, 2, figsize=(14, 10))
    flat_axes = list(axes.flatten())
    for ax, surface in zip(flat_axes, surfaces, strict=False):
        _render_surface_panel(ax, surface, odds_mode=odds_mode)
    for ax in flat_axes[len(surfaces) :]:
        ax.axis("off")

    title_suffix = "Odds Panels" if odds_mode else "Distribution Panels"
    figure.suptitle(
        f'{payload["entity_name"]} market lifespan framework | {payload["calc_date"]} | {title_suffix}',
        fontsize=14,
    )
    figure.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(figure)
    return output_path


def _markdown_surface_row(surface: dict[str, object]) -> str:
    aged = _safe_float(surface.get("current_wave_average_aged_prob"))
    odds = _safe_float(surface.get("current_wave_remaining_vs_aged_odds"))
    aged_label = "-" if aged is None else f"{aged:.3f}"
    odds_label = "-" if odds is None else f"{odds:.3f}"
    return (
        f'| {surface["surface_label"]} | {surface["sample_size"]} | '
        f'{surface["amplitude_metric_name"]} | '
        f'{" / ".join(surface["amplitude_axis_labels"][1:4])} | '
        f'{" / ".join(surface["duration_axis_labels"][1:4])} | '
        f'{aged_label} | {odds_label} |'
    )


def write_market_lifespan_report_bundle(
    output_root: Path,
    payload: dict[str, object],
) -> dict[str, Path]:
    output_root.mkdir(parents=True, exist_ok=True)
    calc_date_token = str(payload["calc_date"]).replace("-", "")
    prefix = f'{payload["entity_scope"].lower()}_{payload["entity_code"]}_{calc_date_token}'.replace("::", "_")

    distribution_path = output_root / f"{prefix}__market_lifespan_distribution_panels.png"
    odds_path = output_root / f"{prefix}__market_lifespan_odds_panels.png"
    markdown_path = output_root / f"{prefix}__market_lifespan_report.md"
    json_path = output_root / f"{prefix}__market_lifespan_report.json"

    render_market_lifespan_panels(distribution_path, payload, odds_mode=False)
    render_market_lifespan_panels(odds_path, payload, odds_mode=True)
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        f'# Market Lifespan Framework Report | {payload["entity_name"]}',
        "",
        f'- `calc_date`: `{payload["calc_date"]}`',
        f'- `entity_scope`: `{payload["entity_scope"]}`',
        f'- `entity_code`: `{payload["entity_code"]}`',
        f'- `directory contract`: `repo={payload["directory_contract"]["repo_root"]}` / '
        f'`data={payload["directory_contract"]["data_root"]}` / '
        f'`temp={payload["directory_contract"]["temp_root"]}` / '
        f'`report={payload["directory_contract"]["report_root"]}`',
        "",
        "## Figures",
        "",
        f'![distribution panels]({distribution_path.name})',
        "",
        f'![odds panels]({odds_path.name})',
        "",
        "## Surface Summary",
        "",
        "| surface | sample_size | amplitude_metric | amplitude q25/q50/q75 | duration q25/q50/q75 | avg aged prob | remain/aged odds |",
        "|---|---:|---|---|---|---:|---:|",
    ]
    for surface in payload["surfaces"]:
        lines.append(_markdown_surface_row(surface))
    lines.extend(
        [
            "",
            "## Output Contract",
            "",
            f'- `json summary`: `{json_path.name}`',
            f'- `distribution figure`: `{distribution_path.name}`',
            f'- `odds figure`: `{odds_path.name}`',
            "",
            "This report is product output and belongs in `G:\\EmotionQuant-report`; schema and evidence SoT remain in `G:\\EmotionQuant-gamma` and `G:\\EmotionQuant_data`.",
        ]
    )
    markdown_path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "markdown": markdown_path,
        "distribution_figure": distribution_path,
        "odds_figure": odds_path,
        "json": json_path,
    }
