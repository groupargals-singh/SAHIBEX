from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class ContextExtractionResult:
    """
    Structured current context extracted from existing perception signals.

    This layer is read-only. It does not execute actions, grant authority,
    modify memory, or verify truth.
    """

    input_id: str
    content: str
    source_id: str
    timestamp: str
    subjects: tuple[str, ...] = ()
    actions: tuple[str, ...] = ()
    objects: tuple[str, ...] = ()
    events: tuple[str, ...] = ()
    attributes: tuple[str, ...] = ()
    entity_ids: tuple[str, ...] = ()
    event_ids: tuple[str, ...] = ()
    context_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.input_id, str) or not self.input_id.strip():
            raise ValueError("input_id must be a non-empty string.")

        if not isinstance(self.content, str) or not self.content.strip():
            raise ValueError("content must be a non-empty string.")

        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("source_id must be a non-empty string.")

        if not isinstance(self.timestamp, str) or not self.timestamp.strip():
            raise ValueError("timestamp must be a non-empty string.")

        if not isinstance(self.context_id, str) or not self.context_id.strip():
            raise ValueError("context_id must be a non-empty string.")

        for name, value in (
            ("subjects", self.subjects),
            ("actions", self.actions),
            ("objects", self.objects),
            ("events", self.events),
            ("attributes", self.attributes),
            ("entity_ids", self.entity_ids),
            ("event_ids", self.event_ids),
        ):
            if not isinstance(value, tuple):
                raise TypeError(f"{name} must be a tuple.")

            for item in value:
                if not isinstance(item, str):
                    raise TypeError(f"every item in {name} must be a string.")
                if not item.strip():
                    raise ValueError(
                        f"items in {name} must be non-empty strings."
                    )

    @property
    def has_event(self) -> bool:
        return bool(self.events)

    @property
    def has_entities(self) -> bool:
        return bool(self.entity_ids)

    @property
    def signal_count(self) -> int:
        return (
            len(self.subjects)
            + len(self.actions)
            + len(self.objects)
            + len(self.events)
            + len(self.attributes)
            + len(self.entity_ids)
            + len(self.event_ids)
        )

    def summary(self) -> dict[str, object]:
        return {
            "context_id": self.context_id,
            "input_id": self.input_id,
            "source_id": self.source_id,
            "timestamp": self.timestamp,
            "subjects": self.subjects,
            "actions": self.actions,
            "objects": self.objects,
            "events": self.events,
            "attributes": self.attributes,
            "entity_ids": self.entity_ids,
            "event_ids": self.event_ids,
            "signal_count": self.signal_count,
        }


class ContextExtractionEngine:
    """
    Extracts a structured current context from already-identified signals.

    This engine does not:
    - execute actions
    - grant permissions
    - modify memory
    - modify knowledge
    - access credentials
    - verify truth
    """

    @staticmethod
    def _clean_items(items: object) -> tuple[str, ...]:
        if items is None:
            return ()

        if not isinstance(items, (list, tuple)):
            raise TypeError("signal collections must be lists or tuples.")

        result: list[str] = []

        for item in items:
            if not isinstance(item, str):
                raise TypeError("context signal items must be strings.")

            cleaned = item.strip()

            if cleaned and cleaned not in result:
                result.append(cleaned)

        return tuple(result)

    @staticmethod
    def _extract_ids(items: object) -> tuple[str, ...]:
        if items is None:
            return ()

        if not isinstance(items, (list, tuple)):
            raise TypeError("ID collections must be lists or tuples.")

        result: list[str] = []

        for item in items:
            value = getattr(item, "entity", None)

            if value is not None:
                entity_id = getattr(value, "entity_id", None)

                if isinstance(entity_id, str) and entity_id.strip():
                    if entity_id not in result:
                        result.append(entity_id)
                    continue

            event_id = getattr(item, "event_id", None)

            if isinstance(event_id, str) and event_id.strip():
                if event_id not in result:
                    result.append(event_id)
                continue

            if isinstance(item, str) and item.strip():
                if item not in result:
                    result.append(item)

        return tuple(result)

    def extract(
        self,
        *,
        input_id: str,
        content: str,
        source_id: str,
        timestamp: str,
        subjects: object = (),
        actions: object = (),
        objects: object = (),
        events: object = (),
        attributes: object = (),
        entity_candidates: object = (),
        event_candidates: object = (),
    ) -> ContextExtractionResult:
        if not isinstance(input_id, str) or not input_id.strip():
            raise ValueError("input_id must be a non-empty string.")

        if not isinstance(content, str) or not content.strip():
            raise ValueError("content must be a non-empty string.")

        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("source_id must be a non-empty string.")

        if not isinstance(timestamp, str) or not timestamp.strip():
            raise ValueError("timestamp must be a non-empty string.")

        return ContextExtractionResult(
            input_id=input_id.strip(),
            content=content.strip(),
            source_id=source_id.strip(),
            timestamp=timestamp.strip(),
            subjects=self._clean_items(subjects),
            actions=self._clean_items(actions),
            objects=self._clean_items(objects),
            events=self._clean_items(events),
            attributes=self._clean_items(attributes),
            entity_ids=self._extract_ids(entity_candidates),
            event_ids=self._extract_ids(event_candidates),
        )

    @staticmethod
    def from_perception(
        perception: object,
        *,
        source_id: str,
        timestamp: str,
        entity_candidates: object = (),
        event_candidates: object = (),
    ) -> ContextExtractionResult:
        if perception is None:
            raise ValueError("perception must not be None.")

        input_id = getattr(perception, "input_id", None)
        content = getattr(perception, "content", None)

        if not isinstance(input_id, str) or not input_id.strip():
            raise ValueError("perception.input_id must be non-empty.")

        if not isinstance(content, str) or not content.strip():
            raise ValueError("perception.content must be non-empty.")

        engine = ContextExtractionEngine()

        return engine.extract(
            input_id=input_id,
            content=content,
            source_id=source_id,
            timestamp=timestamp,
            subjects=getattr(perception, "subjects", ()),
            actions=getattr(perception, "actions", ()),
            objects=getattr(perception, "objects", ()),
            events=getattr(perception, "events", ()),
            attributes=getattr(perception, "attributes", ()),
            entity_candidates=entity_candidates,
            event_candidates=event_candidates,
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
    def modifies_memory() -> bool:
        return False

    @staticmethod
    def modifies_knowledge() -> bool:
        return False

    @staticmethod
    def verifies_truth() -> bool:
        return False
