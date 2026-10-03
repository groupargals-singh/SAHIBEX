from core.research.job import (
    ResearchJob,
    ResearchJobStatus,
)
from core.research.research_plan import ResearchPlan
from core.research.research_planner import ResearchPlanner


def main() -> None:
    print("SAHIBEX RESEARCH PLANNER TEST")

    # ---------------------------------------------------------
    # 1. Planner creation
    # ---------------------------------------------------------
    planner = ResearchPlanner()

    assert planner.planner_name == (
        "default_research_planner"
    )

    print("[PASS] planner creation")

    # ---------------------------------------------------------
    # 2. Job -> Plan
    # ---------------------------------------------------------
    job = ResearchJob(
        job_id="job-planner-001",
        query="Research SAHIBEX research architecture",
    )

    plan = planner.create_plan(job)

    assert isinstance(plan, ResearchPlan)
    assert plan.plan_id == "plan-job-planner-001"
    assert plan.job_id == "job-planner-001"
    assert plan.objective == (
        "Research SAHIBEX research architecture"
    )

    print("[PASS] job → research plan")

    # ---------------------------------------------------------
    # 3. Planned steps
    # ---------------------------------------------------------
    assert plan.step_count == 5

    step_ids = [
        step.step_id
        for step in plan.steps
    ]

    assert step_ids == [
        "research-scope",
        "source-acquisition",
        "evidence-extraction",
        "verification",
        "answer-synthesis",
    ]

    print("[PASS] standard research steps")

    # ---------------------------------------------------------
    # 4. Required steps
    # ---------------------------------------------------------
    assert len(plan.required_steps) == 5

    for step in plan.required_steps:
        assert step.required is True

    print("[PASS] required research steps")

    # ---------------------------------------------------------
    # 5. Source acquisition definition
    # ---------------------------------------------------------
    acquisition_step = plan.get_step(
        "source-acquisition"
    )

    assert "web" in acquisition_step.source_types
    assert "search" in acquisition_step.source_types
    assert "rss" in acquisition_step.source_types
    assert "api" in acquisition_step.source_types
    assert "document" in acquisition_step.source_types

    print("[PASS] acquisition planning")

    # ---------------------------------------------------------
    # 6. Planner metadata
    # ---------------------------------------------------------
    assert plan.metadata["planner"] == (
        "default_research_planner"
    )
    assert plan.metadata["planner_version"] == "1.0"

    print("[PASS] planner metadata")

    # ---------------------------------------------------------
    # 7. Job state remains unchanged
    # ---------------------------------------------------------
    assert job.status == ResearchJobStatus.CREATED

    print("[PASS] planner does not mutate job")

    # ---------------------------------------------------------
    # 8. Planner does not execute research
    # ---------------------------------------------------------
    assert plan.step_count > 0

    assert plan.get_step(
        "evidence-extraction"
    ).description

    assert plan.get_step(
        "verification"
    ).description

    assert plan.get_step(
        "answer-synthesis"
    ).description

    print("[PASS] planner remains execution-free")

    # ---------------------------------------------------------
    # 9. Invalid job type
    # ---------------------------------------------------------
    try:
        planner.create_plan("not-a-research-job")
    except TypeError:
        pass
    else:
        raise AssertionError(
            "planner must reject invalid job type"
        )

    print("[PASS] invalid job protection")

    # ---------------------------------------------------------
    # 10. Invalid job lifecycle
    # ---------------------------------------------------------
    planned_job = ResearchJob(
        job_id="job-planner-002",
        query="Invalid lifecycle test",
    )

    planned_job.plan()

    try:
        planner.create_plan(planned_job)
    except RuntimeError:
        pass
    else:
        raise AssertionError(
            "planner must reject already planned jobs"
        )

    print("[PASS] job lifecycle protection")

    # ---------------------------------------------------------
    # 11. Running job protection
    # ---------------------------------------------------------
    running_job = ResearchJob(
        job_id="job-planner-003",
        query="Running lifecycle test",
    )

    running_job.plan()
    running_job.start()

    try:
        planner.create_plan(running_job)
    except RuntimeError:
        pass
    else:
        raise AssertionError(
            "planner must reject running jobs"
        )

    print("[PASS] running job protection")

    # ---------------------------------------------------------
    # 12. Objective preservation
    # ---------------------------------------------------------
    objective_job = ResearchJob(
        job_id="job-planner-004",
        query="  Preserve this research objective  ",
    )

    objective_plan = planner.create_plan(
        objective_job
    )

    assert objective_plan.objective == (
        "Preserve this research objective"
    )

    print("[PASS] objective normalization")

    print("SAHIBEX RESEARCH PLANNER TEST: PASS")


if __name__ == "__main__":
    main()
