from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.backtest.normandy_bof_fat_tail_preservation import (
    build_normandy_bof_control_fat_tail_preservation_digest,
    read_normandy_bof_control_fat_tail_preservation_payload,
    write_normandy_bof_control_fat_tail_preservation_evidence,
)
from src.run_metadata import build_artifact_name, build_run_id, sanitize_label


def _parse_date(text: str) -> date:
    return date.fromisoformat(text)


def _resolve_latest_preservation_path(output_root: Path) -> Path:
    candidates = sorted(
        output_root.glob("*__bof_control_fat_tail_preservation.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(f"No bof_control_fat_tail_preservation evidence found under {output_root}")
    return candidates[0]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Normandy BOF_CONTROL fat-tail preservation digest")
    parser.add_argument(
        "--preservation-path",
        default=None,
        help="Preservation JSON path; default resolves the latest normandy/03-execution/evidence/*__bof_control_fat_tail_preservation.json",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON path; default normandy/03-execution/evidence/<run_id>__bof_control_fat_tail_preservation_digest.json",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output_root = REPO_ROOT / "normandy" / "03-execution" / "evidence"
    preservation_path = (
        Path(args.preservation_path).expanduser().resolve()
        if args.preservation_path
        else _resolve_latest_preservation_path(output_root)
    )
    preservation_payload = read_normandy_bof_control_fat_tail_preservation_payload(preservation_path)
    preservation_payload["preservation_path"] = str(preservation_path)
    start = _parse_date(str(preservation_payload["start"]))
    end = _parse_date(str(preservation_payload["end"]))
    dtt_variant = sanitize_label(str(preservation_payload.get("dtt_variant") or "unknown"))
    summary_run_id = build_run_id(
        scope="normandy_bof_control_fat_tail_preservation_digest",
        mode="dtt",
        variant=dtt_variant,
        start=start,
        end=end,
    )
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else output_root / build_artifact_name(summary_run_id, "bof_control_fat_tail_preservation_digest", "json")
    )

    payload = build_normandy_bof_control_fat_tail_preservation_digest(preservation_payload)
    payload["summary_run_id"] = summary_run_id
    path = write_normandy_bof_control_fat_tail_preservation_evidence(output_path, payload)
    print(f"normandy_bof_control_fat_tail_preservation_digest={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
