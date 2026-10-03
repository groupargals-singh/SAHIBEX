from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from core.agent_planning import AgentPlan
from core.orchestrator.task_state import (
    TaskManager,
    TaskPriority,
)


@dataclass(frozen=True)
class AgentTaskOrchestrationResult:
    success: bool
    plan_id: str
    task_ids: tuple[str, ...]
    blocked_task_ids: tuple[str, ...]
    ready_task_ids: tuple[str, ...]
    orchestration_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    error: str | None = None


class AgentTaskOrchestrator:
    """
    Connects 6P agent plans to the existing 6J task system.

    This layer:
    - creates 6J goals from an AgentPlan
    - creates 6J tasks from decomposed goals
    - preserves goal dependencies
    - identifies READY and BLOCKED tasks

    It does not:
    - execute tasks
    - execute tools
    - grant permissions
    - bypass the Constitution
    """

    def __init__(
        self,
        task_manager: TaskManager,
    ) -> None:
        if not isinstance(task_manager, TaskManager):
            raise TypeError(
                "task_manager must be TaskManager."
            )

        self.task_manager = task_manager

    def create_tasks(
        self,
        plan: AgentPlan,
    ) -> AgentTaskOrchestrationResult:
        if not isinstance(plan, AgentPlan):
            raise TypeError(
                "plan must be AgentPlan."
            )

        goal = self.task_manager.create_goal(
            title=f"Agent Plan {plan.plan_id}",
            description=plan.reason,
        )

        agent_goal_to_task_id: dict[str, str] = {}

        for item in plan.goals:
            task = self.task_manager.create_task(
                goal_id=goal.goal_id,
                title=item.title,
                description=item.objective,
                priority=self._priority_from_plan(
                    plan
                ),
                requires_approval=False,
                dependencies=[],
            )

            agent_goal_to_task_id[
                item.goal_id
            ] = task.task_id

        for item in plan.goals:
            task_id = agent_goal_to_task_id[
                item.goal_id
            ]

            task = self.task_manager.get_task(
                task_id
            )

            if task is None:
                raise RuntimeError(
                    "Created task could not be retrieved."
                )

            dependencies = []

            for dependency in item.dependencies:
                dependency_task_id = (
                    agent_goal_to_task_id.get(
                        dependency
                    )
                )

                if dependency_task_id is None:
                    raise ValueError(
                        "Plan contains dependency "
                        f"outside current plan: "
                        f"{dependency}"
                    )

                dependencies.append(
                    dependency_task_id
                )

            task.dependencies = dependencies

        task_ids = tuple(
            agent_goal_to_task_id[
                item.goal_id
            ]
            for item in plan.goals
        )

        blocked_task_ids = tuple(
            agent_goal_to_task_id[
                item.goal_id
            ]
            for item in plan.goals
            if item.dependencies
        )

        ready_task_ids = tuple(
            agent_goal_to_task_id[
                item.goal_id
            ]
            for item in plan.goals
            if not item.dependencies
        )

        return AgentTaskOrchestrationResult(
            success=True,
            plan_id=plan.plan_id,
            task_ids=task_ids,
            blocked_task_ids=blocked_task_ids,
            ready_task_ids=ready_task_ids,
        )

    @staticmethod
    def _priority_from_plan(
        plan: AgentPlan,
    ) -> TaskPriority:
        if plan.version >= 1:
            return TaskPriority.NORMAL

        return TaskPriority.LOW
