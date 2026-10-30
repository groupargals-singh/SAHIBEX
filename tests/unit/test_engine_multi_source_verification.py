from core.research.engine import ResearchEngine
from core.research.models import (
    Evidence,
    ResearchDocument,
    ResearchFinding,
    ResearchSource,
)


def make_source(source_id, title, publisher, locator):
    return ResearchSource(
        source_id=source_id,
        title=title,
        source_type="web",
        locator=locator,
        publisher=publisher,
        reliability=0.90,
    )


def test_duplicate_publisher_cannot_lend_strength_to_weak_independent_source():
    engine = ResearchEngine()

    source_a = make_source(
        "source-a",
        "Alpha Research",
        "Shared Publisher",
        "https://alpha.example.org/report",
    )
    source_a_mirror = make_source(
        "source-a-mirror",
        "Alpha mirror",
        "Shared Publisher",
        "https://mirror.example.net/report",
    )
    source_b = make_source(
        "source-b",
        "Beta Institute",
        "Independent Publisher",
        "https://beta.example.com/report",
    )

    for source in (source_a, source_a_mirror, source_b):
        engine.register_source(source)

    for document_id, finding_id, source_id in (
        ("doc-strength-a", "finding-strength-a", "source-a"),
        ("doc-strength-mirror", "finding-strength-mirror", "source-a-mirror"),
        ("doc-strength-b", "finding-strength-b", "source-b"),
    ):
        engine.add_document(
            ResearchDocument(
                document_id=document_id,
                source_id=source_id,
                title=f"Research document from {source_id}",
                content="A test claim with source-linked evidence.",
            )
        )
        engine.add_finding(
            ResearchFinding(
                finding_id=finding_id,
                document_id=document_id,
                claim="A test claim with source-linked evidence.",
                confidence=0.95,
            )
        )

    engine.add_evidence(
        Evidence(
            evidence_id="evidence-strong-a",
            finding_id="finding-strength-a",
            source_id="source-a",
            evidence_text="Strong support from the shared publisher.",
            supports=True,
            strength=0.99,
        )
    )
    engine.add_evidence(
        Evidence(
            evidence_id="evidence-strong-mirror",
            finding_id="finding-strength-mirror",
            source_id="source-a-mirror",
            evidence_text="The same publisher repeats the claim.",
            supports=True,
            strength=1.00,
        )
    )
    engine.add_evidence(
        Evidence(
            evidence_id="evidence-weak-b",
            finding_id="finding-strength-b",
            source_id="source-b",
            evidence_text="Weak support from an independent publisher.",
            supports=True,
            strength=0.40,
        )
    )

    candidate = engine.create_knowledge_candidate(
        statement="A test claim with source-linked evidence.",
        finding_ids=[
            "finding-strength-a",
            "finding-strength-mirror",
            "finding-strength-b",
        ],
        confidence=0.95,
    )
    verified = engine.verify_knowledge(candidate.knowledge_id)

    assert verified.verified is False
    assert verified.metadata["verification_status"] == "UNVERIFIED"
    assert verified.metadata["independent_source_count"] == 2
    assert verified.metadata["supporting_source_count"] == 2
    assert verified.metadata["strong_supporting_source_count"] == 1
    assert "each have supporting evidence strength" in (
        verified.metadata["verification_reason"]
    )
    print("[PASS] duplicate publisher cannot inflate independent evidence strength")


