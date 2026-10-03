from __future__ import annotations

from dataclasses import dataclass

from tools.registry import ToolDefinition, ToolRegistry


@dataclass(frozen=True)
class ToolCandidate:
    """
    A discovered tool candidate.

    Discovery only identifies suitable registered tools.
    It does not grant permission or execute anything.
    """

    name: str
    description: str
    score: int
    read_only: bool
    requires_confirmation: bool


class ToolDiscovery:
    """
    Deterministic discovery and selection layer.

    This layer:
    - searches only registered tools
    - ranks matching tools deterministically
    - returns candidates
    - never executes tools
    - never grants permission
    """

    def __init__(self, registry: ToolRegistry) -> None:
        if not isinstance(registry, ToolRegistry):
            raise TypeError(
                "registry must be ToolRegistry"
            )

        self.registry = registry

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {
            token
            for token in text.lower().split()
            if token.strip()
        }

    def discover(
        self,
        query: str,
        *,
        max_results: int = 10,
    ) -> list[ToolCandidate]:
        """
        Discover registered tools matching a query.

        Matching is based on tool name and description.
        Results are ordered by score, then tool name.
        """

        query = query.strip()

        if not query:
            raise ValueError(
                "Discovery query cannot be empty."
            )

        if max_results <= 0:
            raise ValueError(
                "max_results must be greater than zero."
            )

        query_tokens = self._tokens(query)

        candidates: list[ToolCandidate] = []

        for tool in self.registry.list_tools():
            score = self._score_tool(
                tool,
                query_tokens,
                query,
            )

            if score <= 0:
                continue

            candidates.append(
                ToolCandidate(
                    name=tool.name,
                    description=tool.description,
                    score=score,
                    read_only=tool.read_only,
                    requires_confirmation=(
                        tool.requires_confirmation
                    ),
                )
            )

        candidates.sort(
            key=lambda candidate: (
                -candidate.score,
                candidate.name,
            )
        )

        return candidates[:max_results]

    def select(
        self,
        query: str,
    ) -> ToolCandidate | None:
        """
        Select the highest-ranked discovered tool.

        Returns None when no registered tool matches.
        """

        candidates = self.discover(
            query,
            max_results=1,
        )

        if not candidates:
            return None

        return candidates[0]

    @classmethod
    def _score_tool(
        cls,
        tool: ToolDefinition,
        query_tokens: set[str],
        query: str,
    ) -> int:
        name = tool.name.lower()
        description = tool.description.lower()

        score = 0

        if query.lower() in name:
            score += 100

        if query.lower() in description:
            score += 50

        for token in query_tokens:
            if token in name:
                score += 20

            if token in description:
                score += 10

        return score
