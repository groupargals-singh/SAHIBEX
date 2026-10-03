from core.orchestrator.planner import (
    Plan,
    PlanStatus,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main() -> None:
    print("SAHIBEX 6J-7 PLAN EXECUTION STATE TEST")

    plan = Plan(
        title="Execution state test",
        description="Verify plan lifecycle.",
    )

    check(
        plan.status == PlanStatus.PENDING,
        "plan starts in pending state",
    )

    check(
        plan.started_at is None,
        "plan has no start timestamp initially",
    )

    check(
        plan.completed_at is None,
        "plan has no completion timestamp initially",
    )

    plan.mark_ready()

    check(
        plan.status == PlanStatus.READY,
        "plan can become ready",
    )

    plan.mark_running()

    check(
        plan.status == PlanStatus.RUNNING,
        "plan can become running",
    )

    check(
        plan.started_at is not None,
        "running plan records start timestamp",
    )

    plan.mark_waiting_approval()

    check(
        plan.status == PlanStatus.WAITING_APPROVAL,
        "plan can wait for approval",
    )

    plan.mark_running()

    check(
        plan.status == PlanStatus.RUNNING,
        "approved plan can return to running",
    )

    plan.mark_blocked("Dependency is blocked.")

    check(
        plan.status == PlanStatus.BLOCKED,
        "plan can become blocked",
    )

    check(
        plan.error == "Dependency is blocked.",
        "blocked reason is preserved",
    )

    plan.mark_running()

    check(
        plan.status == PlanStatus.RUNNING,
        "blocked plan can resume running",
    )

    plan.complete("Plan completed successfully.")

    check(
        plan.status == PlanStatus.COMPLETED,
        "plan can become completed",
    )

    check(
        plan.result == "Plan completed successfully.",
        "plan result is preserved",
    )

    check(
        plan.completed_at is not None,
        "completed plan records completion timestamp",
    )

    failed_plan = Plan(
        title="Failure state test",
    )

    failed_plan.mark_ready()
    failed_plan.mark_running()
    failed_plan.fail("Execution failed.")

    check(
        failed_plan.status == PlanStatus.FAILED,
        "plan can become failed",
    )

    check(
        failed_plan.error == "Execution failed.",
        "failure reason is preserved",
    )

    cancelled_plan = Plan(
        title="Cancellation state test",
    )

    cancelled_plan.mark_ready()
    cancelled_plan.cancel("User cancelled the plan.")

    check(
        cancelled_plan.status == PlanStatus.CANCELLED,
        "plan can become cancelled",
    )

    check(
        cancelled_plan.error
        == "User cancelled the plan.",
        "cancellation reason is preserved",
    )

    print(
        "SAHIBEX 6J-7 PLAN EXECUTION STATE TEST: PASS"
    )


if __name__ == "__main__":
    main()
