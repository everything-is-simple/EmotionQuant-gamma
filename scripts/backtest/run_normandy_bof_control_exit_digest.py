from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.backtest.normandy_bof_exit import (
    build_normandy_bof_control_exit_digest,
    read_normandy_bof_control_exit_payload,
    write_normandy_bof_control_exit_evidence,
)
from src.run_metadata import build_artifact_name, build_run_id, sanitize_label


def _parse_date(text: str) -> date:
    return date.fromisoformat(text)


def _resolve_latest_matrix_path(output_root: Path) -> Path:
    candidates = sorted(
        output_root.glob("*__bof_control_exit_matrix.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(f"No bof_control_exit_matrix evidence found under {output_root}")
    return candidates[0]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Normandy BOF_CONTROL exit digest")
    parser.add_argument(
        "--matrix-path",
        default=None,
        help="Matrix JSON path; default resolves the latest normandy/03-execution/evidence/*__bof_control_exit_matrix.json",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path; default normandy/03-execution/evidence/<run_id>__bof_control_exit_digest.json",
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
    matrix_payload = read_normandy_bof_control_exit_payload(matrix_path)
    matrix_payload["matrix_path"] = str(matrix_path)
    start = _parse_date(str(matrix_payload["start"]))
    end = _parse_date(str(matrix_payload["end"]))
    dtt_variant = sanitize_label(str(matrix_payload.get("dtt_variant") or "unknown"))
    summary_run_id = build_run_id(
        scope="normandy_bof_control_exit_digest",
        mode="dtt",
        variant=dtt_variant,
        start=start,
        end=end,
    )
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else output_root / build_artifact_name(summary_run_id, "bof_control_exit_digest", "json")
    )

    payload = build_normandy_bof_control_exit_digest(matrix_payload)
    payload["summary_run_id"] = summary_run_id
    path = write_normandy_bof_control_exit_evidence(output_path, payload)
    print(f"normandy_bof_control_exit_digest={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
