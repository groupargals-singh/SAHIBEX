from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class BrainTrustReplacementStore:
    """
    Persistent storage for authenticated brain trust
    evidence replacement relationships.

    This component stores replacement history only.

    It does NOT:
    - grant permission
    - grant authority
    - execute actions
    - change BrainTrustStatus
    - change brain capabilities
    - modify the constitution
    - overwrite previous trust evidence
    """

    FILE_NAME = "brain_trust_replacements.jsonl"

    REQUIRED_FIELDS = {
        "brain_id",
        "previous_provenance",
        "replacement_provenance",
        "reason",
        "provenance",
    }

    def __init__(
        self,
        storage_directory: Path,
    ) -> None:
        self.storage_directory = Path(
            storage_directory
        )

        self.storage_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.file_path = (
            self.storage_directory
            / self.FILE_NAME
        )

    @classmethod
    def _validate_record(
        cls,
        record: dict[str, Any],
    ) -> None:
        if not isinstance(record, dict):
            raise TypeError(
                "record must be a dictionary."
            )

        if not cls.REQUIRED_FIELDS.issubset(record):
            raise ValueError(
                "Replacement record is missing "
                "required fields."
            )

        for field in (
            "brain_id",
            "previous_provenance",
            "replacement_provenance",
            "reason",
            "provenance",
        ):
            value = record.get(field)

            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                raise ValueError(
                    f"Replacement record field "
                    f"'{field}' must be a non-empty string."
                )

        if (
            record["previous_provenance"].strip()
            == record["replacement_provenance"].strip()
        ):
            raise ValueError(
                "Replacement evidence must differ "
                "from previous evidence."
            )

    def append(
        self,
        record: dict[str, Any],
    ) -> None:
        """
        Append one replacement record.

        Existing history is never overwritten.
        """

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
        """
        Read the most recent replacement records.
        """

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
