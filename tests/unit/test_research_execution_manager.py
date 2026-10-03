from core.research.job import ResearchJobStatus
from core.research.research_execution import ResearchExecutionStatus
from core.research.research_execution_manager import (
    ResearchExecutionManager,
)
from core.research.research_executor import ResearchExecutor


def make_manager():
    executor = ResearchExecutor()

    def scope_handler(step, job, plan):
        return {"scope": "defined"}

    def acquisition_handler(step, job, plan):
        return {"sources": 2}

    def extraction_handler(step, job, plan):
        return {"findings": 2}

    def verification_handler(step, job, plan):
        return {"verified": True}

    def answer_handler(step, job, plan):
        return {"answer": "test answer"}

    executor.register_step_handler(
        "research-scope",
        scope_handler,
    )
    executor.register_step_handler(
        "source-acquisition",
        acquisition_handler,
    )
    executor.register_step_handler(
        "evidence-extraction",
        extraction_handler,
    )
    executor.register_step_handler(
        "verification",
        verification_handler,
    )
    executor.register_step_handler(
        "answer-synthesis",
        answer_handler,
    )

    return ResearchExecutionManager(
        executor=executor,
    )


def test_manager_creation():
    manager = ResearchExecutionManager()

    assert manager.manager_name == (
        "default_research_execution_manager"
    )
    assert manager.count_executions() == 0


def test_create_job():
    manager = make_manager()

    job = manager.create_job(
        "job-001",
        "Test research query",
    )

    assert job.job_id == "job-001"
    assert job.status == ResearchJobStatus.CREATED


def test_create_plan():
    manager = make_manager()

    manager.create_job(
        "job-001",
        "Test research query",
    )

    plan = manager.create_plan("job-001")

    assert plan.plan_id == "plan-job-001"
    assert plan.job_id == "job-001"
    assert plan.step_count == 5

    assert manager.status("job-001") == (
        ResearchJobStatus.PLANNED
    )


def test_start_job():
    manager = make_manager()

    manager.create_job(
        "job-001",
        "Test research query",
    )
    manager.create_plan("job-001")

    job = manager.start_job("job-001")

    assert job.status == ResearchJobStatus.RUNNING
    assert manager.status("job-001") == (
        ResearchJobStatus.RUNNING
    )


def test_full_execution_lifecycle():
    manager = make_manager()

    manager.create_job(
        "job-001",
        "Test research query",
    )

    manager.create_plan("job-001")
    manager.start_job("job-001")

    result = manager.execute(
        execution_id="exec-001",
        job_id="job-001",
    )

    assert result.status == ResearchExecutionStatus.COMPLETED
    assert result.is_terminal is True

    assert result.completed_steps == [
        "research-scope",
        "source-acquisition",
        "evidence-extraction",
        "verification",
        "answer-synthesis",
    ]

    assert result.output["verification"]["verified"] is True
    assert result.output["answer-synthesis"]["answer"] == (
        "test answer"
    )

    assert manager.status("job-001") == (
        ResearchJobStatus.COMPLETED
    )

    assert manager.is_terminal("job-001") is True

    assert manager.has_execution("exec-001") is True
    assert manager.count_executions() == 1


def test_execution_retrieval():
    manager = make_manager()

    manager.create_job(
        "job-001",
        "Test research query",
    )
    manager.create_plan("job-001")
    manager.start_job("job-001")

    result = manager.execute(
        execution_id="exec-001",
        job_id="job-001",
    )

    stored = manager.get_execution("exec-001")

    assert stored is result
    assert stored.execution_id == "exec-001"


def test_duplicate_execution_protection():
    manager = make_manager()

    manager.create_job(
        "job-001",
        "Test research query",
    )
    manager.create_plan("job-001")
    manager.start_job("job-001")

    manager.execute(
        execution_id="exec-001",
        job_id="job-001",
    )

    try:
        manager.execute(
            execution_id="exec-001",
            job_id="job-001",
        )
        assert False
    except ValueError:
        pass


def test_execution_requires_running_job():
    manager = make_manager()

    manager.create_job(
        "job-001",
        "Test research query",
    )
    manager.create_plan("job-001")

    try:
        manager.execute(
            execution_id="exec-001",
            job_id="job-001",
        )
        assert False
    except RuntimeError:
        pass


def test_failed_execution_fails_job():
    executor = ResearchExecutor()

    def failing_handler(step, job, plan):
        if step.step_id == "source-acquisition":
            raise RuntimeError("acquisition failure")

        return {"ok": True}

    executor.register_step_handler(
        "research-scope",
        failing_handler,
    )
    executor.register_step_handler(
        "source-acquisition",
        failing_handler,
    )

    manager = ResearchExecutionManager(
        executor=executor,
    )

    manager.create_job(
        "job-001",
        "Test research query",
    )
    manager.create_plan("job-001")
    manager.start_job("job-001")

    result = manager.execute(
        execution_id="exec-001",
        job_id="job-001",
    )

    assert result.status == ResearchExecutionStatus.FAILED
    assert manager.status("job-001") == (
        ResearchJobStatus.FAILED
    )

    assert manager.is_terminal("job-001") is True


def test_execution_ids():
    manager = make_manager()

    manager.create_job(
        "job-001",
        "Test research query",
    )
    manager.create_plan("job-001")
    manager.start_job("job-001")

    manager.execute(
        execution_id="exec-001",
        job_id="job-001",
    )

    assert manager.execution_ids() == ["exec-001"]


def test_cancel_job():
    manager = make_manager()

    manager.create_job(
        "job-001",
        "Test research query",
    )

    job = manager.cancel_job("job-001")

    assert job.status == ResearchJobStatus.CANCELLED
    assert manager.is_terminal("job-001") is True


def test_unknown_execution_protection():
    manager = make_manager()

    try:
        manager.get_execution("missing")
        assert False
    except KeyError:
        pass


if __name__ == "__main__":
    test_manager_creation()
    test_create_job()
    test_create_plan()
    test_start_job()
    test_full_execution_lifecycle()
    test_execution_retrieval()
    test_duplicate_execution_protection()
    test_execution_requires_running_job()
    test_failed_execution_fails_job()
    test_execution_ids()
    test_cancel_job()
    test_unknown_execution_protection()

    print("SAHIBEX RESEARCH EXECUTION MANAGER TEST: PASS")
