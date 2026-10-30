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


def test_research_integration_fails_closed_on_verified_answer_language_mismatch(tmp_path):
    from datetime import datetime, timezone
    from types import SimpleNamespace

    from core.brain.mother_research_integration import MotherResearchIntegration
    from core.research.storage import ResearchStorage

    storage = ResearchStorage(tmp_path / "language-gate.db")
    integration = MotherResearchIntegration(storage=storage)
    english_claim = "Narayan said the government had been working closely with the US government."
    context = SimpleNamespace(
        answer=SimpleNamespace(
            answer=SimpleNamespace(answer=english_claim, verified=True, status="VERIFIED"),
            verification_status="VERIFIED",
            aggregation=None,
            traceability=None,
            query_result=None,
            relevance_candidate_count=1,
            corroborated_candidate_count=1,
            claim_link_diagnostics={},
        ),
        acquisition=SimpleNamespace(sources=[SimpleNamespace(
            source_id="fresh-language-gate-source",
            title="Fresh source",
            locator="https://example.com/fresh",
            published_at=datetime.now(timezone.utc),
        )]),
        extraction=[],
        verification={},
        outputs={},
    )

    class FakeExecutionManager:
        def create_job(self, **kwargs):
            return None

        def create_plan(self, job_id):
            return None

        def start_job(self, job_id):
            return None

        def execute(self, **kwargs):
            return SimpleNamespace(status="completed", error=None)

    class FakeResearchPipeline:
        def context_for(self, job_id):
            return context

    integration.execution_manager = FakeExecutionManager()
    integration.research_pipeline = FakeResearchPipeline()
    try:
        result = integration.research(query="आज AI सुरक्षा में क्या नया है?")
        assert result.success is False
        assert result.status == "insufficient_evidence"
        assert result.verification_status == "LANGUAGE_MISMATCH"
        assert "पर्याप्त प्रमाण सत्यापित नहीं" in result.answer
        assert english_claim not in result.answer
        # Diagnostics describe the final user-facing fallback, not the rejected English candidate.
        assert result.diagnostics["language_consistency"]["status"] == "MATCH"
        assert result.diagnostics["language_consistency"]["matches_query"] is True
    finally:
        storage.close()


def test_verified_answer_language_must_match_query_language():
    assert MotherResearchIntegration._answer_matches_query_language(
        "आज AI सुरक्षा में क्या नया है?",
        "Narayan said the government had been working closely with the US government.",
    ) is False
    assert MotherResearchIntegration._answer_matches_query_language(
        "आज AI सुरक्षा में क्या नया है?",
        "आज की रिपोर्ट के अनुसार सरकार ने सुरक्षा जाँच जारी रखी है।",
    ) is True
    assert MotherResearchIntegration._answer_matches_query_language(
        "latest AI safety security news today",
        "The report describes the latest AI safety security developments.",
    ) is True


def test_explicit_verification_status_is_normalized_before_downstream_gate():
    pipeline_result = SimpleNamespace(
        answer=SimpleNamespace(answer="Verified result.", verified=True),
        verification_status="  verified  ",
    )

    text, status = MotherResearchIntegration._answer_text_and_verification(
        pipeline_result
    )

    assert text == "Verified result."
    assert status == "VERIFIED"


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


def test_unverified_research_can_return_only_public_source_leads():
    context = SimpleNamespace(
        acquisition=SimpleNamespace(
            sources=[
                SimpleNamespace(title="Example source", locator="https://example.com/article"),
                SimpleNamespace(title="Unsafe local source", locator="file:///etc/passwd"),
                SimpleNamespace(title="Duplicate", locator="https://example.com/article"),
            ]
        )
    )
    leads = MotherResearchIntegration._source_leads(context)
    assert leads == ["- Example source — https://example.com/article"]


def test_discovery_leads_survive_empty_publisher_fetch_without_becoming_evidence():
    context = SimpleNamespace(
        acquisition=SimpleNamespace(sources=[]),
        outputs={
            "search_discovery_acquisition": SimpleNamespace(
                sources=[SimpleNamespace(title="Unverified discovery", locator="https://news.example/story")]
            )
        },
    )
    assert MotherResearchIntegration._source_leads(context) == [
        "- Unverified discovery — https://news.example/story"
    ]
    assert context.acquisition.sources == []


