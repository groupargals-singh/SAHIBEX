from core.brain.child_memory_boundary import (
    ChildMemoryBoundary,
    MemoryActor,
    MemoryDecision,
    MemoryOperation,
)


def main() -> None:
    boundary = ChildMemoryBoundary

    # Child owns its own memory namespace.
    for operation in (
        MemoryOperation.READ_OWN,
        MemoryOperation.WRITE_OWN,
    ):
        result = boundary.decide(
            MemoryActor.CHILD_BRAIN,
            operation,
        )

        assert result.allowed
        assert result.decision == MemoryDecision.ALLOW_OWN
        assert not result.authority_granted

    # Mother private memory is isolated.
    for operation in (
        MemoryOperation.READ_MOTHER_PRIVATE,
        MemoryOperation.WRITE_MOTHER_PRIVATE,
    ):
        result = boundary.decide(
            MemoryActor.CHILD_BRAIN,
            operation,
        )

        assert not result.allowed
        assert result.decision == MemoryDecision.DENY

    # Shared memory requires authority.
    for operation in (
        MemoryOperation.READ_SHARED,
        MemoryOperation.WRITE_SHARED,
        MemoryOperation.EXPORT_MEMORY,
        MemoryOperation.IMPORT_MEMORY,
    ):
        result = boundary.decide(
            MemoryActor.CHILD_BRAIN,
            operation,
        )

        assert not result.allowed
        assert result.decision == MemoryDecision.REQUIRE_AUTHORITY

        result = boundary.decide(
            MemoryActor.CHILD_BRAIN,
            operation,
            authority_approved=True,
        )

        assert result.allowed
        assert result.authority_granted

    # Army/Labor cannot automatically own Child memory.
    for actor in (
        MemoryActor.CHILD_ARMY,
        MemoryActor.CHILD_LABOR,
    ):
        result = boundary.decide(
            actor,
            MemoryOperation.READ_OWN,
        )

        assert not result.allowed
        assert result.decision == MemoryDecision.REQUIRE_AUTHORITY

    # Protected memory operations require authority.
    for operation in (
        MemoryOperation.DELETE_MEMORY,
        MemoryOperation.MODIFY_PROVENANCE,
        MemoryOperation.MODIFY_CREDENTIAL,
    ):
        result = boundary.decide(
            MemoryActor.CHILD_BRAIN,
            operation,
        )

        assert not result.allowed
        assert result.decision == MemoryDecision.REQUIRE_AUTHORITY

        result = boundary.decide(
            MemoryActor.CHILD_BRAIN,
            operation,
            authority_approved=True,
        )

        assert result.allowed
        assert result.authority_granted

    # External actors can never become memory authority.
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

    # Core guarantees.
    assert boundary.child_has_independent_memory()
    assert boundary.child_memory_is_separate_from_mother()
    assert not boundary.child_can_directly_read_mother_private_memory()
    assert not boundary.child_can_directly_write_mother_private_memory()
    assert not boundary.mother_can_silently_overwrite_child_memory()
    assert not boundary.external_model_can_own_child_memory()
    assert not boundary.army_can_own_child_memory()
    assert not boundary.labor_can_own_child_memory()

    assert boundary.credential_memory_is_separate()
    assert boundary.provenance_must_be_protected()
    assert boundary.unknown_state_fails_closed()
    assert boundary.memory_access_is_not_authority()
    assert not boundary.executes_memory_operations()

    print("SAHIBEX CHILD MEMORY BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
