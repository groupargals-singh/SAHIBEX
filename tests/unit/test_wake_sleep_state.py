from core.brain.brain_clock import BrainClock, BrainClockState
from core.brain.wake_sleep_state import WakeSleepController, WakeSleepState


def test_initial_sleep_and_security_boundary():
    controller = WakeSleepController()

    assert controller.state is WakeSleepState.SLEEPING
    assert controller.can_process is False
    assert controller.can_heartbeat is True
    assert controller.grants_permission() is False
    assert controller.executes_actions() is False
    assert controller.executes_protected_actions() is False
    assert controller.modifies_system() is False
    assert controller.is_lifecycle_only() is True


def test_wake_and_sleep_are_deterministic():
    controller = WakeSleepController()

    wake = controller.wake("test_wake")
    assert wake.previous is WakeSleepState.SLEEPING
    assert wake.current is WakeSleepState.AWAKE
    assert controller.state is WakeSleepState.AWAKE
    assert controller.can_process is True

    sleep = controller.sleep("test_sleep")
    assert sleep.previous is WakeSleepState.AWAKE
    assert sleep.current is WakeSleepState.SLEEPING
    assert controller.state is WakeSleepState.SLEEPING
    assert controller.can_process is False
    assert [item.reason for item in controller.history] == [
        "test_wake",
        "test_sleep",
    ]


def test_brain_clock_follows_wake_sleep_boundary():
    clock = BrainClock(tick_interval=0.01, sleeper=lambda _: None)
    controller = WakeSleepController(clock=clock)

    assert clock.state is BrainClockState.STOPPED

    controller.wake()
    assert controller.state is WakeSleepState.AWAKE
    assert clock.state is BrainClockState.RUNNING

    controller.sleep()
    assert controller.state is WakeSleepState.SLEEPING
    assert controller.can_process is False
    assert controller.can_heartbeat is True
    assert clock.state is BrainClockState.RUNNING


def test_failed_clock_cannot_be_overridden_by_wake():
    clock = BrainClock()
    clock.start()
    clock.tick(lambda _: (_ for _ in ()).throw(RuntimeError("clock failure")))

    controller = WakeSleepController(clock=clock)

    try:
        controller.wake("failed_clock")
    except RuntimeError as exc:
        assert "failed clock" in str(exc)
    else:
        raise AssertionError("wake must fail when the clock is failed")

    assert controller.state is WakeSleepState.SLEEPING
    assert clock.state is BrainClockState.FAILED


def test_invalid_transitions_and_reasons_are_blocked():
    controller = WakeSleepController()

    try:
        controller.sleep()
    except RuntimeError:
        pass
    else:
        raise AssertionError("sleep from sleeping must fail")

    try:
        controller.wake()
        controller.wake()
    except RuntimeError:
        pass
    else:
        raise AssertionError("wake while awake must fail")

    try:
        controller.sleep("")
    except ValueError:
        pass
    else:
        raise AssertionError("empty reason must fail")
