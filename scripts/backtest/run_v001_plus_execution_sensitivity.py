from __future__ import annotations

# Phase 4 / execution sensitivity:
# - 默认 variant 使用当前 pattern_* 主线命名。
# - 该脚本只比较“排序/风控差异是否进入执行约束”，不负责切默认参数。
# - 工作副本路径必须落 TEMP_PATH；若源库缺窗口，补数顺序仍遵守旧库优先和双 TuShare 兜底规则。

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.config import get_settings
from src.run_metadata import build_artifact_name, build_run_id, sanitize_label

DEFAULT_VARIANTS = [
    "v0_01_dtt_pattern_only",
    "v0_01_dtt_pattern_plus_irs_score",
]

DEFAULT_SCENARIOS = [
    ("top1_pos1", 1, 1),
    ("top1_pos2", 1, 2),
    ("top2_pos1", 2, 1),
    ("top2_pos2", 2, 2),
    ("top50_pos10", 50, 10),
]


@dataclass(frozen=True)
class SensitivityScenario:
    label: str
    dtt_top_n: int
    max_positions: int


@dataclass(frozen=True)
class ScenarioConclusion:
    entered_execution_constraint: bool
    summary: str


def _parse_date(text: str) -> date:
    return date.fromisoformat(text)


def _parse_variants(text: str) -> list[str]:
    variants = [item.strip().lower() for item in text.split(",") if item.strip()]
    if len(variants) < 2:
        raise ValueError("至少需要 2 个 variant 才能做敏感性对比。")
    return variants


def _parse_scenarios(text: str | None) -> list[SensitivityScenario]:
    if text is None or not text.strip():
        return [SensitivityScenario(label=label, dtt_top_n=top_n, max_positions=max_pos) for label, top_n, max_pos in DEFAULT_SCENARIOS]

    scenarios: list[SensitivityScenario] = []
    for chunk in text.split(","):
        item = chunk.strip()
        if not item:
            continue
        parts = [part.strip() for part in item.split(":")]
        if len(parts) != 3:
            raise ValueError(f"非法场景定义: {item}，应为 label:dtt_top_n:max_positions")
        label, dtt_top_n, max_positions = parts
        scenarios.append(
            SensitivityScenario(
                label=sanitize_label(label),
                dtt_top_n=int(dtt_top_n),
                max_positions=int(max_positions),
            )
        )
    if not scenarios:
        raise ValueError("至少需要 1 个敏感性场景。")
    return scenarios


