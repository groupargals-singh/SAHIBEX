from pathlib import Path
from tempfile import TemporaryDirectory

from core.research.engine import ResearchEngine
from core.research.models import (
    Evidence,
    ResearchDocument,
    ResearchFinding,
    ResearchSource,
)
from core.research.pipeline import ResearchIngestionPipeline


def make_source(source_id, title, url, publisher):
    return ResearchSource(
        source_id=source_id,
        title=title,
        source_type="web",
        locator=url,
        publisher=publisher,
        reliability=0.95,
    )


def make_document(source, document_id, content):
    return ResearchDocument(
        document_id=document_id,
        source_id=source.source_id,
        title=f"Document {document_id}",
        content=content,
        content_hash=ResearchEngine.hash_content(content),
    )


def main():
    with TemporaryDirectory() as temp_dir:
        database = Path(temp_dir) / "multi_finding.db"

        source1 = make_source(
            "src-a",
            "Alpha Research",
            "https://alpha.example.org/report",
            "Alpha Research",
        )
        source2 = make_source(
            "src-b",
            "Beta Institute",
            "https://beta.example.net/report",
            "Beta Institute",
        )
        source3 = make_source(
            "src-c",
            "Gamma Review",
            "https://gamma.example.com/report",
            "Gamma Review",
        )

        sources = [source1, source2, source3]

        documents = [
            make_document(
                source1,
                "doc-a",
                "Independent research supports the same claim. Alpha details.",
            ),
            make_document(
                source2,
                "doc-b",
                "Independent research supports the same claim. Beta details.",
            ),
            make_document(
                source3,
                "doc-c",
                "A separate unrelated research finding. Gamma details.",
            ),
        ]

        findings = [
            ResearchFinding(
                finding_id="finding-a",
                document_id="doc-a",
                claim=(
                    "Independent sources support the same research claim."
                ),
                evidence_text="Alpha reports the research claim.",
                confidence=0.95,
            ),
            ResearchFinding(
                finding_id="finding-b",
                document_id="doc-b",
                claim=(
                    "Independent sources support the same research claim."
                ),
                evidence_text="Beta reports the research claim.",
                confidence=0.95,
            ),
            ResearchFinding(
                finding_id="finding-c",
                document_id="doc-c",
                claim="A separate unrelated claim.",
                evidence_text="Gamma reports a different claim.",
                confidence=0.90,
            ),
        ]

        evidence_items = [
            Evidence(
                evidence_id="evidence-a",
                finding_id="finding-a",
                source_id="src-a",
                evidence_text="Alpha provides supporting evidence.",
                supports=True,
                strength=0.95,
            ),
            Evidence(
                evidence_id="evidence-b",
                finding_id="finding-b",
                source_id="src-b",
                evidence_text=(
                    "Beta independently provides supporting evidence."
                ),
                supports=True,
                strength=0.95,
            ),
            Evidence(
                evidence_id="evidence-c",
                finding_id="finding-c",
                source_id="src-c",
                evidence_text="Gamma supports the unrelated claim.",
                supports=True,
                strength=0.90,
            ),
        ]

        with ResearchIngestionPipeline(database) as pipeline:
            for source, document in zip(sources, documents):
                result = pipeline.ingest(source, document)
                assert result.document_stored is True

            for finding in findings:
                pipeline.add_finding(finding)

            for item in evidence_items:
                pipeline.add_evidence(item)

            # Two findings, each supported by a different source.
            result = pipeline.create_knowledge(
                statement=(
                    "Independent sources support the same research claim."
                ),
                finding_ids=["finding-a", "finding-b"],
                evidence_ids=["evidence-a", "evidence-b"],
            )

            assert isinstance(result.verified, bool), (
                "KnowledgeResult.verified must be bool, got "
                f"{type(result.verified).__name__}"
            )
            assert result.verified is True, (
                "KnowledgeResult.verified should be True for verified knowledge"
            )
            print("[PASS] KnowledgeResult.verified is a Boolean")

            knowledge = pipeline.engine.knowledge[result.knowledge_id]

            assert set(knowledge.findings) == {
                "finding-a",
                "finding-b",
            }, knowledge.findings

            assert set(knowledge.evidence) == {
                "evidence-a",
                "evidence-b",
            }, knowledge.evidence

            for evidence_id in ["evidence-a", "evidence-b"]:
                stored = pipeline.storage.get_evidence(evidence_id)
                assert stored.metadata.get("knowledge_id") == (
                    result.knowledge_id
                )

            print("[PASS] two findings linked to one knowledge candidate")
            print("[PASS] both selected evidence records linked")

            # Both independent supporting source groups must be recognized.
            assert knowledge.verified is True, (
                "Two independent supporting source groups should verify "
                "this multi-finding candidate."
            )
            assert (
                knowledge.metadata.get("verification_status") == "VERIFIED"
            )
            assert knowledge.metadata.get("independent_source_count") == 2
            assert knowledge.metadata.get("supporting_source_count") == 2
            assert knowledge.metadata.get("contradicting_source_count") == 0

            print("[PASS] multi-finding candidate verified")
            print("[PASS] two independent supporting source groups counted")

            # Invalid evidence must not create a candidate or modify metadata.
            knowledge_count_before = len(pipeline.engine.knowledge)
            evidence_c_before = dict(
                pipeline.engine.evidence["evidence-c"].metadata
            )

            rejected = False
            try:
                pipeline.create_knowledge(
                    statement="This request must be rejected.",
                    finding_ids=["finding-a", "finding-b"],
                    evidence_ids=[
                        "evidence-a",
                        "evidence-b",
                        "evidence-c",
                    ],
                )
            except ValueError as exc:
                rejected = "does not belong" in str(exc)

            assert rejected, "Unrelated evidence was not rejected"
            assert len(pipeline.engine.knowledge) == knowledge_count_before
            assert (
                pipeline.engine.evidence["evidence-c"].metadata
                == evidence_c_before
            )

            print(
                "[PASS] unrelated evidence rejected before candidate creation"
            )
            print(
                "[PASS] rejection leaves candidate count and metadata unchanged"
            )

    print("SAHIBEX MULTI-FINDING REGRESSION TEST: PASS")


if __name__ == "__main__":
    main()
