from __future__ import annotations

from core.brain.brain_registry import BrainRegistry
from core.brain.specialist_brain import (
    BrainCapability,
    SpecialistBrain,
)
from core.brain.verification import BrainTrustStatus


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    registry = BrainRegistry()

    research = SpecialistBrain(
        name="Research Specialist",
        description="Research-focused specialist brain.",
        specialization="research",
        capabilities={BrainCapability.RESEARCH, BrainCapability.ANALYZE},
    )

    coding = SpecialistBrain(
        name="Coding Specialist",
        description="Code-focused specialist brain.",
        specialization="coding",
        capabilities={BrainCapability.CODE, BrainCapability.CREATE},
    )

    verifier = SpecialistBrain(
        name="Verification Specialist",
        description="Verification-focused specialist brain.",
        specialization="verification",
        capabilities={BrainCapability.VERIFY, BrainCapability.ANALYZE},
    )

    registry.register(research)
    registry.register(coding)
    registry.register(verifier)

    from core.brain.intelligence import (
        BrainIntelligence,
        BrainIntelligenceResult,
    )

    intelligence = BrainIntelligence(registry)

    # Result contract.
    result = intelligence.select_brain(
        specialization="research",
        capability=BrainCapability.RESEARCH,
    )

    check(
        isinstance(result, BrainIntelligenceResult),
        "select_brain must return BrainIntelligenceResult.",
    )

    check(
        result.selected_brain_id == research.brain_id,
        "Matching specialist brain must be selected.",
    )

    check(
        result.reason,
        "Intelligence result must contain a reason.",
    )

    # Capability-aware selection.
    result = intelligence.select_brain(
        capability=BrainCapability.CODE,
    )

    check(
        result.selected_brain_id == coding.brain_id,
        "Capability matching must select the coding brain.",
    )

    # No matching brain.
    result = intelligence.select_brain(
        specialization="medical",
    )

    check(
        result.selected_brain_id is None,
        "Unknown specialization must produce no selection.",
    )

    check(
        result.reason,
        "No-selection result must contain a reason.",
    )

    # Unverified brains must not automatically become trusted.
    check(
        research.trust_status == BrainTrustStatus.UNVERIFIED,
        "New specialist brain must remain unverified.",
    )

    # Load-aware selection.
    research.update_load(
        active_tasks=research.resource_state.max_concurrent_tasks
    )

    result = intelligence.select_brain(
        specialization="research",
    )

    check(
        result.selected_brain_id is None,
        "Brain at capacity must not be selected.",
    )

    research.update_load(active_tasks=0)

    result = intelligence.select_brain(
        specialization="research",
    )

    check(
        result.selected_brain_id == research.brain_id,
        "Available brain must be selectable after load decreases.",
    )

    # Intelligence must not change brain identity.
    original_ids = {
        research.brain_id,
        coding.brain_id,
        verifier.brain_id,
    }

    intelligence.select_brain(
        capability=BrainCapability.ANALYZE
    )

    current_ids = {
        research.brain_id,
        coding.brain_id,
        verifier.brain_id,
    }

    check(
        current_ids == original_ids,
        "Intelligence must preserve brain identities.",
    )

    # Intelligence must not contain permission or credential state.
    intelligence_fields = set(vars(intelligence))

    check(
        "permission" not in intelligence_fields,
        "Intelligence instance must not contain permission fields.",
    )

    check(
        "authorization" not in intelligence_fields,
        "Intelligence instance must not contain authorization fields.",
    )

    check(
        "api_key" not in intelligence_fields,
        "Intelligence instance must not contain credential fields.",
    )

    print("SAHIBEX 6L-10 BRAIN INTELLIGENCE CONTRACT TEST: PASS")


if __name__ == "__main__":
    main()
