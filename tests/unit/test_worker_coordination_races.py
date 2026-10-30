from concurrent.futures import ThreadPoolExecutor
from threading import Event

from core.brain.background_worker_expansion import BackgroundWorkerManager, WorkerLifecycle
from core.brain.inter_module_bus import InterModuleBus
from core.brain.research_learning_command import DepartmentOperation, ResearchLearningCommander, TaskStage


def test_background_worker_rejects_duplicate_run_while_running():
    started = Event()
    release = Event()
    manager = BackgroundWorkerManager(max_workers=2)

    def slow_worker(payload):
        started.set()
        assert release.wait(timeout=3)
        return payload

    manager.register("worker-a", slow_worker)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(manager.run, "worker-a", "first")
        assert started.wait(timeout=2)
        second = manager.run("worker-a", "duplicate")
        assert second.success is False
        assert second.error == "worker is already running"
        assert manager.record("worker-a").lifecycle is WorkerLifecycle.RUNNING
        release.set()
        completed = first.result(timeout=3)

    assert completed.success is True
    assert completed.output == "first"
    assert completed.sequence == 1
    assert len(manager.history("worker-a")) == 1
    assert manager.record("worker-a").runs == 1
    assert manager.record("worker-a").lifecycle is WorkerLifecycle.READY


def test_background_worker_history_sequences_remain_unique_under_concurrency():
    manager = BackgroundWorkerManager(max_workers=1)
    manager.register("worker-a", lambda value: value)
    outputs = [manager.run("worker-a", i) for i in range(5)]
    assert [result.sequence for result in outputs] == [1, 2, 3, 4, 5]
    assert [item.sequence for item in manager.history("worker-a")] == [1, 2, 3, 4, 5]


def test_inter_module_bus_concurrent_sends_have_unique_monotonic_sequences():
    bus = InterModuleBus(max_workers=2)
    with ThreadPoolExecutor(max_workers=8) as pool:
        messages = list(pool.map(lambda i: bus.send("audit", "worker", {"i": i}), range(100)))
    sequences = [message.sequence for message in messages]
    history_sequences = [message.sequence for message in bus.history]
    assert len(set(sequences)) == 100
    assert sorted(sequences) == list(range(1, 101))
    assert sorted(history_sequences) == list(range(1, 101))


def test_department_commander_does_not_trust_false_verification_or_persistence():
    class InconsistentResult:
        success = True
        verified = False
        persisted = False
        verification_status = "VERIFIED"

    result = ResearchLearningCommander().dispatch(
        DepartmentOperation.RESEARCH,
        "audit coordination",
        InconsistentResult,
    )
    assert result.trace.status is TaskStage.UNVERIFIED


def test_department_commander_learning_requires_verified_knowledge_items_when_count_exists():
    class EmptyLearningResult:
        success = True
        verified = True
        persisted = True
        verification_status = "VERIFIED"
        verified_knowledge_count = 0

    result = ResearchLearningCommander().dispatch(
        DepartmentOperation.LEARN,
        "audit coordination",
        EmptyLearningResult,
    )
    assert result.trace.status is TaskStage.UNVERIFIED
