from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.backtest.normandy_sb_refinement import (  # noqa: E402
    build_normandy_sb_refinement_report,
    collect_normandy_sb_refinement_snapshot,
)
from src.backtest.normandy_volman_alpha import (  # noqa: E402
    read_normandy_volman_alpha_payload,
    write_normandy_volman_alpha_evidence,
)
from src.run_metadata import build_artifact_name, sanitize_label  # noqa: E402


def _resolve_latest_path(output_root: Path, pattern: str) -> Path:
    candidates = sorted(
        output_root.glob(pattern),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(f"No evidence found under {output_root} for {pattern}")
    return candidates[0]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Normandy SB refinement or no-go report")
    parser.add_argument(
        "--matrix-path",
        default=None,
        help="Matrix JSON path; default resolves the latest normandy/03-execution/evidence/*__volman_alpha_matrix.json",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="Optional snapshot DuckDB path; default uses matrix_payload['db_path']",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path; default normandy/03-execution/evidence/<matrix_run_id>__sb_refinement_report.json",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output_root = REPO_ROOT / "normandy" / "03-execution" / "evidence"
    matrix_path = (
        Path(args.matrix_path).expanduser().resolve()
        if args.matrix_path
        else _resolve_latest_path(output_root, "*__volman_alpha_matrix.json")
    )
    matrix_payload = read_normandy_volman_alpha_payload(matrix_path)
    matrix_payload["matrix_path"] = str(matrix_path)

    db_path = args.db_path or matrix_payload.get("db_path")
    snapshot_payload = collect_normandy_sb_refinement_snapshot(matrix_payload, db_path)
    payload = build_normandy_sb_refinement_report(matrix_payload, snapshot_payload)

    matrix_summary_run_id = str(matrix_payload.get("summary_run_id") or "")
    matrix_variant = sanitize_label(str(matrix_payload.get("dtt_variant") or "unknown"))
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else output_root / build_artifact_name(matrix_summary_run_id or matrix_variant, "sb_refinement_report", "json")
    )
    path = write_normandy_volman_alpha_evidence(output_path, payload)
    print(f"normandy_sb_refinement_report={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
