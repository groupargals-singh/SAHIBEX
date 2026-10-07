from core.brain.emergency_stop import EmergencyStop, EmergencyStopState


def main() -> None:
    stop = EmergencyStop()
    assert stop.state is EmergencyStopState.CLEAR
    assert stop.allows_protected_execution()
    assert not stop.grants_permission()

    event = stop.engage("operator emergency")
    assert stop.engaged
    assert event.reason == "operator emergency"
    assert stop.requires_execution_block()
    assert not stop.allows_protected_execution()
    assert not stop.executes_actions()
    assert not stop.modifies_system()
    assert not stop.overrides_human_authority()

    cleared = stop.clear("operator cleared")
    assert cleared.state is EmergencyStopState.CLEAR
    assert stop.allows_protected_execution()
    assert len(stop.history) == 2

    try:
        stop.engage("")
    except ValueError:
        pass
    else:
        raise AssertionError("empty reason must fail")

    print("EMERGENCY_STOP_SMOKE_PASS")


if __name__ == "__main__":
    main()
