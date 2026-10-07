from core.brain.learning_expansion import (
    PHASE_M_VERSION,
    LearningExpansion,
)


def main() -> None:
    engine = LearningExpansion()
    result = engine.assess()

    assert PHASE_M_VERSION == "PHASE-M-LEARNING-1"
    assert result.phase == "M"
    assert result.version == PHASE_M_VERSION
    assert len(result.scores) == 15
    assert result.ready is True
    assert tuple(result.scores) == engine.ITEM_IDS

    assert engine.assess(safety=0.79).ready is False

    try:
        engine.assess(confidence=1.1)
    except ValueError:
        pass
    else:
        raise AssertionError("out-of-range score must fail")

    security = engine.security_summary()
    assert security == {
        "read_only": True,
        "executes_actions": False,
        "grants_permission": False,
        "modifies_constitution": False,
        "overrides_human_authority": False,
    }

    print("SAHIBEX PHASE M LEARNING EXPANSION TEST: PASS")


if __name__ == "__main__":
    main()
