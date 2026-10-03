from __future__ import annotations

from core.brain.planning_tool_integration import (
    PlanningToolIntegration,
    PlanningToolIntegrationResult,
)


def main() -> None:
    integration = PlanningToolIntegration()

    result = integration.prepare(
        plan_id="plan-001",
        tool_name="read_file",
        task_id="task-001",
    )

    assert isinstance(
        result,
        PlanningToolIntegrationResult,
    )

    assert result.success is True
    assert result.plan_id == "plan-001"
    assert result.tool_name == "read_file"
    assert result.task_id == "task-001"
    assert result.integration_id

    second_result = integration.prepare(
        plan_id="plan-002",
        tool_name="search_local_files",
        task_id="task-002",
    )

    assert second_result.success is True
    assert second_result.integration_id != result.integration_id

    try:
        integration.prepare(
            plan_id="",
            tool_name="read_file",
            task_id="task-001",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty plan ID must be rejected."
        )

    try:
        integration.prepare(
            plan_id="plan-001",
            tool_name="",
            task_id="task-001",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty tool name must be rejected."
        )

    try:
        integration.prepare(
            plan_id="plan-001",
            tool_name="read_file",
            task_id="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty task ID must be rejected."
        )

    fields = PlanningToolIntegrationResult.__dataclass_fields__

    forbidden_fields = {
        "api_key",
        "credential",
        "authorization_token",
        "permission_grant",
    }

    assert forbidden_fields.isdisjoint(fields.keys())

    assert not hasattr(
        PlanningToolIntegration,
        "grant_permission",
    )

    assert not hasattr(
        PlanningToolIntegration,
        "execute_tool",
    )

    print(
        "SAHIBEX 6N-5 PLANNING TOOL INTEGRATION CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
