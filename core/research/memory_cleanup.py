from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


MEMORY_CLEANUP_VERSION = "P2-MCLEAN-1"


@dataclass(frozen=True)
class MemoryCleanupInput:
    memory_id: str
    importance: float = 0.5
    confidence: float = 0.5
    access_frequency: float = 0.5
    age_score: float = 0.5
    future_reuse: float = 0.5
    protected: bool = False
    input_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not isinstance(self.memory_id, str) or not self.memory_id.strip():
            raise ValueError("memory_id must not be empty.")

        for name in (
            "importance",
            "confidence",
            "access_frequency",
            "age_score",
            "future_reuse",
        ):
            value = getattr(self, name)
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1.")

        if not isinstance(self.protected, bool):
            raise TypeError("protected must be bool.")


@dataclass(frozen=True)
class MemoryCleanupResult:
    memory_id: str
    retention_score: float
    cleanup_candidate: bool
    protected: bool
    action: str
    reason: str
    input_id: str
    result_id: str = field(default_factory=lambda: str(uuid4()))


class MemoryCleanupEngine:
    """
    Proposal-only memory cleanup assessment.

    This component identifies memories that may be candidates
    for cleanup. It never deletes, mutates, or forgets memory.
    """

    VERSION = MEMORY_CLEANUP_VERSION

    def assess(
        self,
        cleanup_input: MemoryCleanupInput,
    ) -> MemoryCleanupResult:
        if not isinstance(cleanup_input, MemoryCleanupInput):
            raise TypeError(
                "cleanup_input must be MemoryCleanupInput."
            )

        retention_score = (
            cleanup_input.importance * 0.25
            + cleanup_input.confidence * 0.15
            + cleanup_input.access_frequency * 0.15
            + (1.0 - cleanup_input.age_score) * 0.20
            + cleanup_input.future_reuse * 0.25
        )

        retention_score = round(retention_score, 6)

        if cleanup_input.protected:
            return MemoryCleanupResult(
                memory_id=cleanup_input.memory_id,
                retention_score=retention_score,
                cleanup_candidate=False,
                protected=True,
                action="DENY_CLEANUP",
                reason="Protected memory cannot be selected for cleanup.",
                input_id=cleanup_input.input_id,
            )

        cleanup_candidate = retention_score < 0.35

        if cleanup_candidate:
            action = "PROPOSAL_ONLY"
            reason = (
                "Low-retention memory identified as a cleanup candidate; "
                "no deletion or mutation performed."
            )
        else:
            action = "RETAIN"
            reason = "Memory retention score does not justify cleanup."

        return MemoryCleanupResult(
            memory_id=cleanup_input.memory_id,
            retention_score=retention_score,
            cleanup_candidate=cleanup_candidate,
            protected=False,
            action=action,
            reason=reason,
            input_id=cleanup_input.input_id,
        )
