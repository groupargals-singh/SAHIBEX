from datetime import datetime, timezone

from core.research.memory_provenance import (
    MemoryProvenance,
    MemoryProvenanceEngine,
)


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)

    print(f"[PASS] {label}")


def main() -> None:
    print("SAHIBEX PHASE 2 #56 MEMORY PROVENANCE TEST")

    engine = MemoryProvenanceEngine()

    captured_at = datetime.now(timezone.utc)

    provenance = engine.create(
        memory_id="memory-001",
        source_type="user_input",
        source_id="input-001",
        origin="human_user",
        captured_at=captured_at,
        evidence_id="evidence-001",
        transformation="normalized",
        metadata={"channel": "text"},
    )

    check(
        isinstance(provenance, MemoryProvenance),
        "provenance record created",
    )

    check(
        provenance.memory_id == "memory-001",
        "memory identity preserved",
    )

    check(
        provenance.source_type == "user_input",
        "source type preserved",
    )

    check(
        provenance.source_id == "input-001",
        "source identity preserved",
    )

    check(
        provenance.origin == "human_user",
        "origin preserved",
    )

    check(
        provenance.evidence_id == "evidence-001",
        "evidence identity preserved",
    )

    result = engine.validate(provenance)

    check(
        result.valid,
        "complete provenance validates",
    )

    check(
        result.completeness_score == 1.0,
        "complete provenance score is 1.0",
    )

    check(
        result.memory_id == "memory-001",
        "validation preserves memory identity",
    )

    incomplete = engine.create(
        memory_id="memory-002",
        source_type="system",
        source_id="system-001",
        origin="internal",
        captured_at=captured_at,
    )

    incomplete_result = engine.validate(incomplete)

    check(
        incomplete_result.valid,
        "minimum required provenance remains valid",
    )

    check(
        incomplete_result.completeness_score == 1.0,
        "optional provenance fields do not reduce validity",
    )

    try:
        engine.validate("invalid")
    except TypeError:
        print("[PASS] invalid provenance input blocked")
    else:
        raise AssertionError(
            "invalid provenance input was not blocked"
        )

    try:
        MemoryProvenance(
            memory_id="",
            source_type="user_input",
            source_id="input-001",
            origin="human_user",
            captured_at=captured_at,
        )
    except ValueError:
        print("[PASS] empty memory identity blocked")
    else:
        raise AssertionError(
            "empty memory identity was not blocked"
        )

    check(
        provenance.provenance_id != "",
        "provenance has unique identity",
    )

    check(
        provenance.recorded_at is not None,
        "recording timestamp preserved",
    )

    print(
        "SAHIBEX PHASE 2 #56 MEMORY PROVENANCE TEST: PASS"
    )


if __name__ == "__main__":
    main()
