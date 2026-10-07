from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class ObjectTargetResult:
    input_id: str
    targets: tuple[str, ...]
    result_id: str = field(default_factory=lambda: str(uuid4()))


class ObjectTargetIdentificationEngine:
    """Read-only identification of likely object/target tokens."""

    def identify(self, *, input_id: str, content: str) -> ObjectTargetResult:
        if not isinstance(input_id, str) or not input_id.strip():
            raise ValueError("input_id must be non-empty.")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("content must be non-empty.")
        stop = {
            "the", "a", "an", "to", "for", "of", "and", "or", "is",
            "are", "please", "me", "my", "this", "that", "in", "on",
        }
        targets = []
        for token in content.lower().replace(",", " ").replace(".", " ").split():
            if len(token) > 2 and token not in stop and token not in targets:
                targets.append(token)
        return ObjectTargetResult(input_id=input_id.strip(), targets=tuple(targets))

    @staticmethod
    def is_read_only() -> bool:
        return True


@dataclass(frozen=True)
class TemporalUnderstandingResult:
    input_id: str
    temporal_markers: tuple[str, ...]
    result_id: str = field(default_factory=lambda: str(uuid4()))


class TemporalUnderstandingEngine:
    MARKERS = {
        "now", "today", "tomorrow", "yesterday", "before", "after",
        "later", "soon", "currently", "already", "next", "last",
        "morning", "evening", "night", "recently",
    }

    def understand(self, *, input_id: str, content: str) -> TemporalUnderstandingResult:
        if not isinstance(input_id, str) or not input_id.strip():
            raise ValueError("input_id must be non-empty.")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("content must be non-empty.")
        tokens = content.lower().replace(",", " ").replace(".", " ").split()
        markers = tuple(dict.fromkeys(t for t in tokens if t in self.MARKERS))
        return TemporalUnderstandingResult(input_id=input_id.strip(), temporal_markers=markers)

    @staticmethod
    def is_read_only() -> bool:
        return True


@dataclass(frozen=True)
class SpatialUnderstandingResult:
    input_id: str
    spatial_markers: tuple[str, ...]
    result_id: str = field(default_factory=lambda: str(uuid4()))


class SpatialUnderstandingEngine:
    MARKERS = {
        "here", "there", "near", "far", "left", "right", "above",
        "below", "inside", "outside", "front", "behind", "next",
        "between", "under", "over", "around",
    }

    def understand(self, *, input_id: str, content: str) -> SpatialUnderstandingResult:
        if not isinstance(input_id, str) or not input_id.strip():
            raise ValueError("input_id must be non-empty.")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("content must be non-empty.")
        tokens = content.lower().replace(",", " ").replace(".", " ").split()
        markers = tuple(dict.fromkeys(t for t in tokens if t in self.MARKERS))
        return SpatialUnderstandingResult(input_id=input_id.strip(), spatial_markers=markers)

    @staticmethod
    def is_read_only() -> bool:
        return True


@dataclass(frozen=True)
class PerceptionFusionResult:
    input_id: str
    signal_groups: tuple[tuple[str, ...], ...]
    merged_signals: tuple[str, ...]
    result_id: str = field(default_factory=lambda: str(uuid4()))


class PerceptionResultFusionEngine:
    """Merge already-produced perception signals without changing authority."""

    def fuse(self, *, input_id: str, signal_groups: list[tuple[str, ...]]) -> PerceptionFusionResult:
        if not isinstance(input_id, str) or not input_id.strip():
            raise ValueError("input_id must be non-empty.")
        if not isinstance(signal_groups, list) or not signal_groups:
            raise ValueError("signal_groups must contain at least one group.")
        normalized = []
        merged = []
        for group in signal_groups:
            if not isinstance(group, tuple):
                raise TypeError("each signal group must be a tuple.")
            clean = tuple(x.strip() for x in group if isinstance(x, str) and x.strip())
            normalized.append(clean)
            for item in clean:
                if item not in merged:
                    merged.append(item)
        return PerceptionFusionResult(
            input_id=input_id.strip(),
            signal_groups=tuple(normalized),
            merged_signals=tuple(merged),
        )

    @staticmethod
    def is_read_only() -> bool:
        return True
