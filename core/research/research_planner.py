from __future__ import annotations

from core.research.job import ResearchJob, ResearchJobStatus
from core.research.research_plan import ResearchPlan, ResearchStep


class ResearchPlanner:
    """
    Converts a ResearchJob into a validated ResearchPlan.

    The planner does not execute research.
    It does not access the network.
    It does not acquire sources.

    Its only responsibility is planning.
    """

    planner_name = "default_research_planner"

    def create_plan(self, job: ResearchJob) -> ResearchPlan:
        if not isinstance(job, ResearchJob):
            raise TypeError(
                "job must be a ResearchJob"
            )

        if job.status != ResearchJobStatus.CREATED:
            raise RuntimeError(
                "research job must be in created status "
                "before planning"
            )

        query = job.query.strip()

        steps = [
            ResearchStep(
                step_id="research-scope",
                description=(
                    "Define the research scope and "
                    "identify the information required "
                    "to answer the research objective."
                ),
                source_types=[],
                required=True,
            ),
            ResearchStep(
                step_id="source-acquisition",
                description=(
                    "Acquire relevant research sources "
                    "using approved acquisition providers."
                ),
                source_types=[
                    "web",
                    "search",
                    "rss",
                    "api",
                    "document",
                ],
                required=True,
            ),
            ResearchStep(
                step_id="evidence-extraction",
                description=(
                    "Extract findings and supporting "
                    "evidence from acquired documents."
                ),
                source_types=[],
                required=True,
            ),
            ResearchStep(
                step_id="verification",
                description=(
                    "Verify research knowledge against "
                    "supporting and conflicting evidence."
                ),
                source_types=[],
                required=True,
            ),
            ResearchStep(
                step_id="answer-synthesis",
                description=(
                    "Synthesize a traceable research answer "
                    "from verified knowledge."
                ),
                source_types=[],
                required=True,
            ),
        ]

        plan = ResearchPlan(
            plan_id=f"plan-{job.job_id}",
            job_id=job.job_id,
            objective=query,
            steps=steps,
            metadata={
                "planner": self.planner_name,
                "planner_version": "1.0",
            },
        )

        return plan
