from __future__ import annotations

from dataclasses import fields

from dataclasses import is_dataclass


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    # ---------------------------------------------------------
    # 6L-1 Specialist Brain Contract
    # ---------------------------------------------------------
    #
    # Contract requirements:
    #
    # 1. A specialist brain has a stable identity.
    # 2. It has a name and description.
    # 3. It declares its specialization.
    # 4. It declares capabilities.
    # 5. It has an explicit lifecycle state.
    # 6. It can be enabled/disabled through lifecycle state.
    # 7. It must not implicitly inherit another brain's identity.
    # 8. The contract remains model-independent.
    #
    # The production implementation will be introduced only after
    # this contract is verified.
    # ---------------------------------------------------------

    from core.brain.specialist_brain import (
        BrainCapability,
        BrainStatus,
        SpecialistBrain,
    )

    # ---------------------------------------------------------
    # 1. Required types must exist.
    # ---------------------------------------------------------
    check(
        is_dataclass(SpecialistBrain),
        "SpecialistBrain must be a dataclass.",
    )

    check(
        BrainCapability is not None,
        "BrainCapability must exist.",
    )

    check(
        BrainStatus is not None,
        "BrainStatus must exist.",
    )

    # ---------------------------------------------------------
    # 2. Required BrainStatus lifecycle states.
    # ---------------------------------------------------------
    required_statuses = {
        "REGISTERED",
        "READY",
        "ACTIVE",
        "PAUSED",
        "DISABLED",
        "FAILED",
    }

    actual_statuses = {
        member.name
        for member in BrainStatus
    }

    check(
        required_statuses.issubset(actual_statuses),
        "BrainStatus must contain all required lifecycle states.",
    )

    # ---------------------------------------------------------
    # 3. Required SpecialistBrain fields.
    # ---------------------------------------------------------
    field_names = {
        field.name
        for field in fields(SpecialistBrain)
    }

    required_fields = {
        "brain_id",
        "name",
        "description",
        "specialization",
        "capabilities",
        "status",
    }

    check(
        required_fields.issubset(field_names),
        "SpecialistBrain must expose all required fields.",
    )

    # ---------------------------------------------------------
    # 4. Identity must be explicit.
    # ---------------------------------------------------------
    brain = SpecialistBrain(
        name="Research Specialist",
        description="Specialist for research tasks.",
        specialization="research",
        capabilities={
            BrainCapability.RESEARCH,
        },
    )

    check(
        isinstance(brain.brain_id, str),
        "brain_id must be a string.",
    )

    check(
        bool(brain.brain_id),
        "brain_id must not be empty.",
    )

    check(
        brain.name == "Research Specialist",
        "Brain name must be preserved.",
    )

    check(
        brain.description == "Specialist for research tasks.",
        "Brain description must be preserved.",
    )

    check(
        brain.specialization == "research",
        "Brain specialization must be preserved.",
    )

    # ---------------------------------------------------------
    # 5. Capabilities must be explicit.
    # ---------------------------------------------------------
    check(
        BrainCapability.RESEARCH in brain.capabilities,
        "Research capability must be preserved.",
    )

    # ---------------------------------------------------------
    # 6. New brain must start in REGISTERED state.
    # ---------------------------------------------------------
    check(
        brain.status == BrainStatus.REGISTERED,
        "New specialist brain must start REGISTERED.",
    )

    # ---------------------------------------------------------
    # 7. Identity must be unique per instance.
    # ---------------------------------------------------------
    second_brain = SpecialistBrain(
        name="Research Specialist",
        description="Another research specialist.",
        specialization="research",
        capabilities={
            BrainCapability.RESEARCH,
        },
    )

    check(
        brain.brain_id != second_brain.brain_id,
        "Separate brain instances must have separate identities.",
    )

    # ---------------------------------------------------------
    # 8. Model independence.
    # ---------------------------------------------------------
    field_names_lower = {
        name.lower()
        for name in field_names
    }

    forbidden_model_fields = {
        "model",
        "model_name",
        "provider",
        "api_key",
    }

    check(
        field_names_lower.isdisjoint(forbidden_model_fields),
        "SpecialistBrain contract must remain model/provider independent.",
    )

    print(
        "SAHIBEX 6L-1 SPECIALIST BRAIN CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
