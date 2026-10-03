from __future__ import annotations

from dataclasses import dataclass

from core.brain.brain_registry import BrainRegistry
from core.brain.specialist_brain import BrainCapability, SpecialistBrain


@dataclass(frozen=True)
class BrainIntelligenceResult:
    """
    Result of specialist-brain selection intelligence.

    This object describes a selection decision only.
    It does not execute work or grant permissions.
    """

    selected_brain_id: str | None
    reason: str


class BrainIntelligence:
    """
    Specialist-brain selection intelligence.

    Responsibilities:
    - match specialization
    - match capability
    - avoid brains that cannot accept more work
    - return a deterministic selection result

    This layer does not execute tasks, grant permissions,
    or modify brain identity.
    """

    def __init__(self, registry: BrainRegistry) -> None:
        if not isinstance(registry, BrainRegistry):
            raise TypeError("registry must be a BrainRegistry.")

        self.registry = registry

    def select_brain(
        self,
        *,
        specialization: str | None = None,
        capability: BrainCapability | None = None,
    ) -> BrainIntelligenceResult:
        if specialization is not None:
            if not isinstance(specialization, str) or not specialization.strip():
                raise ValueError(
                    "specialization must be a non-empty string when provided."
                )

        if capability is not None and not isinstance(
            capability,
            BrainCapability,
        ):
            raise TypeError(
                "capability must be a BrainCapability when provided."
            )

        if specialization is None and capability is None:
            raise ValueError(
                "At least one selection criterion is required."
            )

        candidates = self.registry.list_all()

        matching: list[SpecialistBrain] = []

        for brain in candidates:
            if specialization is not None:
                if brain.specialization != specialization:
                    continue

            if capability is not None:
                if not brain.has_capability(capability):
                    continue

            if not brain.can_accept_work():
                continue

            matching.append(brain)

        if not matching:
            return BrainIntelligenceResult(
                selected_brain_id=None,
                reason="No available specialist brain matches the requested criteria.",
            )

        matching.sort(
            key=lambda brain: (
                brain.resource_state.active_tasks,
                brain.brain_id,
            )
        )

        selected = matching[0]

        criteria: list[str] = []

        if specialization is not None:
            criteria.append(f"specialization={specialization}")

        if capability is not None:
            criteria.append(f"capability={capability.value}")

        reason = (
            "Selected the available specialist brain with the lowest active "
            f"load matching {', '.join(criteria)}."
        )

        return BrainIntelligenceResult(
            selected_brain_id=selected.brain_id,
            reason=reason,
        )
