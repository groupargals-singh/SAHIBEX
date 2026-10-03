from __future__ import annotations

from core.brain.permission_constitution_integration import (
    MasterPermissionConstitutionIntegration,
    MasterPermissionConstitutionResult,
)


def main() -> None:
    integration = MasterPermissionConstitutionIntegration()

    result = integration.evaluate(
        action="research",
        allowed=True,
        requires_confirmation=False,
        reason="Research is allowed within the autonomous boundary.",
    )

    assert isinstance(
        result,
        MasterPermissionConstitutionResult,
    )

    assert result.success is True
    assert result.action == "research"
    assert result.allowed is True
    assert result.requires_confirmation is False
    assert result.reason == (
        "Research is allowed within the autonomous boundary."
    )
    assert result.integration_id

    protected_result = integration.evaluate(
        action="write",
        allowed=False,
        requires_confirmation=True,
        reason="Protected action requires explicit user confirmation.",
    )

    assert protected_result.success is True
    assert protected_result.action == "write"
    assert protected_result.allowed is False
    assert protected_result.requires_confirmation is True

    assert protected_result.integration_id != (
        result.integration_id
    )

    try:
        integration.evaluate(
            action="",
            allowed=True,
            requires_confirmation=False,
            reason="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty action must be rejected."
        )

    try:
        integration.evaluate(
            action="research",
            allowed=True,
            requires_confirmation=False,
            reason="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty reason must be rejected."
        )

    try:
        integration.evaluate(
            action="research",
            allowed="yes",
            requires_confirmation=False,
            reason="test",
        )
    except TypeError:
        pass
    else:
        raise AssertionError(
            "Non-boolean allowed must be rejected."
        )

    try:
        integration.evaluate(
            action="research",
            allowed=True,
            requires_confirmation="no",
            reason="test",
        )
    except TypeError:
        pass
    else:
        raise AssertionError(
            "Non-boolean requires_confirmation must be rejected."
        )

    fields = (
        MasterPermissionConstitutionResult
        .__dataclass_fields__
    )

    forbidden_fields = {
        "api_key",
        "credential",
        "authorization_token",
        "permission_grant",
    }

    assert forbidden_fields.isdisjoint(fields.keys())

    assert not hasattr(
        MasterPermissionConstitutionIntegration,
        "grant_permission",
    )

    assert not hasattr(
        MasterPermissionConstitutionIntegration,
        "override_constitution",
    )

    assert not hasattr(
        MasterPermissionConstitutionIntegration,
        "execute_action",
    )

    print(
        "SAHIBEX 6N-8 PERMISSION CONSTITUTION "
        "INTEGRATION CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
