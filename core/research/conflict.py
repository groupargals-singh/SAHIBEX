from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from core.research.models import KnowledgeCandidate


@dataclass(frozen=True)
class ConflictPair:
    first_knowledge_id: str
    second_knowledge_id: str
    first_statement: str
    second_statement: str
    reason: str


@dataclass(frozen=True)
class ConflictAnalysisResult:
    total_candidates: int
    conflict_count: int
    conflicts: List[ConflictPair]
    conflict_ids: List[str]
    consistent_ids: List[str]
    status: str


class ResearchConflictDetector:
    """
    Conservative deterministic conflict detector.

    This is a foundation layer, not full semantic reasoning.

    It detects conflicts only when:
    1. Two statements are identical except for an explicit negation.
    2. Two statements share the same context but contain a known
       contradictory lexical pair.

    Unknown semantic relationships are NOT treated as conflicts.
    """

    NEGATION_WORDS = {
        "not",
        "no",
        "never",
        "cannot",
        "can't",
        "doesn't",
        "doesnt",
        "isn't",
        "isnt",
        "aren't",
        "arent",
        "wasn't",
        "wasnt",
        "weren't",
        "werent",
        "without",
    }

    CONTRADICTION_PAIRS = {
        ("safe", "unsafe"),
        ("secure", "insecure"),
        ("enabled", "disabled"),
        ("active", "inactive"),
        ("valid", "invalid"),
        ("verified", "unverified"),
        ("available", "unavailable"),
        ("supported", "unsupported"),
        ("allowed", "blocked"),
        ("true", "false"),
        ("possible", "impossible"),
        ("connected", "disconnected"),
        ("online", "offline"),
        ("present", "absent"),
        ("success", "failure"),
        ("successful", "unsuccessful"),
    }

    @staticmethod
    def _normalize(statement: str) -> str:
        if not isinstance(statement, str):
            return ""

        text = statement.lower().strip()

        punctuation = ",.!?;:()[]{}\"'"

        for char in punctuation:
            text = text.replace(char, " ")

        return " ".join(text.split())

    @classmethod
    def _tokens(cls, statement: str) -> list[str]:
        normalized = cls._normalize(statement)
        return normalized.split() if normalized else []

    @classmethod
    def _remove_negation(cls, tokens: list[str]) -> tuple[list[str], bool]:
        remaining = []
        found = False

        for token in tokens:
            if token in cls.NEGATION_WORDS:
                found = True
            else:
                remaining.append(token)

        return remaining, found

    @classmethod
    def _explicit_negation_conflict(
        cls,
        first: str,
        second: str,
    ) -> bool:
        first_tokens = cls._tokens(first)
        second_tokens = cls._tokens(second)

        first_base, first_negated = cls._remove_negation(first_tokens)
        second_base, second_negated = cls._remove_negation(second_tokens)

        if first_base != second_base:
            return False

        return first_negated != second_negated

    @classmethod
    def _lexical_conflict(
        cls,
        first: str,
        second: str,
    ) -> bool:
        first_tokens = cls._tokens(first)
        second_tokens = cls._tokens(second)

        if len(first_tokens) != len(second_tokens):
            return False

        differences = []

        for first_token, second_token in zip(first_tokens, second_tokens):
            if first_token == second_token:
                continue

            pair = tuple(sorted((first_token, second_token)))

            known_pairs = {
                tuple(sorted(pair_item))
                for pair_item in cls.CONTRADICTION_PAIRS
            }

            if pair in known_pairs:
                differences.append(pair)
            else:
                return False

        return len(differences) == 1

    @classmethod
    def detect_pair(
        cls,
        first: KnowledgeCandidate,
        second: KnowledgeCandidate,
    ) -> ConflictPair | None:
        if first.knowledge_id == second.knowledge_id:
            return None

        if not first.statement or not second.statement:
            return None

        if cls._explicit_negation_conflict(
            first.statement,
            second.statement,
        ):
            reason = "same statement with opposite explicit negation"

        elif cls._lexical_conflict(
            first.statement,
            second.statement,
        ):
            reason = "same context with contradictory lexical term"

        else:
            return None

        return ConflictPair(
            first_knowledge_id=first.knowledge_id,
            second_knowledge_id=second.knowledge_id,
            first_statement=first.statement,
            second_statement=second.statement,
            reason=reason,
        )

    def analyze(
        self,
        knowledge_items: Iterable[KnowledgeCandidate],
    ) -> ConflictAnalysisResult:
        items = list(knowledge_items)

        conflicts: list[ConflictPair] = []
        conflict_ids: set[str] = set()

        for index, first in enumerate(items):
            for second in items[index + 1:]:
                conflict = self.detect_pair(first, second)

                if conflict is None:
                    continue

                conflicts.append(conflict)
                conflict_ids.add(first.knowledge_id)
                conflict_ids.add(second.knowledge_id)

        consistent_ids = [
            item.knowledge_id
            for item in items
            if item.knowledge_id not in conflict_ids
        ]

        if not items:
            status = "NO_RESULT"
        elif conflicts:
            status = "CONFLICT_DETECTED"
        else:
            status = "CONSISTENT"

        return ConflictAnalysisResult(
            total_candidates=len(items),
            conflict_count=len(conflicts),
            conflicts=conflicts,
            conflict_ids=sorted(conflict_ids),
            consistent_ids=consistent_ids,
            status=status,
        )
