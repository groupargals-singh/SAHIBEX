from __future__ import annotations

from core.research.acquisition import (
    AcquisitionRequest,
    ResearchAcquisitionEngine,
    ResearchAcquisitionProvider,
)
from core.research.provider_router import (
    ResearchProviderRouter,
)


class DummyProvider(ResearchAcquisitionProvider):
    def __init__(
        self,
        name: str,
        requires_network: bool = False,
    ) -> None:
        self.provider_name = name
        self.requires_network = requires_network

    def acquire(self, request):
        raise NotImplementedError


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def build_engine() -> ResearchAcquisitionEngine:
    return ResearchAcquisitionEngine(
        providers=[
            DummyProvider(
                "direct_web",
                requires_network=True,
            ),
            DummyProvider(
                "search",
                requires_network=True,
            ),
            DummyProvider(
                "rss_atom",
                requires_network=True,
            ),
            DummyProvider(
                "rest_json_api",
                requires_network=True,
            ),
            DummyProvider(
                "document",
                requires_network=False,
            ),
        ]
    )


def main() -> None:
    engine = build_engine()

    router = ResearchProviderRouter(
        engine
    )

    check(
        engine.providers()
        == [
            "direct_web",
            "document",
            "rest_json_api",
            "rss_atom",
            "search",
        ],
        "unexpected provider registration",
    )

    print(
        "[PASS] router sees registered providers"
    )

    # ---------------------------------------------------------
    # Explicit document
    # ---------------------------------------------------------
    request = AcquisitionRequest(
        query="read local research",
        source_type="document",
        metadata={
            "path": "documents/test.txt",
        },
    )

    route = router.route(request)

    check(
        route.provider_name == "document",
        "document source_type did not route to document",
    )

    print(
        "[PASS] explicit document routing"
    )

    # ---------------------------------------------------------
    # Explicit RSS
    # ---------------------------------------------------------
    request = AcquisitionRequest(
        query="latest feed",
        source_type="rss",
    )

    route = router.route(request)

    check(
        route.provider_name == "rss_atom",
        "rss source_type did not route to rss_atom",
    )

    print(
        "[PASS] explicit RSS routing"
    )

    # ---------------------------------------------------------
    # Explicit API
    # ---------------------------------------------------------
    request = AcquisitionRequest(
        query="API research",
        source_type="api",
    )

    route = router.route(request)

    check(
        route.provider_name == "rest_json_api",
        "api source_type did not route to rest_json_api",
    )

    print(
        "[PASS] explicit API routing"
    )

    # ---------------------------------------------------------
    # Explicit web
    # ---------------------------------------------------------
    request = AcquisitionRequest(
        query="open webpage",
        source_type="web",
        metadata={
            "url": "https://example.com",
        },
    )

    route = router.route(request)

    check(
        route.provider_name == "direct_web",
        "web source_type did not route to direct_web",
    )

    print(
        "[PASS] explicit web routing"
    )

    # ---------------------------------------------------------
    # Explicit search
    # ---------------------------------------------------------
    request = AcquisitionRequest(
        query="AI security research",
        source_type="search",
    )

    route = router.route(request)

    check(
        route.provider_name == "search",
        "search source_type did not route to search",
    )

    print(
        "[PASS] explicit search routing"
    )

    # ---------------------------------------------------------
    # Path metadata without source_type
    # ---------------------------------------------------------
    request = AcquisitionRequest(
        query="read this file",
        metadata={
            "path": "documents/research.txt",
        },
    )

    route = router.route(request)

    check(
        route.provider_name == "document",
        "path metadata did not route to document",
    )

    print(
        "[PASS] path metadata routing"
    )

    # ---------------------------------------------------------
    # URL metadata without source_type
    # ---------------------------------------------------------
    request = AcquisitionRequest(
        query="open this URL",
        metadata={
            "url": "https://example.com/research",
        },
    )

    route = router.route(request)

    check(
        route.provider_name == "direct_web",
        "URL metadata did not route to direct_web",
    )

    print(
        "[PASS] URL metadata routing"
    )

    # ---------------------------------------------------------
    # Generic query defaults to search
    # ---------------------------------------------------------
    request = AcquisitionRequest(
        query="latest AI security research",
    )

    route = router.route(request)

    check(
        route.provider_name == "search",
        "generic research query did not default to search",
    )

    print(
        "[PASS] generic query fallback routing"
    )

    # ---------------------------------------------------------
    # Convenience method
    # ---------------------------------------------------------
    provider_name = router.provider_name(
        AcquisitionRequest(
            query="test search",
        )
    )

    check(
        provider_name == "search",
        "provider_name convenience method failed",
    )

    print(
        "[PASS] provider_name convenience method"
    )

    # ---------------------------------------------------------
    # Unsupported source type
    # ---------------------------------------------------------
    try:
        router.route(
            AcquisitionRequest(
                query="unknown source",
                source_type="unknown_provider",
            )
        )
    except ValueError:
        print(
            "[PASS] unsupported source type blocked"
        )
    else:
        raise AssertionError(
            "unsupported source type was not blocked"
        )

    # ---------------------------------------------------------
    # Wrong request type
    # ---------------------------------------------------------
    try:
        router.route("not-a-request")
    except TypeError:
        print(
            "[PASS] invalid request type blocked"
        )
    else:
        raise AssertionError(
            "invalid request type was not blocked"
        )

    # ---------------------------------------------------------
    # Missing provider
    # ---------------------------------------------------------
    incomplete_engine = ResearchAcquisitionEngine(
        providers=[
            DummyProvider("search"),
        ]
    )

    incomplete_router = ResearchProviderRouter(
        incomplete_engine
    )

    try:
        incomplete_router.route(
            AcquisitionRequest(
                query="local document",
                source_type="document",
            )
        )
    except KeyError:
        print(
            "[PASS] unregistered provider blocked"
        )
    else:
        raise AssertionError(
            "unregistered provider was not blocked"
        )

    print()
    print(
        "SAHIBEX PROVIDER ROUTER TEST: PASS"
    )


if __name__ == "__main__":
    main()
