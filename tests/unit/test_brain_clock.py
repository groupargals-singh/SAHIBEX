from __future__ import annotations

import pytest

from core.brain.brain_clock import (
    BrainClock,
    BrainClockState,
    ClockTick,
)


class FakeClock:
    def __init__(self) -> None:
        self.value = 10.0

    def __call__(self) -> float:
        value = self.value
        self.value += 0.5
        return value


def test_initial_state_and_security_boundary() -> None:
    clock = BrainClock(tick_interval=0.1)
    assert clock.state == BrainClockState.STOPPED
    assert clock.sequence == 0
    assert clock.last_tick is None
    assert clock.grants_permission() is False
    assert clock.executes_actions() is False
    assert clock.modifies_system() is False
    assert clock.is_scheduler_only() is True


def test_start_tick_and_sequence() -> None:
    fake = FakeClock()
    clock = BrainClock(tick_interval=0.1, clock=fake, sleeper=lambda _: None)
    clock.start()

    tick = clock.tick()

    assert isinstance(tick, ClockTick)
    assert tick.sequence == 1
    assert tick.monotonic_time == 10.0
    assert clock.sequence == 1
    assert clock.last_tick == tick


def test_run_produces_deterministic_ticks_without_real_sleep() -> None:
    fake = FakeClock()
    sleeps: list[float] = []
    clock = BrainClock(
        tick_interval=0.25,
        clock=fake,
        sleeper=sleeps.append,
    )
    clock.start()

    ticks = clock.run(max_ticks=3)

    assert [tick.sequence for tick in ticks] == [1, 2, 3]
    assert [tick.monotonic_time for tick in ticks] == [10.0, 10.5, 11.0]
    assert sleeps == [0.25, 0.25]


def test_pause_resume_and_stop() -> None:
    clock = BrainClock(tick_interval=0.1)
    clock.start()
    clock.pause()
    assert clock.state == BrainClockState.PAUSED

    with pytest.raises(RuntimeError):
        clock.tick()

    clock.resume()
    assert clock.state == BrainClockState.RUNNING
    clock.stop()
    assert clock.state == BrainClockState.STOPPED


def test_callback_failure_enters_failed_state() -> None:
    clock = BrainClock(tick_interval=0.1)
    clock.start()

    def fail(_: ClockTick) -> None:
        raise RuntimeError("event failure")

    with pytest.raises(RuntimeError, match="event failure"):
        clock.tick(fail)

    assert clock.state == BrainClockState.FAILED
    assert clock.failure_reason == "event failure"

    with pytest.raises(RuntimeError, match="reset"):
        clock.start()


def test_reset_clears_failure_and_sequence() -> None:
    clock = BrainClock(tick_interval=0.1)
    clock.start()

    with pytest.raises(RuntimeError):
        clock.tick(lambda _: (_ for _ in ()).throw(RuntimeError("x")))

    clock.reset()

    assert clock.state == BrainClockState.STOPPED
    assert clock.sequence == 0
    assert clock.last_tick is None
    assert clock.failure_reason == ""


def test_invalid_transitions_and_arguments_are_blocked() -> None:
    with pytest.raises(ValueError):
        BrainClock(tick_interval=0)

    clock = BrainClock()
    with pytest.raises(RuntimeError):
        clock.tick()
    with pytest.raises(RuntimeError):
        clock.pause()
    with pytest.raises(RuntimeError):
        clock.resume()

    clock.start()
    with pytest.raises(ValueError):
        clock.run(max_ticks=0)
    with pytest.raises(TypeError):
        clock.tick(callback="not-callable")
