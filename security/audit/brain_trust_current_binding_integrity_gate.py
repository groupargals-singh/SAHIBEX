from __future__ import annotations

from security.audit.brain_trust_current_binding import (
    BrainTrustCurrentBinding,
)
from security.audit.brain_trust_current_binding_resolver import (
    BrainTrustCurrentBindingResolver,
)


class BrainTrustCurrentBindingIntegrityGate:
    """
    Final integrity gate for current trust evidence.

    This gate verifies that the resolved current evidence:

    - belongs to the exact brain,
    - is authenticated,
    - belongs to a valid trust lineage,
    - is the latest authenticated evidence,
    - remains persistent and unambiguous.

    This gate does not grant permission, authority,
    execution rights, or system control.
    """

    def __init__(
        self,
        storage_directory,
    ) -> None:
        self.resolver = BrainTrustCurrentBindingResolver(
            storage_directory
        )

    def verify(
        self,
        brain_id: str,
    ) -> BrainTrustCurrentBinding:
        """
        Verify and return the final current trust binding.
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

        binding = self.resolver.resolve_current(
            brain_id
        )

        if binding.brain_id != brain_id:
            raise ValueError(
                "Current binding belongs to another brain."
            )

        if not binding.current_provenance.strip():
            raise ValueError(
                "Current binding has no provenance."
            )

        if not binding.root_provenance.strip():
            raise ValueError(
                "Current binding has no root provenance."
            )

        if binding.depth < 1:
            raise ValueError(
                "Current binding has invalid lineage depth."
            )

        historical_binding = self.resolver.resolve(
            brain_id=brain_id,
            current_provenance=(
                binding.current_provenance
            ),
        )

        if (
            historical_binding.current_provenance
            != binding.current_provenance
        ):
            raise ValueError(
                "Current provenance failed lineage consistency."
            )

        if (
            historical_binding.root_provenance
            != binding.root_provenance
        ):
            raise ValueError(
                "Current root provenance failed lineage consistency."
            )

        if historical_binding.depth != binding.depth:
            raise ValueError(
                "Current lineage depth failed consistency."
            )

        return binding
