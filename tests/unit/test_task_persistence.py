from pathlib import Path
from tempfile import TemporaryDirectory

from core.orchestrator.task_state import (
    TaskManager,
    TaskPriority,
    TaskStatus,
)
from core.research.storage import ResearchStorage


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main() -> None:
    print("SAHIBEX 6J-3 TASK PERSISTENCE TEST")

    with TemporaryDirectory() as temp_dir:
        database_path = Path(temp_dir) / "task_persistence.db"

        # ---------------------------------------------------------
        # Create planning objects
        # ---------------------------------------------------------

        manager = TaskManager()

        goal = manager.create_goal(
            title="Persistent Planning Goal",
            description="Goal for task persistence testing.",
        )

        task = manager.create_task(
            goal_id=goal.goal_id,
            title="Persistent Task",
            description="Task that must survive storage restart.",
            priority=TaskPriority.HIGH,
            requires_approval=True,
            parent_task_id="parent-task-001",
            dependencies=[
                "dependency-001",
                "dependency-002",
            ],
        )

        check(
            task.status == TaskStatus.PENDING,
            "task starts in pending state",
        )

        check(
            task.priority == TaskPriority.HIGH,
            "task priority preserved before persistence",
        )

        check(
            task.requires_approval is True,
            "task approval requirement preserved before persistence",
        )

        check(
            task.parent_task_id == "parent-task-001",
            "parent task identity preserved before persistence",
        )

        check(
            task.dependencies == [
                "dependency-001",
                "dependency-002",
            ],
            "task dependencies preserved before persistence",
        )

        # ---------------------------------------------------------
        # First storage session
        # ---------------------------------------------------------

        storage = ResearchStorage(database_path)

        storage.save_goal(goal)
        storage.save_task(
            task,
            goal_id=goal.goal_id,
        )

        check(
            storage.goal_count() == 1,
            "one goal persisted",
        )

        check(
            storage.task_count() == 1,
            "one task persisted",
        )

        stored_task = storage.get_task(task.task_id)

        check(
            stored_task is not None,
            "persisted task can be retrieved",
        )

        check(
            stored_task.task_id == task.task_id,
            "task identity survives persistence",
        )

        check(
            stored_task.title == task.title,
            "task title survives persistence",
        )

        check(
            stored_task.description == task.description,
            "task description survives persistence",
        )

        check(
            stored_task.status == TaskStatus.PENDING,
            "task status survives persistence",
        )

        check(
            stored_task.priority == TaskPriority.HIGH,
            "task priority survives persistence",
        )

        check(
            stored_task.requires_approval is True,
            "task approval requirement survives persistence",
        )

        check(
            stored_task.parent_task_id == "parent-task-001",
            "parent task identity survives persistence",
        )

        check(
            stored_task.dependencies == [
                "dependency-001",
                "dependency-002",
            ],
            "task dependencies survive persistence",
        )

        stored_goal = storage.get_goal(goal.goal_id)

        check(
            stored_goal is not None,
            "persisted goal can be retrieved",
        )

        check(
            stored_goal.goal_id == goal.goal_id,
            "goal identity survives persistence",
        )

        check(
            stored_goal.title == goal.title,
            "goal title survives persistence",
        )

        check(
            stored_goal.description == goal.description,
            "goal description survives persistence",
        )

        check(
            len(stored_goal.tasks) == 1,
            "goal task association survives persistence",
        )

        check(
            stored_goal.tasks[0].task_id == task.task_id,
            "goal preserves persisted task identity",
        )

        storage.close()

        # ---------------------------------------------------------
        # Storage restart
        # ---------------------------------------------------------

        storage = ResearchStorage(database_path)

        check(
            storage.goal_count() == 1,
            "goal survives storage restart",
        )

        check(
            storage.task_count() == 1,
            "task survives storage restart",
        )

        restarted_task = storage.get_task(task.task_id)

        check(
            restarted_task is not None,
            "task can be retrieved after storage restart",
        )

        check(
            restarted_task.task_id == task.task_id,
            "task identity survives restart",
        )

        check(
            restarted_task.title == task.title,
            "task title survives restart",
        )

        check(
            restarted_task.description == task.description,
            "task description survives restart",
        )

        check(
            restarted_task.status == TaskStatus.PENDING,
            "task status survives restart",
        )

        check(
            restarted_task.priority == TaskPriority.HIGH,
            "task priority survives restart",
        )

        check(
            restarted_task.requires_approval is True,
            "task approval requirement survives restart",
        )

        check(
            restarted_task.parent_task_id == "parent-task-001",
            "parent task identity survives restart",
        )

        check(
            restarted_task.dependencies == [
                "dependency-001",
                "dependency-002",
            ],
            "task dependencies survive restart",
        )

        restarted_goal = storage.get_goal(goal.goal_id)

        check(
            restarted_goal is not None,
            "goal can be retrieved after storage restart",
        )

        check(
            restarted_goal.goal_id == goal.goal_id,
            "goal identity survives restart",
        )

        check(
            restarted_goal.title == goal.title,
            "goal title survives restart",
        )

        check(
            restarted_goal.description == goal.description,
            "goal description survives restart",
        )

        check(
            len(restarted_goal.tasks) == 1,
            "goal task association survives restart",
        )

        check(
            restarted_goal.tasks[0].task_id == task.task_id,
            "goal preserves task identity after restart",
        )

        # ---------------------------------------------------------
        # List APIs
        # ---------------------------------------------------------

        tasks = storage.list_tasks()

        check(
            len(tasks) == 1,
            "list_tasks returns persisted task",
        )

        check(
            tasks[0].task_id == task.task_id,
            "list_tasks preserves task identity",
        )

        tasks_for_goal = storage.list_tasks(
            goal_id=goal.goal_id,
        )

        check(
            len(tasks_for_goal) == 1,
            "list_tasks filters by goal",
        )

        check(
            tasks_for_goal[0].task_id == task.task_id,
            "goal-filtered task identity is preserved",
        )

        goals = storage.list_goals()

        check(
            len(goals) == 1,
            "list_goals returns persisted goal",
        )

        check(
            goals[0].goal_id == goal.goal_id,
            "list_goals preserves goal identity",
        )

        storage.close()

    print("SAHIBEX 6J-3 TASK PERSISTENCE TEST: PASS")


if __name__ == "__main__":
    main()
