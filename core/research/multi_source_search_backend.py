from __future__ import annotations

import queue
import threading
import time
from typing import Iterable
from urllib.parse import urlsplit, urlunsplit

from core.research.search_provider import (
    SearchProviderBackend,
    SearchResult,
)


# Global limit across all MultiSourceSearchBackend instances.
# A slot remains occupied until the actual backend call finishes,
# even when the caller's search timeout has expired.
_MAX_ACTIVE_BACKEND_CALLS = 5
_ACTIVE_BACKEND_SLOTS = threading.BoundedSemaphore(
    _MAX_ACTIVE_BACKEND_CALLS
)


class MultiSourceSearchBackend(SearchProviderBackend):
    """Run independent search engines with bounded worker usage.

    Results are discovery leads, not verified facts. Provider failures
    are isolated. Timed-out calls may continue in daemon threads, but
    their slots remain reserved until those calls actually finish.
    """

    backend_name = "multi_source"

    def __init__(
        self,
        backends: Iterable[SearchProviderBackend],
        *,
        timeout_seconds: float = 12.0,
    ) -> None:
        self.backends = tuple(backends)

        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or timeout_seconds <= 0
        ):
            raise ValueError("timeout_seconds must be positive")

        self.timeout_seconds = float(timeout_seconds)

        if not self.backends:
            raise ValueError(
                "at least one search backend is required"
            )

        if any(
            not isinstance(item, SearchProviderBackend)
            for item in self.backends
        ):
            raise TypeError(
                "all backends must implement SearchProviderBackend"
            )

        names = [
            str(getattr(item, "backend_name", "")).strip()
            for item in self.backends
        ]

        if any(not name for name in names):
            raise ValueError(
                "each backend must have a non-empty backend_name"
            )

        if len(set(names)) != len(names):
            raise ValueError("backend names must be unique")

    @staticmethod
    def _canonical_url(url: str) -> str:
        parsed = urlsplit(url.strip())
        scheme = parsed.scheme.casefold()
        host = (parsed.hostname or "").casefold().removeprefix(
            "www."
        )

        if scheme not in {"http", "https"} or not host:
            return ""

        try:
            port = parsed.port
        except ValueError:
            return ""

        if (
            port is None
            or (scheme == "https" and port == 443)
            or (scheme == "http" and port == 80)
        ):
            netloc = host
        else:
            netloc = f"{host}:{port}"

        path = parsed.path.rstrip("/") or "/"

        tracking_prefixes = ("utm_",)
        ignored = {
            "gclid",
            "fbclid",
            "ocid",
            "ved",
            "usg",
            "ref",
            "source",
        }

        query_parts = []

        for part in parsed.query.split("&") if parsed.query else []:
            key = part.partition("=")[0].casefold()

            if key in ignored or key.startswith(tracking_prefixes):
                continue

            query_parts.append(part)

        query = "&".join(sorted(query_parts))

        return urlunsplit(
            (scheme, netloc, path, query, "")
        )

    def search(
        self,
        query: str,
        *,
        max_results: int,
    ) -> list[SearchResult]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")

        if (
            not isinstance(max_results, int)
            or isinstance(max_results, bool)
            or max_results <= 0
        ):
            raise ValueError(
                "max_results must be a positive integer"
            )

        batches_by_name: dict[str, list[SearchResult]] = {}
        failed_names: set[str] = set()
        completed_names: set[str] = set()
        started_names: list[str] = []

        completions: queue.Queue[
            tuple[str, list[SearchResult] | None, bool]
        ] = queue.Queue()

        # Search fan-out is used on phone-class runtimes. Asking every RSS
        # backend for 10 results can make it fetch 30 feed entries and exceed
        # the shared deadline; then fast Google wrappers survive while slower
        # direct publisher results (notably Bing RSS) are discarded. Five leads
        # per engine are enough for diversity; the merged result still obeys
        # the caller's max_results limit.
        per_backend_limit = min(max_results, 5)

        def run_backend(
            name: str,
            backend: SearchProviderBackend,
        ) -> None:
            try:
                results = backend.search(
                    query.strip(),
                    max_results=per_backend_limit,
                )

                if not isinstance(results, list) or any(
                    not isinstance(item, SearchResult)
                    for item in results
                ):
                    raise TypeError(
                        "backend returned invalid search results"
                    )

                completions.put((name, results, False))

            except Exception:
                # Do not expose provider exceptions or credentials.
                completions.put((name, None, True))

            finally:
                # Release capacity only when the actual call ends.
                _ACTIVE_BACKEND_SLOTS.release()

        # Start only calls for which a global slot is immediately
        # available. Never create an unbounded waiting queue.
        for backend in self.backends:
            name = str(backend.backend_name)

            if not _ACTIVE_BACKEND_SLOTS.acquire(blocking=False):
                failed_names.add(name)
                continue

            worker = threading.Thread(
                target=run_backend,
                args=(name, backend),
                name=f"sahibex-search-{name}",
                daemon=True,
            )

            try:
                worker.start()
                started_names.append(name)
            except Exception:
                _ACTIVE_BACKEND_SLOTS.release()
                failed_names.add(name)

        # Use one overall deadline for the fan-out.
        deadline = time.monotonic() + self.timeout_seconds

        while len(completed_names) < len(started_names):
            remaining = deadline - time.monotonic()

            if remaining <= 0:
                break

            try:
                name, results, failed = completions.get(
                    timeout=remaining
                )
            except queue.Empty:
                break

            completed_names.add(name)

            if failed or results is None:
                failed_names.add(name)
            else:
                batches_by_name[name] = results

        # Any started call that did not report completion by the
        # deadline is considered timed out for this search only.
        failed_names.update(
            name
            for name in started_names
            if name not in completed_names
        )

        # Restore configured order for deterministic output and
        # provenance, regardless of worker completion order.
        batches = [
            (str(backend.backend_name), batches_by_name[str(backend.backend_name)])
            for backend in self.backends
            if str(backend.backend_name) in batches_by_name
        ]

        errors = [
            str(backend.backend_name)
            for backend in self.backends
            if str(backend.backend_name) in failed_names
        ]

        merged: list[SearchResult] = []
        seen: set[str] = set()

        depth = max(
            (len(items) for _, items in batches),
            default=0,
        )

        succeeded_names = [name for name, _ in batches]

        for index in range(depth):
            for name, items in batches:
                if index >= len(items):
                    continue

                item = items[index]

                try:
                    canonical = self._canonical_url(item.url)
                except (TypeError, ValueError):
                    continue

                if not canonical or canonical in seen:
                    continue

                seen.add(canonical)

                metadata = dict(item.metadata or {})
                metadata["discovery_only"] = True
                metadata["search_backend"] = name
                metadata["multi_source_engines_succeeded"] = (
                    succeeded_names
                )
                metadata["multi_source_engines_failed"] = errors

                merged.append(
                    SearchResult(
                        title=item.title,
                        url=item.url,
                        snippet=item.snippet,
                        publisher=item.publisher,
                        author=item.author,
                        published_at=item.published_at,
                        rank=len(merged) + 1,
                        metadata=metadata,
                    )
                )

                if len(merged) >= max_results:
                    return merged

        if merged:
            return merged

        if errors:
            raise RuntimeError(
                "all configured search backends failed: "
                + ", ".join(errors)
            )

        raise RuntimeError(
            "configured search backends returned no usable results"
        )
