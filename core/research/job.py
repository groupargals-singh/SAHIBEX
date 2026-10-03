from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional


class ResearchJobStatus:
    CREATED = "created"
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


_VALID_STATUSES = {
    ResearchJobStatus.CREATED,
    ResearchJobStatus.PLANNED,
    ResearchJobStatus.RUNNING,
    ResearchJobStatus.COMPLETED,
    ResearchJobStatus.FAILED,
    ResearchJobStatus.CANCELLED,
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ResearchJob:
    """
    Controlled lifecycle contract for a SAHIBEX research job.

    A ResearchJob represents one user-requested research task.

    Lifecycle:

        CREATED
           ↓
        PLANNED
           ↓
        RUNNING
           ↓
        COMPLETED

    Failure/cancellation may occur from an active state.
    """

    job_id: str
    query: str
    status: str = ResearchJobStatus.CREATED
    created_at: datetime = field(default_factory=_utc_now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.job_id, str) or not self.job_id.strip():
            raise ValueError("job_id must be a non-empty string")

        if not isinstance(self.query, str) or not self.query.strip():
            raise ValueError("query must be a non-empty string")

        if self.status not in _VALID_STATUSES:
            raise ValueError(
                f"invalid research job status: {self.status}"
            )

        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")

        if self.error is not None and not isinstance(self.error, str):
            raise ValueError("error must be a string or None")

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            ResearchJobStatus.COMPLETED,
            ResearchJobStatus.FAILED,
            ResearchJobStatus.CANCELLED,
        }

    def plan(self) -> None:
        if self.status != ResearchJobStatus.CREATED:
            raise RuntimeError(
                f"cannot plan research job from status: {self.status}"
            )

        self.status = ResearchJobStatus.PLANNED

    def start(self) -> None:
        if self.status != ResearchJobStatus.PLANNED:
            raise RuntimeError(
                f"cannot start research job from status: {self.status}"
            )

        self.status = ResearchJobStatus.RUNNING
        self.started_at = _utc_now()
        self.error = None

    def complete(self) -> None:
        if self.status != ResearchJobStatus.RUNNING:
            raise RuntimeError(
                f"cannot complete research job from status: {self.status}"
            )

        self.status = ResearchJobStatus.COMPLETED
        self.completed_at = _utc_now()
        self.error = None

    def fail(self, error: str) -> None:
        if self.status not in {
            ResearchJobStatus.PLANNED,
            ResearchJobStatus.RUNNING,
        }:
            raise RuntimeError(
                f"cannot fail research job from status: {self.status}"
            )

        if not isinstance(error, str) or not error.strip():
            raise ValueError("error must be a non-empty string")

        self.status = ResearchJobStatus.FAILED
        self.completed_at = _utc_now()
        self.error = error

    def cancel(self) -> None:
        if self.status not in {
            ResearchJobStatus.CREATED,
            ResearchJobStatus.PLANNED,
            ResearchJobStatus.RUNNING,
        }:
            raise RuntimeError(
                f"cannot cancel research job from status: {self.status}"
            )

        self.status = ResearchJobStatus.CANCELLED
        self.completed_at = _utc_now()

    def snapshot(self) -> Dict[str, object]:
        return {
            "job_id": self.job_id,
            "query": self.query,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "started_at": (
                self.started_at.isoformat()
                if self.started_at is not None
                else None
            ),
            "completed_at": (
                self.completed_at.isoformat()
                if self.completed_at is not None
                else None
            ),
            "error": self.error,
            "metadata": dict(self.metadata),
        }
