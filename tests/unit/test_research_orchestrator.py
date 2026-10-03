from core.research.job import ResearchJobStatus
from core.research.research_execution import ResearchExecutionStatus
from core.research.research_execution_manager import (
    ResearchExecutionManager,
)
from core.research.research_executor import ResearchExecutor
from core.research.research_orchestrator import (
    ResearchOrchestrationResult,
    ResearchOrchestrator,
)


def make_orchestrator():
    executor = ResearchExecutor()

    def scope_handler(step, job, plan):
        return {"scope": "defined"}

    def acquisition_handler(step, job, plan):
        return {"sources": 3}

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

    manager = ResearchExecutionManager(
        executor=executor,
    )

    return ResearchOrchestrator(
        execution_manager=manager,
    )


def test_orchestrator_creation():
    orchestrator = ResearchOrchestrator()

    assert (
        orchestrator.orchestrator_name
        == "default_research_orchestrator"
    )


def test_create_job():
    orchestrator = make_orchestrator()

    job = orchestrator.create_job(
        "job-001",
        "Test research query",
    )

    assert job.job_id == "job-001"
    assert job.status == ResearchJobStatus.CREATED


def test_create_plan():
    orchestrator = make_orchestrator()

    orchestrator.create_job(
        "job-001",
        "Test research query",
    )

    plan = orchestrator.create_plan("job-001")

    assert plan.plan_id == "plan-job-001"
    assert plan.job_id == "job-001"
    assert plan.step_count == 5


def test_start_job():
    orchestrator = make_orchestrator()

    orchestrator.create_job(
        "job-001",
        "Test research query",
    )
    orchestrator.create_plan("job-001")

    job = orchestrator.start_job("job-001")

    assert job.status == ResearchJobStatus.RUNNING


def test_full_orchestration_run():
    orchestrator = make_orchestrator()

    orchestrator.create_job(
        "job-001",
        "Test research query",
    )

    result = orchestrator.run(
        job_id="job-001",
        execution_id="exec-001",
    )

    assert isinstance(
        result,
        ResearchOrchestrationResult,
    )

    assert result.job_id == "job-001"
    assert result.plan_id == "plan-job-001"
    assert result.execution_id == "exec-001"

    assert result.status == (
        ResearchExecutionStatus.COMPLETED
    )

    assert result.job_status == (
        ResearchJobStatus.COMPLETED
    )

    assert result.completed is True
    assert result.failed is False

    assert result.execution.completed_steps == [
        "research-scope",
        "source-acquisition",
        "evidence-extraction",
        "verification",
        "answer-synthesis",
    ]

    assert (
        result.execution.output[
            "answer-synthesis"
        ]["answer"]
        == "test answer"
    )


def test_orchestration_status():
    orchestrator = make_orchestrator()

    orchestrator.create_job(
        "job-001",
        "Test research query",
    )

    assert orchestrator.status("job-001") == (
        ResearchJobStatus.CREATED
    )


def test_get_execution():
    orchestrator = make_orchestrator()

    orchestrator.create_job(
        "job-001",
        "Test research query",
    )

    result = orchestrator.run(
        job_id="job-001",
        execution_id="exec-001",
    )

    stored = orchestrator.get_execution("exec-001")

    assert stored is result.execution
    assert stored.execution_id == "exec-001"


def test_invalid_job_id():
    orchestrator = make_orchestrator()

    try:
        orchestrator.run(
            job_id="",
            execution_id="exec-001",
        )
        assert False
    except ValueError:
        pass


def test_invalid_execution_id():
    orchestrator = make_orchestrator()

    orchestrator.create_job(
        "job-001",
        "Test research query",
    )

    try:
        orchestrator.run(
            job_id="job-001",
            execution_id="",
        )
        assert False
    except ValueError:
        pass


def test_duplicate_execution_protection():
    orchestrator = make_orchestrator()

    orchestrator.create_job(
        "job-001",
        "Test research query",
    )

    orchestrator.run(
        job_id="job-001",
        execution_id="exec-001",
    )

    try:
        orchestrator.run(
            job_id="job-001",
            execution_id="exec-001",
        )
        assert False
    except RuntimeError:
        pass


def test_already_running_job_protection():
    orchestrator = make_orchestrator()

    orchestrator.create_job(
        "job-001",
        "Test research query",
    )
    orchestrator.create_plan("job-001")
    orchestrator.start_job("job-001")

    try:
        orchestrator.run(
            job_id="job-001",
            execution_id="exec-001",
        )
        assert False
    except RuntimeError:
        pass


if __name__ == "__main__":
    test_orchestrator_creation()
    test_create_job()
    test_create_plan()
    test_start_job()
    test_full_orchestration_run()
    test_orchestration_status()
    test_get_execution()
    test_invalid_job_id()
    test_invalid_execution_id()
    test_duplicate_execution_protection()
    test_already_running_job_protection()

    print("SAHIBEX RESEARCH ORCHESTRATOR TEST: PASS")
