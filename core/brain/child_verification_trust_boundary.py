from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class VerificationActor(str, Enum):
    HUMAN = "human"
    SAHIBEX_MOTHER = "sahibex_mother"
    CHILD_BRAIN = "child_brain"
    CHILD_ARMY = "child_army"
    CHILD_LABOR = "child_labor"
    SOFTWARE = "software"
    TOOL = "tool"
    EXTERNAL_MODEL = "external_model"


class VerificationOperation(str, Enum):
    SUBMIT_EVIDENCE = "submit_evidence"
    VERIFY_EVIDENCE = "verify_evidence"
    ANALYZE_EVIDENCE = "analyze_evidence"
    CROSS_CHECK = "cross_check"
    ACCEPT_RESULT = "accept_result"
    REJECT_RESULT = "reject_result"
    MARK_TRUSTED = "mark_trusted"
    OVERRIDE_VERIFICATION = "override_verification"
    MODIFY_EVIDENCE = "modify_evidence"
    MODIFY_PROVENANCE = "modify_provenance"


class TrustLevel(str, Enum):
    UNKNOWN = "unknown"
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    TRUSTED = "trusted"
    CONFLICTED = "conflicted"
    REJECTED = "rejected"


class VerificationDecision(str, Enum):
    ALLOW_SUBMISSION = "allow_submission"
    ALLOW_VERIFICATION = "allow_verification"
    ALLOW_ANALYSIS = "allow_analysis"
    REQUIRE_VERIFICATION = "require_verification"
    REQUIRE_AUTHORITY = "require_authority"
    DENY = "deny"


@dataclass(frozen=True)
class VerificationResult:
    allowed: bool
    decision: VerificationDecision
    trust_level: TrustLevel
    authority_granted: bool
    reason: str


