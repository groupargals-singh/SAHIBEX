from core.research.job import (
    ResearchJob,
    ResearchJobStatus,
)


def main() -> None:
    print("SAHIBEX RESEARCH JOB TEST")

    # ---------------------------------------------------------
    # 1. Creation
    # ---------------------------------------------------------
    job = ResearchJob(
        job_id="job-test-001",
        query="What is SAHIBEX?",
    )

    assert job.job_id == "job-test-001"
    assert job.query == "What is SAHIBEX?"
    assert job.status == ResearchJobStatus.CREATED
    assert job.is_terminal is False

    print("[PASS] job creation")

    # ---------------------------------------------------------
    # 2. Created -> Planned
    # ---------------------------------------------------------
    job.plan()

    assert job.status == ResearchJobStatus.PLANNED
    assert job.is_terminal is False

    print("[PASS] created → planned")

    # ---------------------------------------------------------
    # 3. Planned -> Running
    # ---------------------------------------------------------
    job.start()

    assert job.status == ResearchJobStatus.RUNNING
    assert job.started_at is not None
    assert job.is_terminal is False

    print("[PASS] planned → running")

    # ---------------------------------------------------------
    # 4. Running -> Completed
    # ---------------------------------------------------------
    job.complete()

    assert job.status == ResearchJobStatus.COMPLETED
    assert job.completed_at is not None
    assert job.error is None
    assert job.is_terminal is True

    print("[PASS] running → completed")

    # ---------------------------------------------------------
    # 5. Terminal state protection
    # ---------------------------------------------------------
    try:
        job.start()
    except RuntimeError:
        pass
    else:
        raise AssertionError(
            "completed job must not be restarted"
        )

    try:
        job.plan()
    except RuntimeError:
        pass
    else:
        raise AssertionError(
            "completed job must not be replanned"
        )

    print("[PASS] terminal state protection")

    # ---------------------------------------------------------
    # 6. Failure lifecycle
    # ---------------------------------------------------------
    failed_job = ResearchJob(
        job_id="job-test-002",
        query="Failure test",
    )

    failed_job.plan()
    failed_job.start()
    failed_job.fail("test failure")

    assert failed_job.status == ResearchJobStatus.FAILED
    assert failed_job.error == "test failure"
    assert failed_job.completed_at is not None
    assert failed_job.is_terminal is True

    print("[PASS] failure lifecycle")

    # ---------------------------------------------------------
    # 7. Cancellation
    # ---------------------------------------------------------
    cancelled_job = ResearchJob(
        job_id="job-test-003",
        query="Cancellation test",
    )

    cancelled_job.cancel()

    assert cancelled_job.status == ResearchJobStatus.CANCELLED
    assert cancelled_job.completed_at is not None
    assert cancelled_job.is_terminal is True

    print("[PASS] cancellation lifecycle")

    # ---------------------------------------------------------
    # 8. Invalid transition protection
    # ---------------------------------------------------------
    invalid_job = ResearchJob(
        job_id="job-test-004",
        query="Invalid transition test",
    )

    try:
        invalid_job.start()
    except RuntimeError:
        pass
    else:
        raise AssertionError(
            "created job must not start directly"
        )

    try:
        invalid_job.complete()
    except RuntimeError:
        pass
    else:
        raise AssertionError(
            "created job must not complete directly"
        )

    print("[PASS] invalid transition protection")

    # ---------------------------------------------------------
    # 9. Snapshot
    # ---------------------------------------------------------
    snapshot = failed_job.snapshot()

    assert snapshot["job_id"] == "job-test-002"
    assert snapshot["query"] == "Failure test"
    assert snapshot["status"] == ResearchJobStatus.FAILED
    assert snapshot["error"] == "test failure"
    assert snapshot["created_at"] is not None
    assert snapshot["completed_at"] is not None
    assert isinstance(snapshot["metadata"], dict)

    print("[PASS] job snapshot")

    # ---------------------------------------------------------
    # 10. Input validation
    # ---------------------------------------------------------
    try:
        ResearchJob(
            job_id="",
            query="valid",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "blank job_id must be rejected"
        )

    try:
        ResearchJob(
            job_id="job-test-005",
            query="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "blank query must be rejected"
        )

    print("[PASS] input validation")

    print("SAHIBEX RESEARCH JOB TEST: PASS")


if __name__ == "__main__":
    main()
