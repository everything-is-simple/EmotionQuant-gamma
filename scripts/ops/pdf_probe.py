from __future__ import annotations

import argparse
import json
from pathlib import Path

import fitz
import numpy as np
import pdfplumber
from PIL import Image
from rapidocr_onnxruntime import RapidOCR


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Probe a PDF and report whether pages are text-based or likely scanned"
    )
    parser.add_argument("pdf_path", help="Path to the input PDF")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help="Maximum number of pages to inspect; default inspects the first 5 pages",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=200,
        help="Render DPI for OCR; default is 200",
    )
    parser.add_argument(
        "--text-threshold",
        type=int,
        default=40,
        help="Minimum direct-text character count to classify a page as text-readable",
    )
    parser.add_argument(
        "--ocr-threshold",
        type=int,
        default=20,
        help="Minimum OCR character count to classify a page as OCR-readable",
    )
    parser.add_argument(
        "--ocr-all",
        action="store_true",
        help="Run OCR even when a page already has extractable text",
    )
    parser.add_argument(
        "--render-dir",
        default=None,
        help="Optional directory to save rendered page PNGs",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional JSON output path; defaults to stdout only",
    )
    return parser


def _normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return " ".join(text.split())


def _snippet(text: str, limit: int = 120) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _render_page(page: fitz.Page, dpi: int) -> Image.Image:
    zoom = dpi / 72.0
    pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    return Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)


def _ocr_page(engine: RapidOCR, image: Image.Image) -> tuple[str, float | None]:
    result, _ = engine(np.array(image))
    if not result:
        return "", None
    text_parts = [item[1] for item in result if len(item) >= 2 and item[1]]
    confidences = [float(item[2]) for item in result if len(item) >= 3]
    avg_confidence = sum(confidences) / len(confidences) if confidences else None
    return _normalize_text(" ".join(text_parts)), avg_confidence


def _classify_page(
    direct_text: str,
    ocr_text: str,
    text_threshold: int,
    ocr_threshold: int,
) -> tuple[str, bool]:
    direct_chars = len(direct_text)
    ocr_chars = len(ocr_text)
    # 优先承认真正可抽取的文本页；只有直接文本很弱、OCR 明显更强时才判成扫描页。
    if direct_chars >= text_threshold:
        return "direct_text", False
    if ocr_chars >= ocr_threshold:
        return "ocr", True
    return "unreadable_or_sparse", False


def probe_pdf(
    pdf_path: Path,
    max_pages: int,
    dpi: int,
    text_threshold: int,
    ocr_threshold: int,
    ocr_all: bool,
    render_dir: Path | None,
) -> dict[str, object]:
    pdf_path = pdf_path.expanduser().resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if render_dir is not None:
        render_dir.mkdir(parents=True, exist_ok=True)

    engine = RapidOCR()
    page_summaries: list[dict[str, object]] = []
    scanned_page_count = 0

    with fitz.open(pdf_path) as doc, pdfplumber.open(str(pdf_path)) as plumber_doc:
        pages_to_probe = min(max_pages, len(doc))
        for index in range(pages_to_probe):
            fitz_page = doc[index]
            plumber_page = plumber_doc.pages[index]

            direct_text = _normalize_text(plumber_page.extract_text())
            render_image = _render_page(fitz_page, dpi)
            ocr_text = ""
            ocr_confidence = None

            if ocr_all or len(direct_text) < text_threshold:
                ocr_text, ocr_confidence = _ocr_page(engine, render_image)

            read_mode, likely_scanned = _classify_page(
                direct_text=direct_text,
                ocr_text=ocr_text,
                text_threshold=text_threshold,
                ocr_threshold=ocr_threshold,
            )
            if likely_scanned:
                scanned_page_count += 1

            rendered_path = None
            if render_dir is not None:
                rendered_path = render_dir / f"{pdf_path.stem}_page_{index + 1:03d}.png"
                render_image.save(rendered_path)

            page_summaries.append(
                {
                    "page_number": index + 1,
                    "direct_text_chars": len(direct_text),
                    "ocr_text_chars": len(ocr_text),
                    "recommended_read_mode": read_mode,
                    "likely_scanned_page": likely_scanned,
                    "direct_text_snippet": _snippet(direct_text),
                    "ocr_text_snippet": _snippet(ocr_text),
                    "ocr_avg_confidence": ocr_confidence,
                    "rendered_image_path": str(rendered_path) if rendered_path else None,
                    "image_size": {
                        "width": render_image.width,
                        "height": render_image.height,
                    },
                }
            )

    probed_pages = len(page_summaries)
    likely_scanned_pdf = scanned_page_count > 0 and scanned_page_count >= max(1, probed_pages // 2)
    recommended_pipeline = "ocr-first" if likely_scanned_pdf else "text-first"

    return {
        "pdf_path": str(pdf_path),
        "probed_pages": probed_pages,
        "text_threshold": text_threshold,
        "ocr_threshold": ocr_threshold,
        "dpi": dpi,
        "likely_scanned_pdf": likely_scanned_pdf,
        "recommended_pipeline": recommended_pipeline,
        "page_summaries": page_summaries,
    }


def main() -> int:
    args = build_parser().parse_args()
    render_dir = Path(args.render_dir).expanduser().resolve() if args.render_dir else None
    payload = probe_pdf(
        pdf_path=Path(args.pdf_path),
        max_pages=args.max_pages,
        dpi=args.dpi,
        text_threshold=args.text_threshold,
        ocr_threshold=args.ocr_threshold,
        ocr_all=args.ocr_all,
        render_dir=render_dir,
    )
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
