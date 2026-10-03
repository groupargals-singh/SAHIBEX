from __future__ import annotations

from typing import Callable, Dict, Optional

from core.research.job import ResearchJob, ResearchJobStatus
from core.research.research_execution import (
    ResearchExecutionRequest,
    ResearchExecutionResult,
)
from core.research.research_plan import ResearchPlan, ResearchStep


class ResearchExecutor:
    """
    Controlled executor for a ResearchPlan.

    The executor is intentionally provider-agnostic.
    Actual acquisition/research providers are injected as step handlers.
    """

    executor_name = "default_research_executor"

    def __init__(
        self,
        step_handlers: Optional[
            Dict[str, Callable[[ResearchStep, ResearchJob, ResearchPlan], object]]
        ] = None,
    ) -> None:
        self._step_handlers: Dict[
            str,
            Callable[[ResearchStep, ResearchJob, ResearchPlan], object],
        ] = {}

        if step_handlers is not None:
            if not isinstance(step_handlers, dict):
                raise TypeError("step_handlers must be a dictionary")

            for step_id, handler in step_handlers.items():
                self.register_step_handler(step_id, handler)

    def register_step_handler(
        self,
        step_id: str,
        handler: Callable[[ResearchStep, ResearchJob, ResearchPlan], object],
    ) -> None:
        if not isinstance(step_id, str) or not step_id.strip():
            raise ValueError("step_id must be a non-empty string")

        if not callable(handler):
            raise TypeError("handler must be callable")

        if step_id in self._step_handlers:
            raise ValueError(
                f"step handler already registered: {step_id}"
            )

        self._step_handlers[step_id] = handler

    def has_step_handler(self, step_id: str) -> bool:
        return step_id in self._step_handlers

    def step_handler_ids(self) -> list[str]:
        return sorted(self._step_handlers.keys())

    def execute(
        self,
        job: ResearchJob,
        plan: ResearchPlan,
        request: ResearchExecutionRequest,
    ) -> ResearchExecutionResult:
        if not isinstance(job, ResearchJob):
            raise TypeError("job must be a ResearchJob")

        if not isinstance(plan, ResearchPlan):
            raise TypeError("plan must be a ResearchPlan")

        if not isinstance(request, ResearchExecutionRequest):
            raise TypeError(
                "request must be a ResearchExecutionRequest"
            )

        if request.job_id != job.job_id:
            raise ValueError(
                "execution request job_id does not match job"
            )

        if request.plan_id != plan.plan_id:
            raise ValueError(
                "execution request plan_id does not match plan"
            )

        if job.status != ResearchJobStatus.RUNNING:
            raise RuntimeError(
                "research job must be running before execution"
            )

        result = ResearchExecutionResult(
            execution_id=request.execution_id,
            job_id=request.job_id,
            plan_id=request.plan_id,
            metadata={
                **request.metadata,
                "executor": self.executor_name,
            },
        )

        result.start()

        try:
            for step in plan.steps:
                handler = self._step_handlers.get(step.step_id)

                if handler is None:
                    if step.required:
                        result.fail(
                            f"no handler registered for required step: "
                            f"{step.step_id}",
                            failed_step=step.step_id,
                        )
                        return result

                    continue

                output = handler(step, job, plan)

                if output is not None:
                    result.output[step.step_id] = output

                result.record_step(step.step_id)

            result.complete(output=result.output)
            return result

        except Exception as exc:
            if result.status == "running":
                result.fail(
                    str(exc) or exc.__class__.__name__,
                )

            return result
