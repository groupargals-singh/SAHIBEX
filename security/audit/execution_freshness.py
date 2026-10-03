from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from security.audit.execution_provenance import ExecutionProvenance


class ExecutionFreshnessGuard:
    """
    Persistent replay/freshness boundary for real SAHIBEX executions.

    Security boundary:
    - detects reuse of an already-consumed execution identity
    - persists consumed execution identities
    - authenticates freshness records with execution provenance
    - is safe for concurrent callers

    It does NOT:
    - execute tools
    - grant permission
    - change confirmation
    - authorize actions
    - modify the constitution
    """

    LOG_FILE_NAME = "sahibex_execution_consumed.jsonl"

    def __init__(self, storage_directory: Path) -> None:
        self.storage_directory = Path(storage_directory)
        self.storage_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.log_file = (
            self.storage_directory / self.LOG_FILE_NAME
        )

        self.provenance = ExecutionProvenance(
            self.storage_directory
        )

        self._lock = threading.Lock()

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()

    @staticmethod
    def _validate_execution_id(
        execution_id: str,
    ) -> str:
        if (
            not isinstance(execution_id, str)
            or not execution_id.strip()
        ):
            raise ValueError(
                "execution_id must be a non-empty string."
            )

        return execution_id.strip()

    def _read_consumed_ids(self) -> set[str]:
        consumed: set[str] = set()

        if not self.log_file.exists():
            return consumed

        lines = self.log_file.read_text(
            encoding="utf-8"
        ).splitlines()

        for line in lines:
            if not line.strip():
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            if not isinstance(record, dict):
                continue

            execution_id = record.get("execution_id")

            if (
                isinstance(execution_id, str)
                and execution_id.strip()
            ):
                consumed.add(execution_id.strip())

        return consumed

    def is_consumed(
        self,
        execution_id: str,
    ) -> bool:
        execution_id = self._validate_execution_id(
            execution_id
        )

        with self._lock:
            return execution_id in self._read_consumed_ids()

    def consume(
        self,
        evidence: dict[str, Any],
    ) -> bool:
        """
        Atomically claim an execution identity for fresh use.

        Returns:
            True  -> first use, identity consumed successfully.
            False -> identity was already consumed (replay).
        """

        if not isinstance(evidence, dict):
            raise TypeError(
                "evidence must be a dictionary."
            )

        execution_id = self._validate_execution_id(
            str(evidence.get("execution_id", ""))
        )

        with self._lock:
            consumed = self._read_consumed_ids()

            if execution_id in consumed:
                return False

            record = {
                "execution_id": execution_id,
                "consumed_at": self._timestamp(),
            }

            record["provenance"] = self.provenance.sign(
                record
            )

            serialized = json.dumps(
                record,
                sort_keys=True,
                default=str,
            )

            with self.log_file.open(
                "a",
                encoding="utf-8",
            ) as handle:
                handle.write(serialized)
                handle.write("\n")
                handle.flush()

            return True

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
            except json.JSONDecodeError:
                continue

            if isinstance(record, dict):
                records.append(record)

        return records
