from security.audit.brain_trust_lifecycle import (
    BrainTrustEvidenceLifecycle,
    BrainTrustEvidenceLifecycleDecision,
)


def test_active_lifecycle() -> None:
    decision = BrainTrustEvidenceLifecycleDecision(
        BrainTrustEvidenceLifecycle.ACTIVE,
        "Authenticated evidence is currently valid.",
    )

    assert decision.lifecycle == (
        BrainTrustEvidenceLifecycle.ACTIVE
    )
    assert decision.is_active is True
    assert decision.is_invalidated is False


def test_invalidated_lifecycle() -> None:
    decision = BrainTrustEvidenceLifecycleDecision(
        BrainTrustEvidenceLifecycle.INVALIDATED,
        "Evidence was explicitly invalidated.",
    )

    assert decision.lifecycle == (
        BrainTrustEvidenceLifecycle.INVALIDATED
    )
    assert decision.is_active is False
    assert decision.is_invalidated is True


def test_lifecycle_states_are_explicit() -> None:
    assert BrainTrustEvidenceLifecycle.ACTIVE.value == "active"
    assert (
        BrainTrustEvidenceLifecycle.INVALIDATED.value
        == "invalidated"
    )


def test_reason_is_preserved() -> None:
    reason = "Evidence invalidated after security review."

    decision = BrainTrustEvidenceLifecycleDecision(
        BrainTrustEvidenceLifecycle.INVALIDATED,
        reason,
    )

    assert decision.reason == reason


def test_empty_reason_is_rejected() -> None:
    try:
        BrainTrustEvidenceLifecycleDecision(
            BrainTrustEvidenceLifecycle.ACTIVE,
            "",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty lifecycle reason must be rejected."
        )


def test_invalid_lifecycle_type_is_rejected() -> None:
    try:
        BrainTrustEvidenceLifecycleDecision(
            "active",
            "Invalid type test.",
        )
    except TypeError:
        pass
    else:
        raise AssertionError(
            "Invalid lifecycle type must be rejected."
        )


def test_lifecycle_has_no_authority_controls() -> None:
    public_names = set(
        dir(BrainTrustEvidenceLifecycleDecision)
    )

    forbidden = {
        "grant_permission",
        "authorize",
        "execute",
        "change_constitution",
        "override_parent",
        "change_capabilities",
    }

    assert not (public_names & forbidden)


def run_all_tests() -> None:
    test_active_lifecycle()
    test_invalidated_lifecycle()
    test_lifecycle_states_are_explicit()
    test_reason_is_preserved()
    test_empty_reason_is_rejected()
    test_invalid_lifecycle_type_is_rejected()
    test_lifecycle_has_no_authority_controls()

    print(
        "SAHIBEX 6P-26 TRUST EVIDENCE LIFECYCLE "
        "CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    run_all_tests()
