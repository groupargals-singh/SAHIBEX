from __future__ import annotations

from core.brain.brain_registry import BrainRegistry
from core.brain.intelligence import BrainIntelligence
from core.brain.operational_specialist_dispatch import (
    OperationalSpecialistDispatcher,
    SpecialistDispatchResult,
)
from core.brain.specialist_brain import (
    BrainCapability,
    BrainStatus,
    SpecialistBrain,
)


def main() -> None:
    registry = BrainRegistry()

    research_brain = SpecialistBrain(
        name="Research Runtime Brain",
        description="Handles research requests.",
        specialization="research",
        capabilities={
            BrainCapability.RESEARCH,
            BrainCapability.ANALYZE,
        },
    )

    coding_brain = SpecialistBrain(
        name="Coding Runtime Brain",
        description="Handles coding requests.",
        specialization="coding",
        capabilities={
            BrainCapability.CODE,
            BrainCapability.CREATE,
        },
    )

    research_brain.transition_to(BrainStatus.READY)
    coding_brain.transition_to(BrainStatus.READY)

    registry.register(research_brain)
    registry.register(coding_brain)

    intelligence = BrainIntelligence(registry)

    dispatcher = OperationalSpecialistDispatcher(
        registry=registry,
        intelligence=intelligence,
    )

    calls: list[tuple[str, dict[str, object]]] = []

    def research_handler(
        request: str,
        metadata: dict[str, object],
    ) -> dict[str, object]:
        calls.append((request, metadata))
        return {
            "handled": True,
            "type": "research",
            "request": request,
        }

    dispatcher.register_handler(
        research_brain.brain_id,
        research_handler,
    )

    # ---------------------------------------------------------
    # 1. Real dispatch to selected specialist
    # ---------------------------------------------------------
    result = dispatcher.dispatch(
        request="Research AI security.",
        specialization="research",
        capability=BrainCapability.RESEARCH,
        metadata={"test": True},
    )

    assert isinstance(result, SpecialistDispatchResult)
    assert result.success is True
    assert result.brain_id == research_brain.brain_id
    assert result.result["handled"] is True
    assert result.result["type"] == "research"

    # Handler must receive normalized runtime metadata.
    assert len(calls) == 1
    assert calls[0][0] == "Research AI security."
    assert calls[0][1]["brain_id"] == research_brain.brain_id
    assert calls[0][1]["specialization"] == "research"
    assert calls[0][1]["test"] is True

    # Runtime state must be released after dispatch.
    assert research_brain.status == BrainStatus.READY
    assert research_brain.resource_state.active_tasks == 0

    # ---------------------------------------------------------
    # 2. Unknown handler must not execute
    # ---------------------------------------------------------
    missing_handler = dispatcher.dispatch(
        request="Write code.",
        specialization="coding",
        capability=BrainCapability.CODE,
    )

    assert missing_handler.success is False
    assert missing_handler.brain_id == coding_brain.brain_id
    assert "no registered runtime handler" in missing_handler.error.lower()
    assert coding_brain.status == BrainStatus.READY
    assert coding_brain.resource_state.active_tasks == 0

    # ---------------------------------------------------------
    # 3. Unknown specialization must fail safely
    # ---------------------------------------------------------
    no_brain = dispatcher.dispatch(
        request="Handle finance.",
        specialization="finance",
        capability=BrainCapability.ANALYZE,
    )

    assert no_brain.success is False
    assert no_brain.brain_id is None

    # ---------------------------------------------------------
    # 4. Handler failure must release runtime state
    # ---------------------------------------------------------
    failing_brain = SpecialistBrain(
        name="Failing Research Brain",
        description="Test failure brain.",
        specialization="failure-research",
        capabilities={BrainCapability.RESEARCH},
    )

    failing_brain.transition_to(BrainStatus.READY)
    registry.register(failing_brain)

    def failing_handler(
        request: str,
        metadata: dict[str, object],
    ) -> object:
        raise RuntimeError("intentional test failure")

    dispatcher.register_handler(
        failing_brain.brain_id,
        failing_handler,
    )

    failed = dispatcher.dispatch(
        request="Trigger failure.",
        specialization="failure-research",
        capability=BrainCapability.RESEARCH,
    )

    assert failed.success is False
    assert failed.brain_id == failing_brain.brain_id
    assert "intentional test failure" in failed.error

    assert failing_brain.status == BrainStatus.READY
    assert failing_brain.resource_state.active_tasks == 0

    # ---------------------------------------------------------
    # 5. Protected capabilities are not permission grants
    # ---------------------------------------------------------
    dispatcher_methods = set(dir(dispatcher))

    assert "grant_permission" not in dispatcher_methods
    assert "modify_constitution" not in dispatcher_methods
    assert "execute_command" not in dispatcher_methods

    # ---------------------------------------------------------
    # 6. Duplicate handler registration must be rejected
    # ---------------------------------------------------------
    duplicate_rejected = False

    try:
        dispatcher.register_handler(
            research_brain.brain_id,
            research_handler,
        )
    except ValueError:
        duplicate_rejected = True

    assert duplicate_rejected is True

    print(
        "SAHIBEX 6O-5 SPECIALIST BRAIN REAL DISPATCH TEST: PASS"
    )


if __name__ == "__main__":
    main()
