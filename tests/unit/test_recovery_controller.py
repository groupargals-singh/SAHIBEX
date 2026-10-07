from core.brain.recovery_controller import RecoveryController, RecoveryState


def main() -> None:
    r = RecoveryController()
    assert r.state is RecoveryState.READY

    assert r.begin("fault detected").state is RecoveryState.RECOVERING
    assert r.complete("state restored").state is RecoveryState.RECOVERED
    assert r.reset("ready again").state is RecoveryState.READY
    assert r.fail("recovery fault").state is RecoveryState.FAILED

    assert len(r.history) == 4
    assert not r.grants_permission()
    assert not r.executes_actions()
    assert not r.modifies_system()
    assert not r.overrides_human_authority()

    try:
        r.begin("")
    except ValueError:
        pass
    else:
        raise AssertionError("empty reason must fail")

    print("RECOVERY_CONTROLLER_SMOKE_PASS")


if __name__ == "__main__":
    main()
