from core.research.job import ResearchJob, ResearchJobStatus
from core.research.research_execution import (
    ResearchExecutionRequest,
    ResearchExecutionStatus,
)
from core.research.research_executor import ResearchExecutor
from core.research.research_plan import ResearchPlan, ResearchStep


def make_job():
    job = ResearchJob(
        job_id="job-001",
        query="Test research query",
    )
    job.plan()
    job.start()
    return job


def make_plan():
    return ResearchPlan(
        plan_id="plan-job-001",
        job_id="job-001",
        objective="Test research query",
        steps=[
            ResearchStep(
                step_id="step-one",
                description="First step",
                required=True,
            ),
            ResearchStep(
                step_id="step-two",
                description="Second step",
                required=True,
            ),
        ],
    )


def make_request():
    return ResearchExecutionRequest(
        execution_id="exec-001",
        job_id="job-001",
        plan_id="plan-job-001",
    )


def test_executor_creation():
    executor = ResearchExecutor()

    assert executor.executor_name == "default_research_executor"
    assert executor.step_handler_ids() == []


def test_step_handler_registration():
    executor = ResearchExecutor()

    def handler(step, job, plan):
        return "ok"

    executor.register_step_handler("step-one", handler)

    assert executor.has_step_handler("step-one") is True
    assert executor.step_handler_ids() == ["step-one"]


def test_execution_with_registered_handlers():
    job = make_job()
    plan = make_plan()
    request = make_request()

    executor = ResearchExecutor()

    def first_handler(step, job, plan):
        return {"result": "first"}

    def second_handler(step, job, plan):
        return {"result": "second"}

    executor.register_step_handler("step-one", first_handler)
    executor.register_step_handler("step-two", second_handler)

    result = executor.execute(
        job=job,
        plan=plan,
        request=request,
    )

    assert result.status == ResearchExecutionStatus.COMPLETED
    assert result.is_terminal is True
    assert result.completed_steps == [
        "step-one",
        "step-two",
    ]
    assert result.output["step-one"]["result"] == "first"
    assert result.output["step-two"]["result"] == "second"


def test_required_step_without_handler_fails():
    job = make_job()
    plan = make_plan()
    request = make_request()

    executor = ResearchExecutor()

    result = executor.execute(
        job=job,
        plan=plan,
        request=request,
    )

    assert result.status == ResearchExecutionStatus.FAILED
    assert result.is_terminal is True
    assert result.failed_step == "step-one"
    assert "no handler registered" in result.error


def test_optional_step_without_handler_is_skipped():
    job = make_job()

    plan = ResearchPlan(
        plan_id="plan-job-001",
        job_id="job-001",
        objective="Test research query",
        steps=[
            ResearchStep(
                step_id="required-step",
                description="Required step",
                required=True,
            ),
            ResearchStep(
                step_id="optional-step",
                description="Optional step",
                required=False,
            ),
        ],
    )

    request = make_request()

    executor = ResearchExecutor()

    def required_handler(step, job, plan):
        return "required"

    executor.register_step_handler(
        "required-step",
        required_handler,
    )

    result = executor.execute(
        job=job,
        plan=plan,
        request=request,
    )

    assert result.status == ResearchExecutionStatus.COMPLETED
    assert result.completed_steps == ["required-step"]
    assert "optional-step" not in result.output


def test_handler_exception_fails_execution():
    job = make_job()
    plan = make_plan()
    request = make_request()

    executor = ResearchExecutor()

    def failing_handler(step, job, plan):
        raise RuntimeError("handler failure")

    executor.register_step_handler(
        "step-one",
        failing_handler,
    )

    result = executor.execute(
        job=job,
        plan=plan,
        request=request,
    )

    assert result.status == ResearchExecutionStatus.FAILED
    assert result.is_terminal is True
    assert result.error == "handler failure"


def test_job_must_be_running():
    job = ResearchJob(
        job_id="job-001",
        query="Test research query",
    )

    plan = make_plan()
    request = make_request()
    executor = ResearchExecutor()

    try:
        executor.execute(job, plan, request)
        assert False
    except RuntimeError:
        pass


def test_job_id_mismatch_is_blocked():
    job = make_job()
    plan = make_plan()

    request = ResearchExecutionRequest(
        execution_id="exec-001",
        job_id="different-job",
        plan_id="plan-job-001",
    )

    executor = ResearchExecutor()

    try:
        executor.execute(job, plan, request)
        assert False
    except ValueError as exc:
        assert "job_id" in str(exc)


def test_plan_id_mismatch_is_blocked():
    job = make_job()
    plan = make_plan()

    request = ResearchExecutionRequest(
        execution_id="exec-001",
        job_id="job-001",
        plan_id="different-plan",
    )

    executor = ResearchExecutor()

    try:
        executor.execute(job, plan, request)
        assert False
    except ValueError as exc:
        assert "plan_id" in str(exc)


def test_duplicate_handler_registration_is_blocked():
    executor = ResearchExecutor()

    def handler(step, job, plan):
        return None

    executor.register_step_handler("step-one", handler)

    try:
        executor.register_step_handler("step-one", handler)
        assert False
    except ValueError:
        pass


def test_invalid_handler_registration_is_blocked():
    executor = ResearchExecutor()

    try:
        executor.register_step_handler("step-one", None)
        assert False
    except TypeError:
        pass


if __name__ == "__main__":
    test_executor_creation()
    test_step_handler_registration()
    test_execution_with_registered_handlers()
    test_required_step_without_handler_fails()
    test_optional_step_without_handler_is_skipped()
    test_handler_exception_fails_execution()
    test_job_must_be_running()
    test_job_id_mismatch_is_blocked()
    test_plan_id_mismatch_is_blocked()
    test_duplicate_handler_registration_is_blocked()
    test_invalid_handler_registration_is_blocked()

    print("SAHIBEX RESEARCH EXECUTOR TEST: PASS")
