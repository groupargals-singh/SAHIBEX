from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProvenanceResult:
    verified: bool
    execution_id: str
    reason: str


class ExecutionProvenance:
    """
    Authenticated provenance boundary for real SAHIBEX executions.

    Provenance proves that an evidence record was produced through the
    trusted execution-evidence path using the same authenticated key.

    Provenance does NOT:
    - grant permission
    - execute tools
    - change confirmation
    - modify the constitution
    - authorize actions
    """

    ENV_KEY = "SAHIBEX_PROVENANCE_KEY"
    KEY_FILE_NAME = ".sahibex_provenance.key"

    def __init__(self, storage_directory: Path) -> None:
        self.storage_directory = Path(storage_directory)
        self.storage_directory.mkdir(parents=True, exist_ok=True)

        self.key = self._load_or_create_key()

    def _load_or_create_key(self) -> bytes:
        configured = os.getenv(self.ENV_KEY)

        if configured and configured.strip():
            return configured.encode("utf-8")

        key_path = self.storage_directory / self.KEY_FILE_NAME

        if key_path.exists():
            key = key_path.read_bytes()

            if len(key) < 32:
                raise RuntimeError(
                    "SAHIBEX provenance key is too short."
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
    def _canonical_payload(evidence: dict[str, Any]) -> bytes:
        payload = dict(evidence)

        payload.pop("provenance", None)

        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")

    def sign(self, evidence: dict[str, Any]) -> str:
        payload = self._canonical_payload(evidence)

        return hmac.new(
            self.key,
            payload,
            hashlib.sha256,
        ).hexdigest()

    def verify(
        self,
        evidence: dict[str, Any],
    ) -> ProvenanceResult:
        execution_id = str(
            evidence.get("execution_id", "")
        ).strip()

        if not execution_id:
            return ProvenanceResult(
                verified=False,
                execution_id="",
                reason="Missing execution_id.",
            )

        supplied = evidence.get("provenance")

        if not isinstance(supplied, str) or not supplied.strip():
            return ProvenanceResult(
                verified=False,
                execution_id=execution_id,
                reason="Missing provenance proof.",
            )

        expected = self.sign(evidence)

        if not hmac.compare_digest(
            supplied,
            expected,
        ):
            return ProvenanceResult(
                verified=False,
                execution_id=execution_id,
                reason="Provenance authentication failed.",
            )

        return ProvenanceResult(
            verified=True,
            execution_id=execution_id,
            reason="Authenticated execution provenance verified.",
        )
