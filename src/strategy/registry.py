from __future__ import annotations

from src.config import Settings
from src.strategy.pas_bof import BofDetector
from src.strategy.pas_bpb import BpbDetector
from src.strategy.pas_cpb import CpbDetector
from src.strategy.pas_pb import PbDetector
from src.strategy.pas_tst import TstDetector
from src.strategy.pattern_base import PatternDetector

ALL_DETECTORS = {
    "bof": BofDetector,
    "bpb": BpbDetector,
    "pb": PbDetector,
    "tst": TstDetector,
    "cpb": CpbDetector,
}


def get_active_detectors(config: Settings) -> list[PatternDetector]:
    patterns = config.pas_effective_patterns
    unsupported = [name for name in patterns if name not in ALL_DETECTORS]
    if unsupported:
        raise ValueError(f"Unsupported PAS patterns: {', '.join(sorted(unsupported))}")
    if not config.pas_registry_enabled and len(patterns) > 1:
        raise ValueError("PAS_REGISTRY_ENABLED=False only supports a single active pattern")

    detectors: list[PatternDetector] = []
    for name in patterns:
        detector_cls = ALL_DETECTORS[name]
        detectors.append(detector_cls(config))
    return detectors
