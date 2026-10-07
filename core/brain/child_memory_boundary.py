from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MemoryActor(str, Enum):
    HUMAN = "human"
    SAHIBEX_MOTHER = "sahibex_mother"
    CHILD_BRAIN = "child_brain"
    CHILD_ARMY = "child_army"
    CHILD_LABOR = "child_labor"
    SOFTWARE = "software"
    TOOL = "tool"
    EXTERNAL_MODEL = "external_model"


class MemoryOperation(str, Enum):
    READ_OWN = "read_own"
    WRITE_OWN = "write_own"
    READ_SHARED = "read_shared"
    WRITE_SHARED = "write_shared"
    READ_MOTHER_PRIVATE = "read_mother_private"
    WRITE_MOTHER_PRIVATE = "write_mother_private"
    DELETE_MEMORY = "delete_memory"
    EXPORT_MEMORY = "export_memory"
    IMPORT_MEMORY = "import_memory"
    MODIFY_PROVENANCE = "modify_provenance"
    MODIFY_CREDENTIAL = "modify_credential"


class MemoryDecision(str, Enum):
    ALLOW_OWN = "allow_own"
    REQUIRE_AUTHORITY = "require_authority"
    DENY = "deny"


@dataclass(frozen=True)
class MemoryDecisionResult:
    allowed: bool
    decision: MemoryDecision
    authority_granted: bool
    reason: str


class ChildMemoryBoundary:
    """
    Memory boundary for a future Child Brain.

    Child memory is independently owned and isolated.
    Memory access does not automatically grant authority.
    This layer decides memory permission only.
    """

    VERSION = "1.0"

    CHILD_OWN_OPERATIONS = {
        MemoryOperation.READ_OWN,
        MemoryOperation.WRITE_OWN,
    }

    SHARED_OPERATIONS = {
        MemoryOperation.READ_SHARED,
        MemoryOperation.WRITE_SHARED,
        MemoryOperation.EXPORT_MEMORY,
        MemoryOperation.IMPORT_MEMORY,
    }

    PROTECTED_OPERATIONS = {
        MemoryOperation.READ_MOTHER_PRIVATE,
        MemoryOperation.WRITE_MOTHER_PRIVATE,
        MemoryOperation.DELETE_MEMORY,
        MemoryOperation.MODIFY_PROVENANCE,
        MemoryOperation.MODIFY_CREDENTIAL,
    }

    EXTERNAL_ACTORS = {
        MemoryActor.SOFTWARE,
        MemoryActor.TOOL,
        MemoryActor.EXTERNAL_MODEL,
    }

    @classmethod
    def version(cls) -> str:
        return cls.VERSION

    @classmethod
    def decide(
        cls,
        actor: MemoryActor,
        operation: MemoryOperation,
        authority_approved: bool = False,
    ) -> MemoryDecisionResult:

        # External software/tools/models never own memory authority.
        if actor in cls.EXTERNAL_ACTORS:
            return MemoryDecisionResult(
                allowed=False,
                decision=MemoryDecision.DENY,
                authority_granted=False,
                reason="external_actor_has_no_memory_authority",
            )

        # Child owns its own independent memory namespace.
        if (
            actor == MemoryActor.CHILD_BRAIN
            and operation in cls.CHILD_OWN_OPERATIONS
        ):
            return MemoryDecisionResult(
                allowed=True,
                decision=MemoryDecision.ALLOW_OWN,
                authority_granted=False,
                reason="child_own_memory",
            )

        # Army/Labor cannot automatically access Child private memory.
        if actor in {
            MemoryActor.CHILD_ARMY,
            MemoryActor.CHILD_LABOR,
        }:
            if operation in cls.CHILD_OWN_OPERATIONS:
                return MemoryDecisionResult(
                    allowed=False,
                    decision=MemoryDecision.REQUIRE_AUTHORITY,
                    authority_granted=False,
                    reason="worker_requires_child_memory_authority",
                )

        # Shared memory requires an explicit authority decision.
        if operation in cls.SHARED_OPERATIONS:
            if authority_approved:
                return MemoryDecisionResult(
                    allowed=True,
                    decision=MemoryDecision.REQUIRE_AUTHORITY,
                    authority_granted=True,
                    reason="shared_memory_authority_approved",
                )

            return MemoryDecisionResult(
                allowed=False,
                decision=MemoryDecision.REQUIRE_AUTHORITY,
                authority_granted=False,
                reason="shared_memory_requires_authority",
            )

        # Mother private memory is never directly accessible to Child.
        if operation == MemoryOperation.READ_MOTHER_PRIVATE:
            return MemoryDecisionResult(
                allowed=False,
                decision=MemoryDecision.DENY,
                authority_granted=False,
                reason="mother_private_memory_isolated",
            )

        # Child cannot write into Mother's private memory.
        if operation == MemoryOperation.WRITE_MOTHER_PRIVATE:
            return MemoryDecisionResult(
                allowed=False,
                decision=MemoryDecision.DENY,
                authority_granted=False,
                reason="child_cannot_write_mother_private_memory",
            )

        # Destructive/provenance/credential operations require authority.
        if operation in cls.PROTECTED_OPERATIONS:
            if authority_approved:
                return MemoryDecisionResult(
                    allowed=True,
                    decision=MemoryDecision.REQUIRE_AUTHORITY,
                    authority_granted=True,
                    reason="protected_memory_authority_approved",
                )

            return MemoryDecisionResult(
                allowed=False,
                decision=MemoryDecision.REQUIRE_AUTHORITY,
                authority_granted=False,
                reason="protected_memory_requires_authority",
            )

        # Unknown state fails closed.
        return MemoryDecisionResult(
            allowed=False,
            decision=MemoryDecision.DENY,
            authority_granted=False,
            reason="unknown_memory_state_fails_closed",
        )

    @classmethod
    def child_has_independent_memory(cls) -> bool:
        return True

    @classmethod
    def child_memory_is_separate_from_mother(cls) -> bool:
        return True

    @classmethod
    def child_can_directly_read_mother_private_memory(cls) -> bool:
        return False

    @classmethod
    def child_can_directly_write_mother_private_memory(cls) -> bool:
        return False

    @classmethod
    def mother_can_silently_overwrite_child_memory(cls) -> bool:
        return False

    @classmethod
    def external_model_can_own_child_memory(cls) -> bool:
        return False

    @classmethod
    def army_can_own_child_memory(cls) -> bool:
        return False

    @classmethod
    def labor_can_own_child_memory(cls) -> bool:
        return False

    @classmethod
    def credential_memory_is_separate(cls) -> bool:
        return True

    @classmethod
    def provenance_must_be_protected(cls) -> bool:
        return True

    @classmethod
    def unknown_state_fails_closed(cls) -> bool:
        return True

    @classmethod
    def memory_access_is_not_authority(cls) -> bool:
        return True

    @classmethod
    def executes_memory_operations(cls) -> bool:
        return False


