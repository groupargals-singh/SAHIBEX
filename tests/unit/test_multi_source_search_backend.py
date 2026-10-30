from core.research.multi_source_search_backend import MultiSourceSearchBackend
from core.research.search_provider import SearchProviderBackend, SearchResult


class StubBackend(SearchProviderBackend):
    def __init__(self, name, results=None, error=None):
        self.backend_name = name
        self.results = list(results or [])
        self.error = error
        self.calls = []

    def search(self, query, *, max_results):
        self.calls.append((query, max_results))
        if self.error:
            raise RuntimeError("simulated provider outage")
        return self.results[:max_results]


def result(title, url):
    return SearchResult(title=title, url=url, snippet="unverified discovery")


def test_multi_source_backend_combines_and_round_robins_independent_engines():
    google = StubBackend("google_news_rss", [
        result("A", "https://publisher-a.example/story?utm_source=google"),
        result("B", "https://publisher-b.example/story"),
    ])
    bing = StubBackend("bing_news_rss", [
        result("A duplicate", "https://www.publisher-a.example/story"),
        result("C", "https://publisher-c.example/story"),
    ])
    ddg = StubBackend("duckduckgo_html", [
        result("D", "https://publisher-d.example/story"),
    ])

    merged = MultiSourceSearchBackend([google, bing, ddg]).search("test topic", max_results=4)

    assert [item.title for item in merged] == ["A", "D", "B", "C"]
    assert [item.rank for item in merged] == [1, 2, 3, 4]
    assert merged[0].metadata["discovery_only"] is True
    assert merged[0].metadata["search_backend"] == "google_news_rss"
    assert merged[0].metadata["multi_source_engines_succeeded"] == [
        "google_news_rss", "bing_news_rss", "duckduckgo_html"
    ]


def test_multi_source_backend_isolates_one_engine_failure():
    broken = StubBackend("broken_engine", error=True)
    working = StubBackend("working_engine", [result("Usable", "https://publisher.example/story")])

    merged = MultiSourceSearchBackend([broken, working]).search("test topic", max_results=5)

    assert len(merged) == 1
    assert merged[0].title == "Usable"
    assert merged[0].metadata["multi_source_engines_failed"] == ["broken_engine"]


def test_multi_source_backend_caps_per_engine_fetch_to_preserve_slow_direct_sources():
    google = StubBackend("google_news_rss", [
        result(f"Google wrapper {index}", f"https://news.google.com/rss/articles/{index}")
        for index in range(5)
    ])
    bing = StubBackend("bing_news_rss", [
        result(f"Publisher {index}", f"https://publisher{index}.example/story")
        for index in range(5)
    ])

    merged = MultiSourceSearchBackend([google, bing], timeout_seconds=1.0).search(
        "current research", max_results=10
    )

    assert google.calls == [("current research", 5)]
    assert bing.calls == [("current research", 5)]
    assert len(merged) == 10
    assert any(item.metadata["search_backend"] == "bing_news_rss" for item in merged)


def test_multi_source_backend_fails_closed_if_all_engines_fail():
    backend = MultiSourceSearchBackend([
        StubBackend("broken_a", error=True),
        StubBackend("broken_b", error=True),
    ])
    try:
        backend.search("test topic", max_results=5)
    except RuntimeError as exc:
        assert "all configured search backends failed" in str(exc)
    else:
        raise AssertionError("expected all-provider failure to be visible")


def test_multi_source_backend_validates_provider_contract():
    try:
        MultiSourceSearchBackend([])
    except ValueError as exc:
        assert "at least one" in str(exc)
    else:
        raise AssertionError("expected empty backend list to be rejected")


def test_multi_source_backend_skips_malformed_urls_without_aborting_good_results():
    backend = StubBackend("working_engine", [
        result("Malformed", "https://publisher.example:bad/story"),
        result("Good", "https://publisher.example/story"),
    ])
    merged = MultiSourceSearchBackend([backend]).search("test topic", max_results=5)
    assert [item.title for item in merged] == ["Good"]

def test_multi_source_returns_fast_results_when_first_engine_times_out():
    import time

    class SlowBackend(StubBackend):
        def search(self, query, *, max_results):
            time.sleep(0.8)
            return super().search(query, max_results=max_results)

    slow = SlowBackend(
        "slow_engine",
        [result("Slow", "https://slow.example/story")],
    )
    fast = StubBackend(
        "fast_engine",
        [result("Fast", "https://fast.example/story")],
    )

    backend = MultiSourceSearchBackend(
        [slow, fast],
        timeout_seconds=0.1,
    )

    started = time.monotonic()
    merged = backend.search("test topic", max_results=5)
    elapsed = time.monotonic() - started

    assert [item.title for item in merged] == ["Fast"]
    assert elapsed < 0.5
    assert merged[0].metadata["multi_source_engines_failed"] == [
        "slow_engine"
    ]
    assert merged[0].metadata["discovery_only"] is True

def test_timed_out_workers_do_not_exceed_global_capacity():
    import threading
    import time

    release = threading.Event()

    class BlockedBackend(StubBackend):
        def search(self, query, *, max_results):
            release.wait(timeout=2.0)
            return super().search(
                query,
                max_results=max_results,
            )

    backends = [
        BlockedBackend(
            f"blocked_{index}",
            [
                result(
                    f"Result {index}",
                    f"https://blocked{index}.example/story",
                )
            ],
        )
        for index in range(5)
    ]

    backend = MultiSourceSearchBackend(
        backends,
        timeout_seconds=0.05,
    )

    try:
        try:
            backend.search("first query", max_results=5)
        except RuntimeError:
            pass

        # The first calls are still blocked. A second search must
        # fail fast rather than creating more worker threads.
        fast = StubBackend(
            "fast_engine",
            [result("Fast", "https://fast.example/story")],
        )

        second = MultiSourceSearchBackend(
            [fast],
            timeout_seconds=0.05,
        )

        try:
            second.search("second query", max_results=1)
        except RuntimeError as exc:
            assert "all configured search backends failed" in str(exc)
        else:
            raise AssertionError(
                "expected capacity exhaustion to fail closed"
            )

        assert fast.calls == []

    finally:
        # Do not leave test workers blocked after an assertion. Wait for their
        # finally blocks to release the global semaphore so the next test does
        # not nondeterministically observe artificial capacity exhaustion.
        release.set()
        import core.research.multi_source_search_backend as backend_module
        deadline = time.monotonic() + 1.0
        while (
            backend_module._ACTIVE_BACKEND_SLOTS._value
            < backend_module._MAX_ACTIVE_BACKEND_CALLS
            and time.monotonic() < deadline
        ):
            time.sleep(0.01)
        assert backend_module._ACTIVE_BACKEND_SLOTS._value == backend_module._MAX_ACTIVE_BACKEND_CALLS


def test_multi_source_backend_fails_closed_when_all_engines_return_empty_results():
    backend = MultiSourceSearchBackend([
        StubBackend("empty_google", []),
        StubBackend("empty_bing", []),
    ])
    try:
        backend.search("query with no matches", max_results=5)
    except RuntimeError as exc:
        assert "returned no usable results" in str(exc)
    else:
        raise AssertionError("empty search must not be reported as successful")
