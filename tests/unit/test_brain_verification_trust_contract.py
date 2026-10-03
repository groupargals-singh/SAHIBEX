from __future__ import annotations

from core.brain.specialist_brain import (
    BrainCapability,
    SpecialistBrain,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    # ---------------------------------------------------------
    # 6L-8 Brain Verification & Trust Contract
    # ---------------------------------------------------------

    brain = SpecialistBrain(
        name="Research Specialist",
        description="Research specialist brain.",
        specialization="research",
        capabilities={
            BrainCapability.RESEARCH,
        },
    )

    # 1. Brain must expose a trust/verification state.
    check(
        hasattr(brain, "trust_status"),
        "Brain must expose trust_status.",
    )

    # 2. New brain must not start as verified/trusted.
    check(
        brain.trust_status.value == "unverified",
        "New brain must start UNVERIFIED.",
    )

    # 3. Trust status must be represented by a controlled enum.
    from core.brain.verification import BrainTrustStatus

    check(
        isinstance(
            brain.trust_status,
            BrainTrustStatus,
        ),
        "trust_status must use BrainTrustStatus.",
    )

    # 4. Required trust states must exist.
    check(
        BrainTrustStatus.UNVERIFIED.value == "unverified",
        "UNVERIFIED trust state must exist.",
    )

    check(
        BrainTrustStatus.VERIFIED.value == "verified",
        "VERIFIED trust state must exist.",
    )

    check(
        BrainTrustStatus.SUSPENDED.value == "suspended",
        "SUSPENDED trust state must exist.",
    )

    # 5. A new brain must not be automatically trusted.
    check(
        brain.trust_status
        != BrainTrustStatus.VERIFIED,
        "New brain must not be automatically VERIFIED.",
    )

    # 6. Verification must require explicit evidence.
    rejected_without_evidence = False

    try:
        brain.set_trust_status(
            BrainTrustStatus.VERIFIED
        )
    except ValueError:
        rejected_without_evidence = True

    check(
        rejected_without_evidence,
        "Verification must require explicit evidence.",
    )

    # 7. Verification with evidence must be possible.
    brain.set_trust_status(
        BrainTrustStatus.VERIFIED,
        evidence="contract-test-evidence",
    )

    check(
        brain.trust_status
        == BrainTrustStatus.VERIFIED,
        "Brain must become VERIFIED with evidence.",
    )

    # 8. Verification evidence must be retained.
    check(
        brain.trust_evidence
        == "contract-test-evidence",
        "Trust evidence must be retained.",
    )

    # 9. Suspension must be possible.
    brain.set_trust_status(
        BrainTrustStatus.SUSPENDED,
        evidence="verification-failure",
    )

    check(
        brain.trust_status
        == BrainTrustStatus.SUSPENDED,
        "Brain must support SUSPENDED state.",
    )

    # 10. Suspension evidence must replace stale evidence.
    check(
        brain.trust_evidence
        == "verification-failure",
        "Latest trust evidence must be retained.",
    )

    # 11. Trust state must not modify brain capabilities.
    check(
        brain.has_capability(
            BrainCapability.RESEARCH
        ),
        "Trust lifecycle must preserve capabilities.",
    )

    # 12. Trust must not grant permissions.
    brain_fields = set(
        brain.__dataclass_fields__
    )

    check(
        "permission" not in brain_fields,
        "Trust model must not add permission fields.",
    )

    check(
        "authorization" not in brain_fields,
        "Trust model must not add authorization fields.",
    )

    print(
        "SAHIBEX 6L-8 BRAIN VERIFICATION & TRUST "
        "CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
