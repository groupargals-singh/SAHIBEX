from __future__ import annotations

from typing import Dict

from core.research.job import ResearchJob, ResearchJobStatus
from core.research.research_plan import ResearchPlan
from core.research.research_planner import ResearchPlanner


class ResearchJobManager:
    """
    Central lifecycle manager for SAHIBEX research jobs.

    Responsibilities:
        - create jobs
        - register jobs
        - retrieve jobs
        - create plans
        - start jobs
        - complete jobs
        - fail jobs
        - cancel jobs

    The manager does not execute research.
    """

    manager_name = "default_research_job_manager"

    def __init__(
        self,
        planner: ResearchPlanner | None = None,
    ) -> None:
        self.planner = (
            planner
            if planner is not None
            else ResearchPlanner()
        )

        self._jobs: Dict[str, ResearchJob] = {}
        self._plans: Dict[str, ResearchPlan] = {}

    def create_job(
        self,
        job_id: str,
        query: str,
    ) -> ResearchJob:
        if not isinstance(job_id, str) or not job_id.strip():
            raise ValueError(
                "job_id must be a non-empty string"
            )

        if not isinstance(query, str) or not query.strip():
            raise ValueError(
                "query must be a non-empty string"
            )

        if job_id in self._jobs:
            raise ValueError(
                f"research job already exists: {job_id}"
            )

        job = ResearchJob(
            job_id=job_id,
            query=query.strip(),
        )

        self._jobs[job_id] = job

        return job

    def register_job(
        self,
        job: ResearchJob,
    ) -> ResearchJob:
        if not isinstance(job, ResearchJob):
            raise TypeError(
                "job must be a ResearchJob"
            )

        if job.job_id in self._jobs:
            raise ValueError(
                f"research job already exists: {job.job_id}"
            )

        self._jobs[job.job_id] = job

        return job

    def get_job(
        self,
        job_id: str,
    ) -> ResearchJob:
        if not isinstance(job_id, str) or not job_id.strip():
            raise ValueError(
                "job_id must be a non-empty string"
            )

        if job_id not in self._jobs:
            raise KeyError(
                f"unknown research job: {job_id}"
            )

        return self._jobs[job_id]

    def jobs(self) -> list[ResearchJob]:
        return list(self._jobs.values())

    def job_ids(self) -> list[str]:
        return sorted(self._jobs.keys())

    def create_plan(
        self,
        job_id: str,
    ) -> ResearchPlan:
        job = self.get_job(job_id)

        plan = self.planner.create_plan(job)

        if plan.plan_id in self._plans:
            raise ValueError(
                f"research plan already exists: {plan.plan_id}"
            )

        self._plans[plan.plan_id] = plan

        job.plan()

        return plan

    def get_plan(
        self,
        plan_id: str,
    ) -> ResearchPlan:
        if not isinstance(plan_id, str) or not plan_id.strip():
            raise ValueError(
                "plan_id must be a non-empty string"
            )

        if plan_id not in self._plans:
            raise KeyError(
                f"unknown research plan: {plan_id}"
            )

        return self._plans[plan_id]

    def plans(self) -> list[ResearchPlan]:
        return list(self._plans.values())

    def start_job(
        self,
        job_id: str,
    ) -> ResearchJob:
        job = self.get_job(job_id)

        job.start()

        return job

    def complete_job(
        self,
        job_id: str,
    ) -> ResearchJob:
        job = self.get_job(job_id)

        job.complete()

        return job

    def fail_job(
        self,
        job_id: str,
        error: str,
    ) -> ResearchJob:
        job = self.get_job(job_id)

        job.fail(error)

        return job

    def cancel_job(
        self,
        job_id: str,
    ) -> ResearchJob:
        job = self.get_job(job_id)

        job.cancel()

        return job

    def status(
        self,
        job_id: str,
    ) -> str:
        return self.get_job(job_id).status

    def is_terminal(
        self,
        job_id: str,
    ) -> bool:
        return self.get_job(job_id).is_terminal

    def snapshot(
        self,
        job_id: str,
    ) -> dict[str, object]:
        return self.get_job(job_id).snapshot()

    def has_job(
        self,
        job_id: str,
    ) -> bool:
        return job_id in self._jobs

    def has_plan(
        self,
        plan_id: str,
    ) -> bool:
        return plan_id in self._plans

    def count_jobs(self) -> int:
        return len(self._jobs)

    def count_plans(self) -> int:
        return len(self._plans)

    def require_planned(
        self,
        job_id: str,
    ) -> ResearchJob:
        job = self.get_job(job_id)

        if job.status != ResearchJobStatus.PLANNED:
            raise RuntimeError(
                "research job must be planned"
            )

        return job