def test_reverification_clears_stale_source_counts_when_evidence_disappears():
    engine = ResearchEngine()
    source_a = make_source(
        "stale-source-a",
        "Alpha Research",
        "Alpha Publisher",
        "https://alpha.example.org/report",
    )
    source_b = make_source(
        "stale-source-b",
        "Beta Research",
        "Beta Publisher",
        "https://beta.example.net/report",
    )
    engine.register_source(source_a)
    engine.register_source(source_b)
    for document_id, finding_id, source_id in (
        ("stale-doc-a", "stale-finding-a", "stale-source-a"),
        ("stale-doc-b", "stale-finding-b", "stale-source-b"),
    ):
        engine.add_document(
            ResearchDocument(
                document_id=document_id,
                source_id=source_id,
                title="Verification lifecycle document",
                content="A claim for stale metadata regression.",
            )
        )
        engine.add_finding(
            ResearchFinding(
                finding_id=finding_id,
                document_id=document_id,
                claim="A claim for stale metadata regression.",
                confidence=0.95,
            )
        )

    for evidence_id, source_id, finding_id in (
        ("stale-evidence-a", "stale-source-a", "stale-finding-a"),
        ("stale-evidence-b", "stale-source-b", "stale-finding-b"),
    ):
        engine.add_evidence(
            Evidence(
                evidence_id=evidence_id,
                finding_id=finding_id,
                source_id=source_id,
                evidence_text="Independent supporting evidence.",
                supports=True,
                strength=0.90,
            )
        )

    candidate = engine.create_knowledge_candidate(
        statement="A claim for stale metadata regression.",
        finding_ids=["stale-finding-a", "stale-finding-b"],
        confidence=0.95,
    )
    assert engine.verify_knowledge(candidate.knowledge_id).verified is True
    assert candidate.metadata["independent_source_count"] == 2

    candidate.evidence.clear()
    rechecked = engine.verify_knowledge(candidate.knowledge_id)
    assert rechecked.verified is False
    assert rechecked.last_verified_at is None
    assert rechecked.metadata["verification_status"] == "UNVERIFIED"
    assert rechecked.metadata["independent_source_count"] == 0
    assert rechecked.metadata["supporting_source_count"] == 0
    assert rechecked.metadata["strong_supporting_source_count"] == 0
    assert rechecked.metadata["contradicting_source_count"] == 0
    assert rechecked.metadata["agreement_score"] == 0.0
    print("[PASS] reverification clears stale source counts when evidence disappears")


def main():
    test_duplicate_publisher_cannot_lend_strength_to_weak_independent_source()
    test_reverification_clears_stale_source_counts_when_evidence_disappears()
    engine = ResearchEngine()

    source_a = make_source(
        "source-a",
        "Alpha Research",
        "Alpha Research Group",
        "https://alpha-research.org/report",
    )
    source_b = make_source(
        "source-b",
        "Beta Institute",
        "Beta Institute",
        "https://beta-institute.net/paper",
    )
    source_c = make_source(
        "source-c",
        "Gamma Review",
        "Gamma Review Organization",
        "https://gamma-review.org/analysis",
    )

    for source in (source_a, source_b, source_c):
        engine.register_source(source)

    for document_id, finding_id, source_id in (
        ("doc-a", "finding-a", "source-a"),
        ("doc-b", "finding-b", "source-b"),
        ("doc-c", "finding-c", "source-c"),
    ):
        engine.add_document(
            ResearchDocument(
                document_id=document_id,
                source_id=source_id,
                title="Research document",
                content="Independent evidence can improve confidence.",
            )
        )
        engine.add_finding(
            ResearchFinding(
                finding_id=finding_id,
                document_id=document_id,
                claim="Independent evidence can improve confidence.",
                evidence_text="Evidence supports the claim.",
                confidence=0.90,
            )
        )

    engine.add_evidence(
        Evidence(
            evidence_id="evidence-a",
            finding_id="finding-a",
            source_id="source-a",
            evidence_text="Alpha supports the claim.",
            supports=True,
            strength=0.90,
        )
    )
    engine.add_evidence(
        Evidence(
            evidence_id="evidence-b",
            finding_id="finding-b",
            source_id="source-b",
            evidence_text="Beta supports the claim.",
            supports=True,
            strength=0.90,
        )
    )

    candidate = engine.create_knowledge_candidate(
        statement="Independent evidence can improve confidence.",
        finding_ids=["finding-a", "finding-b", "finding-c"],
        confidence=0.90,
    )

    candidate = engine.verify_knowledge(candidate.knowledge_id)

    assert candidate.verified is True, (
        candidate.metadata.get("verification_reason")
    )
    assert candidate.metadata["verification_status"] == "VERIFIED"
    assert candidate.metadata["independent_source_count"] >= 2
    assert candidate.metadata["supporting_source_count"] >= 2
    assert candidate.last_verified_at is not None

    print("[PASS] two independent sources verify knowledge")

    engine.add_evidence(
        Evidence(
            evidence_id="evidence-c",
            finding_id="finding-c",
            source_id="source-c",
            evidence_text="Gamma contradicts the claim.",
            supports=False,
            strength=0.95,
        )
    )
    candidate.evidence.append("evidence-c")

    candidate = engine.verify_knowledge(candidate.knowledge_id)

    assert candidate.verified is False
    assert candidate.last_verified_at is None
    assert candidate.metadata["verification_status"] == "CONFLICTED"
    assert candidate.metadata["contradicting_source_count"] >= 1

    print("[PASS] contradictory source blocks verification")
    print("SAHIBEX ENGINE MULTI-SOURCE VERIFICATION TEST: PASS")


if __name__ == "__main__":
    main()
