from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


EPISODIC_MEMORY_VERSION = "P2-EM-1"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class EpisodicMemory:
    """
    Immutable representation of a remembered episode/event.

    Preserves:
    - what happened
    - when it happened
    - context
    - participants/entities
    - outcome
    - source/provenance
    """

    episode_id: str
    event: str
    context: str
    source: str
    occurred_at: datetime = field(default_factory=utc_now)
    recorded_at: datetime = field(default_factory=utc_now)
    participants: List[str] = field(default_factory=list)
    outcome: Optional[str] = None
    importance: float = 0.5
    confidence: float = 0.5
    provenance: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.episode_id, str) or not self.episode_id.strip():
            raise ValueError("episode_id cannot be empty")

        if not isinstance(self.event, str) or not self.event.strip():
            raise ValueError("event cannot be empty")

        if not isinstance(self.context, str):
            raise ValueError("context must be a string")

        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("source cannot be empty")

        if not 0.0 <= self.importance <= 1.0:
            raise ValueError("importance must be between 0 and 1")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        if not isinstance(self.participants, list):
            raise ValueError("participants must be a list")

        if not isinstance(self.provenance, dict):
            raise ValueError("provenance must be a dictionary")

        if not isinstance(self.tags, list):
            raise ValueError("tags must be a list")


class EpisodicMemoryStore:
    """
    Bounded in-process episodic memory store.

    Stores episode objects only.
    No permission or execution authority.
    """

    def __init__(self, capacity: int = 256) -> None:
        if not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("capacity must be a positive integer")

        self.capacity = capacity
        self._episodes: Dict[str, EpisodicMemory] = {}

    def store(self, episode: EpisodicMemory) -> EpisodicMemory:
        if not isinstance(episode, EpisodicMemory):
            raise TypeError("episode must be an EpisodicMemory")

        self._episodes[episode.episode_id] = episode

        while len(self._episodes) > self.capacity:
            oldest_id = min(
                self._episodes,
                key=lambda episode_id: (
                    self._episodes[episode_id].occurred_at,
                    episode_id,
                ),
            )
            del self._episodes[oldest_id]

        return episode

    def get(
        self,
        episode_id: str,
    ) -> Optional[EpisodicMemory]:
        if not isinstance(episode_id, str) or not episode_id.strip():
            raise ValueError(
                "episode_id must be a non-empty string"
            )

        return self._episodes.get(episode_id)

    def contains(self, episode_id: str) -> bool:
        return episode_id in self._episodes

    def by_participant(
        self,
        participant: str,
    ) -> tuple[EpisodicMemory, ...]:
        if not isinstance(participant, str) or not participant.strip():
            raise ValueError(
                "participant must be a non-empty string"
            )

        return tuple(
            episode
            for episode in self._episodes.values()
            if participant in episode.participants
        )

    def by_tag(
        self,
        tag: str,
    ) -> tuple[EpisodicMemory, ...]:
        if not isinstance(tag, str) or not tag.strip():
            raise ValueError(
                "tag must be a non-empty string"
            )

        return tuple(
            episode
            for episode in self._episodes.values()
            if tag in episode.tags
        )

    def recent(
        self,
        limit: int = 10,
    ) -> tuple[EpisodicMemory, ...]:
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError(
                "limit must be a positive integer"
            )

        ordered = sorted(
            self._episodes.values(),
            key=lambda episode: (
                episode.occurred_at,
                episode.recorded_at,
            ),
            reverse=True,
        )

        return tuple(ordered[:limit])

    def count(self) -> int:
        return len(self._episodes)

    def remove(self, episode_id: str) -> bool:
        if not isinstance(episode_id, str) or not episode_id.strip():
            raise ValueError(
                "episode_id must be a non-empty string"
            )

        return self._episodes.pop(
            episode_id,
            None,
        ) is not None

    def clear(self) -> None:
        self._episodes.clear()

    def summary(self) -> dict[str, Any]:
        return {
            "version": EPISODIC_MEMORY_VERSION,
            "capacity": self.capacity,
            "episode_count": self.count(),
            "immutable_episode_objects": True,
            "preserves_event_time": True,
            "preserves_context": True,
            "preserves_provenance": True,
            "grants_permission": False,
            "executes_actions": False,
            "modifies_constitution": False,
        }
