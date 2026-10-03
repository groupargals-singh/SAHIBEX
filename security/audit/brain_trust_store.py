from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from security.audit.brain_trust_lifecycle import (
    BrainTrustEvidenceLifecycle,
)


class BrainTrustStore:
    """
    Persistent storage for authenticated brain trust records.

    This component stores and reads trust records only.

    It does NOT:
    - grant permission
    - grant authority
    - execute actions
    - change trust state
    - modify the constitution

    Lifecycle handling:
    - active
    - invalidated

    Legacy 6P-25 records without a lifecycle remain supported.
    """

    FILE_NAME = "brain_trust_records.jsonl"

    def __init__(self, storage_directory: Path) -> None:
        self.storage_directory = Path(storage_directory)

        self.storage_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.file_path = (
            self.storage_directory
            / self.FILE_NAME
        )

    @staticmethod
    def _validate_record(
        record: dict[str, Any],
    ) -> None:
        if not isinstance(record, dict):
            raise TypeError(
                "record must be a dictionary."
            )

        required = {
            "brain_id",
            "trust_status",
            "evidence",
            "provenance",
        }

        if not required.issubset(record):
            raise ValueError(
                "Trust record is missing required fields."
            )

        lifecycle = record.get("lifecycle")

        # Lifecycle is optional for backward compatibility
        # with the original 6P-25 trust records.
        if lifecycle is None:
            return

        if not isinstance(lifecycle, str):
            raise ValueError(
                "Trust evidence lifecycle must be a string."
            )

        lifecycle = lifecycle.strip()

        if not lifecycle:
            raise ValueError(
                "Trust evidence lifecycle cannot be empty."
            )

        valid_lifecycles = {
            item.value
            for item in BrainTrustEvidenceLifecycle
        }

        if lifecycle not in valid_lifecycles:
            raise ValueError(
                "Unknown trust evidence lifecycle."
            )

    def append(
        self,
        record: dict[str, Any],
    ) -> None:
        self._validate_record(record)

        with self.file_path.open(
            "a",
            encoding="utf-8",
        ) as handle:
            handle.write(
                json.dumps(
                    record,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            )

    def read_recent(
        self,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        if not isinstance(limit, int):
            raise TypeError(
                "limit must be an integer."
            )

        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero."
            )

        if not self.file_path.exists():
            return []

        records: list[dict[str, Any]] = []

        with self.file_path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            for line in handle:
                line = line.strip()

                if not line:
                    continue

                record = json.loads(line)

                if isinstance(record, dict):
                    records.append(record)

        return records[-limit:]
