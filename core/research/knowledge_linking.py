from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


VALID_TARGET_TYPES = {
    "entity",
    "concept",
    "relationship",
}


@dataclass(frozen=True)
class KnowledgeLink:
    """
    Directed link from a knowledge object to a knowledge-graph object.

    Supported target types:
    - entity
    - concept
    - relationship
    """

    knowledge_id: str
    target_id: str
    target_type: str

    def __post_init__(self) -> None:
        if not self.knowledge_id.strip():
            raise ValueError(
                "knowledge_id cannot be empty"
            )

        if not self.target_id.strip():
            raise ValueError(
                "target_id cannot be empty"
            )

        if self.target_type not in VALID_TARGET_TYPES:
            raise ValueError(
                f"invalid target_type: {self.target_type}"
            )


class KnowledgeLinker:
    """
    In-memory knowledge linking service.

    Relationship direction:

        Knowledge
            |
            +--> Entity
            +--> Concept
            +--> Relationship

    This layer intentionally does not modify KnowledgeCandidate.
    """

    def __init__(self) -> None:
        self._links: Dict[
            Tuple[str, str, str],
            KnowledgeLink,
        ] = {}

    def link(
        self,
        knowledge_id: str,
        target_id: str,
        target_type: str,
    ) -> KnowledgeLink:
        link = KnowledgeLink(
            knowledge_id=knowledge_id,
            target_id=target_id,
            target_type=target_type,
        )

        key = (
            link.knowledge_id,
            link.target_type,
            link.target_id,
        )

        existing = self._links.get(key)

        if existing is not None:
            return existing

        self._links[key] = link
        return link

    def links_for_knowledge(
        self,
        knowledge_id: str,
    ) -> List[KnowledgeLink]:
        if not knowledge_id.strip():
            raise ValueError(
                "knowledge_id cannot be empty"
            )

        return [
            link
            for link in self._links.values()
            if link.knowledge_id == knowledge_id
        ]

    def knowledge_for_target(
        self,
        target_id: str,
        target_type: str,
    ) -> List[str]:
        if not target_id.strip():
            raise ValueError(
                "target_id cannot be empty"
            )

        if target_type not in VALID_TARGET_TYPES:
            raise ValueError(
                f"invalid target_type: {target_type}"
            )

        return [
            link.knowledge_id
            for link in self._links.values()
            if (
                link.target_id == target_id
                and link.target_type == target_type
            )
        ]

    def link_count(self) -> int:
        return len(self._links)

    def clear(self) -> None:
        self._links.clear()

    def summary(self) -> dict:
        return {
            "link_count": self.link_count(),
        }
