from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from security.audit.brain_trust_provenance import (
    BrainTrustProvenance,
)
from security.audit.brain_trust_replacement_store import (
    BrainTrustReplacementStore,
)


@dataclass(frozen=True)
class BrainTrustLineageVerification:
    """
    Result of persistent trust-evidence lineage verification.

    This verifies evidence history only.

    It does NOT:
    - grant permission
    - grant authority
    - execute actions
    - change trust status
    - change capabilities
    - modify the constitution
    """

    verified: bool
    brain_id: str
    record_count: int
    reason: str


class BrainTrustLineageVerifier:
    """
    Verifies persistent replacement history for one brain.
    """

    def __init__(
        self,
        storage_directory: Path,
    ) -> None:
        self.storage_directory = Path(
            storage_directory
        )

        self.replacement_store = (
            BrainTrustReplacementStore(
                self.storage_directory
            )
        )

        self.provenance = BrainTrustProvenance(
            self.storage_directory
        )

    def verify(
        self,
        *,
        brain_id: str,
    ) -> BrainTrustLineageVerification:
        if (
            not isinstance(brain_id, str)
            or not brain_id.strip()
        ):
            raise ValueError(
                "brain_id is required."
            )

        brain_id = brain_id.strip()

        history = (
            self.replacement_store.read_recent(
                limit=1000000
            )
        )

        brain_history = [
            record
            for record in history
            if record.get("brain_id") == brain_id
        ]

        if not brain_history:
            return BrainTrustLineageVerification(
                verified=True,
                brain_id=brain_id,
                record_count=0,
                reason="No replacement history exists.",
            )

        for record in brain_history:
            previous = str(
                record.get(
                    "previous_provenance",
                    "",
                )
            ).strip()

            replacement = str(
                record.get(
                    "replacement_provenance",
                    "",
                )
            ).strip()

            reason = str(
                record.get(
                    "reason",
                    "",
                )
            ).strip()

            proof = str(
                record.get(
                    "provenance",
                    "",
                )
            ).strip()

            if not previous:
                return BrainTrustLineageVerification(
                    verified=False,
                    brain_id=brain_id,
                    record_count=len(brain_history),
                    reason=(
                        "Missing previous provenance."
                    ),
                )

            if not replacement:
                return BrainTrustLineageVerification(
                    verified=False,
                    brain_id=brain_id,
                    record_count=len(brain_history),
                    reason=(
                        "Missing replacement provenance."
                    ),
                )

            if not reason:
                return BrainTrustLineageVerification(
                    verified=False,
                    brain_id=brain_id,
                    record_count=len(brain_history),
                    reason=(
                        "Missing replacement reason."
                    ),
                )

            if not proof:
                return BrainTrustLineageVerification(
                    verified=False,
                    brain_id=brain_id,
                    record_count=len(brain_history),
                    reason=(
                        "Missing replacement authentication."
                    ),
                )

            if (
                previous.strip()
                == replacement.strip()
            ):
                return BrainTrustLineageVerification(
                    verified=False,
                    brain_id=brain_id,
                    record_count=len(brain_history),
                    reason=(
                        "Previous and replacement "
                        "provenance are identical."
                    ),
                )

            if not self.provenance.verify_replacement(
                brain_id=brain_id,
                previous_provenance=previous,
                replacement_provenance=replacement,
                reason=reason,
                provenance=proof,
            ):
                return BrainTrustLineageVerification(
                    verified=False,
                    brain_id=brain_id,
                    record_count=len(brain_history),
                    reason=(
                        "Replacement authentication "
                        "failed."
                    ),
                )

        return BrainTrustLineageVerification(
            verified=True,
            brain_id=brain_id,
            record_count=len(brain_history),
            reason=(
                "All persistent replacement records "
                "are authenticated."
            ),
        )
