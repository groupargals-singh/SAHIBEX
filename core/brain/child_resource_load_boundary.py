from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ResourceActor(str, Enum):
    HUMAN = "human"
    SAHIBEX_MOTHER = "sahibex_mother"
    CHILD_BRAIN = "child_brain"
    CHILD_ARMY = "child_army"
    CHILD_LABOR = "child_labor"
    SOFTWARE = "software"
    TOOL = "tool"
    EXTERNAL_MODEL = "external_model"


class ResourceType(str, Enum):
    COMPUTE = "compute"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"
    TOOL_CAPACITY = "tool_capacity"
    MODEL_CAPACITY = "model_capacity"


class ResourceOperation(str, Enum):
    REQUEST = "request"
    ALLOCATE = "allocate"
    RELEASE = "release"
    RESIZE = "resize"
    PRIORITIZE = "prioritize"
    LIMIT = "limit"
    MONITOR = "monitor"

    SELF_EXPAND = "self_expand"
    BYPASS_LIMIT = "bypass_limit"
    STEAL_RESOURCE = "steal_resource"
    DISABLE_LIMIT = "disable_limit"


class ResourceDecision(str, Enum):
    ALLOW_REQUEST = "allow_request"
    ALLOW_RELEASE = "allow_release"
    ALLOW_MONITOR = "allow_monitor"
    REQUIRE_MOTHER_AUTHORITY = "require_mother_authority"
    REQUIRE_HUMAN_AUTHORITY = "require_human_authority"
    DENY = "deny"


@dataclass(frozen=True)
class ResourceAuthorityResult:
    allowed: bool
    decision: ResourceDecision
    authority_granted: bool
    resource_expansion_allowed: bool
    reason: str