def test_insufficient_evidence_message_is_hindi_for_hindi_query():
    message = MotherResearchIntegration._insufficient_evidence_message(
        "आज AI सुरक्षा में क्या नया है?",
        ["- आधिकारिक स्रोत — https://example.com/report"],
    )
    assert "पर्याप्त प्रमाण सत्यापित नहीं" in message
    assert "सत्यापित निष्कर्ष नहीं" in message
    assert "https://example.com/report" in message
    assert "I couldn't verify" not in message


def test_insufficient_evidence_message_remains_english_for_english_query():
    message = MotherResearchIntegration._insufficient_evidence_message(
        "What is new in AI security?",
        [],
    )
    assert "I couldn't verify enough reliable evidence" in message


def test_search_blocked_failure_is_localized_and_does_not_expose_raw_error():
    message = MotherResearchIntegration._execution_failure_message(
        "आज AI सुरक्षा में क्या नया है?",
        "DuckDuckGo returned an anti-bot challenge instead of search results; internal marker",
    )
    assert "सर्च सेवा ने" in message
    assert "बिना जाँचे कोई निष्कर्ष नहीं बनाया" in message
    assert "DuckDuckGo" not in message
    assert "internal marker" not in message


def test_search_blocked_english_failure_is_actionable_and_safe():
    message = MotherResearchIntegration._execution_failure_message(
        "What is new in AI security?",
        "No live search provider is configured",
    )
    assert "approved alternative search backend" in message
    assert "No live search provider" not in message


def test_pipeline_diagnostics_exposes_bounded_stage_counts_without_page_bodies():
    context = SimpleNamespace(
        outputs={
            "publisher_fetch": {
                "status": "partial",
                "requested": 10,
                "acquired": 3,
                "details": ["short fetch warning", "x" * 500],
                "page_body": "MUST_NOT_BE_EXPOSED",
            },
            "corroboration_discovery": {
                "candidate_url_count": 14,
                "selected_diverse_url_count": 10,
                "attempted_queries": ["headline latest"],
                "expansion_queries": ["latest AI safety news", "latest AI security news"],
                "failed_queries": [],
                "expansion_failures": [],
            },
        },
        verification={"documents": 3, "finding_count": 4, "evidence_count": 1, "status": "evidence_available", "truth_status": "not_evaluated"},
        extraction=[SimpleNamespace(findings=[SimpleNamespace(evidence_stored=True), SimpleNamespace(evidence_stored=False)])],
        answer=SimpleNamespace(
            status="NOT_VERIFIED",
            verified=False,
            evidence_count=1,
            arbitration=SimpleNamespace(
                accepted=False,
                status="REJECTED",
                reasons=("candidate_claim_sets_disagree", "unresolved_conflicts_present"),
            ),
        ),
    )

    diagnostics = MotherResearchIntegration._pipeline_diagnostics(context)
    assert diagnostics["publisher_fetch"]["acquired"] == 3
    assert len(diagnostics["publisher_fetch"]["errors"]) == 2
    assert len(diagnostics["publisher_fetch"]["errors"][1]) <= 180
    assert diagnostics["discovery"]["selected_diverse_url_count"] == 10
    assert diagnostics["discovery"]["attempted_expansions"] == 2
    assert diagnostics["evidence_verification"]["evidence_count"] == 1
    assert diagnostics["extraction"]["evidence_stored"] == 1
    assert diagnostics["answer"]["verified"] is False
    assert diagnostics["arbitration"]["status"] == "REJECTED"
    assert diagnostics["arbitration"]["reasons"] == [
        "candidate_claim_sets_disagree",
        "unresolved_conflicts_present",
    ]
    assert "page_body" not in diagnostics["publisher_fetch"]
    assert "MUST_NOT_BE_EXPOSED" not in repr(diagnostics)


