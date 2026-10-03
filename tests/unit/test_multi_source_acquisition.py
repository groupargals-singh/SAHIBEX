from __future__ import annotations

from core.research.acquisition import (
    AcquisitionRequest,
    AcquisitionResult,
    AcquiredSource,
    ResearchAcquisitionEngine,
    ResearchAcquisitionProvider,
)
from core.research.multi_source import (
    ResearchMultiSourceAcquisition,
)


class FakeProvider(
    ResearchAcquisitionProvider
):
    def __init__(
        self,
        name: str,
        source_id: str,
        requires_network: bool,
        content: str,
    ) -> None:
        self.provider_name = name
        self.requires_network = requires_network
        self.source_id = source_id
        self.content = content
        self.calls = 0

    def acquire(
        self,
        request: AcquisitionRequest,
    ) -> AcquisitionResult:
        self.calls += 1

        source = AcquiredSource(
            source_id=self.source_id,
            title=f"{self.provider_name} result",
            source_type=self.provider_name,
            locator=f"{self.provider_name}:test",
            content=self.content,
            metadata={
                "provider": self.provider_name,
            },
        )

        return AcquisitionResult(
            query=request.query,
            sources=[source],
            completed=True,
            status="completed",
            metadata={
                "provider": self.provider_name,
            },
        )


def check(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    search = FakeProvider(
        name="search",
        source_id="source_search",
        requires_network=True,
        content="search result",
    )

    rss = FakeProvider(
        name="rss_atom",
        source_id="source_rss",
        requires_network=True,
        content="rss result",
    )

    document = FakeProvider(
        name="document",
        source_id="source_document",
        requires_network=False,
        content="document result",
    )

    engine = ResearchAcquisitionEngine(
        providers=[
            search,
            rss,
            document,
        ]
    )

    coordinator = ResearchMultiSourceAcquisition(
        acquisition_engine=engine
    )

    print(
        "[PASS] multi-source coordinator created"
    )

    # ---------------------------------------------------------
    # 1. Non-network provider
    # ---------------------------------------------------------

    document_request = AcquisitionRequest(
        query="SAHIBEX multi-source research",
        source_type="document",
        metadata={
            "path": "research/test.txt",
        },
    )

    result = coordinator.acquire(
        [document_request],
        confirmation=False,
    )

    check(
        result.completed is True,
        "document-only acquisition did not complete",
    )

    check(
        result.status == "completed",
        "document-only status mismatch",
    )

    check(
        len(result.sources) == 1,
        "document source missing",
    )

    check(
        document.calls == 1,
        "document provider was not executed",
    )

    check(
        result.failed_providers == [],
        "document provider unexpectedly failed",
    )

    print(
        "[PASS] non-network provider acquisition"
    )

    # ---------------------------------------------------------
    # 2. Network providers must be blocked
    # ---------------------------------------------------------

    search_request = AcquisitionRequest(
        query="SAHIBEX multi-source research",
        source_type="search",
    )

    rss_request = AcquisitionRequest(
        query="SAHIBEX multi-source research",
        source_type="rss",
    )

    blocked = coordinator.acquire(
        [
            search_request,
            rss_request,
        ],
        confirmation=False,
    )

    check(
        blocked.completed is False,
        "network acquisition unexpectedly completed",
    )

    check(
        blocked.status == "failed",
        "blocked network status mismatch",
    )

    check(
        search.calls == 0,
        "search provider executed without permission",
    )

    check(
        rss.calls == 0,
        "RSS provider executed without permission",
    )

    check(
        sorted(blocked.failed_providers)
        == ["rss_atom", "search"],
        "blocked providers were not recorded correctly",
    )

    check(
        blocked.sources == [],
        "blocked network request returned sources",
    )

    print(
        "[PASS] network providers blocked before execution"
    )

    # ---------------------------------------------------------
    # 3. Mixed query must be rejected
    # ---------------------------------------------------------

    try:
        coordinator.acquire(
            [
                AcquisitionRequest(
                    query="query one",
                    source_type="document",
                    metadata={
                        "path": "one.txt",
                    },
                ),
                AcquisitionRequest(
                    query="query two",
                    source_type="document",
                    metadata={
                        "path": "two.txt",
                    },
                ),
            ]
        )

    except ValueError:
        print(
            "[PASS] mixed-query multi-source request blocked"
        )

    else:
        raise AssertionError(
            "mixed-query request was not blocked"
        )

    # ---------------------------------------------------------
    # 4. Empty request
    # ---------------------------------------------------------

    try:
        coordinator.acquire([])

    except ValueError:
        print(
            "[PASS] empty multi-source request blocked"
        )

    else:
        raise AssertionError(
            "empty request was not blocked"
        )

    # ---------------------------------------------------------
    # 5. Invalid request item
    # ---------------------------------------------------------

    try:
        coordinator.acquire(
            ["invalid-request"]
        )

    except TypeError:
        print(
            "[PASS] invalid request item blocked"
        )

    else:
        raise AssertionError(
            "invalid request item was not blocked"
        )

    # ---------------------------------------------------------
    # 6. Duplicate merge
    #
    # Both requests intentionally use the SAME supported
    # provider. The provider returns the same source ID.
    #
    # This verifies the merge layer independently from
    # provider-name routing.
    # ---------------------------------------------------------

    duplicate_provider = FakeProvider(
        name="document",
        source_id="same_source",
        requires_network=False,
        content="same document",
    )

    duplicate_engine = ResearchAcquisitionEngine(
        providers=[
            duplicate_provider,
        ]
    )

    duplicate_coordinator = (
        ResearchMultiSourceAcquisition(
            acquisition_engine=duplicate_engine
        )
    )

    duplicate_request = AcquisitionRequest(
        query="duplicate test",
        source_type="document",
        metadata={
            "path": "same.txt",
        },
    )

    duplicate_result = (
        duplicate_coordinator.acquire(
            [
                duplicate_request,
                duplicate_request,
            ]
        )
    )

    check(
        duplicate_result.completed is True,
        "duplicate acquisition did not complete",
    )

    check(
        duplicate_result.status == "completed",
        "duplicate acquisition status mismatch",
    )

    check(
        len(duplicate_result.provider_results) == 2,
        "both provider acquisitions were not recorded",
    )

    check(
        duplicate_provider.calls == 2,
        "provider was not called twice",
    )

    check(
        len(duplicate_result.sources) == 1,
        "duplicate source was not removed",
    )

    check(
        duplicate_result.sources[0].source_id
        == "same_source",
        "wrong merged source remained",
    )

    print(
        "[PASS] duplicate source merge"
    )

    # ---------------------------------------------------------
    # 7. Router contract preservation
    # ---------------------------------------------------------

    routed_document = coordinator.router.route(
        document_request
    )

    check(
        routed_document.provider_name
        == "document",
        "document router contract changed",
    )

    routed_search = coordinator.router.route(
        search_request
    )

    check(
        routed_search.provider_name
        == "search",
        "search router contract changed",
    )

    routed_rss = coordinator.router.route(
        rss_request
    )

    check(
        routed_rss.provider_name
        == "rss_atom",
        "RSS router contract changed",
    )

    print(
        "[PASS] provider routing contract preserved"
    )

    print()
    print(
        "SAHIBEX MULTI-SOURCE ACQUISITION TEST: PASS"
    )


if __name__ == "__main__":
    main()
