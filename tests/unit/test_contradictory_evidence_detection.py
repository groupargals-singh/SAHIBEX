from datetime import datetime, timezone

import pytest

from core.research.conflict import ResearchConflictDetector
from core.research.conflict_intelligence import (
    CONFLICT_TYPE_NUMERIC_CONTRADICTION,
    ResearchConflictIntelligence,
)
from core.research.models import KnowledgeCandidate


def knowledge(knowledge_id: str, statement: str) -> KnowledgeCandidate:
    now = datetime.now(timezone.utc)
    return KnowledgeCandidate(
        knowledge_id=knowledge_id,
        statement=statement,
        findings=[],
        evidence=[],
        confidence=0.8,
        verified=False,
        created_at=now,
        last_verified_at=None,
        metadata={},
    )


def test_explicit_negation_is_detected() -> None:
    conflict = ResearchConflictDetector.detect_pair(
        knowledge("positive", "The system is safe."),
        knowledge("negative", "The system is not safe."),
    )
    assert conflict is not None
    assert conflict.reason == "same statement with opposite explicit negation"


def test_negative_contraction_is_normalized_before_comparison() -> None:
    conflict = ResearchConflictDetector.detect_pair(
        knowledge("positive", "The system is safe."),
        knowledge("negative", "The system isn't safe."),
    )
    assert conflict is not None
    assert conflict.reason == "same statement with opposite explicit negation"


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ("The service costs 20 dollars", "The service costs 30 dollars"),
        ("The temperature is 21.5 degrees", "The temperature is 22.5 degrees"),
        ("The population is 1,000 people", "The population is 2,000 people"),
    ],
)
def test_same_context_with_different_numeric_value_is_detected(
    first: str, second: str,
) -> None:
    conflict = ResearchConflictDetector.detect_pair(
        knowledge("first", first),
        knowledge("second", second),
    )
    assert conflict is not None
    assert conflict.reason == "same context with contradictory numeric value"


def test_numeric_formatting_difference_is_not_a_conflict() -> None:
    conflict = ResearchConflictDetector.detect_pair(
        knowledge("first", "The population is 1,000 people"),
        knowledge("second", "The population is 1000 people"),
    )
    assert conflict is None


def test_year_change_alone_is_not_assumed_to_be_a_contradiction() -> None:
    conflict = ResearchConflictDetector.detect_pair(
        knowledge("first", "The report was published in 2024"),
        knowledge("second", "The report was published in 2025"),
    )
    assert conflict is None


def test_multiple_negations_are_not_misclassified_as_conflict() -> None:
    conflict = ResearchConflictDetector.detect_pair(
        knowledge("positive", "The system is safe"),
        knowledge("double-negative", "The system is not not safe"),
    )
    assert conflict is None


def test_known_lexical_contradiction_still_detects() -> None:
    conflict = ResearchConflictDetector.detect_pair(
        knowledge("enabled", "Network access is enabled"),
        knowledge("disabled", "Network access is disabled"),
    )
    assert conflict is not None
    assert conflict.reason == "same context with contradictory lexical term"


def test_unrelated_context_is_not_a_conflict() -> None:
    conflict = ResearchConflictDetector.detect_pair(
        knowledge("cost", "The service costs 20 dollars"),
        knowledge("temperature", "The temperature is 30 degrees"),
    )
    assert conflict is None


def test_same_knowledge_id_is_not_compared_against_itself() -> None:
    item = knowledge("same", "The system is safe")
    assert ResearchConflictDetector.detect_pair(item, item) is None


def test_numeric_conflict_is_included_in_analysis_summary() -> None:
    result = ResearchConflictDetector().analyze(
        [
            knowledge("first", "The service costs 20 dollars"),
            knowledge("second", "The service costs 30 dollars"),
            knowledge("unrelated", "The system uses Python"),
        ]
    )
    assert result.status == "CONFLICT_DETECTED"
    assert result.conflict_count == 1
    assert result.conflict_ids == ["first", "second"]
    assert result.consistent_ids == ["unrelated"]


def test_numeric_conflict_has_structured_intelligence_type() -> None:
    result = ResearchConflictIntelligence().analyze(
        [
            knowledge("first", "The service costs 20 dollars"),
            knowledge("second", "The service costs 30 dollars"),
        ]
    )
    assert result.total_conflicts == 1
    assert result.assessments[0].conflict_type == CONFLICT_TYPE_NUMERIC_CONTRADICTION
