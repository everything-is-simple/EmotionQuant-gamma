from __future__ import annotations

# Phase 4 / windowed sensitivity:
# - 默认 variant 使用当前 pattern_* 命名，不再沿用旧 bof_* 别名。
# - 每个子窗口都拆到独立 working db，副本和缓存固定放 TEMP_PATH，避免长窗口把正式库和仓库目录打脏。
# - 该脚本只重放既有数据，不直接补数；若窗口缺口存在，必须先按旧库优先、双 TuShare 通道兜底补齐。

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.run_metadata import build_artifact_name, build_run_id

DEFAULT_VARIANTS = [
    "v0_01_dtt_pattern_plus_irs_score",
    "v0_01_dtt_pattern_plus_irs_mss_score",
]
DEFAULT_WINDOWS = [
    ("mid_window", "2025-12-22", "2026-02-24"),
]
DEFAULT_SCENARIOS = [
    ("top1_pos1", 1, 1),
    ("top1_pos2", 1, 2),
    ("top2_pos1", 2, 1),
    ("top2_pos2", 2, 2),
    ("top50_pos10", 50, 10),
]


@dataclass(frozen=True)
class WindowSpec:
    label: str
    start: date
    end: date


@dataclass(frozen=True)
class ScenarioSpec:
    label: str
    dtt_top_n: int
    max_positions: int


def _parse_date(text: str) -> date:
    return date.fromisoformat(text)


def _parse_windows(text: str | None) -> list[WindowSpec]:
    if text is None or not text.strip():
        return [
            WindowSpec(label=label, start=_parse_date(start), end=_parse_date(end))
            for label, start, end in DEFAULT_WINDOWS
        ]

    windows: list[WindowSpec] = []
    for chunk in text.split(","):
        item = chunk.strip()
        if not item:
            continue
        parts = [part.strip() for part in item.split(":")]
        if len(parts) != 3:
            raise ValueError(f"非法窗口定义: {item}，应为 label:start:end")
        label, start_text, end_text = parts
        windows.append(WindowSpec(label=label, start=_parse_date(start_text), end=_parse_date(end_text)))
    if not windows:
        raise ValueError("至少需要一个窗口。")
    return windows


def _parse_scenarios(text: str | None) -> list[ScenarioSpec]:
    if text is None or not text.strip():
        return [
            ScenarioSpec(label=label, dtt_top_n=top_n, max_positions=max_positions)
            for label, top_n, max_positions in DEFAULT_SCENARIOS
        ]

    scenarios: list[ScenarioSpec] = []
    for chunk in text.split(","):
        item = chunk.strip()
        if not item:
            continue
        parts = [part.strip() for part in item.split(":")]
        if len(parts) != 3:
            raise ValueError(f"非法场景定义: {item}，应为 label:dtt_top_n:max_positions")
        label, top_n_text, max_positions_text = parts
        scenarios.append(
            ScenarioSpec(
                label=label,
                dtt_top_n=int(top_n_text),
                max_positions=int(max_positions_text),
            )
        )
    if not scenarios:
        raise ValueError("至少需要一个场景。")
    return scenarios


def _parse_variants(text: str) -> list[str]:
    variants = [item.strip().lower() for item in text.split(",") if item.strip()]
    if len(variants) != 2:
        raise ValueError("窗口敏感性脚本当前只支持 2 个 variant 对比。")
    return variants


def _window_payload(window: WindowSpec) -> dict[str, object]:
    return {
        "label": window.label,
        "start": window.start.isoformat(),
        "end": window.end.isoformat(),
    }


