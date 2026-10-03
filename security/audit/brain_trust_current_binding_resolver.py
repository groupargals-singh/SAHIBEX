from __future__ import annotations

from security.audit.brain_trust_current_binding import (
    BrainTrustCurrentBinding,
)
from security.audit.brain_trust_lineage_integrity_gate import (
    BrainTrustLineageIntegrityGate,
)
from security.audit.brain_trust_provenance import (
    BrainTrustProvenance,
)
from security.audit.brain_trust_store import BrainTrustStore


class BrainTrustCurrentBindingResolver:
    """
    Resolve authenticated trust evidence into a current-binding object.

    This component establishes evidence identity only.
    It does not grant permission, authority, or execution rights.
    """

    def __init__(
        self,
        storage_directory,
    ) -> None:
        self.storage_directory = storage_directory

        self.provenance = BrainTrustProvenance(
            storage_directory
        )

        self.trust_store = BrainTrustStore(
            storage_directory
        )

        self.gate = BrainTrustLineageIntegrityGate(
            storage_directory=storage_directory
        )

    def _current_provenance_exists(
        self,
        *,
        brain_id: str,
        current_provenance: str,
    ) -> bool:
        """
        Verify that current_provenance belongs to an
        authenticated trust lineage for this exact brain.

        A provenance is accepted when it is either:

        1. A persisted original trust record.
        2. An authenticated replacement provenance.
        3. An authenticated previous provenance in a
           replacement relationship.

        This establishes evidence identity only.
        It does not establish that the evidence is
        the latest/current evidence.
        """

        trust_records = self.trust_store.read_recent(
            limit=1000000
        )

        for record in trust_records:
            record_brain_id = str(
                record.get("brain_id", "")
            ).strip()

            record_provenance = str(
                record.get("provenance", "")
            ).strip()

            if record_brain_id != brain_id:
                continue

            if record_provenance != current_provenance:
                continue

            if not self.provenance.verify(record):
                continue

            return True

        replacement_records = (
            self.gate.verifier.replacement_store.read_recent(
                limit=1000000
            )
        )

        for record in replacement_records:
            record_brain_id = str(
                record.get("brain_id", "")
            ).strip()

            if record_brain_id != brain_id:
                continue

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

            authentication = str(
                record.get(
                    "provenance",
                    "",
                )
            ).strip()

            if not previous:
                continue

            if not replacement:
                continue

            if not reason:
                continue

            if not authentication:
                continue

            authenticated = (
                self.provenance.verify_replacement(
                    brain_id=brain_id,
                    previous_provenance=previous,
                    replacement_provenance=replacement,
                    reason=reason,
                    provenance=authentication,
                )
            )

            if not authenticated:
                continue

            if current_provenance in {
                previous,
                replacement,
            }:
                return True

        return False

    def resolve(
        self,
        *,
        brain_id: str,
        current_provenance: str,
    ) -> BrainTrustCurrentBinding:
        """
        Resolve an authenticated provenance into a
        lineage-bound trust binding.
        """

        if not isinstance(brain_id, str):
            raise TypeError(
                "brain_id must be a string."
            )

        if not brain_id.strip():
            raise ValueError(
                "brain_id must not be empty."
            )

        if not isinstance(
            current_provenance,
            str,
        ):
            raise TypeError(
                "current_provenance must be a string."
            )

        if not current_provenance.strip():
            raise ValueError(
                "current_provenance must not be empty."
            )

        brain_id = brain_id.strip()
        current_provenance = current_provenance.strip()

        if not self._current_provenance_exists(
            brain_id=brain_id,
            current_provenance=current_provenance,
        ):
            raise ValueError(
                "Current provenance is not an authenticated "
                "trust record for this brain."
            )

        resolution = self.gate.verify(
            brain_id=brain_id,
            current_provenance=current_provenance,
        )

        return BrainTrustCurrentBinding(
            brain_id=resolution.brain_id,
            current_provenance=(
                resolution.current_provenance
            ),
            root_provenance=resolution.root_provenance,
            depth=resolution.depth,
        )

    def resolve_current(
        self,
        brain_id: str,
    ) -> BrainTrustCurrentBinding:
        """
        Resolve the latest authenticated trust evidence
        as the current binding for the exact brain.

        Unlike resolve(), this method does not accept an
        arbitrary historical provenance. It derives the
        current provenance from authenticated replacement
        history.

        This establishes evidence currentness only.
        It does not grant permission, authority, or execution.
        """

        if not isinstance(brain_id, str):
            raise TypeError(
                "brain_id must be a string."
            )

        if not brain_id.strip():
            raise ValueError(
                "brain_id must not be empty."
            )

        brain_id = brain_id.strip()

        replacement_records = (
            self.gate.verifier.replacement_store.read_recent(
                limit=1000000
            )
        )

        brain_replacements = []

        for record in replacement_records:
            record_brain_id = str(
                record.get("brain_id", "")
            ).strip()

            if record_brain_id != brain_id:
                continue

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

            authentication = str(
                record.get(
                    "provenance",
                    "",
                )
            ).strip()

            if not previous:
                raise ValueError(
                    "Replacement record has no previous provenance."
                )

            if not replacement:
                raise ValueError(
                    "Replacement record has no replacement provenance."
                )

            if not reason:
                raise ValueError(
                    "Replacement record has no reason."
                )

            if not authentication:
                raise ValueError(
                    "Replacement record has no authentication."
                )

            authenticated = (
                self.provenance.verify_replacement(
                    brain_id=brain_id,
                    previous_provenance=previous,
                    replacement_provenance=replacement,
                    reason=reason,
                    provenance=authentication,
                )
            )

            if not authenticated:
                raise ValueError(
                    "Unauthenticated replacement history detected."
                )

            brain_replacements.append(
                {
                    "previous": previous,
                    "replacement": replacement,
                }
            )

        if not brain_replacements:
            trust_records = self.trust_store.read_recent(
                limit=1000000
            )

            for record in trust_records:
                record_brain_id = str(
                    record.get("brain_id", "")
                ).strip()

                if record_brain_id != brain_id:
                    continue

                provenance = str(
                    record.get("provenance", "")
                ).strip()

                if not provenance:
                    continue

                if not self.provenance.verify(record):
                    continue

                binding = self.resolve(
                    brain_id=brain_id,
                    current_provenance=provenance,
                )

                return binding

            raise ValueError(
                "No authenticated current trust evidence "
                "exists for this brain."
            )

        previous_provenances = {
            item["previous"]
            for item in brain_replacements
        }

        replacement_provenances = {
            item["replacement"]
            for item in brain_replacements
        }

        terminal_provenances = (
            replacement_provenances
            - previous_provenances
        )

        if len(terminal_provenances) != 1:
            raise ValueError(
                "Current trust evidence is ambiguous."
            )

        current_provenance = next(
            iter(terminal_provenances)
        )

        return self.resolve(
            brain_id=brain_id,
            current_provenance=current_provenance,
        )
