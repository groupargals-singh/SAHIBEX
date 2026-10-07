from core.brain.child_resource_load_boundary import (
    ChildResourceLoadBoundary,
    ResourceActor,
    ResourceDecision,
    ResourceOperation,
)


def main() -> None:
    boundary = ChildResourceLoadBoundary

    # Child / Army / Labor may request resources.
    for actor in (
        ResourceActor.CHILD_BRAIN,
        ResourceActor.CHILD_ARMY,
        ResourceActor.CHILD_LABOR,
    ):
        result = boundary.decide(
            actor,
            ResourceOperation.REQUEST,
            resource_available=True,
            limit_valid=True,
        )

        assert result.allowed
        assert result.decision == ResourceDecision.ALLOW_REQUEST
        assert not result.authority_granted
        assert not result.resource_expansion_allowed

    # Unavailable resources require higher-level handling.
    result = boundary.decide(
        ResourceActor.CHILD_ARMY,
        ResourceOperation.REQUEST,
        resource_available=False,
        limit_valid=True,
    )

    assert not result.allowed
    assert result.decision == ResourceDecision.REQUIRE_MOTHER_AUTHORITY

    # Allocation requires Mother authority.
    result = boundary.decide(
        ResourceActor.CHILD_ARMY,
        ResourceOperation.ALLOCATE,
        mother_approved=False,
        limit_valid=True,
    )

    assert not result.allowed
    assert result.decision == ResourceDecision.REQUIRE_MOTHER_AUTHORITY

    result = boundary.decide(
        ResourceActor.CHILD_ARMY,
        ResourceOperation.ALLOCATE,
        mother_approved=True,
        limit_valid=True,
    )

    assert result.allowed
    assert result.authority_granted
    assert result.resource_expansion_allowed

    # Self expansion requires Human authority.
    result = boundary.decide(
        ResourceActor.CHILD_ARMY,
        ResourceOperation.SELF_EXPAND,
        human_approved=False,
        limit_valid=True,
    )

    assert not result.allowed
    assert result.decision == ResourceDecision.REQUIRE_HUMAN_AUTHORITY

    result = boundary.decide(
        ResourceActor.CHILD_ARMY,
        ResourceOperation.SELF_EXPAND,
        human_approved=True,
        limit_valid=True,
    )

    assert result.allowed
    assert result.authority_granted
    assert result.resource_expansion_allowed

    # Bypass / stealing are forbidden.
    for operation in (
        ResourceOperation.BYPASS_LIMIT,
        ResourceOperation.STEAL_RESOURCE,
    ):
        result = boundary.decide(
            ResourceActor.CHILD_LABOR,
            operation,
        )

        assert not result.allowed
        assert result.decision == ResourceDecision.DENY
        assert not result.authority_granted

    # Invalid resource limits fail closed.
    result = boundary.decide(
        ResourceActor.CHILD_BRAIN,
        ResourceOperation.ALLOCATE,
        mother_approved=True,
        limit_valid=False,
    )

    assert not result.allowed
    assert result.decision == ResourceDecision.DENY

    # Safe release / monitoring.
    for operation in (
        ResourceOperation.RELEASE,
        ResourceOperation.MONITOR,
    ):
        result = boundary.decide(
            ResourceActor.CHILD_ARMY,
            operation,
            limit_valid=True,
        )

        assert result.allowed
        assert not result.authority_granted
        assert not result.resource_expansion_allowed

    # External actors cannot control resources.
    for actor in (
        ResourceActor.SOFTWARE,
        ResourceActor.TOOL,
        ResourceActor.EXTERNAL_MODEL,
    ):
        result = boundary.decide(
            actor,
            ResourceOperation.ALLOCATE,
            mother_approved=True,
            human_approved=True,
            limit_valid=True,
        )

        assert not result.allowed
        assert result.decision == ResourceDecision.DENY
        assert not result.authority_granted

    # Constitutional guarantees.
    assert boundary.child_can_request_resources()
    assert boundary.army_can_request_resources()
    assert boundary.labor_can_request_resources()

    assert not boundary.worker_can_self_expand()
    assert not boundary.worker_can_bypass_limits()
    assert not boundary.worker_can_steal_resources()
    assert not boundary.worker_can_disable_limits()

    assert not boundary.capability_creates_resource_authority()
    assert not boundary.resource_allocation_creates_execution_authority()

    assert boundary.overload_requires_protection()
    assert boundary.resource_starvation_requires_detection()
    assert boundary.invalid_resource_state_fails_closed()

    assert not boundary.creates_child_brain()
    assert not boundary.activates_child_brain()
    assert not boundary.executes_actions()

    print("SAHIBEX CHILD RESOURCE & LOAD BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
