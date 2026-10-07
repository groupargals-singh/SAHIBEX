from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from uuid import uuid4

from core.brain.root_identity import SahibexRootIdentity


@dataclass(frozen=True)
class SahibexRootInstanceIdentity:
    """
    Unique runtime identity of one SAHIBEX Mother Brain instance.

    This identity identifies a particular runtime instance of SAHIBEX.
    It does NOT identify:
      - an execution
      - a tool
      - a Child Brain
      - a permission grant
      - constitutional authority

    The instance is cryptographically bound to the immutable
    SahibexRootIdentity.
    """

    root_identity: SahibexRootIdentity = field(
        default_factory=SahibexRootIdentity,
    )

    instance_id: str = field(
        default_factory=lambda: f"sahibex-instance-{uuid4()}",
    )

    identity_version: str = field(
        default="1.0",
        init=False,
    )

    root_binding_fingerprint: str = field(
        default="",
        init=False,
    )

    fingerprint: str = field(
        default="",
        init=False,
    )

    def __post_init__(self) -> None:
        if not self.root_identity.validate():
            raise ValueError(
                "invalid_root_identity"
            )

        if not self.instance_id.strip():
            raise ValueError(
                "instance_id_required"
            )

        root_binding = self._calculate_root_binding_fingerprint()
        object.__setattr__(
            self,
            "root_binding_fingerprint",
            root_binding,
        )

        object.__setattr__(
            self,
            "fingerprint",
            self._calculate_fingerprint(),
        )

    def _canonical_identity(self) -> dict[str, str]:
        return {
            "instance_id": self.instance_id,
            "identity_version": self.identity_version,
            "root_binding_fingerprint": self.root_binding_fingerprint,
        }

    def _calculate_root_binding_fingerprint(self) -> str:
        payload = json.dumps(
            {
                "root_id": self.root_identity.ROOT_ID,
                "brain_id": self.root_identity.BRAIN_ID,
                "brain_role": self.root_identity.BRAIN_ROLE,
                "constitution_id": self.root_identity.CONSTITUTION_ID,
                "identity_version": self.root_identity.IDENTITY_VERSION,
                "root_fingerprint": self.root_identity.fingerprint,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return hashlib.sha256(payload).hexdigest()

    def _calculate_fingerprint(self) -> str:
        payload = json.dumps(
            self._canonical_identity(),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return hashlib.sha256(payload).hexdigest()

    def verify_root_binding(self) -> bool:
        return (
            self.root_binding_fingerprint
            == self._calculate_root_binding_fingerprint()
        )

    def verify_integrity(self) -> bool:
        return (
            self.root_identity.validate()
            and self.verify_root_binding()
            and self.fingerprint == self._calculate_fingerprint()
        )

    def is_mother_instance(self) -> bool:
        return (
            self.root_identity.is_mother_brain()
            and self.instance_id.startswith("sahibex-instance-")
        )

    def is_child_identity(self) -> bool:
        return self.root_identity.is_child_identity()

    def is_execution_identity(self) -> bool:
        return self.instance_id.startswith("execution-")

    def grants_authority(self) -> bool:
        """
        Runtime identity never grants constitutional or execution authority.
        """
        return False

    def validate(self) -> bool:
        return (
            self.verify_integrity()
            and self.is_mother_instance()
            and not self.is_child_identity()
            and not self.is_execution_identity()
            and self.grants_authority() is False
        )
