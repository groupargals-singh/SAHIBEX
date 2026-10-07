from core.research.memory_compression import (
    MemoryCompressionEngine,
    MemoryCompressionInput,
)


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)

    print(f"[PASS] {label}")


def main() -> None:
    print("SAHIBEX PHASE 2 #60 MEMORY COMPRESSION TEST")

    engine = MemoryCompressionEngine()

    source = (
        "SAHIBEX    stores   linked   memory concepts "
        "without unnecessary duplication."
    )

    result = engine.compress(
        MemoryCompressionInput(
            memory_id="memory-001",
            content=source,
            importance=0.8,
            preserve_exact_source=True,
        )
    )

    check(
        result.memory_id == "memory-001",
        "memory identity preserved",
    )

    check(
        result.compressed_content
        == "SAHIBEX stores linked memory concepts "
        "without unnecessary duplication.",
        "compact representation created",
    )

    check(
        result.compressed_length < result.original_length,
        "compressed representation is smaller",
    )

    check(
        0.0 < result.compression_ratio < 1.0,
        "compression ratio is valid",
    )

    check(
        result.information_preserved,
        "information preservation flag remains true",
    )

    check(
        result.exact_source_preserved,
        "exact source preservation requested",
    )

    check(
        result.action == "PROPOSAL_ONLY",
        "compression remains proposal only",
    )

    check(
        result.original_content == source,
        "original memory content remains unchanged",
    )

    unchanged = engine.compress(
        MemoryCompressionInput(
            memory_id="memory-002",
            content="Already compact memory.",
            preserve_exact_source=True,
        )
    )

    check(
        unchanged.action == "NO_CHANGE",
        "already compact memory requires no change",
    )

    check(
        unchanged.original_content
        == unchanged.compressed_content,
        "already compact content remains unchanged",
    )

    try:
        engine.compress("invalid")
    except TypeError:
        print("[PASS] invalid compression input blocked")
    else:
        raise AssertionError(
            "invalid compression input was not blocked"
        )

    try:
        MemoryCompressionInput(
            memory_id="",
            content="valid memory",
        )
    except ValueError:
        print("[PASS] empty memory identity blocked")
    else:
        raise AssertionError(
            "empty memory identity was not blocked"
        )

    try:
        MemoryCompressionInput(
            memory_id="memory-003",
            content="valid memory",
            importance=1.5,
        )
    except ValueError:
        print("[PASS] invalid importance range blocked")
    else:
        raise AssertionError(
            "invalid importance range was not blocked"
        )

    check(
        result.result_id != "",
        "compression result has unique identity",
    )

    check(
        result.input_id != "",
        "compression input has unique identity",
    )

    print("SAHIBEX PHASE 2 #60 MEMORY COMPRESSION TEST: PASS")


if __name__ == "__main__":
    main()
