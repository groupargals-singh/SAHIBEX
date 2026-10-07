"""Tests for Phase Q independent child brain expansion."""

from core.brain.independent_child_brain_expansion import (
    PHASE_Q_VERSION,
    IndependentChildBrainExpansion,
)


def main() -> None:
    engine = IndependentChildBrainExpansion()

    assert PHASE_Q_VERSION == "PHASE-Q-INDEPENDENT-CHILD-1"
    assert len(engine.ITEM_IDS) == 17
    assert len(engine.ITEM_NAMES) == 17
    assert engine.ITEM_IDS[0] == "Q-01"
    assert engine.ITEM_IDS[-1] == "Q-17"

    full = engine.assess(
        brain_foundation=True, brain_identity=True, independent_soul=True,
        constitution=True, purpose=True, memory=True, knowledge=True,
        reasoning=True, planning=True, learning=True, runtime=True,
        communication=True, internal_army=True, internal_labor=True,
        mother_authority_boundary=True, human_authority_boundary=True,
        safety_boundary=True,
    )
    assert full.ready is True
    assert all(full.item_results.values())

    partial = engine.assess(
        brain_foundation=True, brain_identity=True, independent_soul=True,
        constitution=True, purpose=True, memory=False, knowledge=True,
        reasoning=True, planning=True, learning=True, runtime=True,
        communication=True, internal_army=True, internal_labor=True,
        mother_authority_boundary=True, human_authority_boundary=True,
        safety_boundary=True,
    )
    assert partial.ready is False
    assert partial.item_results["Q-06"] is False

    security = engine.security_summary()
    assert security == {
        "read_only": True,
        "executes_actions": False,
        "grants_permission": False,
        "modifies_constitution": False,
        "overrides_human_authority": False,
        "modifies_child_soul": False,
        "overrides_mother_authority": False,
    }

    try:
        engine.assess(
            brain_foundation=True, brain_identity=True, independent_soul=True,
            constitution=True, purpose=True, memory=True, knowledge=True,
            reasoning=True, planning=True, learning=True, runtime=True,
            communication=True, internal_army=True, internal_labor=True,
            mother_authority_boundary=True, human_authority_boundary=True,
            safety_boundary=1,
        )
    except TypeError:
        pass
    else:
        raise AssertionError("Non-bool Phase Q input was accepted")

    print("SAHIBEX PHASE Q INDEPENDENT CHILD BRAIN EXPANSION TEST: PASS")


if __name__ == "__main__":
    main()
