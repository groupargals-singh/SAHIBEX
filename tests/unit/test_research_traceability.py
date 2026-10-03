from datetime import datetime, timezone

from core.research.models import Evidence, KnowledgeCandidate, ResearchSource
from core.research.traceability import ResearchTraceabilityEngine


def now():
    return datetime.now(timezone.utc)


def check(condition, message):
    assert condition, message
    print(f"[PASS] {message}")


def make_knowledge(
    knowledge_id,
    statement,
    confidence=0.9,
    verified=True,
):
    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement=statement,
        findings=[],
        evidence=[],
        confidence=confidence,
        verified=verified,
        created_at=now(),
        last_verified_at=now() if verified else None,
        metadata={},
    )


def make_source(
    source_id,
    title,
    reliability=0.9,
):
    return ResearchSource(
        source_id=source_id,
        title=title,
        source_type="test",
        locator=f"test://{source_id}",
        publisher="SAHIBEX TEST",
        reliability=reliability,
        accessed_at=now(),
    )


def make_evidence(
    evidence_id,
    finding_id,
    source_id,
    text,
    strength=0.9,
    supports=True,
    knowledge_id=None,
):
    metadata = {}

    if knowledge_id is not None:
        metadata["knowledge_id"] = knowledge_id

    return Evidence(
        evidence_id=evidence_id,
        finding_id=finding_id,
        source_id=source_id,
        evidence_text=text,
        supports=supports,
        strength=strength,
        created_at=now(),
        metadata=metadata,
    )


def test_basic_traceability():
    engine = ResearchTraceabilityEngine()

    knowledge = make_knowledge(
        "k1",
        "Python is widely used for software development.",
    )

    source = make_source(
        "src1",
        "Python Documentation",
        reliability=0.95,
    )

    evidence = make_evidence(
        "ev1",
        "finding1",
        "src1",
        "The source describes Python as a programming language.",
        knowledge_id="k1",
    )

    result = engine.trace(
        [knowledge],
        [evidence],
        [source],
    )

    check(
        result.status == "TRACEABLE",
        "basic traceability",
    )

    check(
        result.knowledge_count == 1,
        "knowledge count",
    )

    check(
        result.evidence_count == 1,
        "evidence count",
    )

    check(
        result.source_count == 1,
        "source count",
    )

    trace = result.traces[0]

    check(
        trace.knowledge_id == "k1",
        "knowledge ID preserved",
    )

    check(
        len(trace.evidence) == 1,
        "evidence linked to knowledge",
    )

    check(
        len(trace.sources) == 1,
        "source linked to evidence",
    )


def test_multiple_evidence():
    engine = ResearchTraceabilityEngine()

    knowledge = make_knowledge(
        "k1",
        "Python is widely used for software development.",
    )

    source = make_source(
        "src1",
        "Python Documentation",
    )

    evidence_one = make_evidence(
        "ev1",
        "finding1",
        "src1",
        "Evidence one.",
        strength=0.8,
        knowledge_id="k1",
    )

    evidence_two = make_evidence(
        "ev2",
        "finding2",
        "src1",
        "Evidence two.",
        strength=0.9,
        knowledge_id="k1",
    )

    result = engine.trace(
        [knowledge],
        [evidence_one, evidence_two],
        [source],
    )

    check(
        result.evidence_count == 2,
        "multiple evidence items preserved",
    )

    check(
        len(result.traces[0].evidence) == 2,
        "multiple evidence attached to knowledge",
    )


def test_duplicate_source_protection():
    engine = ResearchTraceabilityEngine()

    knowledge = make_knowledge(
        "k1",
        "Python is widely used for software development.",
    )

    source = make_source(
        "src1",
        "Python Documentation",
    )

    evidence_one = make_evidence(
        "ev1",
        "finding1",
        "src1",
        "Evidence one.",
        knowledge_id="k1",
    )

    evidence_two = make_evidence(
        "ev2",
        "finding2",
        "src1",
        "Evidence two.",
        knowledge_id="k1",
    )

    result = engine.trace(
        [knowledge],
        [evidence_one, evidence_two],
        [source],
    )

    check(
        result.evidence_count == 2,
        "both evidence items retained",
    )

    check(
        result.source_count == 1,
        "duplicate source deduplicated",
    )

    check(
        len(result.traces[0].sources) == 1,
        "source appears once in trace",
    )


def test_missing_source():
    engine = ResearchTraceabilityEngine()

    knowledge = make_knowledge(
        "k1",
        "Python is widely used for software development.",
    )

    evidence = make_evidence(
        "ev1",
        "finding1",
        "missing-source",
        "Evidence without available source.",
        knowledge_id="k1",
    )

    result = engine.trace(
        [knowledge],
        [evidence],
        [],
    )

    check(
        result.status == "EVIDENCE_WITHOUT_SOURCE",
        "missing source handled safely",
    )

    check(
        result.evidence_count == 1,
        "evidence preserved without source",
    )

    check(
        result.source_count == 0,
        "missing source not fabricated",
    )


def test_missing_knowledge_id():
    engine = ResearchTraceabilityEngine()

    knowledge = make_knowledge(
        "k1",
        "Python is widely used for software development.",
    )

    source = make_source(
        "src1",
        "Python Documentation",
    )

    evidence = make_evidence(
        "ev1",
        "finding1",
        "src1",
        "Evidence without explicit knowledge mapping.",
    )

    result = engine.trace(
        [knowledge],
        [evidence],
        [source],
    )

    check(
        result.status == "NO_TRACEABLE_EVIDENCE",
        "missing knowledge mapping handled safely",
    )

    check(
        result.evidence_count == 0,
        "unmapped evidence not falsely attached",
    )


def test_unknown_knowledge_id():
    engine = ResearchTraceabilityEngine()

    knowledge = make_knowledge(
        "k1",
        "Python is widely used for software development.",
    )

    source = make_source(
        "src1",
        "Python Documentation",
    )

    evidence = make_evidence(
        "ev1",
        "finding1",
        "src1",
        "Evidence points to unknown knowledge.",
        knowledge_id="unknown-knowledge",
    )

    result = engine.trace(
        [knowledge],
        [evidence],
        [source],
    )

    check(
        result.status == "NO_TRACEABLE_EVIDENCE",
        "unknown knowledge ID handled safely",
    )

    check(
        result.evidence_count == 0,
        "unknown knowledge evidence rejected",
    )


def test_no_evidence():
    engine = ResearchTraceabilityEngine()

    knowledge = make_knowledge(
        "k1",
        "Python is widely used for software development.",
    )

    result = engine.trace(
        [knowledge],
        [],
        [],
    )

    check(
        result.status == "NO_TRACEABLE_EVIDENCE",
        "no evidence status",
    )

    check(
        result.evidence_count == 0,
        "no evidence count",
    )


def test_no_knowledge():
    engine = ResearchTraceabilityEngine()

    result = engine.trace(
        [],
        [],
        [],
    )

    check(
        result.status == "NO_KNOWLEDGE",
        "no knowledge status",
    )

    check(
        result.knowledge_count == 0,
        "no knowledge count",
    )


def main():
    print("SAHIBEX RESEARCH TRACEABILITY TEST")

    test_basic_traceability()
    test_multiple_evidence()
    test_duplicate_source_protection()
    test_missing_source()
    test_missing_knowledge_id()
    test_unknown_knowledge_id()
    test_no_evidence()
    test_no_knowledge()

    print("SAHIBEX RESEARCH TRACEABILITY TEST: PASS")


if __name__ == "__main__":
    main()
