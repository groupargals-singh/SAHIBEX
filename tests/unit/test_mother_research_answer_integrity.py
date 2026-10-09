from types import SimpleNamespace

from core.brain.mother_research_integration import MotherResearchIntegration


def test_nested_research_answer_returns_plain_text_and_verified_status():
    pipeline_result = SimpleNamespace(
        answer=SimpleNamespace(
            answer="  Evidence-backed result.  ",
            verified=True,
            status="VERIFIED",
        )
    )

    text, status = MotherResearchIntegration._answer_text_and_verification(
        pipeline_result
    )

    assert text == "Evidence-backed result."
    assert status == "VERIFIED"
    assert "namespace" not in text


def test_unverified_research_answer_is_not_promoted_to_verified():
    pipeline_result = SimpleNamespace(
        answer=SimpleNamespace(
            answer="A result without verified knowledge.",
            verified=False,
            status="UNVERIFIED",
        )
    )

    text, status = MotherResearchIntegration._answer_text_and_verification(
        pipeline_result
    )

    assert text == "A result without verified knowledge."
    assert status == "NOT_VERIFIED"


def test_missing_verification_evidence_falls_back_to_unknown():
    pipeline_result = SimpleNamespace(
        answer=SimpleNamespace(answer="Some generated result.")
    )

    text, status = MotherResearchIntegration._answer_text_and_verification(
        pipeline_result
    )

    assert text == "Some generated result."
    assert status == "UNKNOWN"


def test_explicit_pipeline_verification_status_is_preserved():
    pipeline_result = SimpleNamespace(
        answer=SimpleNamespace(answer="Checked result.", verified=False),
        verification_status="INDEPENDENTLY_CHECKED",
    )

    text, status = MotherResearchIntegration._answer_text_and_verification(
        pipeline_result
    )

    assert text == "Checked result."
    assert status == "INDEPENDENTLY_CHECKED"


def test_stale_quality_status_is_never_reported_as_verified():
    pipeline_result = SimpleNamespace(
        answer=SimpleNamespace(
            answer="Stale result.",
            verified=False,
            status="STALE",
        )
    )

    text, status = MotherResearchIntegration._answer_text_and_verification(
        pipeline_result
    )

    assert text == "Stale result."
    assert status == "NOT_VERIFIED"


def test_legacy_plain_string_adapter_still_works_without_false_verification():
    pipeline_result = SimpleNamespace(answer="Plain text result")

    text, status = MotherResearchIntegration._answer_text_and_verification(
        pipeline_result
    )

    assert text == "Plain text result"
    assert status == "UNKNOWN"
