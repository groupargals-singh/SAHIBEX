from core.research.research_execution import (
    ResearchExecutionRequest,
    ResearchExecutionResult,
    ResearchExecutionStatus,
)


def test_execution_request_creation():
    request = ResearchExecutionRequest(
        execution_id="exec-001",
        job_id="job-001",
        plan_id="plan-job-001",
    )

    assert request.execution_id == "exec-001"
    assert request.job_id == "job-001"
    assert request.plan_id == "plan-job-001"


def test_execution_result_creation():
    result = ResearchExecutionResult(
        execution_id="exec-001",
        job_id="job-001",
        plan_id="plan-job-001",
    )

    assert result.status == ResearchExecutionStatus.CREATED
    assert result.completed_steps == []
    assert result.failed_step is None
    assert result.error is None
    assert result.output == {}
    assert result.is_terminal is False


def test_execution_start():
    result = ResearchExecutionResult(
        execution_id="exec-001",
        job_id="job-001",
        plan_id="plan-job-001",
    )

    result.start()

    assert result.status == ResearchExecutionStatus.RUNNING
    assert result.is_terminal is False


def test_execution_step_recording():
    result = ResearchExecutionResult(
        execution_id="exec-001",
        job_id="job-001",
        plan_id="plan-job-001",
    )

    result.start()
    result.record_step("research-scope")
    result.record_step("source-acquisition")

    assert result.completed_steps == [
        "research-scope",
        "source-acquisition",
    ]


def test_execution_completion():
    result = ResearchExecutionResult(
        execution_id="exec-001",
        job_id="job-001",
        plan_id="plan-job-001",
    )

    result.start()
    result.record_step("research-scope")
    result.complete(
        output={
            "knowledge_count": 3,
            "verified": True,
        }
    )

    assert result.status == ResearchExecutionStatus.COMPLETED
    assert result.is_terminal is True
    assert result.output["knowledge_count"] == 3
    assert result.output["verified"] is True


def test_execution_failure():
    result = ResearchExecutionResult(
        execution_id="exec-001",
        job_id="job-001",
        plan_id="plan-job-001",
    )

    result.start()
    result.record_step("research-scope")
    result.fail(
        "source acquisition failed",
        failed_step="source-acquisition",
    )

    assert result.status == ResearchExecutionStatus.FAILED
    assert result.is_terminal is True
    assert result.error == "source acquisition failed"
    assert result.failed_step == "source-acquisition"


def test_execution_cancellation():
    result = ResearchExecutionResult(
        execution_id="exec-001",
        job_id="job-001",
        plan_id="plan-job-001",
    )

    result.cancel()

    assert result.status == ResearchExecutionStatus.CANCELLED
    assert result.is_terminal is True


def test_execution_transition_protection():
    result = ResearchExecutionResult(
        execution_id="exec-001",
        job_id="job-001",
        plan_id="plan-job-001",
    )

    try:
        result.complete()
        assert False
    except RuntimeError:
        pass

    result.start()
    result.complete()

    try:
        result.start()
        assert False
    except RuntimeError:
        pass


def test_duplicate_step_protection():
    result = ResearchExecutionResult(
        execution_id="exec-001",
        job_id="job-001",
        plan_id="plan-job-001",
    )

    result.start()
    result.record_step("research-scope")

    try:
        result.record_step("research-scope")
        assert False
    except ValueError:
        pass


def test_execution_snapshot():
    result = ResearchExecutionResult(
        execution_id="exec-001",
        job_id="job-001",
        plan_id="plan-job-001",
        metadata={
            "executor": "test-executor",
        },
    )

    result.start()
    result.record_step("research-scope")
    result.complete(
        output={
            "verified": True,
        }
    )

    snapshot = result.snapshot()

    assert snapshot["execution_id"] == "exec-001"
    assert snapshot["job_id"] == "job-001"
    assert snapshot["plan_id"] == "plan-job-001"
    assert snapshot["status"] == ResearchExecutionStatus.COMPLETED
    assert snapshot["completed_steps"] == ["research-scope"]
    assert snapshot["output"]["verified"] is True
    assert snapshot["metadata"]["executor"] == "test-executor"


def test_execution_input_validation():
    try:
        ResearchExecutionRequest(
            execution_id="",
            job_id="job-001",
            plan_id="plan-001",
        )
        assert False
    except ValueError:
        pass

    try:
        ResearchExecutionResult(
            execution_id="exec-001",
            job_id="",
            plan_id="plan-001",
        )
        assert False
    except ValueError:
        pass

    try:
        ResearchExecutionResult(
            execution_id="exec-001",
            job_id="job-001",
            plan_id="plan-001",
            status="invalid",
        )
        assert False
    except ValueError:
        pass


if __name__ == "__main__":
    test_execution_request_creation()
    test_execution_result_creation()
    test_execution_start()
    test_execution_step_recording()
    test_execution_completion()
    test_execution_failure()
    test_execution_cancellation()
    test_execution_transition_protection()
    test_duplicate_step_protection()
    test_execution_snapshot()
    test_execution_input_validation()

    print("SAHIBEX RESEARCH EXECUTION CONTRACT TEST: PASS")
