from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BrainTrustCurrentBinding:
    """
    Authenticated binding for the current trust evidence
    of one brain.

    This object represents evidence state only.

    It does NOT:
    - grant permission
    - grant authority
    - execute actions
    - change BrainTrustStatus
    - modify capabilities
    - modify the constitution
    """

    brain_id: str
    current_provenance: str
    root_provenance: str
    depth: int

    def __post_init__(self) -> None:
        if (
            not isinstance(self.brain_id, str)
            or not self.brain_id.strip()
        ):
            raise ValueError(
                "brain_id is required."
            )

        if (
            not isinstance(
                self.current_provenance,
                str,
            )
            or not self.current_provenance.strip()
        ):
            raise ValueError(
                "current_provenance is required."
            )

        if (
            not isinstance(
                self.root_provenance,
                str,
            )
            or not self.root_provenance.strip()
        ):
            raise ValueError(
                "root_provenance is required."
            )

        if (
            not isinstance(self.depth, int)
            or isinstance(self.depth, bool)
            or self.depth < 1
        ):
            raise ValueError(
                "depth must be a positive integer."
            )

    @property
    def is_root_current(self) -> bool:
        """
        True when current evidence is also the root evidence.
        """
        return (
            self.current_provenance.strip()
            == self.root_provenance.strip()
        )

    def canonical_payload(self) -> bytes:
        """
        Deterministic representation of the binding.
        """
        return (
            f"{self.brain_id.strip()}\n"
            f"{self.current_provenance.strip()}\n"
            f"{self.root_provenance.strip()}\n"
            f"{self.depth}"
        ).encode("utf-8")
