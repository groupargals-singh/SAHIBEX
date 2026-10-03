from __future__ import annotations

import json
import os
import secrets
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from security.audit.execution_provenance import ExecutionProvenance


@dataclass(frozen=True)
class ExecutionEvidence:
    execution_id: str
    timestamp: str
    tool: str
    action: str
    permission_allowed: bool
    confirmation_required: bool
    confirmation_provided: bool
    attempts: int
    result: Any
    verification_status: str
    recovery_status: str
    final_status: str
    error: Any
    risk: str
    reason: str
    provenance: str | None = None


class ExecutionEvidenceRecorder:
    """
    Persistent execution-evidence recorder.

    Security boundary:
    - records execution evidence
    - authenticates real execution provenance
    - reads persisted evidence

    It does NOT:
    - execute tools
    - invoke tools
    - grant permission
    - require permission
    - change confirmation
    - modify constitution
    - update constitution
    """

    LOG_FILE_NAME = "sahibex_execution_evidence.jsonl"
    PROVENANCE_KEY_ENV = "SAHIBEX_PROVENANCE_KEY"

    def __init__(self, log_directory: Path) -> None:
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.log_file = (
            self.log_directory / self.LOG_FILE_NAME
        )

        self._lock = threading.Lock()

        self.provenance = ExecutionProvenance(
            self.log_directory
        )

    @staticmethod
    def _validate_common(
        *,
        tool: str,
        action: str,
        confirmation_required: bool,
        confirmation_provided: bool,
        attempts: int,
        verification_status: str,
        recovery_status: str,
        final_status: str,
        risk: str,
        reason: str,
    ) -> None:
        if not isinstance(tool, str) or not tool.strip():
            raise ValueError("tool must be a non-empty string.")

        if not isinstance(action, str) or not action.strip():
            raise ValueError(
                "action must be a non-empty string."
            )

        if not isinstance(
            confirmation_required,
            bool,
        ):
            raise ValueError(
                "confirmation_required must be bool."
            )

        if not isinstance(
            confirmation_provided,
            bool,
        ):
            raise ValueError(
                "confirmation_provided must be bool."
            )

        if (
            confirmation_provided
            and not confirmation_required
        ):
            raise ValueError(
                "confirmation_provided cannot be true "
                "when confirmation_required is false."
            )

        if not isinstance(attempts, int) or attempts < 1:
            raise ValueError(
                "attempts must be an integer >= 1."
            )

        for name, value in (
            (
                "verification_status",
                verification_status,
            ),
            (
                "recovery_status",
                recovery_status,
            ),
            (
                "final_status",
                final_status,
            ),
            ("risk", risk),
            ("reason", reason),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"{name} must be a non-empty string."
                )

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()

    @staticmethod
    def _canonical_evidence(
        evidence: dict[str, Any],
    ) -> dict[str, Any]:
        data = dict(evidence)

        data.pop("provenance", None)

        return data

    def _append_record(
        self,
        record: dict[str, Any],
    ) -> None:
        serialized = json.dumps(
            record,
            sort_keys=True,
            default=str,
        )

        with self._lock:
            with self.log_file.open(
                "a",
                encoding="utf-8",
            ) as handle:
                handle.write(serialized)
                handle.write("\n")

    def record(
        self,
        *,
        execution_id: str | None = None,
        tool: str,
        action: str,
        permission_allowed: bool,
        confirmation_required: bool,
        confirmation_provided: bool,
        attempts: int,
        result: Any,
        verification_status: str,
        recovery_status: str,
        final_status: str,
        error: Any,
        risk: str,
        reason: str,
    ) -> ExecutionEvidence:
        """
        Record normal execution evidence.

        This method remains compatible with existing
        6P-10 / 6P-11 synthetic and integration tests.
        """

        if execution_id is None:
            execution_id = str(secrets.token_hex(16))

        if (
            not isinstance(execution_id, str)
            or not execution_id.strip()
        ):
            raise ValueError(
                "execution_id must be a non-empty string."
            )

        if not isinstance(permission_allowed, bool):
            raise ValueError(
                "permission_allowed must be bool."
            )

        self._validate_common(
            tool=tool,
            action=action,
            confirmation_required=confirmation_required,
            confirmation_provided=confirmation_provided,
            attempts=attempts,
            verification_status=verification_status,
            recovery_status=recovery_status,
            final_status=final_status,
            risk=risk,
            reason=reason,
        )

        timestamp = self._timestamp()

        evidence = ExecutionEvidence(
            execution_id=execution_id,
            timestamp=timestamp,
            tool=tool,
            action=action,
            permission_allowed=permission_allowed,
            confirmation_required=confirmation_required,
            confirmation_provided=confirmation_provided,
            attempts=attempts,
            result=result,
            verification_status=verification_status,
            recovery_status=recovery_status,
            final_status=final_status,
            error=error,
            risk=risk,
            reason=reason,
            provenance=None,
        )

        record = {
            "execution_id": evidence.execution_id,
            "timestamp": evidence.timestamp,
            "tool": evidence.tool,
            "action": evidence.action,
            "permission_allowed": (
                evidence.permission_allowed
            ),
            "confirmation_required": (
                evidence.confirmation_required
            ),
            "confirmation_provided": (
                evidence.confirmation_provided
            ),
            "attempts": evidence.attempts,
            "result": evidence.result,
            "verification_status": (
                evidence.verification_status
            ),
            "recovery_status": (
                evidence.recovery_status
            ),
            "final_status": evidence.final_status,
            "error": evidence.error,
            "risk": evidence.risk,
            "reason": evidence.reason,
        }

        self._append_record(record)

        return evidence

    def record_authenticated(
        self,
        *,
        execution_id: str,
        tool: str,
        action: str,
        permission_allowed: bool,
        confirmation_required: bool,
        confirmation_provided: bool,
        attempts: int,
        result: Any,
        verification_status: str,
        recovery_status: str,
        final_status: str,
        error: Any,
        risk: str,
        reason: str,
    ) -> ExecutionEvidence:
        """
        Record evidence with authenticated provenance.

        Intended for the REAL execution pipeline.

        Provenance:
            execution facts
                    |
                    v
            authenticated MAC
                    |
                    v
            persisted evidence

        Provenance does NOT grant authority or permission.
        """

        if (
            not isinstance(execution_id, str)
            or not execution_id.strip()
        ):
            raise ValueError(
                "execution_id must be a non-empty string."
            )

        if not isinstance(permission_allowed, bool):
            raise ValueError(
                "permission_allowed must be bool."
            )

        self._validate_common(
            tool=tool,
            action=action,
            confirmation_required=confirmation_required,
            confirmation_provided=confirmation_provided,
            attempts=attempts,
            verification_status=verification_status,
            recovery_status=recovery_status,
            final_status=final_status,
            risk=risk,
            reason=reason,
        )

        timestamp = self._timestamp()

        base_record = {
            "execution_id": execution_id,
            "timestamp": timestamp,
            "tool": tool,
            "action": action,
            "permission_allowed": permission_allowed,
            "confirmation_required": confirmation_required,
            "confirmation_provided": confirmation_provided,
            "attempts": attempts,
            "result": result,
            "verification_status": verification_status,
            "recovery_status": recovery_status,
            "final_status": final_status,
            "error": error,
            "risk": risk,
            "reason": reason,
        }

        provenance = self.provenance.sign(
            base_record
        )

        authenticated_record = dict(base_record)
        authenticated_record["provenance"] = provenance

        self._append_record(authenticated_record)

        return ExecutionEvidence(
            execution_id=execution_id,
            timestamp=timestamp,
            tool=tool,
            action=action,
            permission_allowed=permission_allowed,
            confirmation_required=confirmation_required,
            confirmation_provided=confirmation_provided,
            attempts=attempts,
            result=result,
            verification_status=verification_status,
            recovery_status=recovery_status,
            final_status=final_status,
            error=error,
            risk=risk,
            reason=reason,
            provenance=provenance,
        )

    def read_recent(
        self,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        if not isinstance(limit, int) or limit < 1:
            raise ValueError(
                "limit must be an integer >= 1."
            )

        if not self.log_file.exists():
            return []

        lines = self.log_file.read_text(
            encoding="utf-8"
        ).splitlines()

        records: list[dict[str, Any]] = []

        for line in lines[-limit:]:
            if not line.strip():
                continue

            try:
                record = json.loads(line)

                if isinstance(record, dict):
                    records.append(record)

            except json.JSONDecodeError:
                continue

        return records
