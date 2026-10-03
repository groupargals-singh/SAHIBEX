from __future__ import annotations

from typing import Optional

from core.research.job import ResearchJob, ResearchJobStatus
from core.research.research_execution import (
    ResearchExecutionRequest,
    ResearchExecutionResult,
)
from core.research.research_executor import ResearchExecutor
from core.research.research_job_manager import ResearchJobManager
from core.research.research_plan import ResearchPlan


class ResearchExecutionManager:
    """
    Coordinates the complete controlled research execution lifecycle.
    """

    manager_name = "default_research_execution_manager"

    def __init__(
        self,
        job_manager: Optional[ResearchJobManager] = None,
        executor: Optional[ResearchExecutor] = None,
    ) -> None:
        self.job_manager = (
            job_manager
            if job_manager is not None
            else ResearchJobManager()
        )

        self.executor = (
            executor
            if executor is not None
            else ResearchExecutor()
        )

        self._executions: dict[
            str,
            ResearchExecutionResult,
        ] = {}

    def create_job(
        self,
        job_id: str,
        query: str,
    ) -> ResearchJob:
        return self.job_manager.create_job(
            job_id=job_id,
            query=query,
        )

    def get_job(
        self,
        job_id: str,
    ) -> ResearchJob:
        return self.job_manager.get_job(job_id)

    def create_plan(
        self,
        job_id: str,
    ) -> ResearchPlan:
        return self.job_manager.create_plan(job_id)

    def get_plan(
        self,
        plan_id: str,
    ) -> ResearchPlan:
        return self.job_manager.get_plan(plan_id)

    def start_job(
        self,
        job_id: str,
    ) -> ResearchJob:
        return self.job_manager.start_job(job_id)

    def execute(
        self,
        execution_id: str,
        job_id: str,
    ) -> ResearchExecutionResult:
        if not isinstance(execution_id, str) or not execution_id.strip():
            raise ValueError(
                "execution_id must be a non-empty string"
            )

        if execution_id in self._executions:
            raise ValueError(
                f"research execution already exists: {execution_id}"
            )

        job = self.job_manager.get_job(job_id)

        if job.status != ResearchJobStatus.RUNNING:
            raise RuntimeError(
                "research job must be running before execution"
            )

        plan_id = f"plan-{job.job_id}"
        plan = self.job_manager.get_plan(plan_id)

        request = ResearchExecutionRequest(
            execution_id=execution_id,
            job_id=job.job_id,
            plan_id=plan.plan_id,
        )

        result = self.executor.execute(
            job=job,
            plan=plan,
            request=request,
        )

        self._executions[execution_id] = result

        if result.status == "completed":
            self.job_manager.complete_job(job.job_id)

        elif result.status == "failed":
            self.job_manager.fail_job(
                job.job_id,
                result.error or "research execution failed",
            )

        return result

    def get_execution(
        self,
        execution_id: str,
    ) -> ResearchExecutionResult:
        if (
            not isinstance(execution_id, str)
            or not execution_id.strip()
        ):
            raise ValueError(
                "execution_id must be a non-empty string"
            )

        if execution_id not in self._executions:
            raise KeyError(
                f"unknown research execution: {execution_id}"
            )

        return self._executions[execution_id]

    def execution_ids(self) -> list[str]:
        return sorted(self._executions.keys())

    def has_execution(
        self,
        execution_id: str,
    ) -> bool:
        return execution_id in self._executions

    def count_executions(self) -> int:
        return len(self._executions)

    def cancel_job(
        self,
        job_id: str,
    ) -> ResearchJob:
        return self.job_manager.cancel_job(job_id)

    def status(
        self,
        job_id: str,
    ) -> str:
        return self.job_manager.status(job_id)

    def is_terminal(
        self,
        job_id: str,
    ) -> bool:
        return self.job_manager.is_terminal(job_id)
