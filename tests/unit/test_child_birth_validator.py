from core.brain.child_birth_validator import ChildBirthSpecificationValidator


def main() -> None:
    validator = ChildBirthSpecificationValidator

    # Empty specification must fail closed.
    result = validator.validate({})

    assert not result.valid
    assert result.errors

    # Unsafe inheritance must be rejected.
    unsafe = {
        "forbidden_inheritance": ("mother_brain_identity",),
    }

    result = validator.validate(unsafe)

    assert not result.valid
    assert "forbidden_inheritance:mother_brain_identity" in result.errors

    # Forbidden birth state must be rejected.
    invalid_state = {
        "birth_state": "partial_birth",
    }

    result = validator.validate(invalid_state)

    assert not result.valid
    assert "forbidden_state:partial_birth" in result.errors

    # Authority escalation must be rejected.
    escalation = {
        "authority_escalation": True,
    }

    result = validator.validate(escalation)

    assert not result.valid
    assert "authority_escalation" in result.errors

    # Self-authorization must be rejected.
    self_auth = {
        "self_authorization": True,
    }

    result = validator.validate(self_auth)

    assert not result.valid
    assert "self_authorization" in result.errors

    # Validator itself must NEVER create or activate a Child.
    assert validator.fails_closed()
    assert not validator.creates_child()
    assert not validator.activates_child()

    print("SAHIBEX CHILD BIRTH VALIDATOR TEST: PASS")


if __name__ == "__main__":
    main()
