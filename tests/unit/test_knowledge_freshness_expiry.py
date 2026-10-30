from datetime import datetime, timedelta, timezone
import hashlib

from core.brain.knowledge_brain import KnowledgeBrain
from core.research.models import (
    Evidence,
    KnowledgeCandidate,
    ResearchDocument,
    ResearchFinding,
    ResearchSource,
)
from core.research.storage import ResearchStorage


CURRENT_QUERY = "latest AI safety news"
CLAIM = "AI safety news report from a trusted publisher describes a model release."


def _seed_verified_claim(storage: ResearchStorage, *, key: str, age: timedelta | None):
    now = datetime.now(timezone.utc)
    source_id = f"{key}-source"
    document_id = f"{key}-document"
    finding_id = f"{key}-finding"
    evidence_id = f"{key}-evidence"
    published_at = now - age if age is not None else None
    source = ResearchSource(
        source_id=source_id,
        title="AI safety report",
        source_type="web",
        locator=f"https://{key}.example.org/report",
        publisher=f"{key} publisher",
        published_at=published_at,
        reliability=0.9,
    )
    content = CLAIM
    document = ResearchDocument(
        document_id=document_id,
        source_id=source_id,
        title=source.title,
        content=content,
        content_hash=hashlib.sha256(content.encode()).hexdigest(),
    )
    finding = ResearchFinding(
        finding_id=finding_id,
        document_id=document_id,
        claim=CLAIM,
        evidence_text=CLAIM,
        confidence=0.95,
    )
    evidence = Evidence(
        evidence_id=evidence_id,
        finding_id=finding_id,
        source_id=source_id,
        evidence_text=CLAIM,
        supports=True,
        strength=0.95,
        created_at=now,
        metadata={"knowledge_id": key},
    )
    candidate = KnowledgeCandidate(
        knowledge_id=key,
        statement=CLAIM,
        findings=[finding_id],
        evidence=[evidence_id],
        confidence=0.95,
        verified=True,
        created_at=now,
        last_verified_at=now,
        metadata={"source_id": source_id},
    )
    storage.save_source(source)
    storage.save_document(document)
    storage.save_finding(finding)
    storage.save_evidence(evidence)
    storage.save_knowledge(candidate)
    storage.record_knowledge_verification(
        knowledge_id=key,
        status="VERIFIED",
        reason="Test fixture contains a persisted source, finding, and evidence record.",
        verified_at=now,
    )
    return candidate


def test_current_news_retrieval_rejects_stale_verified_knowledge(tmp_path):
    storage = ResearchStorage(tmp_path / "stale.db")
    brain = KnowledgeBrain(storage=storage)
    candidate = _seed_verified_claim(
        storage, key="stale-news", age=timedelta(days=8)
    )

    assert brain.retrieve(CURRENT_QUERY, verified_only=True).knowledge_ids == ()
    # The same old report can still be found for a non-current descriptive query.
    assert brain.retrieve("Explain the AI safety report", verified_only=True).knowledge_ids == (
        candidate.knowledge_id,
    )
    storage.close()


def test_current_news_retrieval_accepts_fresh_provenance(tmp_path):
    storage = ResearchStorage(tmp_path / "fresh.db")
    brain = KnowledgeBrain(storage=storage)
    candidate = _seed_verified_claim(
        storage, key="fresh-news", age=timedelta(hours=2)
    )

    assert brain.retrieve(CURRENT_QUERY, verified_only=True).knowledge_ids == (
        candidate.knowledge_id,
    )
    storage.close()


def test_current_news_retrieval_fails_closed_without_source_timestamp(tmp_path):
    storage = ResearchStorage(tmp_path / "unknown-date.db")
    brain = KnowledgeBrain(storage=storage)
    candidate = _seed_verified_claim(storage, key="unknown-date", age=None)

    assert brain.retrieve(CURRENT_QUERY, verified_only=True).knowledge_ids == ()
    assert brain.retrieve("Explain the AI safety report", verified_only=True).knowledge_ids == (
        candidate.knowledge_id,
    )
    storage.close()


def test_token_fallback_cannot_drop_original_current_query_scope(tmp_path):
    storage = ResearchStorage(tmp_path / "fallback.db")
    brain = KnowledgeBrain(storage=storage)
    _seed_verified_claim(storage, key="fallback-stale", age=timedelta(days=8))

    # "AI" alone is not a freshness-sensitive query, but it must inherit the
    # original "latest news today" intent from the caller's fallback search.
    assert brain.retrieve(
        "AI",
        verified_only=True,
        freshness_query=CURRENT_QUERY,
    ).knowledge_ids == ()
    storage.close()
