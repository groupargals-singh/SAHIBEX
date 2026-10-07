from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class ChildSecurityBoundary:
    security_identity: str
    brain_id: str
    soul_id: str
    constitution_id: str
    runtime_boundary: str
    filesystem_boundary: str
    network_boundary: str
    credential_boundary: str
    tool_boundary: str
    external_model_boundary: str
    security_controls: tuple[str, ...]
    failure_controls: tuple[str, ...]


class ChildSecurityBoundaryBuilder:
    """
    Builds and validates the security/isolation blueprint
    for a future Child Brain.

    This builder does NOT create, activate, authorize, or
    provision credentials for a Child.
    """

    VERSION = "1.0"

    SECURITY_CONTROLS = (
        "isolated_security_identity",
        "isolated_credentials",
        "isolated_runtime_boundary",
        "sandbox_boundary",
        "filesystem_boundary",
        "network_boundary",
        "tool_boundary",
        "external_model_boundary",
        "prompt_injection_defense",
        "credential_exfiltration_defense",
        "sandbox_escape_defense",
        "unauthorized_control_defense",
        "capability_is_not_authority",
        "least_privilege",
        "permission_gated_protected_action",
    )

    FAILURE_CONTROLS = (
        "security_failure_fails_closed",
        "unknown_security_state_fails_closed",
        "credential_boundary_failure_blocks_activation",
        "runtime_boundary_failure_blocks_activation",
        "filesystem_boundary_failure_blocks_activation",
        "network_boundary_failure_blocks_activation",
        "tool_boundary_failure_blocks_activation",
        "external_model_boundary_failure_blocks_activation",
        "prompt_injection_failure_blocks_protected_action",
        "sandbox_escape_detection_triggers_containment",
        "unauthorized_control_triggers_containment",
        "security_events_must_be_audited",
    )

    @classmethod
    def version(cls) -> str:
        return cls.VERSION

    @staticmethod
    def _new_security_id() -> str:
        return f"child-security-{uuid4()}"

    @classmethod
    def build(
        cls,
        brain_id: str,
        soul_id: str,
        constitution_id: str,
        security_identity: str | None = None,
    ) -> ChildSecurityBoundary:

        if not brain_id.strip():
            raise ValueError("brain_id_required")

        if not soul_id.strip():
            raise ValueError("soul_id_required")

        if not constitution_id.strip():
            raise ValueError("constitution_id_required")

        final_security_identity = (
            security_identity.strip()
            if security_identity
            else cls._new_security_id()
        )

        if not final_security_identity:
            raise ValueError("security_identity_required")

        return ChildSecurityBoundary(
            security_identity=final_security_identity,
            brain_id=brain_id.strip(),
            soul_id=soul_id.strip(),
            constitution_id=constitution_id.strip(),
            runtime_boundary="isolated-runtime",
            filesystem_boundary="isolated-filesystem",
            network_boundary="permission-gated-network",
            credential_boundary="isolated-credential-boundary",
            tool_boundary="permission-gated-tools",
            external_model_boundary="isolated-external-model-boundary",
            security_controls=cls.SECURITY_CONTROLS,
            failure_controls=cls.FAILURE_CONTROLS,
        )

    @classmethod
    def validate(cls, boundary: ChildSecurityBoundary) -> bool:
        required_values = (
            boundary.security_identity,
            boundary.brain_id,
            boundary.soul_id,
            boundary.constitution_id,
            boundary.runtime_boundary,
            boundary.filesystem_boundary,
            boundary.network_boundary,
            boundary.credential_boundary,
            boundary.tool_boundary,
            boundary.external_model_boundary,
        )

        if any(not value.strip() for value in required_values):
            return False

        if not boundary.security_identity.startswith(
            "child-security-"
        ):
            return False

        if not set(cls.SECURITY_CONTROLS).issubset(
            set(boundary.security_controls)
        ):
            return False

        if not set(cls.FAILURE_CONTROLS).issubset(
            set(boundary.failure_controls)
        ):
            return False

        return True

    @staticmethod
    def is_separate_from_mother(
        boundary: ChildSecurityBoundary,
        mother_security_identity: str,
    ) -> bool:
        return boundary.security_identity != mother_security_identity

    @staticmethod
    def can_issue_credentials() -> bool:
        return False

    @staticmethod
    def can_grant_authority() -> bool:
        return False

    @staticmethod
    def can_escalate_authority() -> bool:
        return False

    @staticmethod
    def can_disable_security_boundary() -> bool:
        return False

    @staticmethod
    def can_bypass_verification() -> bool:
        return False

    @staticmethod
    def can_bypass_audit() -> bool:
        return False

    @staticmethod
    def fails_closed() -> bool:
        return True

    @staticmethod
    def requires_security_audit() -> bool:
        return True

    @staticmethod
    def creates_child() -> bool:
        return False

    @staticmethod
    def activates_child() -> bool:
        return False

    @staticmethod
    def authorizes_child() -> bool:
        return False


def main() -> None:
    builder = ChildSecurityBoundaryBuilder

    boundary = builder.build(
        brain_id="child-brain-test",
        soul_id="child-soul-test",
        constitution_id="child-constitution-test",
    )

    assert builder.version() == "1.0"
    assert builder.validate(boundary)

    assert boundary.security_identity.startswith(
        "child-security-"
    )

    assert boundary.brain_id == "child-brain-test"
    assert boundary.soul_id == "child-soul-test"
    assert boundary.constitution_id == "child-constitution-test"

    assert builder.is_separate_from_mother(
        boundary,
        mother_security_identity="mother-security",
    )

    assert builder.fails_closed()
    assert builder.requires_security_audit()

    assert not builder.can_issue_credentials()
    assert not builder.can_grant_authority()
    assert not builder.can_escalate_authority()
    assert not builder.can_disable_security_boundary()
    assert not builder.can_bypass_verification()
    assert not builder.can_bypass_audit()

    assert not builder.creates_child()
    assert not builder.activates_child()
    assert not builder.authorizes_child()

    print("SAHIBEX CHILD SECURITY BOUNDARY TEST: PASS")


if __name__ == "__main__":
    main()