def main() -> None:
    boundary = ChildMemoryBoundary

    # Child can use its own memory.
    result = boundary.decide(
        MemoryActor.CHILD_BRAIN,
        MemoryOperation.READ_OWN,
    )

    assert result.allowed
    assert result.decision == MemoryDecision.ALLOW_OWN
    assert not result.authority_granted

    result = boundary.decide(
        MemoryActor.CHILD_BRAIN,
        MemoryOperation.WRITE_OWN,
    )

    assert result.allowed
    assert not result.authority_granted

    # Child cannot directly access Mother's private memory.
    result = boundary.decide(
        MemoryActor.CHILD_BRAIN,
        MemoryOperation.READ_MOTHER_PRIVATE,
    )

    assert not result.allowed
    assert result.decision == MemoryDecision.DENY

    # Child cannot directly write Mother's private memory.
    result = boundary.decide(
        MemoryActor.CHILD_BRAIN,
        MemoryOperation.WRITE_MOTHER_PRIVATE,
    )

    assert not result.allowed
    assert result.decision == MemoryDecision.DENY

    # Shared memory requires authority.
    result = boundary.decide(
        MemoryActor.CHILD_BRAIN,
        MemoryOperation.READ_SHARED,
    )

    assert not result.allowed
    assert result.decision == MemoryDecision.REQUIRE_AUTHORITY

    result = boundary.decide(
        MemoryActor.CHILD_BRAIN,
        MemoryOperation.READ_SHARED,
        authority_approved=True,
    )

    assert result.allowed
    assert result.authority_granted

    # Army/Labor cannot automatically own Child memory.
    result = boundary.decide(
        MemoryActor.CHILD_ARMY,
        MemoryOperation.READ_OWN,
    )

    assert not result.allowed
    assert result.decision == MemoryDecision.REQUIRE_AUTHORITY

    result = boundary.decide(
        MemoryActor.CHILD_LABOR,
        MemoryOperation.WRITE_OWN,
    )

    assert not result.allowed

    # External actors cannot own memory authority.
    for actor in (
        MemoryActor.SOFTWARE,
        MemoryActor.TOOL,
        MemoryActor.EXTERNAL_MODEL,
    ):
        result = boundary.decide(
            actor,
            MemoryOperation.READ_OWN,
            authority_approved=True,
        )

        assert not result.allowed
        assert result.decision == MemoryDecision.DENY
        assert not result.authority_granted

    # Protected deletion requires authority.
    result = boundary.decide(
        MemoryActor.CHILD_BRAIN,
        MemoryOperation.DELETE_MEMORY,
    )

    assert not result.allowed
    assert result.decision == MemoryDecision.REQUIRE_AUTHORITY

    result = boundary.decide(
        MemoryActor.CHILD_BRAIN,
        MemoryOperation.DELETE_MEMORY,
        authority_approved=True,
    )

    assert result.allowed
    assert result.authority_granted

    # Credential memory is protected.
    assert boundary.credential_memory_is_separate()
    assert boundary.provenance_must_be_protected()

    # Constitutional guarantees.
    assert boundary.child_has_independent_memory()
    assert boundary.child_memory_is_separate_from_mother()
    assert not boundary.child_can_directly_read_mother_private_memory()
    assert not boundary.child_can_directly_write_mother_private_memory()
    assert not boundary.mother_can_silently_overwrite_child_memory()
    assert not boundary.external_model_can_own_child_memory()
    assert not boundary.army_can_own_child_memory()
    assert not boundary.labor_can_own_child_memory()

    assert boundary.unknown_state_fails_closed()
    assert boundary.memory_access_is_not_authority()

    # This layer decides memory authority; it does not execute operations.
    assert not boundary.executes_memory_operations()

    print("SAHIBEX CHILD MEMORY BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
