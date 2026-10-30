import time
from pathlib import Path

import pytest

from core.brain.managed_worker_runtime import ManagedWorkerRuntime


def add(a, b):
    return a + b


def boom():
    raise RuntimeError("expected worker failure")


def low_memory():
    raise MemoryError("simulated bounded low-memory failure")


def sleep_forever():
    time.sleep(10)
    return "too late"


def test_process_worker_completes_and_persists_metadata(tmp_path):
    runtime = ManagedWorkerRuntime(tmp_path / "tasks.db")
    submitted = runtime.submit("sum-1", add, args=(2, 5), timeout_seconds=2)
    assert submitted.status == "running"
    result = runtime.wait("sum-1")
    assert (result.status, result.result) == ("completed", 7)
    assert runtime.get("sum-1").status == "completed"
    assert runtime.submit("sum-1", add, args=(9, 9)).status == "completed"


def test_worker_exception_is_failed_not_success(tmp_path):
    runtime = ManagedWorkerRuntime(tmp_path / "tasks.db")
    runtime.submit("bad-1", boom, timeout_seconds=2)
    result = runtime.wait("bad-1")
    assert result.status == "failed"
    assert "expected worker failure" in result.error


def test_hard_timeout_terminates_worker_process(tmp_path):
    runtime = ManagedWorkerRuntime(tmp_path / "tasks.db")
    runtime.submit("slow-1", sleep_forever, timeout_seconds=0.1)
    result = runtime.wait("slow-1")
    assert result.status == "timed_out"
    assert "terminated" in result.error
    assert runtime.get("slow-1").status == "timed_out"


def test_operator_cancel_terminates_running_worker(tmp_path):
    runtime = ManagedWorkerRuntime(tmp_path / "tasks.db")
    runtime.submit("cancel-1", sleep_forever, timeout_seconds=10)
    result = runtime.cancel("cancel-1", "operator requested stop")
    assert result.status == "cancelled"
    assert runtime.get("cancel-1").status == "cancelled"


def test_restart_marks_orphaned_running_tasks_failed(tmp_path):
    path = tmp_path / "tasks.db"
    runtime = ManagedWorkerRuntime(path)
    runtime.submit("orphan-1", sleep_forever, timeout_seconds=10)
    # Simulate a manager restart: active worker must not be treated as resumable.
    runtime._active["orphan-1"][0].terminate()
    runtime._active["orphan-1"][0].join(timeout=1)
    runtime._active["orphan-1"][1].close()
    runtime._active.clear()
    restarted = ManagedWorkerRuntime(path)
    result = restarted.get("orphan-1")
    assert result.status == "failed"
    assert "restarted" in result.error


@pytest.mark.parametrize("timeout", [0, -1, 301, True])
def test_invalid_timeout_rejected(tmp_path, timeout):
    runtime = ManagedWorkerRuntime(tmp_path / "tasks.db")
    with pytest.raises(ValueError):
        runtime.submit("invalid", add, args=(1, 2), timeout_seconds=timeout)


def test_capacity_limit_rejects_extra_worker(tmp_path):
    runtime = ManagedWorkerRuntime(tmp_path / "tasks.db", max_workers=1)
    runtime.submit("first", sleep_forever, timeout_seconds=10)
    with pytest.raises(RuntimeError, match="capacity"):
        runtime.submit("second", add, args=(1, 2))
    runtime.cancel("first")

def test_automatic_retries_rejected_without_idempotency_contract(tmp_path):
    runtime = ManagedWorkerRuntime(tmp_path / "tasks.db")
    with pytest.raises(ValueError, match="idempotent"):
        runtime.submit("unsafe-retry", add, args=(1, 2), max_retries=1)


def test_memory_error_is_failed_not_false_success_and_runtime_recovers(tmp_path):
    runtime = ManagedWorkerRuntime(tmp_path / "tasks-memory.db")
    runtime.submit("memory-1", low_memory, timeout_seconds=2)
    failed = runtime.wait("memory-1")
    assert failed.status == "failed"
    assert "MemoryError" in (failed.error or "")
    assert runtime.get("memory-1").status == "failed"

    runtime.submit("after-memory-1", add, args=(3, 4), timeout_seconds=2)
    recovered = runtime.wait("after-memory-1")
    assert (recovered.status, recovered.result) == ("completed", 7)
