from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from src.config import Settings
from src.data.store import Store

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class RunDescriptor:
    run_id: str
    mode: str
    variant: str


def config_hash_from_settings(config: Settings) -> str:
    payload = config.model_dump(mode="json")
    body = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def git_commit() -> str | None:
    try:
        output = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
            cwd=REPO_ROOT,
        ).strip()
        return output or None
    except Exception:
        return None


def sanitize_label(value: str) -> str:
    normalized = re.sub(r"[^0-9A-Za-z_]+", "_", value.strip().lower())
    return re.sub(r"_+", "_", normalized).strip("_") or "unknown"


def resolve_mode_variant(config: Settings) -> tuple[str, str]:
    mode = config.pipeline_mode_normalized
    if mode == "legacy":
        return mode, "legacy_bof_baseline"
    return mode, sanitize_label(config.dtt_variant_normalized)


def build_run_id(
    scope: str,
    mode: str,
    variant: str,
    signal_date: date | None = None,
    start: date | None = None,
    end: date | None = None,
    now: datetime | None = None,
) -> str:
    current = now or datetime.utcnow()
    scope_slug = sanitize_label(scope)
    mode_slug = sanitize_label(mode)
    variant_slug = sanitize_label(variant)
    # run_id 只编码最关键的追溯维度：运行类型、链路模式、variant、日期窗口和时间戳。
    if signal_date is not None:
        date_tag = f"d{signal_date:%Y%m%d}"
    elif start is not None and end is not None:
        date_tag = f"w{start:%Y%m%d}_{end:%Y%m%d}"
    else:
        date_tag = f"n{current:%Y%m%d}"
    time_tag = current.strftime("t%H%M%S")
    return f"{scope_slug}_{mode_slug}_{variant_slug}_{date_tag}_{time_tag}"


def build_artifact_name(run_id: str, artifact_kind: str, extension: str) -> str:
    kind_slug = sanitize_label(artifact_kind)
    ext = extension.lstrip(".")
    return f"{run_id}__{kind_slug}.{ext}"


def build_data_snapshot(store: Store) -> str:
    # 数据快照只记录可复现锚点，不试图内嵌完整统计，避免 run 元数据过重。
    snapshot = {
        "db_name": store.db_path.name,
        "schema_version": store.get_schema_version().schema_version,
        "l1_stock_daily_max": store.get_max_date("l1_stock_daily"),
        "l2_stock_adj_daily_max": store.get_max_date("l2_stock_adj_daily"),
        "l3_mss_daily_max": store.get_max_date("l3_mss_daily"),
        "l3_irs_daily_max": store.get_max_date("l3_irs_daily"),
    }
    return json.dumps(snapshot, ensure_ascii=False, sort_keys=True, default=str)


def start_run(
    store: Store,
    scope: str,
    modules: Sequence[str],
    config: Settings,
    runtime_env: str,
    artifact_root: str,
    signal_date: date | None = None,
    start: date | None = None,
    end: date | None = None,
) -> RunDescriptor:
    mode, variant = resolve_mode_variant(config)
    run_id = build_run_id(
        scope=scope,
        mode=mode,
        variant=variant,
        signal_date=signal_date,
        start=start,
        end=end,
    )
    row = pd.DataFrame(
        [
            {
                "run_id": run_id,
                "start_time": datetime.utcnow(),
                "end_time": None,
                "modules": ",".join(modules),
                "status": "RUNNING",
                "error_summary": None,
                "config_hash": config_hash_from_settings(config),
                "data_snapshot": build_data_snapshot(store),
                "git_commit": git_commit(),
                "runtime_env": runtime_env,
                "mode": mode,
                "variant": variant,
                "artifact_root": artifact_root,
            }
        ]
    )
    # `_meta_runs` 是运行级锚点：sidecar、evidence、回放都必须能先追到这里。
    store.bulk_upsert("_meta_runs", row)
    return RunDescriptor(run_id=run_id, mode=mode, variant=variant)


def finish_run(store: Store, run_id: str, status: str, error_summary: str | None = None) -> None:
    existing = store.read_df("SELECT * FROM _meta_runs WHERE run_id = ?", (run_id,))
    if existing.empty:
        return
    row = existing.iloc[0].to_dict()
    row["end_time"] = datetime.utcnow()
    row["status"] = status
    row["error_summary"] = error_summary
    store.bulk_upsert("_meta_runs", pd.DataFrame([row]))
