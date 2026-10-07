from core.brain.internal_state_bus import InternalStateBus


def main() -> None:
    bus = InternalStateBus()
    seen = []
    bus.subscribe("health", seen.append)

    event = bus.publish("health", "healthy", "health_monitor")
    assert event.sequence == 1
    assert bus.get("health") == "healthy"
    assert seen == [event]

    bus.publish("mode", "sleep", "wake_sleep")
    assert bus.get("mode") == "sleep"
    assert bus.sequence == 2
    assert len(bus.history) == 2
    assert not bus.grants_permission()
    assert not bus.executes_actions()
    assert not bus.modifies_system()

    try:
        bus.publish("", 1, "test")
    except ValueError:
        pass
    else:
        raise AssertionError("empty topic must fail")

    print("INTERNAL_STATE_BUS_SMOKE_PASS")


if __name__ == "__main__":
    main()
