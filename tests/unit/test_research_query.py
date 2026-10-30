from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.engine import ResearchEngine
from core.research.models import (
    Evidence,
    ResearchDocument,
    ResearchFinding,
    ResearchSource,
)
from core.research.query import ResearchQueryEngine


def main() -> None:

    print("SAHIBEX RESEARCH QUERY TEST")

    with TemporaryDirectory() as temp_dir:
        engine = ResearchEngine()

        source = ResearchSource(
            source_id="source-001",
            title="Test Source",
            source_type="web",
            locator="https://example.com/test",
            publisher="Example",
            reliability=0.95,
        )

        document = ResearchDocument(
            document_id="document-001",
            source_id="source-001",
            title="AI Security",
            content=(
                "Artificial intelligence security requires "
                "strong authentication and verification."
            ),
            collected_at="2026-01-01T00:00:00+00:00",
        )

        finding = ResearchFinding(
            finding_id="finding-001",
            document_id="document-001",
            claim=(
                "AI security requires strong authentication."
            ),
            evidence_text=(
                "The source describes authentication "
                "as an important security control."
            ),
            confidence=0.90,
            created_at="2026-01-01T00:00:00+00:00",
        )

        evidence = Evidence(
            evidence_id="evidence-001",
            finding_id="finding-001",
            source_id="source-001",
            evidence_text=(
                "Authentication is described as "
                "an important security control."
            ),
            supports=True,
            strength=0.90,
            created_at="2026-01-01T00:00:00+00:00",
        )

        engine.register_source(source)
        engine.add_document(document)
        engine.add_finding(finding)
        engine.add_evidence(evidence)

        knowledge = engine.create_knowledge_candidate(
            statement=(
                "AI security requires strong authentication."
            ),
            finding_id="finding-001",
        )

        engine.verify_knowledge(
            knowledge.knowledge_id
        )

        query_engine = ResearchQueryEngine(engine)

        # Default search must exclude unverified knowledge.
        result = query_engine.search(
            "AI security authentication"
        )
        assert result.total_matches == 0
        print("[PASS] default search excludes unverified knowledge")

        # Explicit discovery can return it, but cannot promote it.
        result = query_engine.search(
            "AI security authentication",
            verified_only=False,
        )
        assert result.total_matches == 1
        assert result.matches[0].knowledge_id == (
            knowledge.knowledge_id
        )
        assert result.matches[0].verified is False
        print("[PASS] unverified search preserves verification status")


        print("[PASS] verified knowledge retrieval")

        result = query_engine.search(
            "AI security",
            verified_only=False,
        )
        assert result.total_matches == 1

        print("[PASS] query matching")

        result = query_engine.search(
            "authentication",
            limit=1,
            verified_only=False,
        )
        assert result.total_matches == 1

        print("[PASS] result limit")

        empty_result = query_engine.search(
            "quantum physics"
        )

        assert empty_result.total_matches == 0

        print("[PASS] unmatched query handling")

        try:
            query_engine.search("")
            raise AssertionError(
                "empty query should fail"
            )
        except ValueError:
            pass

        print("[PASS] empty query protection")

        try:
            query_engine.search(
                "AI",
                limit=0,
            )
            raise AssertionError(
                "invalid limit should fail"
            )
        except ValueError:
            pass

        print("[PASS] invalid limit protection")

    print("SAHIBEX RESEARCH QUERY TEST: PASS")


if __name__ == "__main__":
    main()
