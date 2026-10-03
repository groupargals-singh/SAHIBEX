from __future__ import annotations

from core.brain.brain_registry import BrainRegistry
from core.brain.specialist_brain import (
    BrainCapability,
    SpecialistBrain,
)


class BrainSelector:
    """
    Candidate selector for SAHIBEX specialist brains.

    Responsibilities:
    - select brains by specialization
    - select brains by capability
    - combine specialization and capability criteria

    This class does not:
    - execute a brain
    - invoke a model
    - grant permission
    - authorize protected actions
    - change brain state
    """

    def __init__(
        self,
        registry: BrainRegistry,
    ) -> None:
        if not isinstance(registry, BrainRegistry):
            raise TypeError(
                "registry must be a BrainRegistry."
            )

        self.registry = registry

    def select(
        self,
        *,
        specialization: str | None = None,
        capability: BrainCapability | None = None,
    ) -> list[SpecialistBrain]:

        if specialization is None and capability is None:
            raise ValueError(
                "At least one selection criterion is required."
            )

        if specialization is not None:
            if not isinstance(specialization, str):
                raise TypeError(
                    "specialization must be a string."
                )

            specialization = specialization.strip()

            if not specialization:
                raise ValueError(
                    "specialization cannot be empty."
                )

        if capability is not None:
            if not isinstance(capability, BrainCapability):
                raise TypeError(
                    "capability must be a BrainCapability."
                )

        candidates = self.registry.list_all()

        if specialization is not None:
            normalized = specialization.lower()

            candidates = [
                brain
                for brain in candidates
                if brain.specialization.strip().lower()
                == normalized
            ]

        if capability is not None:
            candidates = [
                brain
                for brain in candidates
                if brain.has_capability(capability)
            ]

        return candidates
