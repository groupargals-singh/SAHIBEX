from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from core.research.knowledge_registry import Entity


@dataclass(frozen=True)
class EntityCandidate:
    """
    Entity candidate identified from input.

    This is an identification result, not a verified fact.
    """

    entity: Entity
    confidence: float
    source_input_id: str
    candidate_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        if not isinstance(self.entity, Entity):
            raise TypeError("entity must be an Entity.")

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

        if not isinstance(self.source_input_id, str):
            raise TypeError(
                "source_input_id must be a string."
            )

        if not self.source_input_id.strip():
            raise ValueError(
                "source_input_id must be non-empty."
            )

        if not isinstance(self.candidate_id, str):
            raise TypeError(
                "candidate_id must be a string."
            )

        if not self.candidate_id.strip():
            raise ValueError(
                "candidate_id must be non-empty."
            )


@dataclass(frozen=True)
class EntityIdentificationResult:
    input_id: str
    candidates: tuple[EntityCandidate, ...]
    identification_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        if not isinstance(self.input_id, str):
            raise TypeError("input_id must be a string.")

        if not self.input_id.strip():
            raise ValueError(
                "input_id must be non-empty."
            )

        if not isinstance(self.candidates, tuple):
            raise TypeError(
                "candidates must be a tuple."
            )

        for candidate in self.candidates:
            if not isinstance(candidate, EntityCandidate):
                raise TypeError(
                    "all candidates must be EntityCandidate."
                )

        if not isinstance(self.identification_id, str):
            raise TypeError(
                "identification_id must be a string."
            )

        if not self.identification_id.strip():
            raise ValueError(
                "identification_id must be non-empty."
            )


class EntityIdentificationEngine:
    """
    Deterministic first-stage entity identification.

    This layer:
    - identifies candidate entities
    - reuses the existing Entity model
    - does not persist entities
    - does not verify identity
    - does not grant authority
    - does not execute actions
    """

    KNOWN_ENTITY_PATTERNS = {
        "sahibex": "system",
        "python": "technology",
        "github": "service",
        "termux": "software",
        "android": "platform",
        "india": "country",
        "ai": "technology",
    }

    def identify(
        self,
        *,
        input_id: str,
        content: str,
    ) -> EntityIdentificationResult:
        if not isinstance(input_id, str):
            raise TypeError(
                "input_id must be a string."
            )

        normalized_input_id = input_id.strip()

        if not normalized_input_id:
            raise ValueError(
                "input_id must be non-empty."
            )

        if not isinstance(content, str):
            raise TypeError(
                "content must be a string."
            )

        normalized_content = " ".join(
            content.strip().split()
        )

        if not normalized_content:
            raise ValueError(
                "content must be non-empty."
            )

        tokens = self._tokens(normalized_content)

        candidates: list[EntityCandidate] = []
        seen: set[str] = set()

        for token in tokens:
            normalized_token = token.lower()

            entity_type = self.KNOWN_ENTITY_PATTERNS.get(
                normalized_token
            )

            if entity_type is None:
                continue

            entity_id = (
                f"candidate-{entity_type}-"
                f"{normalized_token}"
            )

            if entity_id in seen:
                continue

            seen.add(entity_id)

            entity = Entity(
                entity_id=entity_id,
                name=normalized_token,
                entity_type=entity_type,
            )

            candidates.append(
                EntityCandidate(
                    entity=entity,
                    confidence=0.80,
                    source_input_id=normalized_input_id,
                )
            )

        return EntityIdentificationResult(
            input_id=normalized_input_id,
            candidates=tuple(candidates),
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
            .replace("(", " ")
            .replace(")", " ")
        )

        return tuple(
            token
            for token in cleaned.split()
            if token
        )

    @staticmethod
    def is_persistent() -> bool:
        return False

    @staticmethod
    def verifies_identity() -> bool:
        return False

    @staticmethod
    def grants_permission() -> bool:
        return False

    @staticmethod
    def executes_actions() -> bool:
        return False