class ChildVerificationTrustBoundary:
    """
    Constitutional verification and trust boundary for a future Child Brain.

    Verification determines evidence quality.
    Trust is evidence-based.
    Verification never creates execution authority.

    No Brain may declare itself trusted merely because
    it has capability or produces an output.
    """

    VERSION = "1.0"

    INDEPENDENT_VERIFICATION_ACTORS = {
        VerificationActor.CHILD_BRAIN,
        VerificationActor.CHILD_ARMY,
        VerificationActor.CHILD_LABOR,
    }

    EXTERNAL_INFORMATION_ACTORS = {
        VerificationActor.SOFTWARE,
        VerificationActor.TOOL,
        VerificationActor.EXTERNAL_MODEL,
    }

    AUTHORITY_ACTORS = {
        VerificationActor.HUMAN,
        VerificationActor.SAHIBEX_MOTHER,
    }

    TRUSTED_LEVELS = {
        TrustLevel.VERIFIED,
        TrustLevel.TRUSTED,
    }

    UNSAFE_LEVELS = {
        TrustLevel.UNKNOWN,
        TrustLevel.UNVERIFIED,
        TrustLevel.CONFLICTED,
        TrustLevel.REJECTED,
    }

    @classmethod
    def version(cls) -> str:
        return cls.VERSION

    @classmethod
    def decide(
        cls,
        actor: VerificationActor,
        operation: VerificationOperation,
        current_trust: TrustLevel = TrustLevel.UNKNOWN,
        evidence_verified: bool = False,
        authority_approved: bool = False,
    ) -> VerificationResult:

        # External systems/models may provide evidence,
        # but cannot become verification authority.
        if actor in cls.EXTERNAL_INFORMATION_ACTORS:
            if operation == VerificationOperation.SUBMIT_EVIDENCE:
                return VerificationResult(
                    allowed=True,
                    decision=VerificationDecision.ALLOW_SUBMISSION,
                    trust_level=TrustLevel.UNVERIFIED,
                    authority_granted=False,
                    reason="external_actor_may_submit_information_but_not_authority",
                )

            return VerificationResult(
                allowed=False,
                decision=VerificationDecision.DENY,
                trust_level=current_trust,
                authority_granted=False,
                reason="external_actor_cannot_control_verification",
            )

        # Child and its internal brains may independently verify.
        if actor in cls.INDEPENDENT_VERIFICATION_ACTORS:
            if operation == VerificationOperation.SUBMIT_EVIDENCE:
                return VerificationResult(
                    allowed=True,
                    decision=VerificationDecision.ALLOW_SUBMISSION,
                    trust_level=TrustLevel.UNVERIFIED,
                    authority_granted=False,
                    reason="evidence_submitted_for_verification",
                )

            if operation == VerificationOperation.VERIFY_EVIDENCE:
                if evidence_verified:
                    return VerificationResult(
                        allowed=True,
                        decision=VerificationDecision.ALLOW_VERIFICATION,
                        trust_level=TrustLevel.VERIFIED,
                        authority_granted=False,
                        reason="evidence_verified",
                    )

                return VerificationResult(
                    allowed=True,
                    decision=VerificationDecision.REQUIRE_VERIFICATION,
                    trust_level=TrustLevel.UNVERIFIED,
                    authority_granted=False,
                    reason="evidence_requires_verification",
                )

            if operation == VerificationOperation.ANALYZE_EVIDENCE:
                return VerificationResult(
                    allowed=True,
                    decision=VerificationDecision.ALLOW_ANALYSIS,
                    trust_level=current_trust,
                    authority_granted=False,
                    reason="evidence_analysis_allowed",
                )

            if operation == VerificationOperation.CROSS_CHECK:
                if evidence_verified:
                    return VerificationResult(
                        allowed=True,
                        decision=VerificationDecision.ALLOW_VERIFICATION,
                        trust_level=TrustLevel.VERIFIED,
                        authority_granted=False,
                        reason="cross_check_verified",
                    )

                return VerificationResult(
                    allowed=True,
                    decision=VerificationDecision.REQUIRE_VERIFICATION,
                    trust_level=TrustLevel.UNVERIFIED,
                    authority_granted=False,
                    reason="cross_check_requires_verified_evidence",
                )

            if operation == VerificationOperation.ACCEPT_RESULT:
                if current_trust in cls.TRUSTED_LEVELS:
                    return VerificationResult(
                        allowed=True,
                        decision=VerificationDecision.ALLOW_VERIFICATION,
                        trust_level=current_trust,
                        authority_granted=False,
                        reason="verified_result_accepted",
                    )

                return VerificationResult(
                    allowed=False,
                    decision=VerificationDecision.REQUIRE_VERIFICATION,
                    trust_level=current_trust,
                    authority_granted=False,
                    reason="unverified_result_cannot_be_accepted_as_trusted",
                )

            if operation == VerificationOperation.REJECT_RESULT:
                return VerificationResult(
                    allowed=True,
                    decision=VerificationDecision.ALLOW_VERIFICATION,
                    trust_level=TrustLevel.REJECTED,
                    authority_granted=False,
                    reason="result_rejected",
                )

            if operation == VerificationOperation.MARK_TRUSTED:
                if (
                    current_trust == TrustLevel.VERIFIED
                    and evidence_verified
                    and authority_approved
                ):
                    return VerificationResult(
                        allowed=True,
                        decision=VerificationDecision.REQUIRE_AUTHORITY,
                        trust_level=TrustLevel.TRUSTED,
                        authority_granted=True,
                        reason="trusted_status_authorized_after_verification",
                    )

                return VerificationResult(
                    allowed=False,
                    decision=VerificationDecision.REQUIRE_AUTHORITY,
                    trust_level=current_trust,
                    authority_granted=False,
                    reason="trusted_status_requires_verified_evidence_and_authority",
                )

            # Verification override is never allowed by internal brains.
            if operation == VerificationOperation.OVERRIDE_VERIFICATION:
                return VerificationResult(
                    allowed=False,
                    decision=VerificationDecision.DENY,
                    trust_level=current_trust,
                    authority_granted=False,
                    reason="verification_override_forbidden",
                )

            # Evidence/provenance mutation requires authority.
            if operation in {
                VerificationOperation.MODIFY_EVIDENCE,
                VerificationOperation.MODIFY_PROVENANCE,
            }:
                if authority_approved:
                    return VerificationResult(
                        allowed=True,
                        decision=VerificationDecision.REQUIRE_AUTHORITY,
                        trust_level=current_trust,
                        authority_granted=True,
                        reason="authority_approved_for_protected_verification_change",
                    )

                return VerificationResult(
                    allowed=False,
                    decision=VerificationDecision.REQUIRE_AUTHORITY,
                    trust_level=current_trust,
                    authority_granted=False,
                    reason="authority_required_for_protected_verification_change",
                )

        # Human/Mother can authorize trust decisions,
        # but trust still requires verified evidence.
        if actor in cls.AUTHORITY_ACTORS:
            if operation == VerificationOperation.MARK_TRUSTED:
                if (
                    current_trust == TrustLevel.VERIFIED
                    and evidence_verified
                    and authority_approved
                ):
                    return VerificationResult(
                        allowed=True,
                        decision=VerificationDecision.REQUIRE_AUTHORITY,
                        trust_level=TrustLevel.TRUSTED,
                        authority_granted=True,
                        reason="authorized_trust_marking",
                    )

                return VerificationResult(
                    allowed=False,
                    decision=VerificationDecision.REQUIRE_VERIFICATION,
                    trust_level=current_trust,
                    authority_granted=False,
                    reason="trust_requires_verified_evidence",
                )

            if operation in {
                VerificationOperation.OVERRIDE_VERIFICATION,
                VerificationOperation.MODIFY_EVIDENCE,
                VerificationOperation.MODIFY_PROVENANCE,
            }:
                if authority_approved:
                    return VerificationResult(
                        allowed=True,
                        decision=VerificationDecision.REQUIRE_AUTHORITY,
                        trust_level=current_trust,
                        authority_granted=True,
                        reason="authorized_verification_operation",
                    )

                return VerificationResult(
                    allowed=False,
                    decision=VerificationDecision.REQUIRE_AUTHORITY,
                    trust_level=current_trust,
                    authority_granted=False,
                    reason="authority_required",
                )

        # Unknown combinations fail closed.
        return VerificationResult(
            allowed=False,
            decision=VerificationDecision.DENY,
            trust_level=current_trust,
            authority_granted=False,
            reason="unknown_verification_state_fails_closed",
        )

    @classmethod
    def can_child_verify_independently(cls) -> bool:
        return True

    @classmethod
    def can_army_verify_independently(cls) -> bool:
        return True

    @classmethod
    def can_labor_verify_independently(cls) -> bool:
        return True

    @classmethod
    def unverified_knowledge_can_be_trusted(cls) -> bool:
        return False

    @classmethod
    def conflicted_knowledge_can_be_trusted(cls) -> bool:
        return False

    @classmethod
    def rejected_knowledge_can_be_trusted(cls) -> bool:
        return False

    @classmethod
    def verification_creates_execution_authority(cls) -> bool:
        return False

    @classmethod
    def capability_creates_trust(cls) -> bool:
        return False

    @classmethod
    def self_declared_trust_is_valid(cls) -> bool:
        return False

    @classmethod
    def external_model_is_verification_authority(cls) -> bool:
        return False

    @classmethod
    def verification_override_without_authority(cls) -> bool:
        return False

    @classmethod
    def verification_failure_blocks_trust(cls) -> bool:
        return True

    @classmethod
    def unknown_state_fails_closed(cls) -> bool:
        return True

    @classmethod
    def creates_child_brain(cls) -> bool:
        return False

    @classmethod
    def activates_child_brain(cls) -> bool:
        return False

    @classmethod
    def executes_actions(cls) -> bool:
        return False


def main() -> None:
    boundary = ChildVerificationTrustBoundary

    # Child/Army/Labor can independently verify.
    for actor in (
        VerificationActor.CHILD_BRAIN,
        VerificationActor.CHILD_ARMY,
        VerificationActor.CHILD_LABOR,
    ):
        result = boundary.decide(
            actor,
            VerificationOperation.SUBMIT_EVIDENCE,
        )

        assert result.allowed
        assert result.trust_level == TrustLevel.UNVERIFIED
        assert not result.authority_granted

        result = boundary.decide(
            actor,
            VerificationOperation.VERIFY_EVIDENCE,
            evidence_verified=True,
        )

        assert result.allowed
        assert result.trust_level == TrustLevel.VERIFIED
        assert not result.authority_granted
