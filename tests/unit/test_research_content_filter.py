from core.research.content_filter import ResearchContentFilter
from core.research.extractor import ResearchExtractor
from core.research.models import ResearchDocument


def test_research_content_filter_rejects_explicit_page_boilerplate():
    gate = ResearchContentFilter()
    decision = gate.evaluate("Join our WhatsApp Channel to get the latest news, exclusives and videos on WhatsApp.")
    assert decision.accepted is False
    assert decision.reason == "page_boilerplate"


def test_research_content_filter_rejects_too_short_fragments():
    decision = ResearchContentFilter().evaluate("Click here.")
    assert decision.accepted is False
    assert decision.reason == "page_boilerplate"


def test_research_content_filter_keeps_uncertain_substantive_content():
    text = "The European Commission sent information requests to more than 30 AI companies in late August."
    decision = ResearchContentFilter().evaluate(text)
    assert decision.accepted is True
    assert decision.reason == "candidate_content"


def test_extractor_filters_page_chrome_but_preserves_article_claims():
    doc = ResearchDocument(
        document_id="doc-filter-1", source_id="source-filter-1",
        title="Filter test",
        content=(
            "The European Commission sent information requests to more than 30 AI companies in late August. "
            "Join our WhatsApp Channel to get the latest news, exclusives and videos on WhatsApp. "
            "The EU AI Act sets rules based on the risk level of different AI applications."
        ),
    )
    findings = ResearchExtractor().extract(doc)
    claims = [item.claim for item in findings]
    assert len(claims) == 2
    assert all("WhatsApp Channel" not in claim for claim in claims)
    assert any("European Commission" in claim for claim in claims)


def test_research_content_filter_keeps_short_but_potentially_factual_claims():
    decision = ResearchContentFilter().evaluate("GDP grew 5%.")
    assert decision.accepted is True
