"""Evidence gate for factual answers at the Main Brain boundary.

Structural quality checks are deliberately not treated as factual verification.
Only verified knowledge with attached evidence can ground a factual answer.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class FactualEvidenceAssessment:
    status: str
    answer: str | None
    knowledge_ids: tuple[str, ...]
    reason: str


_STOPWORDS = {
    "the", "is", "are", "was", "were", "do", "does", "did", "why", "what",
    "when", "where", "who", "which", "how", "a", "an", "of", "in", "to",
    "for", "and", "or", "on", "at", "with", "by", "does", "need", "needs",
    "क्या", "है", "हैं", "हो", "क्यों", "कब", "कहाँ", "कहां", "कौन", "कैसे",
    "किस", "की", "का", "के", "में", "पर", "से", "और", "एक", "को", "लिए",
    "होता", "होती", "होते", "बताओ", "बताइए", "समझाओ", "समझाइए",
    "kya", "kyu", "kyon", "kab", "kahan", "kaise", "ka", "ki", "ke",
    "hai", "hain", "ko", "se", "aur", "mein", "me", "liye", "batao",
}
_NEGATIONS = {
    "not", "no", "never", "cannot", "can't", "doesn't", "don't", "without",
    "मत", "mat",
}


def _tokens(text: str) -> set[str]:
    return {
        token for token in re.findall(r"[\w]+", text.casefold(), flags=re.UNICODE)
        if len(token) > 1 and token not in _STOPWORDS
    }


def is_factual_question(question: str) -> bool:
    """Conservative multilingual detector for questions asking factual claims."""
    if not isinstance(question, str) or not question.strip():
        return False
    text = " ".join(question.casefold().split())
    return bool(re.search(
        r"^(?:why|what|when|where|who|which|how|is|are|was|were|do|does|did|"
        r"define|explain|describe|tell me about)\b|"
        r"(?:क्या|क्यों|कब|कहाँ|कहां|कौन|कैसे|किस|बताइए|बताओ|समझाइए|समझाओ)|"
        r"\b(?:kya|kyu|kyon|kab|kahan|kaise)\b",
        text,
        flags=re.IGNORECASE,
    ))


def assess_verified_knowledge(
    question: str,
    knowledge_items: Iterable[object],
    *,
    minimum_confidence: float = 0.75,
) -> FactualEvidenceAssessment:
    """Return a grounded answer only from relevant, verified, evidenced knowledge."""
    query_tokens = _tokens(question)
    if not query_tokens:
        return FactualEvidenceAssessment(
            "INSUFFICIENT_EVIDENCE", None, (), "question_has_no_retrievable_terms"
        )

    relevant: list[tuple[object, set[str]]] = []
    for item in knowledge_items:
        statement = getattr(item, "statement", "")
        evidence = getattr(item, "evidence", None)
        verified = getattr(item, "verified", False) is True
        confidence = getattr(item, "confidence", 0.0)
        if not isinstance(statement, str) or not statement.strip():
            continue
        if not isinstance(evidence, (list, tuple)) or not any(
            isinstance(entry, str) and entry.strip() for entry in evidence
        ):
            continue
        if not verified or not isinstance(confidence, (int, float)):
            continue
        if confidence < minimum_confidence:
            continue
        statement_tokens = _tokens(statement)
        shared = query_tokens & statement_tokens
        if not shared:
            continue
        overlap = len(shared) / max(1, len(query_tokens))
        # One key term is enough for a short one-topic query; otherwise require
        # a second shared term to avoid grounding an answer on a loose match.
        if overlap >= 0.30 or (len(query_tokens) <= 2 and len(shared) == 1):
            relevant.append((item, statement_tokens))

    if not relevant:
        return FactualEvidenceAssessment(
            "INSUFFICIENT_EVIDENCE", None, (),
            "no_relevant_verified_knowledge_with_evidence",
        )

    # Conservatively reject close-topic claims that differ in negation polarity.
    for index, (left, left_tokens) in enumerate(relevant):
        left_statement = str(getattr(left, "statement", ""))
        left_negated = bool(_tokens(left_statement) & _NEGATIONS)
        for right, right_tokens in relevant[index + 1:]:
            right_statement = str(getattr(right, "statement", ""))
            right_negated = bool(_tokens(right_statement) & _NEGATIONS)
            # Compare overlap on the user's actual topic terms rather than
            # whole-sentence Jaccard: extra explanatory words must not hide a
            # contradiction between two claims about the same subject.
            shared_topic = query_tokens & left_tokens & right_tokens
            if left_negated != right_negated and len(shared_topic) >= min(2, len(query_tokens)):
                return FactualEvidenceAssessment(
                    "CONFLICTING_EVIDENCE", None, (),
                    "relevant_verified_knowledge_contains_conflicting_polarity",
                )

    # Prefer the highest-confidence entries and keep output bounded.
    relevant.sort(
        key=lambda pair: float(getattr(pair[0], "confidence", 0.0)),
        reverse=True,
    )
    selected = relevant[:3]
    statements: list[str] = []
    ids: list[str] = []
    for item, _ in selected:
        statement = str(getattr(item, "statement", "")).strip()
        knowledge_id = str(getattr(item, "knowledge_id", "")).strip()
        if statement and statement not in statements and knowledge_id:
            statements.append(statement)
            ids.append(knowledge_id)

    if not statements:
        return FactualEvidenceAssessment(
            "INSUFFICIENT_EVIDENCE", None, (),
            "verified_knowledge_missing_stable_identity",
        )
    return FactualEvidenceAssessment(
        "VERIFIED_KNOWLEDGE", " ".join(statements), tuple(ids),
        "answer_returned_directly_from_relevant_verified_knowledge",
    )
