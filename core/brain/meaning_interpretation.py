from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class MeaningInterpretationResult:
    """
    Semantic interpretation of an already extracted context.

    This layer explains what the available signals represent.
    It does not execute actions, grant authority, modify memory,
    or verify external truth.
    """

    input_id: str
    interpretation: str
    subject: str
    situation: str
    state: str
    relationships: tuple[str, ...] = ()
    context_signals: tuple[str, ...] = ()
    confidence: float = 0.0
    interpretation_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        if not isinstance(self.input_id, str) or not self.input_id.strip():
            raise ValueError("input_id must be a non-empty string.")

        if not isinstance(self.interpretation, str) or not self.interpretation.strip():
            raise ValueError("interpretation must be a non-empty string.")

        if not isinstance(self.subject, str) or not self.subject.strip():
            raise ValueError("subject must be a non-empty string.")

        if not isinstance(self.situation, str) or not self.situation.strip():
            raise ValueError("situation must be a non-empty string.")

        if not isinstance(self.state, str) or not self.state.strip():
            raise ValueError("state must be a non-empty string.")

        if not isinstance(self.interpretation_id, str):
            raise TypeError("interpretation_id must be a string.")

        if not self.interpretation_id.strip():
            raise ValueError("interpretation_id must be non-empty.")

        if isinstance(self.confidence, bool):
            raise TypeError("confidence must be numeric.")

        if not isinstance(self.confidence, (int, float)):
            raise TypeError("confidence must be numeric.")

        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1.")

        for name, values in (
            ("relationships", self.relationships),
            ("context_signals", self.context_signals),
        ):
            if not isinstance(values, tuple):
                raise TypeError(f"{name} must be a tuple.")

            for value in values:
                if not isinstance(value, str):
                    raise TypeError(
                        f"every item in {name} must be a string."
                    )

                if not value.strip():
                    raise ValueError(
                        f"items in {name} must be non-empty strings."
                    )

    def summary(self) -> dict[str, object]:
        return {
            "interpretation_id": self.interpretation_id,
            "input_id": self.input_id,
            "subject": self.subject,
            "situation": self.situation,
            "state": self.state,
            "relationships": self.relationships,
            "context_signals": self.context_signals,
            "confidence": float(self.confidence),
            "interpretation": self.interpretation,
        }


class MeaningInterpretationEngine:
    """
    Deterministic semantic interpretation engine.

    It converts context signals into a compact semantic description.

    It does not:
    - execute actions
    - grant permissions
    - modify memory
    - modify knowledge
    - access credentials
    - verify external truth
    """

    @staticmethod
    def _clean(values: object) -> tuple[str, ...]:
        if values is None:
            return ()

        if not isinstance(values, (list, tuple)):
            raise TypeError("values must be a list or tuple.")

        result: list[str] = []

        for value in values:
            if not isinstance(value, str):
                raise TypeError("meaning signals must be strings.")

            cleaned = value.strip()

            if cleaned and cleaned not in result:
                result.append(cleaned)

        return tuple(result)

    @staticmethod
    def _first(values: tuple[str, ...], default: str) -> str:
        return values[0] if values else default

    def interpret(
        self,
        *,
        input_id: str,
        content: str,
        subjects: object = (),
        actions: object = (),
        objects: object = (),
        events: object = (),
        attributes: object = (),
    ) -> MeaningInterpretationResult:
        if not isinstance(input_id, str) or not input_id.strip():
            raise ValueError("input_id must be a non-empty string.")

        if not isinstance(content, str) or not content.strip():
            raise ValueError("content must be a non-empty string.")

        subject_values = self._clean(subjects)
        action_values = self._clean(actions)
        object_values = self._clean(objects)
        event_values = self._clean(events)
        attribute_values = self._clean(attributes)

        subject = self._first(subject_values, "unknown subject")

        if event_values:
            situation = f"event: {', '.join(event_values)}"
        elif action_values:
            situation = f"action: {', '.join(action_values)}"
        else:
            situation = "general situation"

        if attribute_values:
            state = ", ".join(attribute_values)
        elif event_values:
            state = "event detected"
        elif action_values:
            state = "action identified"
        else:
            state = "state unknown"

        relationships: list[str] = []

        for action in action_values:
            for obj in object_values:
                relationships.append(f"{action} -> {obj}")

        context_signals = (
            subject_values
            + action_values
            + object_values
            + event_values
            + attribute_values
        )

        if not context_signals:
            confidence = 0.30
        elif len(context_signals) >= 5:
            confidence = 0.85
        elif len(context_signals) >= 3:
            confidence = 0.75
        else:
            confidence = 0.60

        interpretation = (
            f"{subject} is associated with {situation}; "
            f"current state: {state}."
        )

        return MeaningInterpretationResult(
            input_id=input_id.strip(),
            interpretation=interpretation,
            subject=subject,
            situation=situation,
            state=state,
            relationships=tuple(relationships),
            context_signals=context_signals,
            confidence=confidence,
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
