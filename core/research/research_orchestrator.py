from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.research.job import ResearchJob, ResearchJobStatus
from core.research.research_execution import (
    ResearchExecutionResult,
)
from core.research.research_execution_manager import (
    ResearchExecutionManager,
)
from core.research.research_plan import ResearchPlan


@dataclass(frozen=True)
class ResearchOrchestrationResult:
    """
    Final result returned by the research orchestration layer.
    """

    job_id: str
    plan_id: str
    execution_id: str
    status: str
    job_status: str
    plan: ResearchPlan
    execution: ResearchExecutionResult

    @property
    def completed(self) -> bool:
        return (
            self.status == "completed"
            and self.job_status == ResearchJobStatus.COMPLETED
        )

    @property
    def failed(self) -> bool:
        return (
            self.status == "failed"
            or self.job_status == ResearchJobStatus.FAILED
        )


class ResearchOrchestrator:
    """
    Top-level controller for one controlled research run.

    The orchestrator coordinates lifecycle only.
    It does not implement acquisition, extraction,
    verification, or answer synthesis itself.
    """

    orchestrator_name = "default_research_orchestrator"

    def __init__(
        self,
        execution_manager: Optional[
            ResearchExecutionManager
        ] = None,
    ) -> None:
        self.execution_manager = (
            execution_manager
            if execution_manager is not None
            else ResearchExecutionManager()
        )

    def create_job(
        self,
        job_id: str,
        query: str,
    ) -> ResearchJob:
        return self.execution_manager.create_job(
            job_id=job_id,
            query=query,
        )

    def create_plan(
        self,
        job_id: str,
    ) -> ResearchPlan:
        return self.execution_manager.create_plan(job_id)

    def start_job(
        self,
        job_id: str,
    ) -> ResearchJob:
        return self.execution_manager.start_job(job_id)

    def run(
        self,
        job_id: str,
        execution_id: str,
    ) -> ResearchOrchestrationResult:
        if (
            not isinstance(job_id, str)
            or not job_id.strip()
        ):
            raise ValueError(
                "job_id must be a non-empty string"
            )

        if (
            not isinstance(execution_id, str)
            or not execution_id.strip()
        ):
            raise ValueError(
                "execution_id must be a non-empty string"
            )

        job = self.execution_manager.get_job(job_id)

        if job.status == ResearchJobStatus.CREATED:
            plan = self.execution_manager.create_plan(job_id)
            job = self.execution_manager.get_job(job_id)

        elif job.status == ResearchJobStatus.PLANNED:
            plan = self.execution_manager.get_plan(
                f"plan-{job_id}"
            )

        else:
            raise RuntimeError(
                "research job must be created or planned "
                "before orchestration run"
            )

        if job.status != ResearchJobStatus.PLANNED:
            raise RuntimeError(
                "research job must be planned before execution"
            )

        self.execution_manager.start_job(job_id)

        execution = self.execution_manager.execute(
            execution_id=execution_id,
            job_id=job_id,
        )

        final_job = self.execution_manager.get_job(job_id)

        return ResearchOrchestrationResult(
            job_id=job_id,
            plan_id=plan.plan_id,
            execution_id=execution_id,
            status=execution.status,
            job_status=final_job.status,
            plan=plan,
            execution=execution,
        )

    def status(
        self,
        job_id: str,
    ) -> str:
        return self.execution_manager.status(job_id)

    def get_execution(
        self,
        execution_id: str,
    ) -> ResearchExecutionResult:
        return self.execution_manager.get_execution(
            execution_id
        )
