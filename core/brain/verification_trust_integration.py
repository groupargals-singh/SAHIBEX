from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class MasterVerificationTrustResult:
    """
    Result of integrating verification and specialist trust
    context with the master brain.

    This object carries verification/trust context only.
    It does not grant permissions or execute actions.
    """

    success: bool
    verification_id: str
    brain_id: str
    trust_status: str
    confidence: float
    summary: str
    integration_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be a boolean.")

        if not isinstance(self.verification_id, str):
            raise TypeError(
                "verification_id must be a string."
            )

        if not self.verification_id.strip():
            raise ValueError(
                "verification_id must be a non-empty string."
            )

        if not isinstance(self.brain_id, str):
            raise TypeError("brain_id must be a string.")

        if not self.brain_id.strip():
            raise ValueError(
                "brain_id must be a non-empty string."
            )

        if not isinstance(self.trust_status, str):
            raise TypeError(
                "trust_status must be a string."
            )

        if not self.trust_status.strip():
            raise ValueError(
                "trust_status must be a non-empty string."
            )

        if not isinstance(self.confidence, (int, float)):
            raise TypeError(
                "confidence must be a number."
            )

        if isinstance(self.confidence, bool):
            raise TypeError(
                "confidence must be a number."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1."
            )

        if not isinstance(self.summary, str):
            raise TypeError("summary must be a string.")

        if not self.summary.strip():
            raise ValueError(
                "summary must be a non-empty string."
            )

        if (
            not isinstance(self.integration_id, str)
            or not self.integration_id.strip()
        ):
            raise ValueError(
                "integration_id must be a non-empty string."
            )


class MasterVerificationTrustIntegration:
    """
    Contract-level integration of verification and trust
    context into the master brain.

    This layer validates and normalizes verification/trust
    references. It does not grant permissions, execute
    actions, modify trust, or replace the root authority.
    """

    def integrate(
        self,
        *,
        verification_id: str,
        brain_id: str,
        trust_status: str,
        confidence: float,
        summary: str,
    ) -> MasterVerificationTrustResult:
        if not isinstance(verification_id, str):
            raise TypeError(
                "verification_id must be a string."
            )

        normalized_verification_id = (
            verification_id.strip()
        )

        if not normalized_verification_id:
            raise ValueError(
                "verification_id must be a non-empty string."
            )

        if not isinstance(brain_id, str):
            raise TypeError(
                "brain_id must be a string."
            )

        normalized_brain_id = brain_id.strip()

        if not normalized_brain_id:
            raise ValueError(
                "brain_id must be a non-empty string."
            )

        if not isinstance(trust_status, str):
            raise TypeError(
                "trust_status must be a string."
            )

        normalized_trust_status = trust_status.strip().lower()

        if not normalized_trust_status:
            raise ValueError(
                "trust_status must be a non-empty string."
            )

        if not isinstance(confidence, (int, float)):
            raise TypeError(
                "confidence must be a number."
            )

        if isinstance(confidence, bool):
            raise TypeError(
                "confidence must be a number."
            )

        if not 0.0 <= confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1."
            )

        if not isinstance(summary, str):
            raise TypeError(
                "summary must be a string."
            )

        normalized_summary = summary.strip()

        if not normalized_summary:
            raise ValueError(
                "summary must be a non-empty string."
            )

        return MasterVerificationTrustResult(
            success=True,
            verification_id=normalized_verification_id,
            brain_id=normalized_brain_id,
            trust_status=normalized_trust_status,
            confidence=float(confidence),
            summary=normalized_summary,
        )
