from core.brain.reasoning_modes import ReasoningModesEngine
from core.brain.hypothesis_reasoning import HypothesisReasoningEngine
from core.brain.reasoning_constraints import ConstraintReasoningEngine


def main() -> None:
    modes = ReasoningModesEngine()
    assert modes.deductive(premises=[True, True], conclusion=True).verified
    assert modes.inductive(observations=[1, 2, 3], pattern_support=0.8).verified
    assert modes.abductive(hypotheses=[("A", 0.4), ("B", 0.9)]).conclusion == "B"
    assert modes.causal(cause="A", effect="B", evidence_strength=0.8).verified
    assert modes.comparative(candidates={"A": 0.4, "B": 0.8}).conclusion == "B"

    hypothesis = HypothesisReasoningEngine()
    formed = hypothesis.form(observations=[1, 2, 3], candidate="A explains B")
    assert formed.metadata["requires_evaluation"]
    evaluated = hypothesis.evaluate(hypothesis=formed.hypothesis, evidence=[True, True, True], contradictions=0)
    assert evaluated.accepted
    rejected = hypothesis.evaluate(hypothesis="bad", evidence=[True, False], contradictions=1)
    assert not rejected.accepted

    constraints = ConstraintReasoningEngine()
    solved = constraints.solve(steps=["s1", "s2"], constraints=[True, True], conclusion="done")
    assert solved.valid and not solved.conflicts
    blocked = constraints.solve(steps=["s1"], constraints=[True, False], conclusion="unsafe")
    assert not blocked.valid and blocked.conflicts
    conflict, claims = constraints.detect_conflict(claims=["A", "B"])
    assert conflict and claims == ("A", "B")

    # Security/read-only boundary: these engines expose no execution or permission API.
    for engine in (modes, hypothesis, constraints):
        assert not hasattr(engine, "execute")
        assert not hasattr(engine, "grant_permission")
        assert not hasattr(engine, "modify_constitution")

    print("SAHIBEX PHASE H REASONING EXPANSION TEST: PASS")


if __name__ == "__main__":
    main()
