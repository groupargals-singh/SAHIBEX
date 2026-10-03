from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path
from typing import Any

from security.audit.brain_trust_lifecycle import (
    BrainTrustEvidenceLifecycle,
)


class BrainTrustProvenanceResult:
    def __init__(
        self,
        verified: bool,
        brain_id: str,
        trust_status: str,
        reason: str,
    ) -> None:
        self.verified = verified
        self.brain_id = brain_id
        self.trust_status = trust_status
        self.reason = reason


class BrainTrustProvenance:
    """
    Authenticated provenance boundary for SAHIBEX brain trust evidence.

    This component proves that a trust-evidence record is bound to:
    - one specific brain_id
    - one specific trust status
    - one specific evidence value
    - optionally, one specific evidence lifecycle

    Valid lifecycle values:
    - active
    - invalidated

    It does NOT:
    - grant permission
    - grant authority
    - execute actions
    - change the constitution
    - change brain capabilities
    - automatically change trust state
    """

    ENV_KEY = "SAHIBEX_BRAIN_TRUST_KEY"
    KEY_FILE_NAME = ".sahibex_brain_trust.key"

    def __init__(self, storage_directory: Path) -> None:
        self.storage_directory = Path(storage_directory)

        self.storage_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.key = self._load_or_create_key()

    def _load_or_create_key(self) -> bytes:
        configured = os.getenv(self.ENV_KEY)

        if configured and configured.strip():
            key = configured.encode("utf-8")

            if len(key) < 32:
                raise RuntimeError(
                    "SAHIBEX brain trust key is too short."
                )

            return key

        key_path = (
            self.storage_directory
            / self.KEY_FILE_NAME
        )

        if key_path.exists():
            key = key_path.read_bytes()

            if len(key) < 32:
                raise RuntimeError(
                    "SAHIBEX brain trust key is too short."
                )

            return key

        key = secrets.token_bytes(32)

        key_path.write_bytes(key)

        try:
            key_path.chmod(0o600)
        except OSError:
            pass

        return key

    @staticmethod
    def _canonical_payload(
        record: dict[str, Any],
    ) -> bytes:
        payload = dict(record)

        payload.pop("provenance", None)

        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")

    def sign(
        self,
        *,
        brain_id: str,
        trust_status: str,
        evidence: str,
        lifecycle: str | None = None,
    ) -> str:
        record = {
            "brain_id": brain_id,
            "trust_status": trust_status,
            "evidence": evidence,
        }

        if lifecycle is not None:
            record["lifecycle"] = lifecycle

        payload = self._canonical_payload(record)

        return hmac.new(
            self.key,
            payload,
            hashlib.sha256,
        ).hexdigest()

    def verify(
        self,
        record: dict[str, Any],
    ) -> BrainTrustProvenanceResult:
        if not isinstance(record, dict):
            raise TypeError(
                "record must be a dictionary."
            )

        brain_id = str(
            record.get("brain_id", "")
        ).strip()

        trust_status = str(
            record.get("trust_status", "")
        ).strip()

        evidence = record.get("evidence")

        if not brain_id:
            return BrainTrustProvenanceResult(
                False,
                "",
                trust_status,
                "Missing brain_id.",
            )

        if not trust_status:
            return BrainTrustProvenanceResult(
                False,
                brain_id,
                "",
                "Missing trust_status.",
            )

        if (
            not isinstance(evidence, str)
            or not evidence.strip()
        ):
            return BrainTrustProvenanceResult(
                False,
                brain_id,
                trust_status,
                "Missing trust evidence.",
            )

        lifecycle = record.get("lifecycle")

        if lifecycle is not None:
            lifecycle = str(lifecycle).strip()

            if not lifecycle:
                return BrainTrustProvenanceResult(
                    False,
                    brain_id,
                    trust_status,
                    "Invalid trust evidence lifecycle.",
                )

            valid_lifecycles = {
                item.value
                for item in BrainTrustEvidenceLifecycle
            }

            if lifecycle not in valid_lifecycles:
                return BrainTrustProvenanceResult(
                    False,
                    brain_id,
                    trust_status,
                    "Unknown trust evidence lifecycle.",
                )

        supplied = record.get("provenance")

        if (
            not isinstance(supplied, str)
            or not supplied.strip()
        ):
            return BrainTrustProvenanceResult(
                False,
                brain_id,
                trust_status,
                "Missing trust provenance.",
            )

        expected = self.sign(
            brain_id=brain_id,
            trust_status=trust_status,
            evidence=evidence.strip(),
            lifecycle=lifecycle,
        )

        if not hmac.compare_digest(
            supplied,
            expected,
        ):
            return BrainTrustProvenanceResult(
                False,
                brain_id,
                trust_status,
                "Brain trust provenance authentication failed.",
            )

        return BrainTrustProvenanceResult(
            True,
            brain_id,
            trust_status,
            "Authenticated brain trust provenance verified.",
        )

    def sign_replacement(
        self,
        *,
        brain_id: str,
        previous_provenance: str,
        replacement_provenance: str,
        reason: str,
    ) -> str:
        """
        Authenticate a trust-evidence replacement relationship.

        This proof authenticates evidence history only.
        It does NOT grant permission, authority, or execution rights.
        """

        replacement = {
            "brain_id": brain_id,
            "previous_provenance": previous_provenance,
            "replacement_provenance": replacement_provenance,
            "reason": reason,
        }

        payload = self._canonical_payload(
            replacement
        )

        return hmac.new(
            self.key,
            payload,
            hashlib.sha256,
        ).hexdigest()

    def verify_replacement(
        self,
        *,
        brain_id: str,
        previous_provenance: str,
        replacement_provenance: str,
        reason: str,
        provenance: str,
    ) -> bool:
        """
        Verify an authenticated trust-evidence replacement.

        This verification proves relationship integrity only.
        It does NOT grant permission, authority, or execution rights.
        """

        replacement = {
            "brain_id": brain_id,
            "previous_provenance": previous_provenance,
            "replacement_provenance": replacement_provenance,
            "reason": reason,
        }

        payload = self._canonical_payload(
            replacement
        )

        expected = hmac.new(
            self.key,
            payload,
            hashlib.sha256,
        ).hexdigest()

        if (
            not isinstance(provenance, str)
            or not provenance.strip()
        ):
            return False

        return hmac.compare_digest(
            provenance,
            expected,
        )
