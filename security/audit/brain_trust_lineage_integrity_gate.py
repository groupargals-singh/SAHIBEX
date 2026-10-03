from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from security.audit.brain_trust_lineage_resolver import (
    BrainTrustLineageResolver,
)
from security.audit.brain_trust_lineage_verifier import (
    BrainTrustLineageVerifier,
)


@dataclass(frozen=True)
class BrainTrustLineageIntegrityGateResult:
    passed: bool
    brain_id: str
    current_provenance: str
    root_provenance: str | None
    depth: int
    reason: str


class BrainTrustLineageIntegrityGate:
    """
    Verifies persistent trust-evidence lineage.

    This gate does not grant permissions or authority,
    execute actions, or modify the constitution.
    """

    def __init__(
        self,
        storage_directory: Path,
    ) -> None:
        self.storage_directory = Path(storage_directory)
        self.verifier = BrainTrustLineageVerifier(
            self.storage_directory
        )
        self.resolver = BrainTrustLineageResolver(
            self.storage_directory
        )

    def verify(
        self,
        *,
        brain_id: str,
        current_provenance: str,
    ) -> BrainTrustLineageIntegrityGateResult:
        if (
            not isinstance(brain_id, str)
            or not brain_id.strip()
        ):
            raise ValueError("brain_id is required.")

        if (
            not isinstance(current_provenance, str)
            or not current_provenance.strip()
        ):
            raise ValueError(
                "current_provenance is required."
            )

        brain_id = brain_id.strip()
        current_provenance = current_provenance.strip()

        persistent_result = self.verifier.verify(
            brain_id=brain_id
        )

        if not persistent_result.verified:
            return BrainTrustLineageIntegrityGateResult(
                passed=False,
                brain_id=brain_id,
                current_provenance=current_provenance,
                root_provenance=None,
                depth=0,
                reason=(
                    "Persistent lineage verification failed: "
                    f"{persistent_result.reason}"
                ),
            )

        all_history = (
            self.verifier.replacement_store.read_recent(
                limit=1000000
            )
        )

        for record in all_history:
            owner = str(
                record.get("brain_id", "")
            ).strip()

            if owner == brain_id:
                continue

            previous = str(
                record.get(
                    "previous_provenance", ""
                )
            ).strip()

            replacement = str(
                record.get(
                    "replacement_provenance", ""
                )
            ).strip()

            if current_provenance in {
                previous,
                replacement,
            }:
                return BrainTrustLineageIntegrityGateResult(
                    passed=False,
                    brain_id=brain_id,
                    current_provenance=current_provenance,
                    root_provenance=None,
                    depth=0,
                    reason=(
                        "Cross-brain provenance detected."
                    ),
                )

        try:
            resolved = self.resolver.resolve(
                brain_id=brain_id,
                current_provenance=current_provenance,
            )
        except (TypeError, ValueError) as exc:
            return BrainTrustLineageIntegrityGateResult(
                passed=False,
                brain_id=brain_id,
                current_provenance=current_provenance,
                root_provenance=None,
                depth=0,
                reason=f"Lineage resolution failed: {exc}",
            )

        if (
            not resolved.lineage
            or resolved.lineage[0] != current_provenance
            or resolved.depth != len(resolved.lineage)
        ):
            return BrainTrustLineageIntegrityGateResult(
                passed=False,
                brain_id=brain_id,
                current_provenance=current_provenance,
                root_provenance=None,
                depth=0,
                reason="Resolved lineage integrity check failed.",
            )

        return BrainTrustLineageIntegrityGateResult(
            passed=True,
            brain_id=brain_id,
            current_provenance=current_provenance,
            root_provenance=resolved.root_provenance,
            depth=resolved.depth,
            reason=(
                "Persistent trust-evidence "
                "lineage integrity verified."
            ),
        )
