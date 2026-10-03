from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


@dataclass(frozen=True)
class ResearchSource:
    """
    Describes where research information came from.
    """

    source_id: str
    title: str
    source_type: str
    locator: str

    publisher: Optional[str] = None
    author: Optional[str] = None

    published_at: Optional[datetime] = None
    accessed_at: datetime = field(default_factory=utc_now)

    reliability: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id cannot be empty")

        if not self.title.strip():
            raise ValueError("source title cannot be empty")

        if not self.source_type.strip():
            raise ValueError("source_type cannot be empty")

        if not self.locator.strip():
            raise ValueError("source locator cannot be empty")

        if not 0.0 <= self.reliability <= 1.0:
            raise ValueError("reliability must be between 0 and 1")


@dataclass
class ResearchDocument:
    """
    A collected research document associated with a source.
    """

    document_id: str
    source_id: str
    title: str
    content: str

    collected_at: datetime = field(default_factory=utc_now)

    content_hash: Optional[str] = None
    language: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.document_id.strip():
            raise ValueError("document_id cannot be empty")

        if not self.source_id.strip():
            raise ValueError("source_id cannot be empty")

        if not self.title.strip():
            raise ValueError("document title cannot be empty")

        if not self.content.strip():
            raise ValueError("document content cannot be empty")


@dataclass
class ResearchFinding:
    """
    A specific claim/fact extracted from a research document.
    """

    finding_id: str
    document_id: str
    claim: str

    evidence_text: Optional[str] = None
    confidence: float = 0.0

    created_at: datetime = field(default_factory=utc_now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.finding_id.strip():
            raise ValueError("finding_id cannot be empty")

        if not self.document_id.strip():
            raise ValueError("document_id cannot be empty")

        if not self.claim.strip():
            raise ValueError("claim cannot be empty")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass
class Evidence:
    """
    Evidence supporting or contradicting a finding.
    """

    evidence_id: str
    finding_id: str
    source_id: str

    evidence_text: str
    supports: bool = True

    strength: float = 0.0
    created_at: datetime = field(default_factory=utc_now)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError("evidence_id cannot be empty")

        if not self.finding_id.strip():
            raise ValueError("finding_id cannot be empty")

        if not self.source_id.strip():
            raise ValueError("source_id cannot be empty")

        if not self.evidence_text.strip():
            raise ValueError("evidence_text cannot be empty")

        if not 0.0 <= self.strength <= 1.0:
            raise ValueError("strength must be between 0 and 1")


@dataclass
class KnowledgeCandidate:
    """
    A potential piece of knowledge produced from verified research.
    """

    knowledge_id: str
    statement: str

    findings: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)

    confidence: float = 0.0
    verified: bool = False

    created_at: datetime = field(default_factory=utc_now)
    last_verified_at: Optional[datetime] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.knowledge_id.strip():
            raise ValueError("knowledge_id cannot be empty")

        if not self.statement.strip():
            raise ValueError("knowledge statement cannot be empty")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass
class ResearchResult:
    """
    Final structured output of a research operation.
    """

    research_id: str
    query: str

    sources: List[ResearchSource] = field(default_factory=list)
    documents: List[ResearchDocument] = field(default_factory=list)
    findings: List[ResearchFinding] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    knowledge: List[KnowledgeCandidate] = field(default_factory=list)

    completed: bool = False
    verified: bool = False

    created_at: datetime = field(default_factory=utc_now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.research_id.strip():
            raise ValueError("research_id cannot be empty")

        if not self.query.strip():
            raise ValueError("research query cannot be empty")

    @property
    def source_count(self) -> int:
        return len(self.sources)

    @property
    def document_count(self) -> int:
        return len(self.documents)

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    @property
    def evidence_count(self) -> int:
        return len(self.evidence)

    @property
    def knowledge_count(self) -> int:
        return len(self.knowledge)
