from __future__ import annotations

from core.brain.specialist_brain import (
    BrainCapability,
    SpecialistBrain,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    # ---------------------------------------------------------
    # 6L-3 Brain Capability Model Contract
    # ---------------------------------------------------------

    # 1. Capability enum must expose the core capability types.
    required_capabilities = {
        "THINK",
        "RESEARCH",
        "ANALYZE",
        "CODE",
        "CREATE",
        "VERIFY",
        "PLAN",
        "READ",
    }

    actual_capabilities = {
        capability.name
        for capability in BrainCapability
    }

    check(
        required_capabilities.issubset(actual_capabilities),
        "BrainCapability is missing required capability types.",
    )

    # 2. A brain can explicitly declare multiple capabilities.
    brain = SpecialistBrain(
        name="Research Analyst",
        description="Research and analysis specialist.",
        specialization="research",
        capabilities={
            BrainCapability.RESEARCH,
            BrainCapability.ANALYZE,
            BrainCapability.VERIFY,
        },
    )

    check(
        brain.has_capability(BrainCapability.RESEARCH),
        "Brain must report declared research capability.",
    )

    check(
        brain.has_capability(BrainCapability.ANALYZE),
        "Brain must report declared analysis capability.",
    )

    check(
        brain.has_capability(BrainCapability.VERIFY),
        "Brain must report declared verification capability.",
    )

    # 3. Undeclared capability must return False.
    check(
        not brain.has_capability(BrainCapability.CODE),
        "Undeclared capability must not be reported.",
    )

    # 4. Capability listing must be explicit.
    capabilities = brain.list_capabilities()

    check(
        isinstance(capabilities, set),
        "list_capabilities() must return a set.",
    )

    check(
        capabilities == {
            BrainCapability.RESEARCH,
            BrainCapability.ANALYZE,
            BrainCapability.VERIFY,
        },
        "Capability listing must match declared capabilities.",
    )

    # 5. Capability checks must reject invalid values.
    invalid_rejected = False

    try:
        brain.has_capability("research")
    except TypeError:
        invalid_rejected = True

    check(
        invalid_rejected,
        "Invalid capability values must be rejected.",
    )

    # 6. Capability information must not imply permission.
    #
    # A capability describes what a brain is designed to do.
    # It does not grant authority to perform protected actions.
    check(
        not hasattr(brain, "permission"),
        "Capability model must not embed permission state.",
    )

    check(
        not hasattr(brain, "authorization"),
        "Capability model must not embed authorization state.",
    )

    # 7. Capability objects must remain model-independent.
    field_names = {
        field_name.lower()
        for field_name in brain.__dataclass_fields__
    }

    forbidden_model_fields = {
        "model",
        "model_name",
        "provider",
        "api_key",
    }

    check(
        field_names.isdisjoint(forbidden_model_fields),
        "Capability model must remain model/provider independent.",
    )

    print(
        "SAHIBEX 6L-3 BRAIN CAPABILITY CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
