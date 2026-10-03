from core.research.job import ResearchJobStatus
from core.research.research_job_manager import (
    ResearchJobManager,
)
from core.research.research_plan import ResearchPlan


def main() -> None:
    print("SAHIBEX RESEARCH JOB MANAGER TEST")

    # ---------------------------------------------------------
    # 1. Manager creation
    # ---------------------------------------------------------
    manager = ResearchJobManager()

    assert manager.manager_name == (
        "default_research_job_manager"
    )
    assert manager.count_jobs() == 0
    assert manager.count_plans() == 0
    assert manager.job_ids() == []

    print("[PASS] manager creation")

    # ---------------------------------------------------------
    # 2. Job creation
    # ---------------------------------------------------------
    job = manager.create_job(
        job_id="job-manager-001",
        query="Research SAHIBEX",
    )

    assert job.job_id == "job-manager-001"
    assert job.query == "Research SAHIBEX"
    assert job.status == ResearchJobStatus.CREATED
    assert manager.has_job("job-manager-001")
    assert manager.count_jobs() == 1

    print("[PASS] job creation")

    # ---------------------------------------------------------
    # 3. Job retrieval
    # ---------------------------------------------------------
    retrieved = manager.get_job(
        "job-manager-001"
    )

    assert retrieved is job

    print("[PASS] job retrieval")

    # ---------------------------------------------------------
    # 4. Duplicate job protection
    # ---------------------------------------------------------
    try:
        manager.create_job(
            job_id="job-manager-001",
            query="Duplicate",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "duplicate job IDs must be rejected"
        )

    print("[PASS] duplicate job protection")

    # ---------------------------------------------------------
    # 5. Unknown job protection
    # ---------------------------------------------------------
    try:
        manager.get_job("unknown-job")
    except KeyError:
        pass
    else:
        raise AssertionError(
            "unknown jobs must raise KeyError"
        )

    print("[PASS] unknown job protection")

    # ---------------------------------------------------------
    # 6. Plan creation
    # ---------------------------------------------------------
    plan = manager.create_plan(
        "job-manager-001"
    )

    assert isinstance(plan, ResearchPlan)
    assert plan.plan_id == (
        "plan-job-manager-001"
    )
    assert plan.job_id == (
        "job-manager-001"
    )
    assert manager.count_plans() == 1
    assert manager.has_plan(
        "plan-job-manager-001"
    )

    assert job.status == ResearchJobStatus.PLANNED

    print("[PASS] plan creation")

    # ---------------------------------------------------------
    # 7. Plan retrieval
    # ---------------------------------------------------------
    retrieved_plan = manager.get_plan(
        "plan-job-manager-001"
    )

    assert retrieved_plan is plan

    print("[PASS] plan retrieval")

    # ---------------------------------------------------------
    # 8. Planned-state requirement
    # ---------------------------------------------------------
    planned_job = manager.require_planned(
        "job-manager-001"
    )

    assert planned_job is job
    assert planned_job.status == (
        ResearchJobStatus.PLANNED
    )

    print("[PASS] planned-state validation")

    # ---------------------------------------------------------
    # 9. Start job
    # ---------------------------------------------------------
    started = manager.start_job(
        "job-manager-001"
    )

    assert started is job
    assert job.status == ResearchJobStatus.RUNNING
    assert job.started_at is not None

    print("[PASS] job start")

    # ---------------------------------------------------------
    # 10. Complete job
    # ---------------------------------------------------------
    completed = manager.complete_job(
        "job-manager-001"
    )

    assert completed is job
    assert job.status == (
        ResearchJobStatus.COMPLETED
    )
    assert job.completed_at is not None
    assert manager.is_terminal(
        "job-manager-001"
    )

    print("[PASS] job completion")

    # ---------------------------------------------------------
    # 11. Terminal protection
    # ---------------------------------------------------------
    try:
        manager.start_job(
            "job-manager-001"
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError(
            "completed job must not restart"
        )

    print("[PASS] terminal job protection")

    # ---------------------------------------------------------
    # 12. Failure lifecycle
    # ---------------------------------------------------------
    failed_job = manager.create_job(
        job_id="job-manager-002",
        query="Failure test",
    )

    manager.create_plan("job-manager-002")
    manager.start_job("job-manager-002")

    failed = manager.fail_job(
        "job-manager-002",
        "test failure",
    )

    assert failed is failed_job
    assert failed_job.status == (
        ResearchJobStatus.FAILED
    )
    assert failed_job.error == "test failure"
    assert failed_job.completed_at is not None
    assert manager.is_terminal(
        "job-manager-002"
    )

    print("[PASS] failure lifecycle")

    # ---------------------------------------------------------
    # 13. Cancellation lifecycle
    # ---------------------------------------------------------
    cancelled_job = manager.create_job(
        job_id="job-manager-003",
        query="Cancellation test",
    )

    cancelled = manager.cancel_job(
        "job-manager-003"
    )

    assert cancelled is cancelled_job
    assert cancelled_job.status == (
        ResearchJobStatus.CANCELLED
    )
    assert cancelled_job.completed_at is not None
    assert manager.is_terminal(
        "job-manager-003"
    )

    print("[PASS] cancellation lifecycle")

    # ---------------------------------------------------------
    # 14. Job listing
    # ---------------------------------------------------------
    assert manager.count_jobs() == 3
    assert manager.job_ids() == [
        "job-manager-001",
        "job-manager-002",
        "job-manager-003",
    ]

    assert len(manager.jobs()) == 3

    print("[PASS] job listing")

    # ---------------------------------------------------------
    # 15. Plan listing
    # ---------------------------------------------------------
    assert manager.count_plans() == 2
    assert len(manager.plans()) == 2

    print("[PASS] plan listing")

    # ---------------------------------------------------------
    # 16. Snapshot
    # ---------------------------------------------------------
    snapshot = manager.snapshot(
        "job-manager-002"
    )

    assert snapshot["job_id"] == (
        "job-manager-002"
    )
    assert snapshot["query"] == "Failure test"
    assert snapshot["status"] == (
        ResearchJobStatus.FAILED
    )
    assert snapshot["error"] == "test failure"

    print("[PASS] job snapshot")

    # ---------------------------------------------------------
    # 17. Invalid input protection
    # ---------------------------------------------------------
    try:
        manager.create_job(
            job_id="",
            query="invalid",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "blank job_id must be rejected"
        )

    try:
        manager.create_job(
            job_id="job-manager-004",
            query="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "blank query must be rejected"
        )

    try:
        manager.get_plan("")
    except ValueError:
        pass
    else:
        raise AssertionError(
            "blank plan_id must be rejected"
        )

    print("[PASS] input validation")

    print(
        "SAHIBEX RESEARCH JOB MANAGER TEST: PASS"
    )


if __name__ == "__main__":
    main()
