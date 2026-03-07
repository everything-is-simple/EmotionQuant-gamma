from __future__ import annotations

from src.config import Settings
from src.strategy.pas_bof import BofDetector
from src.strategy.pattern_base import PatternDetector

ALL_DETECTORS = {
    "bof": BofDetector,
    # v0.01 仅启用 bof，其他形态在后续版本接入。
    # "bpb": BpbDetector,
    # "tst": TstDetector,
    # "pb": PbDetector,
    # "cpb": CpbDetector,
}


def get_active_detectors(config: Settings) -> list[PatternDetector]:
    patterns = config.pas_pattern_list
    if patterns != ["bof"]:
        raise ValueError("v0.01 only supports PAS_PATTERNS=bof")

    detectors: list[PatternDetector] = []
    for name in patterns:
        detector_cls = ALL_DETECTORS.get(name)
        if detector_cls is None:
            continue
        detectors.append(detector_cls(config))
    return detectors
