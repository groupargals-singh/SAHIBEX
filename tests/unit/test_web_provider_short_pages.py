from core.research.acquisition import AcquisitionRequest
from core.research.web_provider import DirectWebResearchProvider, WebProviderConfig


class StubProvider(DirectWebResearchProvider):
    def __init__(self, content):
        super().__init__(WebProviderConfig(timeout_seconds=1, max_sources=2))
        self.stub_content = content

    def fetch_url(self, url):
        return {"url": url, "final_url": url, "status": 200,
                "content_type": "text/html", "content": self.stub_content,
                "bytes": len(self.stub_content)}


def test_short_stub_page_is_rejected_for_stable_fact_research():
    provider = StubProvider("<html><head><title>New Delhi</title></head><body>New Delhi is capital.</body></html>")
    result = provider.acquire(AcquisitionRequest(query="What is the capital of India?", max_sources=1,
                                                  metadata={"url": "https://example.com/stub"}))
    assert result.completed is False
    assert result.sources == []
    assert any("article body too short" in item for item in result.metadata["errors"])


def test_substantive_page_can_be_acquired_for_stable_fact_research():
    text = "New Delhi is the capital of India. " * 5
    provider = StubProvider(f"<html><head><title>New Delhi capital</title></head><body><p>{text}</p></body></html>")
    result = provider.acquire(AcquisitionRequest(query="What is the capital of India?", max_sources=1,
                                                  metadata={"url": "https://example.com/article"}))
    assert result.completed is True
    assert len(result.sources) == 1
    assert len(result.sources[0].content) >= provider.MIN_ARTICLE_CHARS
