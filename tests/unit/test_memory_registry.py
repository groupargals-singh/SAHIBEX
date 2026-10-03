from core.research.memory_object import MemoryCandidate
from core.research.memory_registry import MemoryRegistry


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


def main() -> None:
    print("SAHIBEX 6I-2 MEMORY REGISTRY TEST")

    registry = MemoryRegistry()

    memory = MemoryCandidate(
        memory_id="mem-001",
        content="User prefers step-by-step development.",
        memory_type="USER_PREFERENCE",
        source="user",
        importance=0.9,
        confidence=0.95,
        tags=["preference"],
        metadata={"domain": "development"},
    )

    registration = registry.register(memory)

    check(
        registration.is_new is True,
        "memory registration",
    )

    check(
        registration.memory is memory,
        "registered memory identity preserved",
    )

    check(
        registry.count() == 1,
        "memory count",
    )

    check(
        registry.contains("mem-001"),
        "memory existence",
    )

    check(
        registry.get("mem-001") is memory,
        "memory lookup",
    )

    check(
        registry.require("mem-001") is memory,
        "required memory lookup",
    )

    duplicate = MemoryCandidate(
        memory_id="mem-001",
        content="Different content must not replace original.",
        memory_type="OTHER",
        source="test",
    )

    duplicate_result = registry.register(duplicate)

    check(
        duplicate_result.is_new is False,
        "duplicate memory identity protection",
    )

    check(
        duplicate_result.memory is memory,
        "duplicate registration preserves original memory",
    )

    check(
        registry.count() == 1,
        "duplicate does not increase registry count",
    )

    check(
        len(tuple(registry.all())) == 1,
        "all memories enumeration",
    )

    summary = registry.summary()

    check(
        summary["memory_count"] == 1,
        "registry summary",
    )

    try:
        registry.require("unknown-memory")
        raise AssertionError("unknown memory was accepted")
    except KeyError:
        print("[PASS] unknown memory protection")

    registry.clear()

    check(
        registry.count() == 0,
        "registry clear",
    )

    check(
        not registry.contains("mem-001"),
        "memory removed after clear",
    )

    try:
        registry.register("not-a-memory")
        raise AssertionError("invalid memory object was accepted")
    except TypeError:
        print("[PASS] memory type protection")

    print("SAHIBEX 6I-2 MEMORY REGISTRY TEST: PASS")


if __name__ == "__main__":
    main()