def _conclude_scenario(pair_payload: dict[str, object]) -> ScenarioConclusion:
    rank_impact = pair_payload["rank_impact"]
    buy_trade_impact = pair_payload["buy_trade_impact"]
    reject_impact = pair_payload["maxpos_reject_impact"]

    trade_set_changed = int(buy_trade_impact["trade_set_changed_count"])
    quantity_changed = int(buy_trade_impact["quantity_changed_count"])
    reject_set_changed = int(reject_impact["reject_set_changed_count"])
    rank_changed = int(rank_impact["rank_changed_count"])
    selected_changed = int(rank_impact["selected_changed_count"])

    if trade_set_changed > 0 or quantity_changed > 0:
        return ScenarioConclusion(
            entered_execution_constraint=True,
            summary="右侧对比变体已经改变实际 BUY 成交集合或仓位数量，差异已进入执行约束。",
        )
    if reject_set_changed > 0:
        return ScenarioConclusion(
            entered_execution_constraint=True,
            summary="右侧对比变体已经改变 MAX_POSITIONS 拒单集合，差异已进入 Broker 风控边界。",
        )
    if selected_changed > 0:
        return ScenarioConclusion(
            entered_execution_constraint=False,
            summary="右侧对比变体已改变 Strategy Top-N 入选，但还没有传导到实际 BUY 成交或 MAX_POSITIONS 拒单。",
        )
    if rank_changed > 0:
        return ScenarioConclusion(
            entered_execution_constraint=False,
            summary="右侧对比变体只改变了名次，没有进入 Strategy Top-N 或 Broker 执行约束。",
        )
    return ScenarioConclusion(
        entered_execution_constraint=False,
        summary="左右对比变体在该场景下没有形成可观测的排序或执行差异。",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Top-N / max_positions sensitivity evidence for v0.01-plus")
    parser.add_argument("--start", required=True, help="Backtest start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="Backtest end date (YYYY-MM-DD)")
    parser.add_argument("--patterns", default="bof", help="Comma-separated patterns")
    parser.add_argument("--cash", type=float, default=None, help="Initial cash override")
    parser.add_argument("--variants", default=",".join(DEFAULT_VARIANTS), help="Comma-separated DTT variants")
    parser.add_argument(
        "--scenarios",
        default=None,
        help="Comma-separated label:dtt_top_n:max_positions items; default runs top1_pos1,top1_pos2,top2_pos1,top2_pos2,top50_pos10",
    )
    parser.add_argument("--db-path", default=None, help="Execution DuckDB path override")
    parser.add_argument(
        "--skip-rebuild-l3",
        action="store_true",
        help="Reuse existing l3_mss_daily/l3_irs_daily in each working DB",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path, default docs/spec/v0.01-plus/evidence/<run_id>__execution_sensitivity.json",
    )
    return parser


def _run_scenario(
    scenario: SensitivityScenario,
    variants: list[str],
    start: date,
    end: date,
    patterns: list[str],
    cash: float | None,
    db_path: Path,
    skip_rebuild_l3: bool,
    output_root: Path,
    working_root: Path,
) -> dict[str, object]:
    scenario_slug = sanitize_label(scenario.label)
    scenario_output = output_root / f"rank_decomposition__{scenario_slug}__top{scenario.dtt_top_n}_pos{scenario.max_positions}.json"
    working_db = working_root / f"rank_decomp_{scenario_slug}_top{scenario.dtt_top_n}_pos{scenario.max_positions}.duckdb"

    command = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "backtest" / "run_v001_plus_rank_decomposition.py"),
        "--start",
        start.isoformat(),
        "--end",
        end.isoformat(),
        "--patterns",
        ",".join(patterns),
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
        str(scenario_output),
    ]
    if cash is not None:
        command.extend(["--cash", str(cash)])
    if skip_rebuild_l3:
        command.append("--skip-rebuild-l3")

    try:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        stdout = exc.stdout.strip() if exc.stdout else ""
        stderr = exc.stderr.strip() if exc.stderr else ""
        raise RuntimeError(
            "敏感性场景执行失败："
            f"label={scenario.label}, dtt_top_n={scenario.dtt_top_n}, max_positions={scenario.max_positions}\n"
            f"stdout:\n{stdout}\n"
            f"stderr:\n{stderr}"
        ) from exc
    payload = json.loads(scenario_output.read_text(encoding="utf-8"))
    comparisons = payload["comparisons"]
    primary_pair_key = next(iter(comparisons))
    primary_pair = comparisons[primary_pair_key]
    conclusion = _conclude_scenario(primary_pair)
    runs = {item["variant"]: item for item in payload["runs"]}
    left_variant = primary_pair["rank_impact"]["left_variant"]
    right_variant = primary_pair["rank_impact"]["right_variant"]
    left_run = runs[left_variant]
    right_run = runs[right_variant]

    return {
        "label": scenario.label,
        "dtt_top_n": int(scenario.dtt_top_n),
        "max_positions": int(scenario.max_positions),
        "output_path": str(scenario_output),
        "working_db_path": str(working_db),
        "stdout": result.stdout.strip(),
        "primary_pair_key": primary_pair_key,
        "pair_summaries": comparisons,
        "primary_pair_summary": {
            "left_variant": left_variant,
            "right_variant": right_variant,
            "rank_changed_count": int(primary_pair["rank_impact"]["rank_changed_count"]),
            "selected_changed_count": int(primary_pair["rank_impact"]["selected_changed_count"]),
            "trade_set_changed_count": int(primary_pair["buy_trade_impact"]["trade_set_changed_count"]),
            "quantity_changed_count": int(primary_pair["buy_trade_impact"]["quantity_changed_count"]),
            "reject_set_changed_count": int(primary_pair["maxpos_reject_impact"]["reject_set_changed_count"]),
            "left_trade_count": int(left_run["trade_count"]),
            "right_trade_count": int(right_run["trade_count"]),
            "left_profit_factor": left_run["profit_factor"],
            "right_profit_factor": right_run["profit_factor"],
            "left_skip_maxpos_count": left_run["metrics"].get("skip_maxpos_count"),
            "right_skip_maxpos_count": right_run["metrics"].get("skip_maxpos_count"),
        },
        "runs": payload["runs"],
        "entered_execution_constraint": conclusion.entered_execution_constraint,
        "conclusion": conclusion.summary,
    }


def main() -> int:
    args = _build_parser().parse_args()
    cfg = get_settings().model_copy(deep=True)
    start = _parse_date(args.start)
    end = _parse_date(args.end)
    patterns = [item.strip().lower() for item in args.patterns.split(",") if item.strip()]
    variants = _parse_variants(args.variants)
    scenarios = _parse_scenarios(args.scenarios)
    db_path = Path(args.db_path).expanduser().resolve() if args.db_path else cfg.db_path

    output_root = REPO_ROOT / "docs" / "spec" / "v0.01-plus" / "evidence"
    output_root.mkdir(parents=True, exist_ok=True)
    working_root = (cfg.resolved_temp_path / "backtest").resolve()
    working_root.mkdir(parents=True, exist_ok=True)

    summary_run_id = build_run_id(
        scope="execution_sensitivity",
        mode="dtt",
        variant=f"{variants[0]}_vs_{variants[1]}",
        start=start,
        end=end,
    )
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else output_root / build_artifact_name(summary_run_id, "execution_sensitivity", "json")
    )

    scenario_payloads = [
        _run_scenario(
            scenario=scenario,
            variants=variants,
            start=start,
            end=end,
            patterns=patterns or ["bof"],
            cash=args.cash,
            db_path=db_path,
            skip_rebuild_l3=args.skip_rebuild_l3,
            output_root=output_root,
            working_root=working_root,
        )
        for scenario in scenarios
    ]

    payload = {
        "summary_run_id": summary_run_id,
        "source_db_path": str(db_path),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "patterns": patterns or ["bof"],
        "variants": variants,
        "scenarios": [asdict(item) for item in scenarios],
        "results": scenario_payloads,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"execution_sensitivity={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
