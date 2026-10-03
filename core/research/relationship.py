from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class Relationship:
    """
    Directed semantic relationship between two knowledge-graph objects.

    This model is intentionally separate from the existing research
    traceability linkage:

        Knowledge -> Evidence -> Source

    A Relationship represents:

        source -> relationship_type -> target
    """

    relationship_id: str
    source_id: str
    source_type: str
    relationship_type: str
    target_id: str
    target_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.relationship_id.strip():
            raise ValueError(
                "relationship_id cannot be empty"
            )

        if not self.source_id.strip():
            raise ValueError(
                "source_id cannot be empty"
            )

        if not self.source_type.strip():
            raise ValueError(
                "source_type cannot be empty"
            )

        if not self.relationship_type.strip():
            raise ValueError(
                "relationship_type cannot be empty"
            )

        if not self.target_id.strip():
            raise ValueError(
                "target_id cannot be empty"
            )

        if not self.target_type.strip():
            raise ValueError(
                "target_type cannot be empty"
            )
