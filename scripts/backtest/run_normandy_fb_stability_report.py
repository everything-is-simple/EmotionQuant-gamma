from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.backtest.normandy_fb_stability import (
    build_normandy_fb_stability_report,
    collect_normandy_fb_stability_snapshot,
)
from src.backtest.normandy_volman_alpha import (
    read_normandy_volman_alpha_payload,
    write_normandy_volman_alpha_evidence,
)
from src.run_metadata import build_artifact_name, sanitize_label


def _resolve_latest_matrix_path(output_root: Path) -> Path:
    candidates = sorted(
        output_root.glob("*__volman_alpha_matrix.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(f"No volman_alpha_matrix evidence found under {output_root}")
    return candidates[0]


def _resolve_matching_payload_path(
    output_root: Path,
    matrix_summary_run_id: str | None,
    artifact_name: str,
) -> Path | None:
    if not matrix_summary_run_id:
        return None
    candidates = sorted(
        output_root.glob(f"*__{artifact_name}.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for candidate in candidates:
        payload = read_normandy_volman_alpha_payload(candidate)
        if str(payload.get("matrix_summary_run_id") or "") == matrix_summary_run_id:
            return candidate
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Normandy FB stability report")
    parser.add_argument(
        "--matrix-path",
        default=None,
        help="Volman matrix JSON path; default resolves the latest normandy/03-execution/evidence/*__volman_alpha_matrix.json",
    )
    parser.add_argument(
        "--candidate-report-path",
        default=None,
        help="Optional FB candidate report path; default resolves the matching *fb_candidate_report.json",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="Optional snapshot DuckDB path; default uses matrix_payload['db_path']",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path; default normandy/03-execution/evidence/<matrix_run_id>__fb_stability_report.json",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output_root = REPO_ROOT / "normandy" / "03-execution" / "evidence"
    matrix_path = (
        Path(args.matrix_path).expanduser().resolve()
        if args.matrix_path
        else _resolve_latest_matrix_path(output_root)
    )
    matrix_payload = read_normandy_volman_alpha_payload(matrix_path)
    matrix_payload["matrix_path"] = str(matrix_path)
    matrix_summary_run_id = str(matrix_payload.get("summary_run_id") or "")
    candidate_report_path = (
        Path(args.candidate_report_path).expanduser().resolve()
        if args.candidate_report_path
        else _resolve_matching_payload_path(output_root, matrix_summary_run_id, "fb_candidate_report")
    )
    if candidate_report_path is None:
        raise FileNotFoundError("Unable to resolve matching fb_candidate_report evidence")

    candidate_report_payload = read_normandy_volman_alpha_payload(candidate_report_path)
    db_path = args.db_path or matrix_payload.get("db_path")
    snapshot_payload = collect_normandy_fb_stability_snapshot(matrix_payload, db_path)
    payload = build_normandy_fb_stability_report(matrix_payload, candidate_report_payload, snapshot_payload)

    matrix_variant = sanitize_label(str(matrix_payload.get("dtt_variant") or "unknown"))
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else output_root / build_artifact_name(matrix_summary_run_id or matrix_variant, "fb_stability_report", "json")
    )
    path = write_normandy_volman_alpha_evidence(output_path, payload)
    print(f"normandy_fb_stability_report={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
