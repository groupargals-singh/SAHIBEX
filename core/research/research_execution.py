from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class ResearchExecutionStatus:
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


_VALID_STATUSES = {
    ResearchExecutionStatus.CREATED,
    ResearchExecutionStatus.RUNNING,
    ResearchExecutionStatus.COMPLETED,
    ResearchExecutionStatus.FAILED,
    ResearchExecutionStatus.CANCELLED,
}


@dataclass(frozen=True)
class ResearchExecutionRequest:
    """
    Immutable request describing one controlled execution attempt.
    """

    execution_id: str
    job_id: str
    plan_id: str
    metadata: Dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if (
            not isinstance(self.execution_id, str)
            or not self.execution_id.strip()
        ):
            raise ValueError(
                "execution_id must be a non-empty string"
            )

        if not isinstance(self.job_id, str) or not self.job_id.strip():
            raise ValueError(
                "job_id must be a non-empty string"
            )

        if (
            not isinstance(self.plan_id, str)
            or not self.plan_id.strip()
        ):
            raise ValueError(
                "plan_id must be a non-empty string"
            )

        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")


@dataclass
class ResearchExecutionResult:
    """
    Mutable lifecycle/result record for one execution attempt.

    The executor implementation is intentionally separate from this
    contract. This object only records execution state and results.
    """

    execution_id: str
    job_id: str
    plan_id: str
    status: str = ResearchExecutionStatus.CREATED
    completed_steps: List[str] = field(default_factory=list)
    failed_step: Optional[str] = None
    error: Optional[str] = None
    output: Dict[str, object] = field(default_factory=dict)
    metadata: Dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if (
            not isinstance(self.execution_id, str)
            or not self.execution_id.strip()
        ):
            raise ValueError(
                "execution_id must be a non-empty string"
            )

        if not isinstance(self.job_id, str) or not self.job_id.strip():
            raise ValueError(
                "job_id must be a non-empty string"
            )

        if (
            not isinstance(self.plan_id, str)
            or not self.plan_id.strip()
        ):
            raise ValueError(
                "plan_id must be a non-empty string"
            )

        if self.status not in _VALID_STATUSES:
            raise ValueError(
                f"invalid execution status: {self.status}"
            )

        if not isinstance(self.completed_steps, list):
            raise ValueError(
                "completed_steps must be a list"
            )

        if not isinstance(self.output, dict):
            raise ValueError("output must be a dictionary")

        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")

        if self.failed_step is not None and not isinstance(
            self.failed_step,
            str,
        ):
            raise ValueError(
                "failed_step must be a string or None"
            )

        if self.error is not None and not isinstance(
            self.error,
            str,
        ):
            raise ValueError(
                "error must be a string or None"
            )

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            ResearchExecutionStatus.COMPLETED,
            ResearchExecutionStatus.FAILED,
            ResearchExecutionStatus.CANCELLED,
        }

    def start(self) -> None:
        if self.status != ResearchExecutionStatus.CREATED:
            raise RuntimeError(
                "execution can only start from created status"
            )

        self.status = ResearchExecutionStatus.RUNNING

    def record_step(self, step_id: str) -> None:
        if self.status != ResearchExecutionStatus.RUNNING:
            raise RuntimeError(
                "step can only be recorded while execution is running"
            )

        if not isinstance(step_id, str) or not step_id.strip():
            raise ValueError(
                "step_id must be a non-empty string"
            )

        if step_id in self.completed_steps:
            raise ValueError(
                f"step already recorded: {step_id}"
            )

        self.completed_steps.append(step_id)

    def complete(
        self,
        output: Optional[Dict[str, object]] = None,
    ) -> None:
        if self.status != ResearchExecutionStatus.RUNNING:
            raise RuntimeError(
                "execution can only complete from running status"
            )

        if output is not None and not isinstance(output, dict):
            raise ValueError(
                "output must be a dictionary or None"
            )

        self.status = ResearchExecutionStatus.COMPLETED

        if output is not None:
            self.output = dict(output)

        self.error = None
        self.failed_step = None

    def fail(
        self,
        error: str,
        failed_step: Optional[str] = None,
    ) -> None:
        if self.status != ResearchExecutionStatus.RUNNING:
            raise RuntimeError(
                "execution can only fail from running status"
            )

        if not isinstance(error, str) or not error.strip():
            raise ValueError(
                "error must be a non-empty string"
            )

        if failed_step is not None:
            if (
                not isinstance(failed_step, str)
                or not failed_step.strip()
            ):
                raise ValueError(
                    "failed_step must be a non-empty string"
                )

        self.status = ResearchExecutionStatus.FAILED
        self.error = error
        self.failed_step = failed_step

    def cancel(self) -> None:
        if self.status not in {
            ResearchExecutionStatus.CREATED,
            ResearchExecutionStatus.RUNNING,
        }:
            raise RuntimeError(
                "execution cannot be cancelled from "
                f"status: {self.status}"
            )

        self.status = ResearchExecutionStatus.CANCELLED

    def snapshot(self) -> Dict[str, object]:
        return {
            "execution_id": self.execution_id,
            "job_id": self.job_id,
            "plan_id": self.plan_id,
            "status": self.status,
            "completed_steps": list(self.completed_steps),
            "failed_step": self.failed_step,
            "error": self.error,
            "output": dict(self.output),
            "metadata": dict(self.metadata),
        }
