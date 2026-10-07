from core.brain.goal_relevance import (
    GoalRelevanceEngine,
    GoalRelevanceInput,
    GoalRelevanceLevel,
)


def main() -> None:
    engine = GoalRelevanceEngine()

    critical = engine.evaluate(
        GoalRelevanceInput(
            content="Directly completes the active goal",
            goal="Build SAHIBEX Attention Engine",
            semantic_relevance=1.0,
            goal_dependency=1.0,
            expected_contribution=1.0,
            goal_priority=1.0,
        )
    )

    assert critical.level == GoalRelevanceLevel.CRITICAL
    assert critical.relevant is True
    assert critical.relevance_score >= 0.85

    high = engine.evaluate(
        GoalRelevanceInput(
            content="Strongly supports the active goal",
            goal="Build SAHIBEX Attention Engine",
            semantic_relevance=0.8,
            goal_dependency=0.7,
            expected_contribution=0.7,
            goal_priority=0.7,
        )
    )

    assert high.level == GoalRelevanceLevel.HIGH
    assert high.relevant is True

    medium = engine.evaluate(
        GoalRelevanceInput(
            content="Somewhat useful information",
            goal="Build SAHIBEX Attention Engine",
            semantic_relevance=0.5,
            goal_dependency=0.4,
            expected_contribution=0.4,
            goal_priority=0.4,
        )
    )

    assert medium.level == GoalRelevanceLevel.MEDIUM
    assert medium.relevant is True

    low = engine.evaluate(
        GoalRelevanceInput(
            content="Weakly related information",
            goal="Build SAHIBEX Attention Engine",
            semantic_relevance=0.2,
            goal_dependency=0.2,
            expected_contribution=0.2,
            goal_priority=0.2,
        )
    )

    assert low.level == GoalRelevanceLevel.LOW
    assert low.relevant is False

    irrelevant = engine.evaluate(
        GoalRelevanceInput(
            content="Completely unrelated information",
            goal="Build SAHIBEX Attention Engine",
            semantic_relevance=0.0,
            goal_dependency=0.0,
            expected_contribution=0.0,
            goal_priority=0.0,
        )
    )

    assert irrelevant.level == GoalRelevanceLevel.IRRELEVANT
    assert irrelevant.relevant is False

    try:
        GoalRelevanceInput(
            content="Invalid",
            goal="Test goal",
            semantic_relevance=2.0,
            goal_dependency=0.0,
            expected_contribution=0.0,
            goal_priority=0.0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "out-of-range relevance value was accepted"
        )

    print(
        "SAHIBEX PHASE 1 #39 "
        "GOAL-RELEVANCE ENGINE TEST: PASS"
    )


if __name__ == "__main__":
    main()
