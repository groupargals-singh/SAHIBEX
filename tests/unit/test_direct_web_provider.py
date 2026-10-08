from core.research.acquisition import (
    AcquisitionRequest,
    ResearchAcquisitionEngine,
)

from core.research.web_provider import (
    DirectWebResearchProvider,
    WebProviderConfig,
)


class StubWebProvider(
    DirectWebResearchProvider
):
    """
    Test subclass that replaces actual network access.
    """

    def __init__(self):
        super().__init__(
            WebProviderConfig(
                timeout_seconds=2.0,
                max_response_bytes=100_000,
            )
        )

        self.fetch_calls = []

    def fetch_url(
        self,
        url: str,
    ) -> dict:
        self.fetch_calls.append(
            url
        )

        return {
            "url": url,
            "final_url": url,
            "status": 200,
            "content_type": "text/html",
            "content": (
                "<html>"
                "<head>"
                "<title>SAHIBEX Test Page</title>"
                "</head>"
                "<body>"
                "<h1>Research Test</h1>"
                "</body>"
                "</html>"
            ),
            "bytes": 150,
        }


def main():
    print(
        "SAHIBEX DIRECT WEB PROVIDER TEST"
    )

    provider = StubWebProvider()

    # Provider identity.
    assert provider.provider_name == "direct_web"
    assert provider.requires_network is True

    print(
        "[PASS] provider identity"
    )

    # Configuration.
    assert provider.config.timeout_seconds == 2.0
    assert provider.config.max_response_bytes == 100_000

    print(
        "[PASS] provider configuration"
    )

    # Engine registration.
    engine = ResearchAcquisitionEngine(
        providers=[provider]
    )

    assert (
        engine.provider_requires_network(
            "direct_web"
        )
        is True
    )

    print(
        "[PASS] provider registered as network-capable"
    )

    # URL validation.
    provider._validate_url(
        "https://example.com"
    )

    print(
        "[PASS] HTTPS URL accepted"
    )

    provider._validate_url(
        "http://example.com"
    )

    print(
        "[PASS] HTTP URL accepted"
    )

    # Dangerous URLs.
    blocked_urls = [
        "ftp://example.com",
        "file:///etc/passwd",
        "http://localhost",
        "http://127.0.0.1",
        "http://10.0.0.1",
        "http://192.168.1.1",
    ]

    for url in blocked_urls:
        blocked = False

        try:
            provider._validate_url(
                url
            )
        except ValueError:
            blocked = True

        assert blocked is True

    print(
        "[PASS] unsafe URL schemes and private hosts blocked"
    )

    # Acquisition request.
    request = AcquisitionRequest(
        query="SAHIBEX test",
        max_sources=1,
        metadata={
            "url": "https://example.com/test"
        },
    )

    result = provider.acquire(
        request
    )

    assert result.query == request.query
    assert result.completed is True
    assert result.status == "completed"
    assert len(result.sources) == 1

    print(
        "[PASS] acquisition result created"
    )

    source = result.sources[0]

    assert source.source_type == "web"
    assert source.locator == "https://example.com/test"
    assert source.content
    assert source.title == "SAHIBEX Test Page"

    print(
        "[PASS] acquired source metadata and content"
    )

    # Content hash.
    assert (
        len(
            source.metadata["content_hash"]
        )
        == 64
    )

    print(
        "[PASS] SHA-256 content hash generated"
    )

    # Only requested URL should be fetched.
    assert provider.fetch_calls == [
        "https://example.com/test"
    ]

    print(
        "[PASS] requested URL fetched exactly once"
    )

    print(
        "SAHIBEX DIRECT WEB PROVIDER TEST: PASS"
    )


if __name__ == "__main__":
    main()
