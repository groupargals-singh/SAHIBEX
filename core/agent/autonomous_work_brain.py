from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from core.agent_goal import AgentGoal
from core.agent_decomposition import GoalDecompositionEngine, DecomposedGoal
from core.agent_planning import DynamicPlanningEngine, AgentPlan
from core.agent_task_intake import AgentTaskIntake
from core.agent_task_orchestration import AgentTaskOrchestrator
from core.agent.checkpoint_resume import CheckpointResumeStore
from core.agent.long_running_jobs import LongRunningJobManager
from core.brain.failure_recovery_expansion import FailureRecoveryEngine
from core.orchestrator.task_state import TaskManager, TaskStatus


@dataclass(frozen=True)
class AutonomousWorkResult:
    success: bool
    status: str
    objective: str
    plan_id: str
    completed_steps: tuple[str, ...]
    failed_steps: tuple[str, ...]
    response: Any = None
    verification_status: str = "NOT_VERIFIED"
    attempts: int = 0
    checkpoint_sequence: int | None = None
    resumed: bool = False
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AutonomousWorkBrain:
    """SAHIBEX Phase 7 autonomous multi-step work runtime."""

    VERSION = "1.0"

    def __init__(
        self,
        *,
        intake: AgentTaskIntake | None = None,
        decomposer: GoalDecompositionEngine | None = None,
        planner: DynamicPlanningEngine | None = None,
        task_manager: TaskManager | None = None,
        checkpoint_store: CheckpointResumeStore | None = None,
        jobs: LongRunningJobManager | None = None,
        recovery: FailureRecoveryEngine | None = None,
    ) -> None:
        self.intake = intake or AgentTaskIntake()
        self.decomposer = decomposer or GoalDecompositionEngine()
        self.planner = planner or DynamicPlanningEngine()
        self.task_manager = task_manager or TaskManager()
        self.checkpoints = checkpoint_store or CheckpointResumeStore()
        self.jobs = jobs or LongRunningJobManager()
        self.recovery = recovery or FailureRecoveryEngine()
        self.last_plan: AgentPlan | None = None
        self.last_job_id: str | None = None

    def accept_goal(
        self,
        objective: str,
        *,
        intent: str = "execute",
        success_criteria: tuple[str, ...] = ("Objective completed and verified.",),
        constraints: tuple[str, ...] = (),
        priority: int = 0,
        authority_context: str = "user",
        metadata: dict[str, Any] | None = None,
    ) -> AgentGoal:
        result = self.intake.intake(
            objective,
            intent=intent,
            priority=priority,
            constraints=constraints,
            success_criteria=success_criteria,
            authority_context=authority_context,
            metadata=metadata,
        )
        if not result.accepted or result.objective is None:
            raise ValueError("; ".join(result.errors) or "Goal intake rejected.")
        return AgentGoal(
            objective=result.objective.objective,
            intent=result.objective.intent,
            priority=str(result.objective.priority),
            constraints=tuple(result.objective.constraints),
            success_criteria=tuple(result.objective.success_criteria),
            authority_context="user",
            metadata=dict(result.objective.metadata),
        )

    def run(
        self,
        goal: AgentGoal,
        *,
        execute_step: Callable[[DecomposedGoal], Any],
        verify_step: Callable[[DecomposedGoal, Any], bool],
        user_confirmation: bool = False,
        job_id: str | None = None,
        runtime_id: str = "main",
        max_steps: int = 100,
    ) -> AutonomousWorkResult:
        if not isinstance(goal, AgentGoal):
            raise TypeError("goal must be AgentGoal.")
        if not callable(execute_step) or not callable(verify_step):
            raise TypeError("execute_step and verify_step must be callable.")
        if max_steps < 1:
            raise ValueError("max_steps must be >= 1.")

        execution_metadata = {
            "user_confirmation": user_confirmation,
            "authority_context": goal.authority_context,
        }

        decomposition = self.decomposer.decompose(goal)
        if not decomposition.success or not decomposition.goals:
            return self._failed(goal.objective, "", "Goal decomposition failed.")

        plan = self.planner.create_plan(decomposition.goals)
        self.last_plan = plan

        orchestration = AgentTaskOrchestrator(self.task_manager).create_tasks(plan)
        state_goal = self._find_task_goal(orchestration.plan_id)
        if state_goal is None:
            return self._failed(goal.objective, plan.plan_id, "Task orchestration state missing.")

        current_job_id = job_id or f"sahibex-{plan.plan_id}"
        self.last_job_id = current_job_id
        if current_job_id not in self.jobs._jobs:
            self.jobs.create(current_job_id, goal.objective, runtime_id)
        current_status = self.jobs.get(current_job_id).status
        if current_status == "created":
            self.jobs.start(current_job_id)

        completed_titles: set[str] = set()
        results: dict[str, Any] = {}
        resumed = False

        if current_job_id in self.checkpoints._records:
            try:
                state = self.checkpoints.resume_state(current_job_id, runtime_id=runtime_id)
                if state.get("objective") != goal.objective:
                    return self._failed(goal.objective, plan.plan_id, "Checkpoint objective identity mismatch.")
                completed_titles = set(state.get("completed_titles", ()))
                results = dict(state.get("results", {}))
                resumed = bool(completed_titles)
                if current_status in {"failed", "paused"}:
                    self.jobs.resume(current_job_id)
            except (KeyError, ValueError, RuntimeError):
                return self._failed(goal.objective, plan.plan_id, "Checkpoint failed integrity, identity, or lifecycle validation.")

        completed_ids: set[str] = set()
        for task in state_goal.tasks:
            linked = self._agent_goal_for_task(task, plan)
            if linked and linked.title in completed_titles and task.status == TaskStatus.PENDING:
                task.mark_ready()
                task.mark_running()
                task.complete(results.get(linked.title))
                completed_ids.add(linked.goal_id)

        attempts = 0
        completed_titles: list[str] = []
        failed_titles: list[str] = []
        last_checkpoint: int | None = None

        while len(completed_ids) < len(plan.goals) and attempts < max_steps:
            ready = self.task_manager.ready_tasks(state_goal.goal_id)
            ready = [
                task for task in ready
                if (linked := self._agent_goal_for_task(task, plan))
                and linked.goal_id not in completed_ids
            ]
            if not ready:
                self.jobs.fail(current_job_id, "No ready task; dependency graph cannot progress.")
                return AutonomousWorkResult(
                    False, "BLOCKED", goal.objective, plan.plan_id,
                    tuple(completed_titles), tuple(failed_titles),
                    verification_status="NOT_VERIFIED", attempts=attempts,
                    checkpoint_sequence=last_checkpoint, resumed=resumed,
                    error="No ready task; dependency graph cannot progress.",
                    metadata=execution_metadata,
                )

            task = ready[0]
            linked = self._agent_goal_for_task(task, plan)
            assert linked is not None
            if task.status == TaskStatus.PENDING:
                task.mark_ready()
            task.mark_running()
            attempts += 1

            try:
                output = execute_step(linked)
                verified = bool(verify_step(linked, output))
            except Exception as exc:
                failure = self.recovery.detect(
                    f"{current_job_id}:{linked.goal_id}:{attempts}",
                    "result", "autonomous_work", "medium", str(exc)
                )
                if self.recovery.can_retry(failure, task.retry_count, task.max_retries):
                    task.fail(str(exc))
                    task.retry()
                    continue
                task.fail(str(exc))
                failed_titles.append(linked.title)
                self.jobs.fail(current_job_id, str(exc))
                return AutonomousWorkResult(
                    False, "FAILED", goal.objective, plan.plan_id,
                    tuple(completed_titles), tuple(failed_titles),
                    verification_status="NOT_VERIFIED", attempts=attempts,
                    checkpoint_sequence=last_checkpoint, resumed=resumed,
                    error=str(exc), metadata=execution_metadata,
                )

            if not verified:
                failure = self.recovery.detect(
                    f"{current_job_id}:{linked.goal_id}:{attempts}",
                    "result", "verification", "medium",
                    "Step result failed verification."
                )
                if self.recovery.can_retry(failure, task.retry_count, task.max_retries):
                    task.fail("Step result failed verification.")
                    task.retry()
                    continue
                task.fail("Step result failed verification.")
                failed_titles.append(linked.title)
                self.jobs.fail(current_job_id, "Step result failed verification.")
                return AutonomousWorkResult(
                    False, "FAILED", goal.objective, plan.plan_id,
                    tuple(completed_titles), tuple(failed_titles),
                    verification_status="FAILED", attempts=attempts,
                    checkpoint_sequence=last_checkpoint, resumed=resumed,
                    error="Step result failed verification.",
                    metadata=execution_metadata,
                )

            task.complete(output)
            completed_ids.add(linked.goal_id)
            results[linked.title] = output
            completed_titles.append(linked.title)

            cp = self.checkpoints.save(
                current_job_id, runtime_id, attempts,
                {"objective": goal.objective, "completed_titles": sorted(completed_titles), "results": results},
            )
            last_checkpoint = cp.sequence

        if len(completed_ids) != len(plan.goals):
            self.jobs.fail(current_job_id, "Autonomous execution step limit reached.")
            return AutonomousWorkResult(
                False, "FAILED", goal.objective, plan.plan_id,
                tuple(completed_titles), tuple(failed_titles),
                verification_status="NOT_VERIFIED", attempts=attempts,
                checkpoint_sequence=last_checkpoint, resumed=resumed,
                error="Autonomous execution step limit reached.",
                metadata=execution_metadata,
            )

        final_ok = all(
            self._agent_goal_for_task(task, plan) is None
            or task.status == TaskStatus.COMPLETED
            for task in state_goal.tasks
        )
        if not final_ok:
            self.jobs.fail(current_job_id, "Final task-state verification failed.")
            return self._failed(goal.objective, plan.plan_id, "Final task-state verification failed.")

        self.jobs.complete(current_job_id)
        return AutonomousWorkResult(
            True, "COMPLETED", goal.objective, plan.plan_id,
            tuple(completed_titles), tuple(failed_titles),
            response=results.get(plan.goals[-1].title),
            verification_status="VERIFIED", attempts=attempts,
            checkpoint_sequence=last_checkpoint, resumed=resumed,
            metadata={**execution_metadata, "controlled_until_done": True, "final_task_state_verified": True},
        )

    def _find_task_goal(self, plan_id: str):
        for goal in self.task_manager.goals.values():
            if goal.title == f"Agent Plan {plan_id}":
                return goal
        return None

    @staticmethod
    def _agent_goal_for_task(task, plan: AgentPlan) -> DecomposedGoal | None:
        # AgentTaskOrchestrator preserves plan order and task titles.
        for item in plan.goals:
            if item.title == task.title:
                return item
        return None

    @staticmethod
    def _failed(objective: str, plan_id: str, error: str) -> AutonomousWorkResult:
        return AutonomousWorkResult(
            False, "FAILED", objective, plan_id, (), (),
            verification_status="NOT_VERIFIED", error=error
        )

    @staticmethod
    def grants_permission() -> bool:
        return False

    @staticmethod
    def modifies_constitution() -> bool:
        return False
