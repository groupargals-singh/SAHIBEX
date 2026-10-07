from core.brain.risk import (
    RISK_VERSION,
    RiskEngine,
    RiskInput,
)
from core.policies.approval import RiskLevel


def test_low_risk() -> None:
    engine = RiskEngine()

    result = engine.assess(
        RiskInput(
            likelihood=0.10,
            impact=0.10,
            exposure=0.10,
            irreversibility=0.10,
            uncertainty=0.10,
            input_id="input_001",
        )
    )

    assert result.risk_score < 0.35
    assert result.level == RiskLevel.LOW
    assert result.high_risk is False
    assert result.version == RISK_VERSION


def test_high_risk() -> None:
    engine = RiskEngine()

    result = engine.assess(
        RiskInput(
            likelihood=0.80,
            impact=0.80,
            exposure=0.70,
            irreversibility=0.70,
            uncertainty=0.60,
            input_id="input_002",
        )
    )

    assert result.risk_score >= 0.60
    assert result.level == RiskLevel.HIGH
    assert result.high_risk is True


def test_critical_risk() -> None:
    engine = RiskEngine()

    result = engine.assess(
        RiskInput(
            likelihood=1.0,
            impact=1.0,
            exposure=1.0,
            irreversibility=1.0,
            uncertainty=1.0,
            input_id="input_003",
        )
    )

    assert result.risk_score == 1.0
    assert result.level == RiskLevel.CRITICAL


def test_scope_and_security_boundary() -> None:
    engine = RiskEngine()

    assert engine.authorizes_actions() is False
    assert engine.executes_actions() is False
    assert engine.grants_permission() is False
    assert engine.modifies_constitution() is False
    assert engine.replaces_permission_engine() is False


def test_invalid_signal_rejected() -> None:
    engine = RiskEngine()

    try:
        engine.assess(
            RiskInput(
                likelihood=1.5,
                impact=0.5,
                exposure=0.5,
                irreversibility=0.5,
                uncertainty=0.5,
                input_id="input_004",
            )
        )
    except ValueError:
        pass
    else:
        raise AssertionError("invalid risk signal was not rejected")


if __name__ == "__main__":
    test_low_risk()
    test_high_risk()
    test_critical_risk()
    test_scope_and_security_boundary()
    test_invalid_signal_rejected()

    print("SAHIBEX PHASE 1 #38 RISK TEST: PASS")
