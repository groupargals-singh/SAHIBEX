from __future__ import annotations

from core.brain.master_integration import (
    MasterBrainIntegration,
    MasterBrainIntegrationResult,
)


def main() -> None:
    integration = MasterBrainIntegration()

    result = integration.process(
        intent="research",
        summary="Research task prepared for SAHIBEX master brain.",
    )

    assert isinstance(result, MasterBrainIntegrationResult)

    assert result.success is True
    assert result.intent == "research"
    assert result.summary == (
        "Research task prepared for SAHIBEX master brain."
    )
    assert result.result_id

    second_result = integration.process(
        intent="think",
        summary="Reasoning task prepared.",
    )

    assert second_result.success is True
    assert second_result.intent == "think"
    assert second_result.result_id != result.result_id

    try:
        integration.process(
            intent="",
            summary="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty intent must be rejected."
        )

    try:
        integration.process(
            intent="research",
            summary="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty summary must be rejected."
        )

    try:
        integration.process(
            intent="",
            summary="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty intent and summary must be rejected."
        )

    fields = MasterBrainIntegrationResult.__dataclass_fields__

    forbidden_fields = {
        "api_key",
        "credential",
        "authorization_token",
        "permission_grant",
    }

    assert forbidden_fields.isdisjoint(fields.keys())

    assert not hasattr(
        MasterBrainIntegration,
        "grant_permission",
    )

    assert not hasattr(
        MasterBrainIntegration,
        "execute_action",
    )

    print(
        "SAHIBEX 6N-1 MASTER BRAIN INTEGRATION CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
