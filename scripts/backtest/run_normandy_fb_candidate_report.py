from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.backtest.normandy_fb_provenance import build_normandy_fb_candidate_report
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


def _resolve_matching_digest_path(output_root: Path, matrix_summary_run_id: str | None) -> Path | None:
    if not matrix_summary_run_id:
        return None
    candidates = sorted(
        output_root.glob("*__volman_alpha_digest.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for candidate in candidates:
        payload = read_normandy_volman_alpha_payload(candidate)
        if str(payload.get("matrix_summary_run_id") or "") == matrix_summary_run_id:
            return candidate
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Normandy FB focused provenance report")
    parser.add_argument(
        "--matrix-path",
        default=None,
        help="Volman matrix JSON path; default resolves the latest normandy/03-execution/evidence/*__volman_alpha_matrix.json",
    )
    parser.add_argument(
        "--digest-path",
        default=None,
        help="Optional digest JSON path; default resolves the digest whose matrix_summary_run_id matches the selected matrix",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path; default normandy/03-execution/evidence/<matrix_run_id>__fb_candidate_report.json",
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
    digest_path = (
        Path(args.digest_path).expanduser().resolve()
        if args.digest_path
        else _resolve_matching_digest_path(output_root, matrix_summary_run_id)
    )
    digest_payload = read_normandy_volman_alpha_payload(digest_path) if digest_path else None

    payload = build_normandy_fb_candidate_report(matrix_payload, digest_payload)
    matrix_variant = sanitize_label(str(matrix_payload.get("dtt_variant") or "unknown"))
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else output_root / build_artifact_name(matrix_summary_run_id or matrix_variant, "fb_candidate_report", "json")
    )
    path = write_normandy_volman_alpha_evidence(output_path, payload)
    print(f"normandy_fb_candidate_report={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
