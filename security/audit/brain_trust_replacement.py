from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BrainTrustEvidenceReplacement:
    """
    Authenticated relationship between old and new
    brain trust evidence records.

    This relationship describes evidence replacement only.

    It does NOT:
    - grant permission
    - grant authority
    - execute actions
    - change BrainTrustStatus
    - modify capabilities
    - modify the constitution
    """

    brain_id: str
    previous_provenance: str
    replacement_provenance: str
    reason: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.brain_id, str)
            or not self.brain_id.strip()
        ):
            raise ValueError(
                "brain_id is required."
            )

        if (
            not isinstance(self.previous_provenance, str)
            or not self.previous_provenance.strip()
        ):
            raise ValueError(
                "previous_provenance is required."
            )

        if (
            not isinstance(self.replacement_provenance, str)
            or not self.replacement_provenance.strip()
        ):
            raise ValueError(
                "replacement_provenance is required."
            )

        if (
            not isinstance(self.reason, str)
            or not self.reason.strip()
        ):
            raise ValueError(
                "A replacement reason is required."
            )

        if (
            self.previous_provenance.strip()
            == self.replacement_provenance.strip()
        ):
            raise ValueError(
                "Replacement evidence must differ "
                "from previous evidence."
            )

    def canonical_payload(self) -> bytes:
        """
        Return deterministic replacement data for authentication.

        The payload contains the complete replacement relationship.
        """

        return (
            f"{self.brain_id.strip()}\n"
            f"{self.previous_provenance.strip()}\n"
            f"{self.replacement_provenance.strip()}\n"
            f"{self.reason.strip()}"
        ).encode("utf-8")
