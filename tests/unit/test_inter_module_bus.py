from core.brain.inter_module_bus import InterModuleBus


def main() -> None:
    bus = InterModuleBus(max_workers=2)
    seen = []

    bus.subscribe("state", lambda msg: seen.append(("a", msg.payload)))
    bus.subscribe("state", lambda msg: seen.append(("b", msg.payload)))

    results = bus.publish("state", "clock", {"awake": True})
    assert len(results) == 2
    assert all(item is None for item in results)
    assert sorted(seen) == [("a", {"awake": True}), ("b", {"awake": True})]
    assert bus.history[0].sequence == 1
    assert bus.max_workers == 2
    assert not bus.grants_permission()
    assert not bus.executes_protected_actions()
    assert not bus.modifies_system()

    try:
        InterModuleBus(0)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid worker count must fail")

    print("INTER_MODULE_BUS_SMOKE_PASS")


if __name__ == "__main__":
    main()
