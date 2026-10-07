from core.brain.living_child_loop_expansion import PHASE_S_VERSION, LivingChildLoopExpansion


def main():
    engine = LivingChildLoopExpansion()
    assert PHASE_S_VERSION == "PHASE-S-LIVING-CHILD-1"
    assert len(engine.ITEM_IDS) == 17
    assert len(engine.ITEM_NAMES) == 17
    assert engine.ITEM_IDS == tuple(f"S-{i:02d}" for i in range(1, 18))

    full = engine.assess(**{item: True for item in engine.ITEM_IDS})
    assert full.ready and all(full.readiness)

    partial = engine.assess(**{item: True for item in engine.ITEM_IDS[:-1]})
    assert not partial.ready and partial.readiness[-1] is False

    try:
        engine.assess(**{"S-01": "yes"})
    except TypeError:
        pass
    else:
        raise AssertionError("non-bool coverage must fail")

    assert engine.security_summary() == {
        "read_only": True,
        "executes_actions": False,
        "grants_permission": False,
        "modifies_constitution": False,
        "overrides_human_authority": False,
        "overrides_mother_authority": False,
        "modifies_child_identity": False,
    }
    print("SAHIBEX PHASE S LIVING CHILD LOOP EXPANSION TEST: PASS")


if __name__ == "__main__":
    main()
