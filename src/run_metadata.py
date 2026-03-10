from __future__ import annotations

# ---------------------------------------------------------------------------
# run_metadata.py — 运行元数据管理
# ---------------------------------------------------------------------------
# 职责：为每次 backtest / paper / daily run 分配唯一 run_id，
# 并把运行上下文（配置哈希、数据快照、git commit）写入 _meta_runs。
#
# run_id 是整个 trace 体系的根锚点：
#   所有 sidecar / trace / evidence 都必须能通过 run_id 追溯到这里。
#
# 设计约束：
# - run_id 格式：{scope}_{mode}_{variant}_{date_tag}_{time_tag}
# - 同一秒内同一 scope 的两次运行会产生相同 run_id（已知限制，个人量化可接受）
# - config_hash 基于完整 Settings 序列化，任何参数变化都会产生不同 hash
# - git_commit 失败时静默返回 None，不阻断运行
# ---------------------------------------------------------------------------

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

# 仓库根目录：用于 git rev-parse HEAD，定位到正确的 git 仓库。
REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class RunDescriptor:
    run_id: str
    mode: str
    variant: str


def config_hash_from_settings(config: Settings) -> str:
    """对完整 Settings 序列化后取 SHA-256，任何参数变化都会产生不同 hash。"""
    payload = config.model_dump(mode="json")
    body = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def git_commit() -> str | None:
    """获取当前 HEAD commit hash；失败（非 git 仓库或无权限）时静默返回 None。"""
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
    """把任意字符串规范化为 run_id 安全格式：只保留 [0-9A-Za-z_]，连续下划线合并。"""
    normalized = re.sub(r"[^0-9A-Za-z_]+", "_", value.strip().lower())
    return re.sub(r"_+", "_", normalized).strip("_") or "unknown"


def resolve_mode_variant(config: Settings) -> tuple[str, str]:
    """从配置解析 (mode, variant) 二元组，用于构造 run_id 和写入 _meta_runs。"""
    mode = config.pipeline_mode_normalized
    if mode == "legacy":
        # legacy 对照链使用固定 variant 名，避免因 dtt_variant 配置变化而污染历史对照结果。
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
    """
    构造唯一 run_id。格式：{scope}_{mode}_{variant}_{date_tag}_{time_tag}

    date_tag 优先级：
    1. signal_date 不为空 -> d{YYYYMMDD}（单日运行）
    2. start + end 不为空 -> w{YYYYMMDD}_{YYYYMMDD}（窗口运行）
    3. 其他             -> n{YYYYMMDD}（无日期锚点）

    已知限制：同一秒内同一 scope 的两次运行会产生相同 run_id。
    个人量化单机运行场景下可接受；如需严格唯一，可在 time_tag 加微秒或随机后缀。
    """
    current = now or datetime.utcnow()
    scope_slug = sanitize_label(scope)
    mode_slug = sanitize_label(mode)
    variant_slug = sanitize_label(variant)
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
    """
    生成数据状态快照 JSON，记录各关键表的最新日期。

    只记录可复现锚点（表名 + max_date），不内嵌完整统计数据，
    避免 _meta_runs 行过重。回放时可通过这里快速确认数据覆盖范围。
    """
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
