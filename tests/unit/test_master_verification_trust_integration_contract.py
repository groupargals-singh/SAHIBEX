from __future__ import annotations

from core.brain.verification_trust_integration import (
    MasterVerificationTrustIntegration,
    MasterVerificationTrustResult,
)


def main() -> None:
    integration = MasterVerificationTrustIntegration()

    result = integration.integrate(
        verification_id="verification-001",
        brain_id="brain-001",
        trust_status="trusted",
        confidence=0.95,
        summary="Verification and trust context prepared.",
    )

    assert isinstance(
        result,
        MasterVerificationTrustResult,
    )

    assert result.success is True
    assert result.verification_id == "verification-001"
    assert result.brain_id == "brain-001"
    assert result.trust_status == "trusted"
    assert result.confidence == 0.95
    assert result.summary == (
        "Verification and trust context prepared."
    )
    assert result.integration_id

    second_result = integration.integrate(
        verification_id="verification-002",
        brain_id="brain-002",
        trust_status="verified",
        confidence=0.80,
        summary="Additional verification context.",
    )

    assert second_result.success is True
    assert second_result.integration_id != (
        result.integration_id
    )

    try:
        integration.integrate(
            verification_id="",
            brain_id="brain-001",
            trust_status="trusted",
            confidence=0.95,
            summary="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty verification ID must be rejected."
        )

    try:
        integration.integrate(
            verification_id="verification-001",
            brain_id="",
            trust_status="trusted",
            confidence=0.95,
            summary="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty brain ID must be rejected."
        )

    try:
        integration.integrate(
            verification_id="verification-001",
            brain_id="brain-001",
            trust_status="",
            confidence=0.95,
            summary="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty trust status must be rejected."
        )

    try:
        integration.integrate(
            verification_id="verification-001",
            brain_id="brain-001",
            trust_status="trusted",
            confidence=-0.1,
            summary="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Confidence below 0 must be rejected."
        )

    try:
        integration.integrate(
            verification_id="verification-001",
            brain_id="brain-001",
            trust_status="trusted",
            confidence=1.1,
            summary="test",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Confidence above 1 must be rejected."
        )

    try:
        integration.integrate(
            verification_id="verification-001",
            brain_id="brain-001",
            trust_status="trusted",
            confidence=0.95,
            summary="",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty summary must be rejected."
        )

    fields = MasterVerificationTrustResult.__dataclass_fields__

    forbidden_fields = {
        "api_key",
        "credential",
        "authorization_token",
        "permission_grant",
    }

    assert forbidden_fields.isdisjoint(fields.keys())

    assert not hasattr(
        MasterVerificationTrustIntegration,
        "grant_permission",
    )

    assert not hasattr(
        MasterVerificationTrustIntegration,
        "execute_action",
    )

    print(
        "SAHIBEX 6N-7 VERIFICATION TRUST INTEGRATION "
        "CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
