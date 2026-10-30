from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict


KNOWLEDGE_CONFLICT_VERSION = "6H-7"

CONFLICT_TYPE_EXPLICIT_NEGATION = "EXPLICIT_NEGATION"
CONFLICT_TYPE_LEXICAL_CONTRADICTION = "LEXICAL_CONTRADICTION"
CONFLICT_TYPE_NUMERIC_CONTRADICTION = "NUMERIC_CONTRADICTION"
CONFLICT_TYPE_UNKNOWN = "UNKNOWN"

RESOLUTION_RESOLVED = "RESOLVED"
RESOLUTION_UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class KnowledgeConflictRecord:
    """
    Durable knowledge-level conflict record.

    This record preserves the relationship between two conflicting
    knowledge candidates and the result of the existing 6G-5
    conflict analysis/resolution layer.

    This component does not:
    - delete knowledge
    - mutate knowledge
    - mutate evidence
    - mutate sources
    - decide truth independently
    """

    conflict_id: str

    first_knowledge_id: str
    second_knowledge_id: str

    conflict_type: str
    conflict_reason: str

    resolution_status: str
    selected_knowledge_id: str | None

    evidence_score_delta: float
    source_reliability_delta: float
    knowledge_confidence_delta: float

    resolution_reason: str

    created_at: datetime | None = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    version: str = KNOWLEDGE_CONFLICT_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.conflict_id, str):
            raise TypeError("conflict_id must be a string")

        if not self.conflict_id.strip():
            raise ValueError(
                "conflict_id cannot be empty"
            )

        if not isinstance(self.first_knowledge_id, str):
            raise TypeError(
                "first_knowledge_id must be a string"
            )

        if not isinstance(self.second_knowledge_id, str):
            raise TypeError(
                "second_knowledge_id must be a string"
            )

        if not self.first_knowledge_id.strip():
            raise ValueError(
                "first_knowledge_id cannot be empty"
            )

        if not self.second_knowledge_id.strip():
            raise ValueError(
                "second_knowledge_id cannot be empty"
            )

        if (
            self.first_knowledge_id
            == self.second_knowledge_id
        ):
            raise ValueError(
                "a knowledge item cannot conflict with itself"
            )

        if not isinstance(self.conflict_type, str):
            raise TypeError(
                "conflict_type must be a string"
            )

        valid_types = {
            CONFLICT_TYPE_EXPLICIT_NEGATION,
            CONFLICT_TYPE_LEXICAL_CONTRADICTION,
            CONFLICT_TYPE_NUMERIC_CONTRADICTION,
            CONFLICT_TYPE_UNKNOWN,
        }

        if self.conflict_type not in valid_types:
            raise ValueError(
                f"invalid conflict_type: "
                f"{self.conflict_type}"
            )

        if not isinstance(self.conflict_reason, str):
            raise TypeError(
                "conflict_reason must be a string"
            )

        if not self.conflict_reason.strip():
            raise ValueError(
                "conflict_reason cannot be empty"
            )

        if not isinstance(self.resolution_status, str):
            raise TypeError(
                "resolution_status must be a string"
            )

        valid_statuses = {
            RESOLUTION_RESOLVED,
            RESOLUTION_UNRESOLVED,
        }

        if self.resolution_status not in valid_statuses:
            raise ValueError(
                f"invalid resolution_status: "
                f"{self.resolution_status}"
            )

        if self.resolution_status == RESOLUTION_RESOLVED:
            if not self.selected_knowledge_id:
                raise ValueError(
                    "resolved conflict must have "
                    "selected_knowledge_id"
                )

            if self.selected_knowledge_id not in {
                self.first_knowledge_id,
                self.second_knowledge_id,
            }:
                raise ValueError(
                    "selected_knowledge_id must reference "
                    "one of the conflicting knowledge IDs"
                )

        if self.resolution_status == RESOLUTION_UNRESOLVED:
            if self.selected_knowledge_id is not None:
                raise ValueError(
                    "unresolved conflict cannot have "
                    "selected_knowledge_id"
                )

        for field_name, value in (
            (
                "evidence_score_delta",
                self.evidence_score_delta,
            ),
            (
                "source_reliability_delta",
                self.source_reliability_delta,
            ),
            (
                "knowledge_confidence_delta",
                self.knowledge_confidence_delta,
            ),
        ):
            try:
                numeric_value = float(value)
            except (TypeError, ValueError) as exc:
                raise TypeError(
                    f"{field_name} must be numeric"
                ) from exc

            if not -1.0 <= numeric_value <= 1.0:
                raise ValueError(
                    f"{field_name} must be between -1 and 1"
                )

        if not isinstance(self.resolution_reason, str):
            raise TypeError(
                "resolution_reason must be a string"
            )

        if not self.resolution_reason.strip():
            raise ValueError(
                "resolution_reason cannot be empty"
            )

        if self.created_at is not None:
            if not isinstance(self.created_at, datetime):
                raise TypeError(
                    "created_at must be a datetime or None"
                )

        if not isinstance(self.metadata, dict):
            raise TypeError(
                "metadata must be a dictionary"
            )

        if not isinstance(self.version, str):
            raise TypeError(
                "version must be a string"
            )

        if not self.version.strip():
            raise ValueError(
                "version cannot be empty"
            )


__all__ = (
    "KNOWLEDGE_CONFLICT_VERSION",
    "CONFLICT_TYPE_EXPLICIT_NEGATION",
    "CONFLICT_TYPE_LEXICAL_CONTRADICTION",
    "CONFLICT_TYPE_UNKNOWN",
    "RESOLUTION_RESOLVED",
    "RESOLUTION_UNRESOLVED",
    "KnowledgeConflictRecord",
)