def test_execution_failure_message_includes_leads_as_unverified():
    message = MotherResearchIntegration._execution_failure_message(
        "आज AI सुरक्षा में क्या नया है?",
        "publisher fetch could not complete",
        ["- AI safety report — https://news.google.com/rss/articles/example"],
    )
    assert "सत्यापित निष्कर्ष नहीं" in message
    assert "https://news.google.com/rss/articles/example" in message


def test_unhandled_execution_failure_preserves_safe_stage_diagnostics():
    context = SimpleNamespace(
        outputs={
            "publisher_fetch": {
                "status": "failed",
                "requested": 4,
                "acquired": 0,
                "details": ["publisher returned HTTP 403"],
            }
        },
        verification=None,
        extraction=[],
        answer=None,
    )

    def fail_execute(**kwargs):
        raise RuntimeError("injected acquisition failure")

    integration = MotherResearchIntegration.__new__(MotherResearchIntegration)
    integration.execution_manager = SimpleNamespace(
        create_job=lambda **kwargs: None,
        create_plan=lambda job_id: None,
        start_job=lambda job_id: None,
        execute=fail_execute,
    )
    integration.research_pipeline = SimpleNamespace(
        context_for=lambda job_id: context,
    )

    result = integration.research(query="latest AI safety news", confirmation=True)

    assert result.success is False
    assert result.verification_status == "FAILED"
    assert result.error == "injected acquisition failure"
    assert result.diagnostics["publisher_fetch"]["status"] == "failed"
    assert result.diagnostics["publisher_fetch"]["acquired"] == 0
    assert "publisher returned HTTP 403" in result.diagnostics["publisher_fetch"]["errors"]
    assert "page_body" not in result.diagnostics["publisher_fetch"]


def test_configured_translation_adapter_localizes_verified_answer_and_keeps_traceability(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from core.brain.translation_adapter import TranslationResult
    from core.brain.mother_research_integration import MotherResearchIntegration
    from core.research.storage import ResearchStorage

    storage = ResearchStorage(tmp_path / "translation-gate.db")
    integration = MotherResearchIntegration(storage=storage)
    english_claim = "The capital of India is New Delhi."
    context = SimpleNamespace(
        answer=SimpleNamespace(
            answer=SimpleNamespace(answer=english_claim, verified=True, status="VERIFIED"),
            verification_status="VERIFIED", aggregation=None, traceability="TRACEABLE",
            query_result=None, relevance_candidate_count=1, corroborated_candidate_count=1,
            claim_link_diagnostics={},
        ),
        acquisition=SimpleNamespace(sources=[]), extraction=[], verification={}, outputs={},
    )

    class FakeExecutionManager:
        def create_job(self, **kwargs): return None
        def create_plan(self, job_id): return None
        def start_job(self, job_id): return None
        def execute(self, **kwargs): return SimpleNamespace(status="completed", error=None)

    class FakeResearchPipeline:
        def context_for(self, job_id): return context

    monkeypatch.setattr(
        "core.brain.mother_research_integration.MyMemoryTranslationAdapter.configured",
        staticmethod(lambda: True),
    )
    monkeypatch.setattr(
        "core.brain.mother_research_integration.MyMemoryTranslationAdapter.translate",
        lambda self, text, *, source_language, target_language: TranslationResult(
            text="भारत की राजधानी नई दिल्ली है।", provider="mymemory",
            source_language="en", target_language="hi",
            url_tokens_preserved=True, numeric_tokens_preserved=True,
        ),
    )
    integration.execution_manager = FakeExecutionManager()
    integration.research_pipeline = FakeResearchPipeline()
    try:
        result = integration.research(query="भारत की राजधानी क्या है?")
        assert result.success is True
        assert result.verification_status == "VERIFIED"
        assert result.answer == "भारत की राजधानी नई दिल्ली है।"
        assert result.diagnostics["language_consistency"]["status"] == "MATCH"
        assert result.diagnostics["translation"]["status"] == "TRANSLATED_AND_LANGUAGE_CHECKED"
        assert result.diagnostics["translation"]["source_answer_kept_in_traceability"] is True
    finally:
        storage.close()


def test_current_news_freshness_gate_rejects_stale_today_source():
    from datetime import datetime, timedelta, timezone
    from types import SimpleNamespace

    now = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)
    source = SimpleNamespace(
        source_id="stale-source",
        published_at=now - timedelta(days=3),
    )
    result = MotherResearchIntegration._current_news_freshness_gate(
        "latest AI safety news today", [source], now=now
    )
    assert result["status"] == "REJECTED"
    assert result["query_window"] == "24_hours"
    assert result["failures"][0]["reason"] == "source_exceeds_query_freshness_window"


