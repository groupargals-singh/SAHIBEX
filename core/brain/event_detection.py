from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class EventCandidate:
    event_type: str
    source_input_id: str
    confidence: float
    event_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        if not isinstance(self.event_type, str):
            raise TypeError("event_type must be a string.")

        if not self.event_type.strip():
            raise ValueError(
                "event_type must be non-empty."
            )

        if not isinstance(self.source_input_id, str):
            raise TypeError(
                "source_input_id must be a string."
            )

        if not self.source_input_id.strip():
            raise ValueError(
                "source_input_id must be non-empty."
            )

        if not isinstance(self.confidence, (int, float)):
            raise TypeError(
                "confidence must be numeric."
            )

        if isinstance(self.confidence, bool):
            raise TypeError(
                "confidence must be numeric."
            )

        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1."
            )

        if not isinstance(self.event_id, str):
            raise TypeError("event_id must be a string.")

        if not self.event_id.strip():
            raise ValueError(
                "event_id must be non-empty."
            )


@dataclass(frozen=True)
class EventDetectionResult:
    input_id: str
    events: tuple[EventCandidate, ...]
    detection_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        if not isinstance(self.input_id, str):
            raise TypeError("input_id must be a string.")

        if not self.input_id.strip():
            raise ValueError(
                "input_id must be non-empty."
            )

        if not isinstance(self.events, tuple):
            raise TypeError(
                "events must be a tuple."
            )

        for event in self.events:
            if not isinstance(event, EventCandidate):
                raise TypeError(
                    "all events must be EventCandidate."
                )

        if not isinstance(self.detection_id, str):
            raise TypeError(
                "detection_id must be a string."
            )

        if not self.detection_id.strip():
            raise ValueError(
                "detection_id must be non-empty."
            )


class EventDetectionEngine:
    """
    Deterministic event detection over PerceptionResult.events.

    This layer:
    - detects event candidates
    - preserves the perception event vocabulary
    - removes duplicate event types
    - does not verify that events are true
    - does not execute actions
    - does not grant authority
    - does not persist events
    """

    EVENT_CONFIDENCE = 0.80

    def detect(
        self,
        *,
        input_id: str,
        events: tuple[str, ...],
    ) -> EventDetectionResult:
        if not isinstance(input_id, str):
            raise TypeError(
                "input_id must be a string."
            )

        normalized_input_id = input_id.strip()

        if not normalized_input_id:
            raise ValueError(
                "input_id must be non-empty."
            )

        if not isinstance(events, tuple):
            raise TypeError(
                "events must be a tuple."
            )

        detected: list[EventCandidate] = []
        seen: set[str] = set()

        for event in events:
            if not isinstance(event, str):
                raise TypeError(
                    "each event must be a string."
                )

            normalized_event = event.strip().lower()

            if not normalized_event:
                continue

            if normalized_event in seen:
                continue

            seen.add(normalized_event)

            detected.append(
                EventCandidate(
                    event_type=normalized_event,
                    source_input_id=normalized_input_id,
                    confidence=self.EVENT_CONFIDENCE,
                )
            )

        return EventDetectionResult(
            input_id=normalized_input_id,
            events=tuple(detected),
        )

    def detect_from_perception(
        self,
        perception,
    ) -> EventDetectionResult:
        """
        Consume the existing PerceptionResult contract.

        The method intentionally reads only the perception
        event output and does not modify the perception object.
        """
        from core.brain.perception import PerceptionResult

        if not isinstance(perception, PerceptionResult):
            raise TypeError(
                "perception must be a PerceptionResult."
            )

        return self.detect(
            input_id=perception.input_id,
            events=perception.events,
        )

    @staticmethod
    def is_read_only() -> bool:
        return True

    @staticmethod
    def grants_permission() -> bool:
        return False

    @staticmethod
    def executes_actions() -> bool:
        return False

    @staticmethod
    def verifies_truth() -> bool:
        return False

    @staticmethod
    def persists_events() -> bool:
        return False
