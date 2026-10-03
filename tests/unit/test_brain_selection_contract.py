from __future__ import annotations

from core.brain.brain_registry import BrainRegistry
from core.brain.specialist_brain import (
    BrainCapability,
    SpecialistBrain,
)
from core.brain.brain_selection import BrainSelector


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    # ---------------------------------------------------------
    # 6L-4 Brain Selection & Routing Contract
    # ---------------------------------------------------------

    registry = BrainRegistry()

    research_brain = SpecialistBrain(
        name="Research Specialist",
        description="Handles research tasks.",
        specialization="research",
        capabilities={
            BrainCapability.RESEARCH,
            BrainCapability.ANALYZE,
        },
    )

    coding_brain = SpecialistBrain(
        name="Coding Specialist",
        description="Handles coding tasks.",
        specialization="coding",
        capabilities={
            BrainCapability.CODE,
            BrainCapability.CREATE,
        },
    )

    registry.register(research_brain)
    registry.register(coding_brain)

    selector = BrainSelector(registry)

    # 1. Research capability should select research brain.
    research_candidates = selector.select(
        specialization="research",
        capability=BrainCapability.RESEARCH,
    )

    check(
        research_brain in research_candidates,
        "Research brain must be selected for research capability.",
    )

    check(
        coding_brain not in research_candidates,
        "Coding brain must not be selected for research capability.",
    )

    # 2. Coding capability should select coding brain.
    coding_candidates = selector.select(
        specialization="coding",
        capability=BrainCapability.CODE,
    )

    check(
        coding_brain in coding_candidates,
        "Coding brain must be selected for coding capability.",
    )

    check(
        research_brain not in coding_candidates,
        "Research brain must not be selected for coding capability.",
    )

    # 3. Capability-only selection should work.
    analysis_candidates = selector.select(
        capability=BrainCapability.ANALYZE,
    )

    check(
        research_brain in analysis_candidates,
        "Analysis capability must find research brain.",
    )

    # 4. Specialization-only selection should work.
    research_only = selector.select(
        specialization="research",
    )

    check(
        research_brain in research_only,
        "Specialization-only selection must find research brain.",
    )

    # 5. No matching brain must return an empty list.
    missing = selector.select(
        specialization="finance",
    )

    check(
        missing == [],
        "No matching brain must return an empty list.",
    )

    # 6. Invalid capability must be rejected.
    invalid_rejected = False

    try:
        selector.select(
            capability="research",
        )
    except TypeError:
        invalid_rejected = True

    check(
        invalid_rejected,
        "Invalid capability must be rejected.",
    )

    # 7. Empty selection criteria must be rejected.
    empty_rejected = False

    try:
        selector.select()
    except ValueError:
        empty_rejected = True

    check(
        empty_rejected,
        "Selection without criteria must be rejected.",
    )

    # 8. Selector must not execute a brain.
    forbidden_methods = {
        "execute",
        "run",
        "invoke",
    }

    selector_methods = set(dir(selector))

    check(
        selector_methods.isdisjoint(forbidden_methods),
        "BrainSelector must not execute or invoke brains.",
    )

    print(
        "SAHIBEX 6L-4 BRAIN SELECTION CONTRACT TEST: PASS"
    )


if __name__ == "__main__":
    main()
