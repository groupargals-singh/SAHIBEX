from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json


@dataclass(frozen=True)
class SahibexRootIdentity:
    """
    Immutable constitutional identity of the SAHIBEX Mother Brain.

    This object identifies SAHIBEX itself.
    It is NOT an execution identity, model identity, tool identity,
    Child Brain identity, or permission grant.
    """

    ROOT_ID: str = field(
        default="sahibex-root",
        init=False,
    )
    BRAIN_ID: str = field(
        default="sahibex-master-brain",
        init=False,
    )
    BRAIN_ROLE: str = field(
        default="mother_brain",
        init=False,
    )
    CONSTITUTION_ID: str = field(
        default="sahibex-root-constitution-v1",
        init=False,
    )
    IDENTITY_VERSION: str = field(
        default="1.0",
        init=False,
    )
    fingerprint: str = field(
        default="",
        init=False,
    )

    def __post_init__(self) -> None:
        fingerprint = self._calculate_fingerprint()

        object.__setattr__(
            self,
            "fingerprint",
            fingerprint,
        )

    def _canonical_identity(self) -> dict[str, str]:
        return {
            "root_id": self.ROOT_ID,
            "brain_id": self.BRAIN_ID,
            "brain_role": self.BRAIN_ROLE,
            "constitution_id": self.CONSTITUTION_ID,
            "identity_version": self.IDENTITY_VERSION,
        }

    def _calculate_fingerprint(self) -> str:
        payload = json.dumps(
            self._canonical_identity(),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return hashlib.sha256(payload).hexdigest()

    def verify_integrity(self) -> bool:
        return self.fingerprint == self._calculate_fingerprint()

    def is_mother_brain(self) -> bool:
        return (
            self.BRAIN_ID == "sahibex-master-brain"
            and self.BRAIN_ROLE == "mother_brain"
        )

    def is_child_identity(self) -> bool:
        return self.BRAIN_ID.startswith("child-brain-")

    def is_external_identity(self) -> bool:
        return not self.is_mother_brain()

    def grants_authority(self) -> bool:
        """
        Identity establishes identity only.

        It never grants execution or constitutional authority.
        """
        return False

    def constitution_binding_valid(self) -> bool:
        return self.CONSTITUTION_ID == "sahibex-root-constitution-v1"

    def validate(self) -> bool:
        return (
            self.verify_integrity()
            and self.ROOT_ID == "sahibex-root"
            and self.BRAIN_ID == "sahibex-master-brain"
            and self.BRAIN_ROLE == "mother_brain"
            and self.constitution_binding_valid()
            and not self.is_child_identity()
            and self.grants_authority() is False
        )