def _scenario_payload(scenario: ScenarioSpec) -> dict[str, object]:
    return {
        "label": scenario.label,
        "dtt_top_n": scenario.dtt_top_n,
        "max_positions": scenario.max_positions,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run windowed DTT sensitivity matrix")
    parser.add_argument("--windows", default=None, help="Comma-separated label:start:end windows")
    parser.add_argument("--scenarios", default=None, help="Comma-separated label:dtt_top_n:max_positions scenarios")
    parser.add_argument("--variants", default=",".join(DEFAULT_VARIANTS), help="Comma-separated variants")
    parser.add_argument("--patterns", default="bof", help="Comma-separated patterns")
    parser.add_argument("--db-path", default=None, help="Execution DuckDB path override")
    parser.add_argument("--memory-limit", default="4GB", help="DuckDB memory limit for child runs")
    parser.add_argument(
        "--skip-rebuild-l3",
        action="store_true",
        help="Reuse existing l3_mss_daily/l3_irs_daily in the working DB instead of rebuilding them",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path, default docs/spec/v0.01-plus/evidence/<run_id>__windowed_sensitivity.json",
    )
    return parser


def _collect_summary(result_path: Path) -> dict[str, object]:
    # 子任务先各自落单文件，这里只提取判断 Gate 需要的最小摘要，避免 summary 过重。
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    comparison_key = next(iter(payload["comparisons"].keys()))
    comparison = payload["comparisons"][comparison_key]
    rank_impact = comparison["rank_impact"]
    buy_trade_impact = comparison["buy_trade_impact"]
    maxpos_reject_impact = comparison["maxpos_reject_impact"]
    return {
        "result_path": str(result_path),
        "summary_run_id": payload["summary_run_id"],
        "comparison_key": comparison_key,
        "runs": [
            {
                "variant": run["variant"],
                "trade_count": run["trade_count"],
                "expected_value": run["expected_value"],
                "profit_factor": run["profit_factor"],
                "max_drawdown": run["max_drawdown"],
                "buy_trade_count": run["buy_trade_count"],
                "buy_reject_maxpos_count": run["buy_reject_maxpos_count"],
            }
            for run in payload["runs"]
        ],
        "rank_impact": {
            "rank_changed_count": rank_impact["rank_changed_count"],
            "selected_changed_count": rank_impact["selected_changed_count"],
            "dates_with_rank_change": rank_impact["dates_with_rank_change"],
            "dates_with_selected_change": rank_impact["dates_with_selected_change"],
        },
        "buy_trade_impact": {
            "trade_set_changed_count": buy_trade_impact["trade_set_changed_count"],
            "quantity_changed_count": buy_trade_impact["quantity_changed_count"],
            "dates_with_trade_set_change": buy_trade_impact["dates_with_trade_set_change"],
            "dates_with_quantity_change": buy_trade_impact["dates_with_quantity_change"],
        },
        "maxpos_reject_impact": {
            "reject_set_changed_count": maxpos_reject_impact["reject_set_changed_count"],
            "dates_with_reject_change": maxpos_reject_impact["dates_with_reject_change"],
        },
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    windows = _parse_windows(args.windows)
    scenarios = _parse_scenarios(args.scenarios)
    variants = _parse_variants(args.variants)
    patterns = args.patterns
    db_path = Path(args.db_path).resolve() if args.db_path else Path(os.getenv("DATA_PATH", "G:\\EmotionQuant_data")) / "emotionquant.duckdb"

    summary_run_id = build_run_id(
        scope="windowed_sensitivity",
        mode="dtt",
        variant=f"{variants[0]}_vs_{variants[1]}",
        start=min(window.start for window in windows),
        end=max(window.end for window in windows),
    )
    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_path = REPO_ROOT / "docs" / "spec" / "v0.01-plus" / "evidence" / build_artifact_name(
            summary_run_id,
            "windowed_sensitivity",
            "json",
        )
    evidence_root = output_path.parent

    results: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []

    for window in windows:
        for scenario in scenarios:
            # 长窗口按“窗口 + 场景”拆分执行，避免一次性全矩阵把 DuckDB 内存打爆。
            child_output = evidence_root / build_artifact_name(
                build_run_id(
                    scope=f"rank_decomp_{window.label}_{scenario.label}",
                    mode="dtt",
                    variant=f"{variants[0]}_vs_{variants[1]}",
                    start=window.start,
                    end=window.end,
                ),
                "rank_decomposition",
                "json",
            )
            working_db = Path("G:/EmotionQuant-temp/backtest") / f"rank_{window.label}_{scenario.label}.duckdb"
            command = [
                sys.executable,
                str(REPO_ROOT / "scripts" / "backtest" / "run_v001_plus_rank_decomposition.py"),
                "--start",
                window.start.isoformat(),
                "--end",
                window.end.isoformat(),
                "--patterns",
                patterns,
                "--variants",
                ",".join(variants),
                "--dtt-top-n",
                str(scenario.dtt_top_n),
                "--max-positions",
                str(scenario.max_positions),
                "--db-path",
                str(db_path),
                "--working-db-path",
                str(working_db),
                "--output",
                str(child_output),
            ]
            if args.skip_rebuild_l3:
                command.append("--skip-rebuild-l3")

            child_env = os.environ.copy()
            if args.memory_limit:
                child_env["DUCKDB_MEMORY_LIMIT"] = args.memory_limit

            try:
                # 每个子任务都走独立子进程，便于单独施加 DuckDB 会话内存上限。
                completed = subprocess.run(
                    command,
                    cwd=REPO_ROOT,
                    env=child_env,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                result_summary = _collect_summary(child_output)
                result_summary["window"] = _window_payload(window)
                result_summary["scenario"] = _scenario_payload(scenario)
                result_summary["memory_limit"] = args.memory_limit
                result_summary["stdout_tail"] = completed.stdout.strip().splitlines()[-10:]
                results.append(result_summary)
            except subprocess.CalledProcessError as exc:
                failures.append(
                    {
                        "window": _window_payload(window),
                        "scenario": _scenario_payload(scenario),
                        "memory_limit": args.memory_limit,
                        "returncode": exc.returncode,
                        "stdout_tail": (exc.stdout or "").strip().splitlines()[-20:],
                        "stderr_tail": (exc.stderr or "").strip().splitlines()[-20:],
                    }
                )

    summary = {
        "summary_run_id": summary_run_id,
        "source_db_path": str(db_path),
        "patterns": [item.strip() for item in patterns.split(",") if item.strip()],
        "variants": variants,
        "windows": [_window_payload(window) for window in windows],
        "scenarios": [_scenario_payload(scenario) for scenario in scenarios],
        "memory_limit": args.memory_limit,
        "completed_count": len(results),
        "failed_count": len(failures),
        "results": results,
        "failures": failures,
    }
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"windowed_sensitivity={output_path}")
    if failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
