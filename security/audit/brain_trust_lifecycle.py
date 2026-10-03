from __future__ import annotations

from enum import Enum


class BrainTrustEvidenceLifecycle(str, Enum):
    ACTIVE = "active"
    INVALIDATED = "invalidated"


class BrainTrustEvidenceLifecycleDecision:
    """
    Lifecycle state for authenticated brain trust evidence.

    This state describes evidence validity only.

    It does NOT:
    - grant permission
    - grant authority
    - execute actions
    - change brain trust status
    - modify capabilities
    - modify the constitution
    """

    def __init__(
        self,
        lifecycle: BrainTrustEvidenceLifecycle,
        reason: str,
    ) -> None:
        if not isinstance(
            lifecycle,
            BrainTrustEvidenceLifecycle,
        ):
            raise TypeError(
                "lifecycle must be a BrainTrustEvidenceLifecycle."
            )

        if (
            not isinstance(reason, str)
            or not reason.strip()
        ):
            raise ValueError(
                "A lifecycle reason is required."
            )

        self.lifecycle = lifecycle
        self.reason = reason.strip()

    @property
    def is_active(self) -> bool:
        return (
            self.lifecycle
            == BrainTrustEvidenceLifecycle.ACTIVE
        )

    @property
    def is_invalidated(self) -> bool:
        return (
            self.lifecycle
            == BrainTrustEvidenceLifecycle.INVALIDATED
        )
