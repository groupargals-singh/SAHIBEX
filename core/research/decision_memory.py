from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


DECISION_MEMORY_VERSION = "P2-DM-1"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class DecisionMemory:
    """
    Structured memory of a past decision.

    Stores:
    - decision context
    - available options
    - selected option
    - decision basis
    - expected outcome
    - actual outcome
    - lesson

    Informational only:
    no execution, permission, or constitutional authority.
    """

    decision_id: str
    decision: str
    context: str
    options: List[str]
    selected_option: str
    decision_basis: str
    expected_outcome: str
    actual_outcome: str
    lesson: str
    source: str
    confidence: float = 0.5
    importance: float = 0.5
    success_score: float = 0.5
    provenance: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    decided_at: datetime = field(default_factory=utc_now)
    recorded_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        for field_name in (
            "decision_id",
            "decision",
            "context",
            "selected_option",
            "decision_basis",
            "expected_outcome",
            "actual_outcome",
            "lesson",
            "source",
        ):
            value = getattr(self, field_name)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be non-empty")

        if not isinstance(self.options, list) or not self.options:
            raise ValueError("options must be a non-empty list")

        if any(
            not isinstance(option, str) or not option.strip()
            for option in self.options
        ):
            raise ValueError("every option must be a non-empty string")

        if self.selected_option not in self.options:
            raise ValueError("selected_option must exist in options")

        for field_name in (
            "confidence",
            "importance",
            "success_score",
        ):
            value = getattr(self, field_name)

            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0 and 1")

        if not isinstance(self.provenance, dict):
            raise TypeError("provenance must be a dictionary")

        if not isinstance(self.tags, list):
            raise TypeError("tags must be a list")


class DecisionMemoryStore:
    """
    Bounded in-process decision memory.

    Stores and retrieves past decisions.
    It does not make or execute decisions.
    """

    def __init__(self, capacity: int = 256) -> None:
        if not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("capacity must be a positive integer")

        self._capacity = capacity
        self._decisions: Dict[str, DecisionMemory] = {}

    @staticmethod
    def _score(decision: DecisionMemory) -> float:
        return (
            decision.success_score * 0.40
            + decision.importance * 0.30
            + decision.confidence * 0.30
        )

    def store(self, decision: DecisionMemory) -> DecisionMemory:
        if not isinstance(decision, DecisionMemory):
            raise TypeError("decision must be a DecisionMemory")

        if decision.decision_id in self._decisions:
            raise ValueError(
                f"decision memory already exists: {decision.decision_id}"
            )

        self._decisions[decision.decision_id] = decision

        if len(self._decisions) > self._capacity:
            oldest = min(
                self._decisions.values(),
                key=lambda item: (
                    item.decided_at,
                    item.recorded_at,
                    item.decision_id,
                ),
            )

            del self._decisions[oldest.decision_id]

        return decision

    def get(self, decision_id: str) -> Optional[DecisionMemory]:
        return self._decisions.get(decision_id)

    def contains(self, decision_id: str) -> bool:
        return decision_id in self._decisions

    def by_success(
        self,
        minimum: float = 0.0,
    ) -> Tuple[DecisionMemory, ...]:
        if not 0.0 <= minimum <= 1.0:
            raise ValueError("minimum must be between 0 and 1")

        matches = [
            decision
            for decision in self._decisions.values()
            if decision.success_score >= minimum
        ]

        return tuple(
            sorted(
                matches,
                key=lambda item: (
                    item.success_score,
                    item.importance,
                    item.confidence,
                    item.decided_at,
                ),
                reverse=True,
            )
        )

    def by_tag(self, tag: str) -> Tuple[DecisionMemory, ...]:
        if not isinstance(tag, str):
            raise TypeError("tag must be a string")

        target = tag.strip().lower()

        matches = [
            decision
            for decision in self._decisions.values()
            if any(
                existing.strip().lower() == target
                for existing in decision.tags
            )
        ]

        return tuple(
            sorted(
                matches,
                key=lambda item: (
                    self._score(item),
                    item.decided_at,
                ),
                reverse=True,
            )
        )

    def search(self, text: str) -> Tuple[DecisionMemory, ...]:
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        query = text.strip().lower()

        if not query:
            return tuple()

        matches = [
            decision
            for decision in self._decisions.values()
            if (
                query in decision.decision.lower()
                or query in decision.context.lower()
                or query in decision.selected_option.lower()
                or query in decision.decision_basis.lower()
                or query in decision.expected_outcome.lower()
                or query in decision.actual_outcome.lower()
                or query in decision.lesson.lower()
                or any(query in option.lower() for option in decision.options)
                or any(query in tag.lower() for tag in decision.tags)
            )
        ]

        return tuple(
            sorted(
                matches,
                key=lambda item: (
                    self._score(item),
                    item.decided_at,
                ),
                reverse=True,
            )
        )

    def lessons(self) -> Tuple[str, ...]:
        ordered = sorted(
            self._decisions.values(),
            key=lambda item: (
                self._score(item),
                item.decided_at,
            ),
            reverse=True,
        )

        return tuple(item.lesson for item in ordered)

    def selected_options(self) -> Tuple[str, ...]:
        ordered = sorted(
            self._decisions.values(),
            key=lambda item: (
                self._score(item),
                item.decided_at,
            ),
            reverse=True,
        )

        return tuple(item.selected_option for item in ordered)

    def recent(self, limit: int = 10) -> Tuple[DecisionMemory, ...]:
        if not isinstance(limit, int) or limit < 0:
            raise ValueError("limit must be a non-negative integer")

        ordered = sorted(
            self._decisions.values(),
            key=lambda item: (
                item.decided_at,
                item.recorded_at,
            ),
            reverse=True,
        )

        return tuple(ordered[:limit])

    def all(self) -> Tuple[DecisionMemory, ...]:
        return tuple(
            sorted(
                self._decisions.values(),
                key=lambda item: (
                    self._score(item),
                    item.decided_at,
                ),
                reverse=True,
            )
        )

    def count(self) -> int:
        return len(self._decisions)

    def remove(self, decision_id: str) -> Optional[DecisionMemory]:
        return self._decisions.pop(decision_id, None)

    def clear(self) -> None:
        self._decisions.clear()

    def summary(self) -> Dict[str, Any]:
        return {
            "version": DECISION_MEMORY_VERSION,
            "capacity": self._capacity,
            "decision_count": len(self._decisions),
            "immutable_decision_objects": True,
            "preserves_options": True,
            "preserves_selected_option": True,
            "preserves_decision_basis": True,
            "preserves_expected_outcome": True,
            "preserves_actual_outcome": True,
            "preserves_lesson": True,
            "preserves_provenance": True,
            "supports_success_retrieval": True,
            "supports_decision_search": True,
            "supports_lesson_retrieval": True,
            "supports_selected_option_retrieval": True,
            "execution_authority": False,
            "grants_permission": False,
            "executes_actions": False,
            "modifies_constitution": False,
        }
