from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class PerceptionResult:
    input_id: str
    content: str
    subjects: tuple[str, ...]
    actions: tuple[str, ...]
    objects: tuple[str, ...]
    events: tuple[str, ...]
    attributes: tuple[str, ...]
    perception_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        if not isinstance(self.input_id, str):
            raise TypeError("input_id must be a string.")
        if not self.input_id.strip():
            raise ValueError("input_id must be non-empty.")

        if not isinstance(self.content, str):
            raise TypeError("content must be a string.")
        if not self.content.strip():
            raise ValueError("content must be non-empty.")

        for name, value in (
            ("subjects", self.subjects),
            ("actions", self.actions),
            ("objects", self.objects),
            ("events", self.events),
            ("attributes", self.attributes),
        ):
            if not isinstance(value, tuple):
                raise TypeError(f"{name} must be a tuple.")

        if not isinstance(self.perception_id, str):
            raise TypeError("perception_id must be a string.")
        if not self.perception_id.strip():
            raise ValueError(
                "perception_id must be non-empty."
            )


class PerceptionParser:
    """
    Deterministic perception parser.

    Converts normalized textual input into structured
    perceptual signals.

    This layer does NOT:
    - decide what to do
    - grant authority
    - execute actions
    - verify truth
    - access external systems
    """

    ACTION_WORDS = frozenset(
        {
            "create",
            "make",
            "build",
            "write",
            "read",
            "search",
            "find",
            "check",
            "test",
            "run",
            "delete",
            "update",
            "open",
            "close",
            "install",
            "learn",
            "analyze",
            "compare",
            "repair",
        }
    )

    EVENT_WORDS = frozenset(
        {
            "happened",
            "started",
            "stopped",
            "failed",
            "completed",
            "changed",
            "updated",
            "created",
            "deleted",
            "detected",
            "received",
            "occurred",
        }
    )

    ATTRIBUTE_WORDS = frozenset(
        {
            "new",
            "old",
            "current",
            "latest",
            "important",
            "urgent",
            "critical",
            "broken",
            "working",
            "failed",
            "successful",
            "red",
            "green",
            "blue",
            "high",
            "low",
        }
    )

    def parse(
        self,
        *,
        input_id: str,
        content: str,
    ) -> PerceptionResult:
        if not isinstance(input_id, str):
            raise TypeError("input_id must be a string.")

        normalized_input_id = input_id.strip()

        if not normalized_input_id:
            raise ValueError(
                "input_id must be non-empty."
            )

        if not isinstance(content, str):
            raise TypeError("content must be a string.")

        normalized_content = " ".join(
            content.strip().split()
        )

        if not normalized_content:
            raise ValueError(
                "content must be non-empty."
            )

        tokens = self._tokens(normalized_content)

        actions = tuple(
            token
            for token in tokens
            if token in self.ACTION_WORDS
        )

        events = tuple(
            token
            for token in tokens
            if token in self.EVENT_WORDS
        )

        attributes = tuple(
            token
            for token in tokens
            if token in self.ATTRIBUTE_WORDS
        )

        objects = self._objects(
            tokens=tokens,
            actions=actions,
            events=events,
        )

        subjects = self._subjects(
            tokens=tokens,
            actions=actions,
            objects=objects,
        )

        return PerceptionResult(
            input_id=normalized_input_id,
            content=normalized_content,
            subjects=subjects,
            actions=actions,
            objects=objects,
            events=events,
            attributes=attributes,
        )

    @staticmethod
    def _tokens(content: str) -> tuple[str, ...]:
        cleaned = (
            content.lower()
            .replace(".", " ")
            .replace(",", " ")
            .replace("!", " ")
            .replace("?", " ")
            .replace(":", " ")
            .replace(";", " ")
        )

        return tuple(
            token
            for token in cleaned.split()
            if token
        )

    @staticmethod
    def _objects(
        *,
        tokens: tuple[str, ...],
        actions: tuple[str, ...],
        events: tuple[str, ...],
    ) -> tuple[str, ...]:
        excluded = set(actions) | set(events)

        return tuple(
            token
            for token in tokens
            if token not in excluded
            and len(token) > 2
        )

    @staticmethod
    def _subjects(
        *,
        tokens: tuple[str, ...],
        actions: tuple[str, ...],
        objects: tuple[str, ...],
    ) -> tuple[str, ...]:
        if not tokens:
            return ()

        first = tokens[0]

        if first in actions:
            return ()

        if first in objects:
            return (first,)

        return (first,)

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
