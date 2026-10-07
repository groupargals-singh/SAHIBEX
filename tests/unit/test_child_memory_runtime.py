from core.brain.child_memory_runtime import (
    ChildMemoryRuntime,
    MemoryDecision,
    MemoryOperation,
)


def main() -> None:
    memory = ChildMemoryRuntime(
        child_brain_id="child-brain-test",
        memory_namespace="child-memory-test",
    )

    result = memory.write("name", "SAHIBEX Child")
    assert result.allowed is True
    assert memory.contains("name")
    assert memory.read("name") == "SAHIBEX Child"

    result = memory.delete(
        "name",
        authority_approved=False,
    )
    assert result.allowed is False
    assert result.decision == MemoryDecision.REQUIRE_AUTHORITY
    assert memory.contains("name")

    result = memory.delete(
        "name",
        authority_approved=True,
    )
    assert result.allowed is True
    assert not memory.contains("name")

    result = memory.write_credential(
        "api_key",
        "secret",
        authority_approved=False,
    )
    assert result.allowed is False

    result = memory.write_credential(
        "api_key",
        "secret",
        authority_approved=True,
    )
    assert result.allowed is True

    assert (
        memory.read_credential(
            "api_key",
            authority_approved=False,
        )
        is None
    )

    assert (
        memory.read_credential(
            "api_key",
            authority_approved=True,
        )
        == "secret"
    )

    result = memory.evaluate(
        MemoryOperation.READ_MOTHER_PRIVATE
    )
    assert result.allowed is False
    assert result.decision == MemoryDecision.DENY

    assert not memory.can_access_mother_private_memory()
    assert not memory.memory_access_grants_authority()
    assert memory.credentials_are_separate()
    assert memory.memory_is_child_isolated()
    assert not memory.can_self_authorize_memory_access()
    assert not memory.grants_authority()

    print("SAHIBEX CHILD MEMORY RUNTIME TEST: PASS")


if __name__ == "__main__":
    main()