def test_current_news_freshness_gate_rejects_unknown_publication_time():
    from datetime import datetime, timezone
    from types import SimpleNamespace

    source = SimpleNamespace(source_id="unknown-date", published_at=None)
    result = MotherResearchIntegration._current_news_freshness_gate(
        "latest AI safety news this week", [source],
        now=datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc),
    )
    assert result["status"] == "REJECTED"
    assert result["failures"][0]["reason"] == "publication_time_unknown"


def test_current_news_freshness_gate_accepts_fresh_weekly_sources():
    from datetime import datetime, timedelta, timezone
    from types import SimpleNamespace

    now = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)
    sources = [
        SimpleNamespace(source_id="fresh-a", published_at=now - timedelta(days=2)),
        SimpleNamespace(source_id="fresh-b", published_at=now - timedelta(days=6)),
    ]
    result = MotherResearchIntegration._current_news_freshness_gate(
        "latest AI safety news this week", sources, now=now
    )
    assert result["status"] == "PASS"
    assert result["source_count"] == 2


def test_stable_fact_query_is_not_rejected_for_old_source_dates():
    from datetime import datetime, timedelta, timezone
    from types import SimpleNamespace

    now = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)
    source = SimpleNamespace(
        source_id="stable-reference",
        published_at=now - timedelta(days=8000),
    )
    assert MotherResearchIntegration._current_news_freshness_gate(
        "भारत की राजधानी क्या है?", [source], now=now
    ) is None


def test_real_research_integration_fails_closed_on_stale_verified_news_answer(tmp_path):
    from datetime import datetime, timedelta, timezone
    from types import SimpleNamespace

    from core.brain.mother_research_integration import MotherResearchIntegration
    from core.research.storage import ResearchStorage

    now = datetime.now(timezone.utc)
    stale_source = SimpleNamespace(
        source_id="live-stale-source",
        title="Old AI safety report",
        locator="https://example.com/old-report",
        published_at=now - timedelta(days=3),
    )
    context = SimpleNamespace(
        answer=SimpleNamespace(
            answer=SimpleNamespace(
                answer="This is today's verified AI safety news.",
                verified=True,
                status="VERIFIED",
            ),
            verification_status="VERIFIED",
            aggregation=None,
            traceability=None,
            query_result=None,
            relevance_candidate_count=1,
            corroborated_candidate_count=1,
            claim_link_diagnostics={},
        ),
        acquisition=SimpleNamespace(sources=[stale_source]),
        extraction=[],
        verification={},
        outputs={},
    )

    class FakeExecutionManager:
        def create_job(self, **kwargs): return None
        def create_plan(self, job_id): return None
        def start_job(self, job_id): return None
        def execute(self, **kwargs): return SimpleNamespace(status="completed", error=None)

    class FakeResearchPipeline:
        def context_for(self, job_id): return context

    storage = ResearchStorage(tmp_path / "freshness-gate.db")
    integration = MotherResearchIntegration(storage=storage)
    integration.execution_manager = FakeExecutionManager()
    integration.research_pipeline = FakeResearchPipeline()
    try:
        result = integration.research(query="latest AI safety news today")
        assert result.success is False
        assert result.status == "insufficient_evidence"
        assert result.verification_status == "STALE"
        assert "today's verified AI safety news" not in result.answer
        gate = result.diagnostics["current_news_freshness_gate"]
        assert gate["status"] == "REJECTED"
        assert gate["query_window"] == "24_hours"
    finally:
        storage.close()
