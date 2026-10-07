from __future__ import annotations

from core.brain.executive_expansion import (
    ExecutiveBrainExpansion,
    PHASE_I_VERSION,
)


def main() -> None:
    engine = ExecutiveBrainExpansion()
    results = engine.assess(
        goal="Complete Phase I safely",
        priority=0.9,
        decision_confidence=0.9,
        risk=0.1,
        uncertainty=0.1,
        memory_available=True,
        knowledge_available=True,
        specialists_available=True,
        execution_monitored=True,
        human_approval_required=True,
    )

    assert PHASE_I_VERSION == "PHASE-I-EXECUTIVE-1"
    assert len(results) == 17
    assert tuple(r.item_id for r in results) == tuple(
        f"I-{i:02d}" for i in range(1, 18)
    )
    assert all(0.0 <= r.score <= 1.0 for r in results)
    assert all(r.ready for r in results)

    blocked = engine.assess(
        goal="High uncertainty decision",
        priority=0.8,
        decision_confidence=0.8,
        risk=0.9,
        uncertainty=0.9,
        memory_available=False,
        knowledge_available=False,
        specialists_available=False,
        execution_monitored=True,
        human_approval_required=True,
    )
    assert not blocked[11].ready
    assert not blocked[12].ready
    assert not blocked[13].ready

    security = engine.security_summary()
    assert security == {
        "read_only": True,
        "executes_actions": False,
        "grants_permission": False,
        "modifies_constitution": False,
        "overrides_human_authority": False,
    }

    forbidden = {"execute", "grant_permission", "modify_constitution"}
    assert not forbidden.intersection(dir(engine))

    print("SAHIBEX PHASE I EXECUTIVE EXPANSION TEST: PASS")


if __name__ == "__main__":
    main()
