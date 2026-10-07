from core.brain.brain_clock import BrainClock, BrainClockState
from core.brain.health_monitor import BrainHealth, HealthMonitor
from core.brain.wake_sleep_state import WakeSleepController, WakeSleepState


def test_sleep_is_online_low_activity():
    clock = BrainClock(tick_interval=0.01, sleeper=lambda _: None)
    lifecycle = WakeSleepController(clock=clock)
    monitor = HealthMonitor(wake_sleep=lifecycle, clock=clock)

    snapshot = monitor.check()

    assert lifecycle.state is WakeSleepState.SLEEPING
    assert snapshot.online is True
    assert snapshot.sleeping is True
    assert snapshot.health is BrainHealth.HEALTHY
    assert snapshot.reason == "online_sleep_mode_low_activity"
    assert monitor.sleep_is_offline() is False
    assert monitor.keeps_mother_brain_online() is True


def test_awake_with_running_clock_is_healthy():
    clock = BrainClock(tick_interval=0.01, sleeper=lambda _: None)
    lifecycle = WakeSleepController(clock=clock)
    monitor = HealthMonitor(wake_sleep=lifecycle, clock=clock)

    lifecycle.wake()
    snapshot = monitor.check()

    assert clock.state is BrainClockState.RUNNING
    assert snapshot.online is True
    assert snapshot.awake is True
    assert snapshot.clock_running is True
    assert snapshot.health is BrainHealth.HEALTHY


def test_awake_without_clock_running_is_degraded():
    clock = BrainClock(tick_interval=0.01, sleeper=lambda _: None)
    lifecycle = WakeSleepController()
    monitor = HealthMonitor(wake_sleep=lifecycle, clock=clock)

    lifecycle.wake()
    snapshot = monitor.check()

    assert snapshot.online is True
    assert snapshot.health is BrainHealth.DEGRADED
    assert snapshot.reason == "awake_but_clock_not_running"


def test_failed_clock_is_critical_and_not_repaired():
    clock = BrainClock()
    lifecycle = WakeSleepController(clock=clock)
    lifecycle.wake()

    def fail_callback(_tick):
        raise RuntimeError("failure")

    try:
        clock.tick(fail_callback)
    except RuntimeError:
        pass

    snapshot = HealthMonitor(wake_sleep=lifecycle, clock=clock).check()

    assert clock.state is BrainClockState.FAILED
    assert snapshot.online is True
    assert snapshot.health is BrainHealth.CRITICAL
    assert snapshot.reason == "brain_clock_failed"


def test_health_monitor_is_observation_only():
    monitor = HealthMonitor()

    assert monitor.is_read_only() is True
    assert monitor.grants_permission() is False
    assert monitor.executes_actions() is False
    assert monitor.modifies_system() is False
