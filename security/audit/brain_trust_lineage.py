from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BrainTrustEvidenceLineage:
    """
    Represents one authenticated link in brain trust
    evidence history.

    This object describes evidence lineage only.

    It does NOT:
    - grant permission
    - grant authority
    - execute actions
    - change BrainTrustStatus
    - change brain capabilities
    - modify the constitution
    """

    brain_id: str
    previous_provenance: str | None
    current_provenance: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.brain_id, str)
            or not self.brain_id.strip()
        ):
            raise ValueError(
                "brain_id is required."
            )

        if (
            not isinstance(self.current_provenance, str)
            or not self.current_provenance.strip()
        ):
            raise ValueError(
                "current_provenance is required."
            )

        if self.previous_provenance is not None:
            if (
                not isinstance(
                    self.previous_provenance,
                    str,
                )
                or not self.previous_provenance.strip()
            ):
                raise ValueError(
                    "previous_provenance must be "
                    "a non-empty string when provided."
                )

            if (
                self.previous_provenance.strip()
                == self.current_provenance.strip()
            ):
                raise ValueError(
                    "Previous and current provenance "
                    "must differ."
                )

    @property
    def is_root(self) -> bool:
        """
        True when this evidence has no predecessor.
        """
        return self.previous_provenance is None

    @property
    def is_replacement(self) -> bool:
        """
        True when this evidence replaces previous evidence.
        """
        return self.previous_provenance is not None

    def canonical_payload(self) -> bytes:
        """
        Deterministic representation of this lineage link.
        """
        previous = (
            ""
            if self.previous_provenance is None
            else self.previous_provenance.strip()
        )

        return (
            f"{self.brain_id.strip()}\n"
            f"{previous}\n"
            f"{self.current_provenance.strip()}"
        ).encode("utf-8")
