from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

_loguru_logger: Any | None = None
try:
    from loguru import logger as _loguru_logger
except Exception:  # pragma: no cover - fallback path
    pass


logger: Any
if _loguru_logger is not None:
    logger = _loguru_logger
else:  # pragma: no cover - fallback path
    logger = logging.getLogger("emotionquant")


def configure_logger(log_file: Path, level: str = "INFO") -> None:
    if _loguru_logger is not None:
        _loguru_logger.remove()
        _loguru_logger.add(log_file, level=level, rotation="10 MB", encoding="utf-8")
        _loguru_logger.add(lambda msg: print(msg, end=""), level=level)
        return

    # stdlib fallback
    logger.setLevel(level.upper())
    logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
