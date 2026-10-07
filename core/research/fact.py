from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Fact:
    """
    Stable atomic fact in the SAHIBEX knowledge graph.

    A Fact represents a normalized statement that can be connected
    to entities, concepts, other facts, evidence, and sources through
    the generic Relationship model.
    """

    fact_id: str
    subject_id: str
    subject_type: str
    predicate: str
    object_id: Optional[str] = None
    object_type: Optional[str] = None
    object_value: Optional[str] = None
    confidence: float = 0.0
    verified: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.fact_id.strip():
            raise ValueError("fact_id cannot be empty")

        if not self.subject_id.strip():
            raise ValueError("subject_id cannot be empty")

        if not self.subject_type.strip():
            raise ValueError("subject_type cannot be empty")

        if not self.predicate.strip():
            raise ValueError("predicate cannot be empty")

        if self.object_id is None and self.object_value is None:
            raise ValueError(
                "fact requires object_id or object_value"
            )

        if self.object_id is not None and not self.object_id.strip():
            raise ValueError("object_id cannot be empty")

        if self.object_type is not None and not self.object_type.strip():
            raise ValueError("object_type cannot be empty")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1"
            )

        if self.object_id is None and self.object_type is not None:
            raise ValueError(
                "object_type requires object_id"
            )
