from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
import json
import math
from pathlib import Path
import shutil

from src.backtest.engine import run_backtest
from src.config import Settings
from src.data.builder import build_layers
from src.data.store import Store


@dataclass(frozen=True)
class AblationScenario:
    label: str
    enable_mss_gate: bool
    enable_irs_filter: bool


@dataclass(frozen=True)
class AblationRunResult:
    label: str
    enable_mss_gate: bool
    enable_irs_filter: bool
    trade_days: int
    trade_count: int
    expected_value: float | None
    profit_factor: float | None
    max_drawdown: float | None
    signals_count: int
    trades_count: int


def build_selector_ablation_scenarios() -> list[AblationScenario]:
    return [
        AblationScenario(label="bof_baseline", enable_mss_gate=False, enable_irs_filter=False),
        AblationScenario(label="bof_plus_mss", enable_mss_gate=True, enable_irs_filter=False),
        AblationScenario(label="bof_plus_mss_plus_irs", enable_mss_gate=True, enable_irs_filter=True),
    ]


def clear_runtime_tables(store: Store) -> None:
    for table in ("l4_pattern_stats", "l4_daily_report", "l4_trades", "l4_orders", "l4_stock_trust", "l3_signals"):
        store.conn.execute(f"DELETE FROM {table}")


def _finite_or_none(value: float | int | None) -> float | None:
    if value is None:
        return None
    cast = float(value)
    if not math.isfinite(cast):
        return None
    return cast


def _snapshot_ablation_metrics(store: Store, start: date, end: date) -> tuple[int, int]:
    signals_count = int(
        store.read_scalar(
            "SELECT COUNT(*) FROM l3_signals WHERE signal_date BETWEEN ? AND ?",
            (start, end),
        )
        or 0
    )
    trades_count = int(
        store.read_scalar(
            "SELECT COUNT(*) FROM l4_trades WHERE execute_date BETWEEN ? AND ?",
            (start, end),
        )
        or 0
    )
    return signals_count, trades_count


def prepare_working_db(source_db: str | Path, working_db: str | Path) -> Path:
    source = Path(source_db).expanduser().resolve()
    target = Path(working_db).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    shutil.copy2(source, target)
    wal_source = source.with_suffix(source.suffix + ".wal")
    wal_target = target.with_suffix(target.suffix + ".wal")
    if wal_source.exists():
        shutil.copy2(wal_source, wal_target)
    elif wal_target.exists():
        wal_target.unlink()
    return target


def run_selector_ablation(
    db_path: str | Path,
    config: Settings,
    start: date,
    end: date,
    patterns: list[str] | None = None,
    initial_cash: float | None = None,
    rebuild_l3: bool = True,
    working_db_path: str | Path | None = None,
) -> dict:
    source_db = Path(db_path).expanduser().resolve()
    db_file = (
        prepare_working_db(source_db, working_db_path)
        if working_db_path is not None
        else source_db
    )

    if rebuild_l3:
        store = Store(db_file)
        try:
            build_layers(store, config, layers=["l3"], start=start, end=end, force=True)
        finally:
            store.close()

    runs: list[AblationRunResult] = []
    for scenario in build_selector_ablation_scenarios():
        clr = Store(db_file)
        try:
            clear_runtime_tables(clr)
        finally:
            clr.close()

        cfg = config.model_copy(deep=True)
        cfg.enable_mss_gate = scenario.enable_mss_gate
        cfg.enable_irs_filter = scenario.enable_irs_filter

        result = run_backtest(
            db_path=db_file,
            config=cfg,
            start=start,
            end=end,
            patterns=patterns,
            initial_cash=initial_cash,
        )

        snap = Store(db_file)
        try:
            signals_count, trades_count = _snapshot_ablation_metrics(snap, start, end)
        finally:
            snap.close()

        runs.append(
            AblationRunResult(
                label=scenario.label,
                enable_mss_gate=scenario.enable_mss_gate,
                enable_irs_filter=scenario.enable_irs_filter,
                trade_days=result.trade_days,
                trade_count=result.trade_count,
                expected_value=_finite_or_none(result.expected_value),
                profit_factor=_finite_or_none(result.profit_factor),
                max_drawdown=_finite_or_none(result.max_drawdown),
                signals_count=signals_count,
                trades_count=trades_count,
            )
        )

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "source_db_path": str(source_db),
        "db_path": str(db_file),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "patterns": patterns or ["bof"],
        "initial_cash": float(initial_cash if initial_cash is not None else config.backtest_initial_cash),
        "runs": [asdict(run) for run in runs],
    }


def write_ablation_evidence(output_path: str | Path, payload: dict) -> Path:
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
