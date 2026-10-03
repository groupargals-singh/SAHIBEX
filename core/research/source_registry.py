from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional

from core.research.models import ResearchSource


@dataclass(frozen=True)
class SourceRegistration:
    source: ResearchSource
    is_new: bool


class SourceRegistry:
    """
    Central registry for research sources.

    Responsibilities:
    - Register research sources.
    - Prevent duplicate source identities.
    - Retrieve sources by ID.
    - Find sources by locator.
    - Find sources by title/publisher.
    """

    def __init__(self) -> None:
        self._sources: Dict[str, ResearchSource] = {}
        self._locator_index: Dict[str, str] = {}

    @staticmethod
    def _normalize_locator(locator: str) -> str:
        return locator.strip().lower()

    def register(self, source: ResearchSource) -> SourceRegistration:
        if not isinstance(source, ResearchSource):
            raise TypeError("source must be a ResearchSource")

        existing_by_id = self._sources.get(source.source_id)
        if existing_by_id is not None:
            return SourceRegistration(
                source=existing_by_id,
                is_new=False,
            )

        normalized_locator = self._normalize_locator(source.locator)

        existing_id = self._locator_index.get(normalized_locator)
        if existing_id is not None:
            return SourceRegistration(
                source=self._sources[existing_id],
                is_new=False,
            )

        self._sources[source.source_id] = source
        self._locator_index[normalized_locator] = source.source_id

        return SourceRegistration(
            source=source,
            is_new=True,
        )

    def get(self, source_id: str) -> Optional[ResearchSource]:
        return self._sources.get(source_id)

    def require(self, source_id: str) -> ResearchSource:
        source = self.get(source_id)

        if source is None:
            raise KeyError(f"Unknown research source: {source_id}")

        return source

    def find_by_locator(self, locator: str) -> Optional[ResearchSource]:
        normalized_locator = self._normalize_locator(locator)
        source_id = self._locator_index.get(normalized_locator)

        if source_id is None:
            return None

        return self._sources[source_id]

    def find(
        self,
        *,
        title: Optional[str] = None,
        publisher: Optional[str] = None,
    ) -> list[ResearchSource]:
        title_normalized = title.strip().lower() if title else None
        publisher_normalized = publisher.strip().lower() if publisher else None

        results: list[ResearchSource] = []

        for source in self._sources.values():
            if title_normalized is not None:
                if source.title.strip().lower() != title_normalized:
                    continue

            if publisher_normalized is not None:
                source_publisher = (source.publisher or "").strip().lower()

                if source_publisher != publisher_normalized:
                    continue

            results.append(source)

        return results

    def contains(self, source_id: str) -> bool:
        return source_id in self._sources

    def all(self) -> Iterable[ResearchSource]:
        return tuple(self._sources.values())

    def count(self) -> int:
        return len(self._sources)

    def clear(self) -> None:
        self._sources.clear()
        self._locator_index.clear()

    def summary(self) -> dict:
        return {
            "source_count": self.count(),
            "locator_index_count": len(self._locator_index),
        }
