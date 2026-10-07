from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4


MEMORY_PROVENANCE_VERSION = "P2-MP-1"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class MemoryProvenance:
    """
    Immutable provenance record for a SAHIBEX memory.

    Provenance describes where a memory came from and how it
    entered the memory system. It does not establish truth,
    grant authority, or permit actions.
    """

    memory_id: str
    source_type: str
    source_id: str
    origin: str
    captured_at: datetime
    recorded_at: datetime = field(default_factory=utc_now)

    evidence_id: str = ""
    parent_memory_id: str = ""
    transformation: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    provenance_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        for name in (
            "memory_id",
            "source_type",
            "source_id",
            "origin",
            "evidence_id",
            "parent_memory_id",
            "transformation",
            "provenance_id",
        ):
            value = getattr(self, name)

            if not isinstance(value, str):
                raise TypeError(f"{name} must be str.")

            if name in (
                "memory_id",
                "source_type",
                "source_id",
                "origin",
                "provenance_id",
            ) and not value.strip():
                raise ValueError(
                    f"{name} must not be empty."
                )

        if not isinstance(self.captured_at, datetime):
            raise TypeError(
                "captured_at must be datetime."
            )

        if not isinstance(self.recorded_at, datetime):
            raise TypeError(
                "recorded_at must be datetime."
            )

        if not isinstance(self.metadata, dict):
            raise TypeError(
                "metadata must be a dictionary."
            )


@dataclass(frozen=True)
class MemoryProvenanceResult:
    provenance_id: str
    memory_id: str
    valid: bool
    completeness_score: float
    reason: str

    result_id: str = field(
        default_factory=lambda: str(uuid4())
    )


class MemoryProvenanceEngine:
    """
    Canonical SAHIBEX Memory Provenance Engine.

    Responsibilities:
    - create immutable provenance records
    - validate provenance completeness
    - assess provenance metadata quality

    This engine does NOT:
    - verify truth
    - modify memories
    - delete memories
    - resolve conflicts
    - execute actions
    - grant permissions
    - access credentials
    - modify the Constitution
    """

    VERSION = MEMORY_PROVENANCE_VERSION

    def create(
        self,
        *,
        memory_id: str,
        source_type: str,
        source_id: str,
        origin: str,
        captured_at: datetime,
        evidence_id: str = "",
        parent_memory_id: str = "",
        transformation: str = "",
        metadata: Dict[str, Any] | None = None,
    ) -> MemoryProvenance:
        return MemoryProvenance(
            memory_id=memory_id,
            source_type=source_type,
            source_id=source_id,
            origin=origin,
            captured_at=captured_at,
            evidence_id=evidence_id,
            parent_memory_id=parent_memory_id,
            transformation=transformation,
            metadata={} if metadata is None else dict(metadata),
        )

    def validate(
        self,
        provenance: MemoryProvenance,
    ) -> MemoryProvenanceResult:
        if not isinstance(
            provenance,
            MemoryProvenance,
        ):
            raise TypeError(
                "provenance must be MemoryProvenance."
            )

        checks = (
            bool(provenance.memory_id.strip()),
            bool(provenance.source_type.strip()),
            bool(provenance.source_id.strip()),
            bool(provenance.origin.strip()),
            isinstance(
                provenance.captured_at,
                datetime,
            ),
            isinstance(
                provenance.recorded_at,
                datetime,
            ),
        )

        score = round(
            sum(1 for check in checks if check)
            / len(checks),
            6,
        )

        valid = all(checks)

        if valid:
            reason = (
                "Memory provenance contains all required "
                "identity, source, origin, and timestamp fields."
            )
        else:
            reason = (
                "Memory provenance is incomplete and "
                "should not be treated as fully traceable."
            )

        return MemoryProvenanceResult(
            provenance_id=provenance.provenance_id,
            memory_id=provenance.memory_id,
            valid=valid,
            completeness_score=score,
            reason=reason,
        )
