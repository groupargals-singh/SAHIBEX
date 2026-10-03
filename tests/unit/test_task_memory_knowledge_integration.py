from core.orchestrator.task_state import (
    Task,
    TaskStatus,
)
from core.orchestrator.planner import Plan


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main() -> None:
    print(
        "SAHIBEX 6J-9 TASK ↔ MEMORY / KNOWLEDGE INTEGRATION TEST"
    )

    # -------------------------------------------------
    # TASK CONTEXT REFERENCES
    # -------------------------------------------------

    task = Task(
        title="Research task",
        description="Task with memory and knowledge context.",
    )

    check(
        hasattr(task, "memory_ids"),
        "task has memory references",
    )

    check(
        hasattr(task, "knowledge_ids"),
        "task has knowledge references",
    )

    check(
        task.memory_ids == [],
        "task memory references start empty",
    )

    check(
        task.knowledge_ids == [],
        "task knowledge references start empty",
    )

    memory_id_1 = "memory-001"
    memory_id_2 = "memory-002"

    knowledge_id_1 = "knowledge-001"
    knowledge_id_2 = "knowledge-002"

    task.add_memory_reference(memory_id_1)
    task.add_memory_reference(memory_id_2)

    check(
        task.memory_ids == [
            memory_id_1,
            memory_id_2,
        ],
        "task preserves memory references",
    )

    task.add_knowledge_reference(
        knowledge_id_1
    )
    task.add_knowledge_reference(
        knowledge_id_2
    )

    check(
        task.knowledge_ids == [
            knowledge_id_1,
            knowledge_id_2,
        ],
        "task preserves knowledge references",
    )

    # -------------------------------------------------
    # DUPLICATE REFERENCE PROTECTION
    # -------------------------------------------------

    task.add_memory_reference(memory_id_1)

    check(
        task.memory_ids.count(memory_id_1) == 1,
        "duplicate memory reference is not duplicated",
    )

    task.add_knowledge_reference(
        knowledge_id_1
    )

    check(
        task.knowledge_ids.count(knowledge_id_1) == 1,
        "duplicate knowledge reference is not duplicated",
    )

    # -------------------------------------------------
    # INVALID REFERENCE PROTECTION
    # -------------------------------------------------

    invalid_memory_blocked = False

    try:
        task.add_memory_reference("")
    except ValueError:
        invalid_memory_blocked = True

    check(
        invalid_memory_blocked,
        "empty memory reference is rejected",
    )

    invalid_knowledge_blocked = False

    try:
        task.add_knowledge_reference("")
    except ValueError:
        invalid_knowledge_blocked = True

    check(
        invalid_knowledge_blocked,
        "empty knowledge reference is rejected",
    )

    # -------------------------------------------------
    # TASK LIFECYCLE PRESERVATION
    # -------------------------------------------------

    task.mark_ready()
    task.mark_running()

    check(
        task.status == TaskStatus.RUNNING,
        "task lifecycle remains functional",
    )

    check(
        task.memory_ids == [
            memory_id_1,
            memory_id_2,
        ],
        "memory references survive task lifecycle",
    )

    check(
        task.knowledge_ids == [
            knowledge_id_1,
            knowledge_id_2,
        ],
        "knowledge references survive task lifecycle",
    )

    # -------------------------------------------------
    # PLAN CONTEXT REFERENCES
    # -------------------------------------------------

    plan = Plan(
        title="Knowledge-aware plan",
        description="Plan with memory and knowledge context.",
    )

    check(
        hasattr(plan, "memory_ids"),
        "plan has memory references",
    )

    check(
        hasattr(plan, "knowledge_ids"),
        "plan has knowledge references",
    )

    check(
        plan.memory_ids == [],
        "plan memory references start empty",
    )

    check(
        plan.knowledge_ids == [],
        "plan knowledge references start empty",
    )

    plan.add_memory_reference("memory-plan-001")
    plan.add_knowledge_reference("knowledge-plan-001")

    check(
        plan.memory_ids == ["memory-plan-001"],
        "plan preserves memory reference",
    )

    check(
        plan.knowledge_ids == ["knowledge-plan-001"],
        "plan preserves knowledge reference",
    )

    # -------------------------------------------------
    # PLAN LIFECYCLE PRESERVATION
    # -------------------------------------------------

    plan.mark_ready()
    plan.mark_running()

    check(
        plan.status.value == "running",
        "plan lifecycle remains functional",
    )

    check(
        plan.memory_ids == ["memory-plan-001"],
        "plan memory reference survives lifecycle",
    )

    check(
        plan.knowledge_ids == ["knowledge-plan-001"],
        "plan knowledge reference survives lifecycle",
    )

    print(
        "SAHIBEX 6J-9 TASK ↔ MEMORY / KNOWLEDGE INTEGRATION TEST: PASS"
    )


if __name__ == "__main__":
    main()
