from core.orchestrator.planner import (
    Plan,
    PlanRegistry,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main() -> None:
    print("SAHIBEX 6J-6 PLAN OBJECT & PLAN REGISTRY TEST")

    registry = PlanRegistry()

    plan = Plan(
        title="Build SAHIBEX planning system",
        description="Create the planning intelligence layer.",
        goal_id="goal-001",
        task_ids=[
            "task-001",
            "task-002",
        ],
        metadata={
            "source": "6J-6-test",
            "version": "1",
        },
    )

    check(
        bool(plan.plan_id),
        "plan has unique identity",
    )

    check(
        plan.title == "Build SAHIBEX planning system",
        "plan title is preserved",
    )

    check(
        plan.description
        == "Create the planning intelligence layer.",
        "plan description is preserved",
    )

    check(
        plan.goal_id == "goal-001",
        "plan goal identity is preserved",
    )

    check(
        plan.task_ids == [
            "task-001",
            "task-002",
        ],
        "plan task identities are preserved",
    )

    check(
        plan.metadata["source"] == "6J-6-test",
        "plan metadata is preserved",
    )

    registry.register(plan)

    check(
        registry.get(plan.plan_id) is plan,
        "registered plan lookup returns same object",
    )

    check(
        registry.count() == 1,
        "registry contains one plan",
    )

    listed = registry.list_plans()

    check(
        len(listed) == 1,
        "list_plans returns registered plan",
    )

    check(
        listed[0] is plan,
        "list_plans preserves plan identity",
    )

    second_plan = Plan(
        title="Second planning test",
        description="Second plan.",
        goal_id="goal-002",
        task_ids=["task-003"],
    )

    registry.register(second_plan)

    check(
        registry.count() == 2,
        "registry contains two plans",
    )

    check(
        registry.get(second_plan.plan_id) is second_plan,
        "second plan lookup returns correct object",
    )

    check(
        plan.plan_id != second_plan.plan_id,
        "plans have unique identities",
    )

    check(
        registry.list_plans()[0] is plan,
        "first registered plan remains preserved",
    )

    isolated_registry = PlanRegistry()

    isolated_plan = Plan(
        title="Isolated plan",
        description="Registry isolation test.",
        goal_id="goal-003",
    )

    isolated_registry.register(isolated_plan)

    check(
        isolated_registry.count() == 1,
        "second registry has its own plan",
    )

    check(
        registry.count() == 2,
        "first registry remains isolated",
    )

    check(
        registry.get(isolated_plan.plan_id) is None,
        "first registry cannot access second registry plan",
    )

    check(
        isolated_registry.get(isolated_plan.plan_id)
        is isolated_plan,
        "second registry preserves its own plan",
    )

    check(
        registry.get("unknown-plan-id") is None,
        "unknown plan lookup returns None",
    )

    print(
        "SAHIBEX 6J-6 PLAN OBJECT & PLAN REGISTRY TEST: PASS"
    )


if __name__ == "__main__":
    main()