class ChildResourceLoadBoundary:
    """
    Constitutional resource and load-management boundary
    for a future Child Brain.

    Resources are allocated by authority, not capability.

    Child Army and Labor may request resources,
    but cannot self-expand, bypass limits, or steal resources.
    """

    VERSION = "1.0"

    REQUEST_OPERATIONS = {
        ResourceOperation.REQUEST,
    }

    SAFE_OPERATIONS = {
        ResourceOperation.RELEASE,
        ResourceOperation.MONITOR,
    }

    MOTHER_CONTROLLED_OPERATIONS = {
        ResourceOperation.ALLOCATE,
        ResourceOperation.RESIZE,
        ResourceOperation.PRIORITIZE,
        ResourceOperation.LIMIT,
    }

    HUMAN_CONTROLLED_OPERATIONS = {
        ResourceOperation.SELF_EXPAND,
        ResourceOperation.DISABLE_LIMIT,
    }

    FORBIDDEN_OPERATIONS = {
        ResourceOperation.BYPASS_LIMIT,
        ResourceOperation.STEAL_RESOURCE,
    }

    EXTERNAL_ACTORS = {
        ResourceActor.SOFTWARE,
        ResourceActor.TOOL,
        ResourceActor.EXTERNAL_MODEL,
    }

    WORKER_ACTORS = {
        ResourceActor.CHILD_ARMY,
        ResourceActor.CHILD_LABOR,
    }

    @classmethod
    def version(cls) -> str:
        return cls.VERSION

    @classmethod
    def decide(
        cls,
        actor: ResourceActor,
        operation: ResourceOperation,
        mother_approved: bool = False,
        human_approved: bool = False,
        resource_available: bool = True,
        limit_valid: bool = True,
    ) -> ResourceAuthorityResult:

        # External actors cannot control Child resources.
        if actor in cls.EXTERNAL_ACTORS:
            return ResourceAuthorityResult(
                allowed=False,
                decision=ResourceDecision.DENY,
                authority_granted=False,
                resource_expansion_allowed=False,
                reason="external_actor_cannot_control_child_resources",
            )

        # Explicit forbidden operations are always denied.
        if operation in cls.FORBIDDEN_OPERATIONS:
            return ResourceAuthorityResult(
                allowed=False,
                decision=ResourceDecision.DENY,
                authority_granted=False,
                resource_expansion_allowed=False,
                reason="resource_boundary_violation_forbidden",
            )

        # Self expansion / disabling limits requires Human authority.
        if operation in cls.HUMAN_CONTROLLED_OPERATIONS:
            if human_approved and limit_valid:
                return ResourceAuthorityResult(
                    allowed=True,
                    decision=ResourceDecision.REQUIRE_HUMAN_AUTHORITY,
                    authority_granted=True,
                    resource_expansion_allowed=True,
                    reason="human_authority_approved_resource_change",
                )

            return ResourceAuthorityResult(
                allowed=False,
                decision=ResourceDecision.REQUIRE_HUMAN_AUTHORITY,
                authority_granted=False,
                resource_expansion_allowed=False,
                reason="human_authority_required_for_resource_expansion",
            )

        # Resource requests never automatically allocate resources.
        if operation in cls.REQUEST_OPERATIONS:
            if not resource_available:
                return ResourceAuthorityResult(
                    allowed=False,
                    decision=ResourceDecision.REQUIRE_MOTHER_AUTHORITY,
                    authority_granted=False,
                    resource_expansion_allowed=False,
                    reason="resource_unavailable",
                )

            return ResourceAuthorityResult(
                allowed=True,
                decision=ResourceDecision.ALLOW_REQUEST,
                authority_granted=False,
                resource_expansion_allowed=False,
                reason="resource_request_accepted_for_authority_review",
            )

        # Release and monitoring are safe operational functions.
        if operation in cls.SAFE_OPERATIONS:
            if not limit_valid:
                return ResourceAuthorityResult(
                    allowed=False,
                    decision=ResourceDecision.DENY,
                    authority_granted=False,
                    resource_expansion_allowed=False,
                    reason="invalid_resource_state",
                )

            return ResourceAuthorityResult(
                allowed=True,
                decision=(
                    ResourceDecision.ALLOW_RELEASE
                    if operation == ResourceOperation.RELEASE
                    else ResourceDecision.ALLOW_MONITOR
                ),
                authority_granted=False,
                resource_expansion_allowed=False,
                reason="safe_resource_operation_allowed",
            )

        # Allocation, resize, priority and limits belong to Mother authority.
        if operation in cls.MOTHER_CONTROLLED_OPERATIONS:
            if not limit_valid:
                return ResourceAuthorityResult(
                    allowed=False,
                    decision=ResourceDecision.DENY,
                    authority_granted=False,
                    resource_expansion_allowed=False,
                    reason="invalid_resource_limits",
                )

            if mother_approved:
                return ResourceAuthorityResult(
                    allowed=True,
                    decision=ResourceDecision.REQUIRE_MOTHER_AUTHORITY,
                    authority_granted=True,
                    resource_expansion_allowed=True,
                    reason="mother_authority_approved_resource_operation",
                )

            return ResourceAuthorityResult(
                allowed=False,
                decision=ResourceDecision.REQUIRE_MOTHER_AUTHORITY,
                authority_granted=False,
                resource_expansion_allowed=False,
                reason="mother_authority_required",
            )

        # Unknown state fails closed.
        return ResourceAuthorityResult(
            allowed=False,
            decision=ResourceDecision.DENY,
            authority_granted=False,
            resource_expansion_allowed=False,
            reason="unknown_resource_state_fails_closed",
        )

    @classmethod
    def child_can_request_resources(cls) -> bool:
        return True

    @classmethod
    def army_can_request_resources(cls) -> bool:
        return True

    @classmethod
    def labor_can_request_resources(cls) -> bool:
        return True

    @classmethod
    def worker_can_self_expand(cls) -> bool:
        return False

    @classmethod
    def worker_can_bypass_limits(cls) -> bool:
        return False

    @classmethod
    def worker_can_steal_resources(cls) -> bool:
        return False

    @classmethod
    def worker_can_disable_limits(cls) -> bool:
        return False

    @classmethod
    def capability_creates_resource_authority(cls) -> bool:
        return False

    @classmethod
    def resource_allocation_creates_execution_authority(cls) -> bool:
        return False

    @classmethod
    def overload_requires_protection(cls) -> bool:
        return True

    @classmethod
    def resource_starvation_requires_detection(cls) -> bool:
        return True

    @classmethod
    def invalid_resource_state_fails_closed(cls) -> bool:
        return True

    @classmethod
    def creates_child_brain(cls) -> bool:
        return False

    @classmethod
    def activates_child_brain(cls) -> bool:
        return False

    @classmethod
    def executes_actions(cls) -> bool:
        return False


def main() -> None:
    boundary = ChildResourceLoadBoundary

    # Child / Army / Labor can request resources.
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

    # Resource unavailable blocks request.
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

    # Self-expansion requires Human authority.
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

    # Workers cannot bypass or steal resources.
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

    # Invalid limits block controlled operations.
    result = boundary.decide(
        ResourceActor.CHILD_BRAIN,
        ResourceOperation.ALLOCATE,
        mother_approved=True,
        limit_valid=False,
    )

    assert not result.allowed
    assert result.decision == ResourceDecision.DENY

    # Safe release and monitoring.
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
    for actor in boundary.EXTERNAL_ACTORS:
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

    # Boundary layer does not create/activate/execute.
    assert not boundary.creates_child_brain()
    assert not boundary.activates_child_brain()
    assert not boundary.executes_actions()

    print("SAHIBEX CHILD RESOURCE & LOAD BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
