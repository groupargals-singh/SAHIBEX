from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.brain.child_birth_specification import ChildBirthSpecification


@dataclass(frozen=True)
class ChildBirthValidationResult:
    valid: bool
    errors: tuple[str, ...]


class ChildBirthSpecificationValidator:
    """
    Validates a future Child Brain birth specification.

    This validator does NOT create or activate a Child Brain.
    """

    @staticmethod
    def validate(specification: dict[str, Any]) -> ChildBirthValidationResult:
        errors: list[str] = []

        required_fields = (
            ChildBirthSpecification.required_identity_fields()
            + ChildBirthSpecification.required_constitution_fields()
            + ChildBirthSpecification.required_brain_components()
            + ChildBirthSpecification.required_authority_boundaries()
            + ChildBirthSpecification.required_security_boundaries()
            + ChildBirthSpecification.required_birth_gates()
            + ChildBirthSpecification.required_post_birth_verification()
        )

        for field in required_fields:
            if field not in specification:
                errors.append(f"missing:{field}")

        forbidden_inheritance = specification.get(
            "forbidden_inheritance",
            (),
        )

        for item in forbidden_inheritance:
            if item in ChildBirthSpecification.forbidden_inheritance():
                errors.append(f"forbidden_inheritance:{item}")

        forbidden_state = specification.get("birth_state")

        if forbidden_state in ChildBirthSpecification.forbidden_child_states():
            errors.append(f"forbidden_state:{forbidden_state}")

        if specification.get("mother_identity_reused", False):
            errors.append("mother_identity_reused")

        if specification.get("mother_soul_reused", False):
            errors.append("mother_soul_reused")

        if specification.get("mother_constitution_reused", False):
            errors.append("mother_constitution_reused")

        if specification.get("authority_escalation", False):
            errors.append("authority_escalation")

        if specification.get("self_authorization", False):
            errors.append("self_authorization")

        if specification.get("human_authorization", False) is not True:
            errors.append("missing_human_authorization")

        if specification.get("mother_authorization", False) is not True:
            errors.append("missing_mother_authorization")

        if specification.get("security_valid", False) is not True:
            errors.append("security_validation_failed")

        if specification.get("constitutional_valid", False) is not True:
            errors.append("constitutional_validation_failed")

        if specification.get("verification_complete", False) is not True:
            errors.append("verification_incomplete")

        if specification.get("audit_ready", False) is not True:
            errors.append("audit_not_ready")

        return ChildBirthValidationResult(
            valid=not errors,
            errors=tuple(errors),
        )

    @staticmethod
    def can_create_child(specification: dict[str, Any]) -> bool:
        """
        Validator only.

        A valid specification does NOT authorize or create a Child.
        """
        result = ChildBirthSpecificationValidator.validate(specification)

        if not result.valid:
            return False

        return False

    @staticmethod
    def can_activate_child(specification: dict[str, Any]) -> bool:
        """
        Activation is never performed by this validator.
        """
        return False

    @staticmethod
    def fails_closed() -> bool:
        return True

    @staticmethod
    def creates_child() -> bool:
        return False

    @staticmethod
    def activates_child() -> bool:
        return False


def main() -> None:
    validator = ChildBirthSpecificationValidator

    invalid_spec = {}

    result = validator.validate(invalid_spec)

    assert not result.valid
    assert result.errors

    assert validator.fails_closed()
    assert not validator.creates_child()
    assert not validator.activates_child()
    assert not validator.can_create_child(invalid_spec)
    assert not validator.can_activate_child(invalid_spec)

    print("SAHIBEX CHILD BIRTH SPECIFICATION VALIDATOR TEST: PASS")


if __name__ == "__main__":
    main()
