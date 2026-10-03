from core.orchestrator.task_state import (
    Task,
    TaskStatus,
)
from core.orchestrator.planner import (
    Plan,
    PlanStatus,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main() -> None:
    print(
        "SAHIBEX 6J-8 FAILURE / RETRY / RECOVERY TEST"
    )

    # -------------------------------------------------
    # TASK RETRY CONTRACT
    # -------------------------------------------------

    task = Task(
        title="Retryable task",
        description="Task used for retry testing.",
    )

    check(
        task.status == TaskStatus.PENDING,
        "task starts in pending state",
    )

    check(
        hasattr(task, "retry_count"),
        "task has retry count",
    )

    check(
        task.retry_count == 0,
        "task retry count starts at zero",
    )

    check(
        hasattr(task, "max_retries"),
        "task has maximum retry configuration",
    )

    task.mark_ready()
    task.mark_running()

    task.fail("First failure")

    check(
        task.status == TaskStatus.FAILED,
        "task can become failed",
    )

    check(
        task.error == "First failure",
        "task failure reason is preserved",
    )

    previous_retry_count = task.retry_count

    task.retry()

    check(
        task.retry_count == previous_retry_count + 1,
        "task retry count increments",
    )

    check(
        task.status == TaskStatus.READY,
        "failed task can recover to ready state",
    )

    task.mark_running()
    task.fail("Second failure")

    task.retry()

    check(
        task.retry_count == 2,
        "second retry increments retry count",
    )

    check(
        task.status == TaskStatus.READY,
        "task remains recoverable within retry limit",
    )

    # -------------------------------------------------
    # RETRY LIMIT
    # -------------------------------------------------

    limited_task = Task(
        title="Limited retry task",
        max_retries=1,
    )

    limited_task.mark_ready()
    limited_task.mark_running()
    limited_task.fail("Limited failure")

    limited_task.retry()

    check(
        limited_task.retry_count == 1,
        "limited task records allowed retry",
    )

    check(
        limited_task.status == TaskStatus.READY,
        "limited task becomes ready after allowed retry",
    )

    limited_task.mark_running()
    limited_task.fail("Retry limit failure")

    retry_blocked = False

    try:
        limited_task.retry()
    except ValueError:
        retry_blocked = True

    check(
        retry_blocked,
        "retry is blocked after maximum retries",
    )

    check(
        limited_task.status == TaskStatus.FAILED,
        "task remains failed after retry limit",
    )

    # -------------------------------------------------
    # PLAN RETRY CONTRACT
    # -------------------------------------------------

    plan = Plan(
        title="Retryable plan",
        description="Plan used for retry testing.",
    )

    check(
        hasattr(plan, "retry_count"),
        "plan has retry count",
    )

    check(
        plan.retry_count == 0,
        "plan retry count starts at zero",
    )

    check(
        hasattr(plan, "max_retries"),
        "plan has maximum retry configuration",
    )

    plan.mark_ready()
    plan.mark_running()
    plan.fail("Plan failure")

    check(
        plan.status == PlanStatus.FAILED,
        "plan can become failed",
    )

    plan.retry()

    check(
        plan.retry_count == 1,
        "plan retry count increments",
    )

    check(
        plan.status == PlanStatus.READY,
        "failed plan can recover to ready state",
    )

    # -------------------------------------------------
    # RECOVERY
    # -------------------------------------------------

    plan.mark_running()
    plan.mark_blocked("External dependency unavailable")

    check(
        plan.status == PlanStatus.BLOCKED,
        "plan can become blocked during recovery",
    )

    plan.retry()

    check(
        plan.retry_count == 2,
        "plan retry count increments during recovery",
    )

    check(
        plan.status == PlanStatus.READY,
        "blocked plan can recover to ready state",
    )

    print(
        "SAHIBEX 6J-8 FAILURE / RETRY / RECOVERY TEST: PASS"
    )


if __name__ == "__main__":
    main()
