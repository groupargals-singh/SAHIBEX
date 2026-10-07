from core.brain.working_memory_expansion import WorkingMemoryExpansionEngine


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"[PASS] {message}")


def main() -> None:
    engine = WorkingMemoryExpansionEngine()

    result = engine.assess(
        relevance=0.9, priority=0.8, recency=0.9, confidence=0.9,
        goal_relevance=0.8, access_strength=0.7, interference=0.1,
        cognitive_load=0.2, task_context=0.9, stability=0.8,
        importance=0.9, continuity=0.8,
    )
    check(result.retained, "working-memory assessment retains high-value context")
    check(0.0 <= result.value <= 1.0, "working-memory score is bounded")

    ranked = engine.rank((0.2, 0.9, 0.5, 0.7))
    check(ranked == (0.9, 0.7, 0.5, 0.2), "working-memory ranking works")

    summary = engine.security_summary()
    check(summary["bounded_cognitive_layer"] is True, "working memory is bounded cognitive layer")
    check(summary["grants_permission"] is False, "working memory grants no permission")
    check(summary["executes_actions"] is False, "working memory executes no actions")
    check(summary["writes_long_term_storage"] is False, "working memory does not write long-term storage")
    check(summary["modifies_constitution"] is False, "working memory cannot modify constitution")
    check(summary["overrides_human_authority"] is False, "working memory cannot override human authority")

    print("SAHIBEX PHASE E EXPANSION TEST: PASS")
    print("PHASE_E_12_ITEM_COVERAGE_REGRESSION_PASS")


if __name__ == "__main__":
    main()
