from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class PlanningToolIntegrationResult:
    """
    Result of preparing a planning-to-tool integration reference.

    This object links a plan and task to a selected tool.
    It does not execute the tool or grant permission.
    """

    success: bool
    plan_id: str
    tool_name: str
    task_id: str
    integration_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be a boolean.")

        if not isinstance(self.plan_id, str):
            raise TypeError("plan_id must be a string.")

        if not self.plan_id.strip():
            raise ValueError(
                "plan_id must be a non-empty string."
            )

        if not isinstance(self.tool_name, str):
            raise TypeError("tool_name must be a string.")

        if not self.tool_name.strip():
            raise ValueError(
                "tool_name must be a non-empty string."
            )

        if not isinstance(self.task_id, str):
            raise TypeError("task_id must be a string.")

        if not self.task_id.strip():
            raise ValueError(
                "task_id must be a non-empty string."
            )

        if (
            not isinstance(self.integration_id, str)
            or not self.integration_id.strip()
        ):
            raise ValueError(
                "integration_id must be a non-empty string."
            )


class PlanningToolIntegration:
    """
    Contract-level integration between planning and tools.

    This layer prepares a validated reference connecting
    a plan, task, and tool.

    It does not execute tools, grant permissions, bypass
    approval, or modify the root permission system.
    """

    def prepare(
        self,
        *,
        plan_id: str,
        tool_name: str,
        task_id: str,
    ) -> PlanningToolIntegrationResult:
        if not isinstance(plan_id, str):
            raise TypeError("plan_id must be a string.")

        normalized_plan_id = plan_id.strip()

        if not normalized_plan_id:
            raise ValueError(
                "plan_id must be a non-empty string."
            )

        if not isinstance(tool_name, str):
            raise TypeError("tool_name must be a string.")

        normalized_tool_name = tool_name.strip()

        if not normalized_tool_name:
            raise ValueError(
                "tool_name must be a non-empty string."
            )

        if not isinstance(task_id, str):
            raise TypeError("task_id must be a string.")

        normalized_task_id = task_id.strip()

        if not normalized_task_id:
            raise ValueError(
                "task_id must be a non-empty string."
            )

        return PlanningToolIntegrationResult(
            success=True,
            plan_id=normalized_plan_id,
            tool_name=normalized_tool_name,
            task_id=normalized_task_id,
        )
