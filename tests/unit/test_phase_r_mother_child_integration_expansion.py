from core.brain.mother_child_integration_expansion import (
    PHASE_R_VERSION,
    MotherChildIntegrationExpansion,
)


def main():
    engine = MotherChildIntegrationExpansion()
    assert PHASE_R_VERSION == "PHASE-R-MOTHER-CHILD-1"
    assert len(engine.ITEM_IDS) == 15
    assert len(engine.ITEM_NAMES) == 15
    assert engine.ITEM_IDS == tuple(f"R-{i:02d}" for i in range(1, 16))

    full = engine.assess(**{item: True for item in engine.ITEM_IDS})
    assert full.ready
    assert all(full.readiness)

    partial = engine.assess(**{item: True for item in engine.ITEM_IDS[:-1]})
    assert not partial.ready
    assert partial.readiness[-1] is False

    try:
        engine.assess(**{"R-01": "yes"})
    except TypeError:
        pass
    else:
        raise AssertionError("non-bool coverage must fail")

    security = engine.security_summary()
    assert security == {
        "read_only": True,
        "executes_actions": False,
        "grants_permission": False,
        "modifies_constitution": False,
        "overrides_human_authority": False,
        "overrides_mother_authority": False,
        "modifies_child_identity": False,
    }
    print("SAHIBEX PHASE R MOTHER-CHILD INTEGRATION EXPANSION TEST: PASS")


if __name__ == "__main__":
    main()
