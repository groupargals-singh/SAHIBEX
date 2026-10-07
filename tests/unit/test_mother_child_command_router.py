from core.brain.mother_child_command_router import (
    CommandRouteDecision,
    CommandType,
    MotherChildCommand,
    MotherChildCommandRouter,
)


def main() -> None:
    router = MotherChildCommandRouter()

    # Autonomous cognition
    command = MotherChildCommand(
        command_id="cmd-001",
        child_brain_id="child-brain-001",
        command_type=CommandType.RESEARCH,
        payload="research AI security",
    )

    result = router.route(command)

    assert result.allowed is True
    assert result.decision == CommandRouteDecision.ROUTE

    # Protected request without Mother approval
    command = MotherChildCommand(
        command_id="cmd-002",
        child_brain_id="child-brain-001",
        command_type=CommandType.PROTECTED_REQUEST,
        payload="write approved research result",
    )

    result = router.route(command)

    assert result.allowed is False
    assert result.decision == CommandRouteDecision.REQUIRE_AUTHORITY

    # Protected request with Mother approval
    result = router.route(
        command,
        mother_approved=True,
    )

    assert result.allowed is True
    assert result.decision == CommandRouteDecision.ROUTE

    # Sensitive request without Human approval
    command = MotherChildCommand(
        command_id="cmd-003",
        child_brain_id="child-brain-001",
        command_type=CommandType.SOUL_REQUEST,
        payload="propose soul change",
    )

    result = router.route(command)

    assert result.allowed is False
    assert result.decision == CommandRouteDecision.REQUIRE_HUMAN

    # Sensitive request with Human approval
    result = router.route(
        command,
        human_approved=True,
    )

    assert result.allowed is True
    assert result.decision == CommandRouteDecision.ROUTE

    # Missing identity
    command = MotherChildCommand(
        command_id="",
        child_brain_id="child-brain-001",
        command_type=CommandType.RESEARCH,
        payload="research",
    )

    result = router.route(command)

    assert result.allowed is False
    assert result.decision == CommandRouteDecision.DENY

    # Missing child identity
    command = MotherChildCommand(
        command_id="cmd-004",
        child_brain_id="",
        command_type=CommandType.RESEARCH,
        payload="research",
    )

    result = router.route(command)

    assert result.allowed is False

    # Missing payload
    command = MotherChildCommand(
        command_id="cmd-005",
        child_brain_id="child-brain-001",
        command_type=CommandType.RESEARCH,
        payload="",
    )

    result = router.route(command)

    assert result.allowed is False

    # Critical authority boundaries
    assert not router.can_child_route_to_mother_as_authority()
    assert not router.can_child_grant_itself_authority()
    assert not router.can_external_model_grant_authority()
    assert not router.can_tool_grant_authority()
    assert not router.can_execute_command()
    assert not router.can_modify_child_soul()
    assert not router.can_modify_child_constitution()

    assert router.requires_mother_for_protected()
    assert router.requires_human_for_sensitive()
    assert router.fails_closed()

    print("SAHIBEX MOTHER CHILD COMMAND ROUTER TEST: PASS")


if __name__ == "__main__":
    main()
