from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re
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
        """Tokenize claims while preserving decimals and contractions.

        ``_normalize`` is intentionally kept unchanged because the answer
        pipeline also uses it for its existing deduplication key.
        """
        if not isinstance(statement, str) or not statement.strip():
            return []

        text = statement.lower().replace("’", "'")
        raw_tokens = re.findall(
            r"(?<!\w)[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|[a-z]+(?:'[a-z]+)?",
            text,
        )
        contractions = {
            "isn't": ("is", "not"), "isnt": ("is", "not"),
            "aren't": ("are", "not"), "arent": ("are", "not"),
            "wasn't": ("was", "not"), "wasnt": ("was", "not"),
            "weren't": ("were", "not"), "werent": ("were", "not"),
            "doesn't": ("does", "not"), "doesnt": ("does", "not"),
            "don't": ("do", "not"), "dont": ("do", "not"),
            "didn't": ("did", "not"), "didnt": ("did", "not"),
            "hasn't": ("has", "not"), "hasnt": ("has", "not"),
            "haven't": ("have", "not"), "havent": ("have", "not"),
            "hadn't": ("had", "not"), "hadnt": ("had", "not"),
            "can't": ("can", "not"), "cant": ("can", "not"),
            "cannot": ("can", "not"), "couldn't": ("could", "not"),
            "couldnt": ("could", "not"), "shouldn't": ("should", "not"),
            "shouldnt": ("should", "not"), "wouldn't": ("would", "not"),
            "wouldnt": ("would", "not"), "mustn't": ("must", "not"),
            "mustnt": ("must", "not"), "won't": ("will", "not"),
            "wont": ("will", "not"),
        }
        tokens: list[str] = []
        for token in raw_tokens:
            tokens.extend(contractions.get(token, (token,)))
        return tokens

    @staticmethod
    def _numeric_value(token: str) -> Decimal | None:
        """Return a safely parsed numeric token, or None for ordinary words."""
        try:
            return Decimal(token.replace(",", ""))
        except (InvalidOperation, ValueError):
            return None

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

        # Multiple negations are ambiguous for this conservative detector.
        first_count = sum(token in cls.NEGATION_WORDS for token in first_tokens)
        second_count = sum(token in cls.NEGATION_WORDS for token in second_tokens)
        if first_count > 1 or second_count > 1:
            return False

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

        known_pairs = {
            tuple(sorted(pair_item))
            for pair_item in cls.CONTRADICTION_PAIRS
        }
        differences = 0

        for first_token, second_token in zip(first_tokens, second_tokens):
            if first_token == second_token:
                continue
            if tuple(sorted((first_token, second_token))) not in known_pairs:
                return False
            differences += 1

        return differences == 1

    @classmethod
    def _numeric_conflict(
        cls,
        first: str,
        second: str,
    ) -> bool:
        """Detect one changed numeric value in otherwise identical context.

        Date-like years are ignored when preceded by an explicit temporal
        marker, since different years can describe different time periods.
        """
        first_tokens = cls._tokens(first)
        second_tokens = cls._tokens(second)
        if not first_tokens or len(first_tokens) != len(second_tokens):
            return False

        differences = 0
        year_context_words = {
            "in", "during", "since", "until", "by", "before", "after", "year",
        }

        for index, (first_token, second_token) in enumerate(
            zip(first_tokens, second_tokens)
        ):
            if first_token == second_token:
                continue

            first_number = cls._numeric_value(first_token)
            second_number = cls._numeric_value(second_token)
            if first_number is None or second_number is None:
                return False
            if first_number == second_number:
                # Formatting variants such as 1,000 and 1000 are equivalent.
                continue

            is_year_pair = (
                first_number == first_number.to_integral_value()
                and second_number == second_number.to_integral_value()
                and 1000 <= abs(first_number) <= 9999
                and 1000 <= abs(second_number) <= 9999
                and index > 0
                and first_tokens[index - 1] in year_context_words
                and second_tokens[index - 1] in year_context_words
            )
            if is_year_pair:
                return False

            differences += 1
            if differences > 1:
                return False

        return differences == 1

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

        elif cls._numeric_conflict(
            first.statement,
            second.statement,
        ):
            reason = "same context with contradictory numeric value"

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
