from __future__ import annotations

from types import SimpleNamespace

from core.research.google_news_rss_search_backend import GoogleNewsRSSSearchBackend


class FakeRSSProvider:
    def __init__(self):
        self.request = None

    def acquire(self, request):
        self.request = request
        return SimpleNamespace(
            sources=[
                SimpleNamespace(
                    title="AI safety report - Publisher",
                    locator="https://news.google.com/rss/articles/example?oc=5",
                    content="<a href='x'>AI safety report</a>",
                    publisher="Google News",
                    published_at="2026-10-09T00:00:00Z",
                )
            ]
        )


def test_google_news_rss_backend_uses_fixed_host_and_marks_results_discovery_only():
    provider = FakeRSSProvider()
    backend = GoogleNewsRSSSearchBackend(provider=provider)
    results = backend.search("AI safety report", max_results=5)

    assert len(results) == 1
    assert results[0].title == "AI safety report - Publisher"
    assert results[0].url.startswith("https://news.google.com/")
    assert results[0].metadata["discovery_only"] is True
    assert results[0].metadata["content_is_search_snippet"] is True
    assert provider.request.metadata["url"].startswith(
        "https://news.google.com/rss/search?"
    )
    assert "AI+safety+report" in provider.request.metadata["url"]
