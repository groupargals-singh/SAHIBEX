from core.agent_state import (
    AgentState,
    AgentStatus,
    VALID_TRANSITIONS,
)


def main() -> None:
    state = AgentState()

    assert state.status == AgentStatus.CREATED
    assert state.agent_id
    assert state.terminal is False
    assert state.active is False

    assert state.can_transition_to(
        AgentStatus.READY
    )

    state.transition(
        AgentStatus.READY,
        reason="Agent initialized.",
    )

    assert state.status == AgentStatus.READY
    assert state.reason == "Agent initialized."

    state.transition(
        AgentStatus.PLANNING,
        reason="Planning objective.",
    )

    assert state.status == AgentStatus.PLANNING
    assert state.active is True

    state.transition(
        AgentStatus.RUNNING,
        reason="Plan approved for execution.",
    )

    state.transition(
        AgentStatus.WAITING_APPROVAL,
        reason="Protected action requires approval.",
    )

    assert state.status == AgentStatus.WAITING_APPROVAL

    state.transition(
        AgentStatus.RUNNING,
        reason="User approval received.",
    )

    state.transition(
        AgentStatus.VERIFYING,
        reason="Execution finished.",
    )

    assert state.status == AgentStatus.VERIFYING

    state.transition(
        AgentStatus.COMPLETED,
        reason="Completion criteria verified.",
    )

    assert state.status == AgentStatus.COMPLETED
    assert state.terminal is True
    assert state.active is False

    try:
        state.transition(AgentStatus.RUNNING)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Terminal agent must not restart."
        )

    recovery_state = AgentState()
    recovery_state.transition(AgentStatus.READY)
    recovery_state.transition(AgentStatus.PLANNING)
    recovery_state.transition(AgentStatus.RUNNING)
    recovery_state.transition(AgentStatus.RECOVERING)

    assert recovery_state.status == AgentStatus.RECOVERING

    recovery_state.transition(
        AgentStatus.READY,
        reason="Recovery completed.",
    )

    assert recovery_state.status == AgentStatus.READY

    blocked_state = AgentState()
    blocked_state.transition(AgentStatus.READY)
    blocked_state.transition(AgentStatus.PLANNING)
    blocked_state.transition(AgentStatus.BLOCKED)

    assert blocked_state.status == AgentStatus.BLOCKED

    blocked_state.transition(
        AgentStatus.RECOVERING,
        reason="Recovering blocked agent.",
    )

    assert blocked_state.status == AgentStatus.RECOVERING

    paused_state = AgentState()
    paused_state.transition(AgentStatus.READY)
    paused_state.transition(AgentStatus.PAUSED)

    assert paused_state.status == AgentStatus.PAUSED

    paused_state.transition(AgentStatus.READY)

    assert paused_state.status == AgentStatus.READY

    assert AgentStatus.CREATED in VALID_TRANSITIONS
    assert AgentStatus.COMPLETED in VALID_TRANSITIONS
    assert AgentStatus.CANCELLED in VALID_TRANSITIONS

    for terminal_status in (
        AgentStatus.COMPLETED,
        AgentStatus.CANCELLED,
    ):
        assert not VALID_TRANSITIONS[terminal_status]

    try:
        AgentState(
            agent_id="",
            status=AgentStatus.CREATED,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty agent_id must raise ValueError."
        )

    try:
        AgentState(
            status="created",
        )
    except TypeError:
        pass
    else:
        raise AssertionError(
            "Invalid status type must raise TypeError."
        )

    print(
        "SAHIBEX 6P-2 AGENT STATE & LIFECYCLE TEST: PASS"
    )


if __name__ == "__main__":
    main()
