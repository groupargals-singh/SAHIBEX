from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from security.audit.brain_trust_provenance import (
    BrainTrustProvenance,
)
from security.audit.brain_trust_replacement_store import (
    BrainTrustReplacementStore,
)


@dataclass(frozen=True)
class BrainTrustLineageResolution:
    """
    Resolved trust-evidence lineage.

    lineage is ordered from current evidence
    backwards toward the original/root evidence.

    Example:

        [C, B, A]

    This object describes evidence history only.

    It does NOT:
    - grant permission
    - grant authority
    - execute actions
    - change trust status
    - change capabilities
    - modify the constitution
    """

    brain_id: str
    current_provenance: str
    lineage: tuple[str, ...]

    @property
    def root_provenance(self) -> str:
        return self.lineage[-1]

    @property
    def depth(self) -> int:
        return len(self.lineage)


class BrainTrustLineageResolver:
    """
    Resolves authenticated brain trust evidence lineage.

    The resolver verifies every replacement relationship
    before accepting it into the resolved chain.
    """

    def __init__(
        self,
        storage_directory: Path,
    ) -> None:
        self.storage_directory = Path(
            storage_directory
        )

        self.replacement_store = (
            BrainTrustReplacementStore(
                self.storage_directory
            )
        )

        self.provenance = BrainTrustProvenance(
            self.storage_directory
        )

    def resolve(
        self,
        *,
        brain_id: str,
        current_provenance: str,
    ) -> BrainTrustLineageResolution:
        if (
            not isinstance(brain_id, str)
            or not brain_id.strip()
        ):
            raise ValueError(
                "brain_id is required."
            )

        if (
            not isinstance(
                current_provenance,
                str,
            )
            or not current_provenance.strip()
        ):
            raise ValueError(
                "current_provenance is required."
            )

        brain_id = brain_id.strip()
        current_provenance = (
            current_provenance.strip()
        )

        history = (
            self.replacement_store.read_recent(
                limit=1000000
            )
        )

        lineage: list[str] = [
            current_provenance
        ]

        visited: set[str] = {
            current_provenance
        }

        current = current_provenance

        while True:
            matching_records = [
                record
                for record in history
                if (
                    record.get("brain_id")
                    == brain_id
                    and record.get(
                        "replacement_provenance"
                    )
                    == current
                )
            ]

            if not matching_records:
                break

            if len(matching_records) > 1:
                raise ValueError(
                    "Ambiguous lineage: multiple "
                    "replacement records point to "
                    "the same provenance."
                )

            record = matching_records[0]

            previous = str(
                record.get(
                    "previous_provenance",
                    "",
                )
            ).strip()

            replacement = str(
                record.get(
                    "replacement_provenance",
                    "",
                )
            ).strip()

            reason = str(
                record.get(
                    "reason",
                    "",
                )
            ).strip()

            proof = str(
                record.get(
                    "provenance",
                    "",
                )
            ).strip()

            if not previous:
                raise ValueError(
                    "Broken lineage: previous "
                    "provenance is missing."
                )

            if not replacement:
                raise ValueError(
                    "Broken lineage: replacement "
                    "provenance is missing."
                )

            if not reason:
                raise ValueError(
                    "Broken lineage: replacement "
                    "reason is missing."
                )

            if not proof:
                raise ValueError(
                    "Broken lineage: replacement "
                    "authentication is missing."
                )

            if not self.provenance.verify_replacement(
                brain_id=brain_id,
                previous_provenance=previous,
                replacement_provenance=replacement,
                reason=reason,
                provenance=proof,
            ):
                raise ValueError(
                    "Unauthenticated replacement "
                    "relationship detected."
                )

            if previous in visited:
                raise ValueError(
                    "Cyclic trust evidence lineage detected."
                )

            visited.add(previous)

            lineage.append(previous)

            current = previous

        return BrainTrustLineageResolution(
            brain_id=brain_id,
            current_provenance=current_provenance,
            lineage=tuple(lineage),
        )
