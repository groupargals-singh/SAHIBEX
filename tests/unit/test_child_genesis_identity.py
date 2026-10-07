from core.brain.child_genesis_identity import ChildGenesisIdentityEngine


def main() -> None:
    engine = ChildGenesisIdentityEngine

    identity = engine.generate(
        child_name="TestChild",
        purpose="Testing future Child identity",
        parent_brain_id="sahibex-mother",
    )

    assert engine.validate(identity)

    # Every core identity must be unique.
    values = {
        identity.brain_id,
        identity.soul_id,
        identity.constitution_id,
        identity.memory_namespace,
        identity.security_identity,
        identity.audit_identity,
    }

    assert len(values) == 6

    # Child identity must not reuse Mother's identity.
    assert engine.is_identity_separate_from_mother(
        identity,
        mother_brain_id="mother-brain",
        mother_soul_id="mother-soul",
        mother_constitution_id="mother-constitution",
        mother_memory_namespace="mother-memory",
        mother_security_identity="mother-security",
        mother_audit_identity="mother-audit",
    )

    # Empty required values must fail.
    try:
        engine.generate(
            child_name="",
            purpose="invalid",
            parent_brain_id="sahibex-mother",
        )
        raise AssertionError("empty child name was accepted")
    except ValueError as exc:
        assert str(exc) == "child_name_required"

    # Identity engine must never authorize or activate a Child.
    assert not engine.creates_child()
    assert not engine.activates_child()
    assert not engine.authorizes_child()

    print("SAHIBEX CHILD GENESIS IDENTITY ENGINE TEST: PASS")


if __name__ == "__main__":
    main()
