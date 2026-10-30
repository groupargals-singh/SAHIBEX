from __future__ import annotations

import pytest

from core.brain.research_learning_brain import ResearchLearningBrain


@pytest.mark.parametrize(
    ("phrase", "expected"),
    [
        ("Search the internet for latest AI safety security news today.", "latest AI safety security news today"),
        ("Please search online for Python typing documentation", "Python typing documentation"),
        ("Search for current NASA Artemis program facts!", "current NASA Artemis program facts"),
        ("Look up OpenAI safety report", "OpenAI safety report"),
        ("Find information about Python", "Python"),
        ("Research India's digital public infrastructure", "India's digital public infrastructure"),
        ("Internet par search karo Bharat ki digital economy", "Bharat ki digital economy"),
        ("इंटरनेट पर खोजो भारत की डिजिटल अर्थव्यवस्था", "भारत की डिजिटल अर्थव्यवस्था"),
    ],
)
def test_normalize_research_query_strips_only_leading_command(phrase, expected):
    assert ResearchLearningBrain.normalize_research_query(phrase) == expected


def test_normalize_research_query_preserves_plain_topic():
    topic = "What is the Python programming language?"
    assert ResearchLearningBrain.normalize_research_query(topic) == topic.rstrip(" .!?।")


@pytest.mark.parametrize("phrase", ["", "   ", "Search the internet for", "Search for ."])
def test_normalize_research_query_rejects_missing_topic(phrase):
    with pytest.raises(ValueError):
        ResearchLearningBrain.normalize_research_query(phrase)


def test_research_topic_sends_normalized_subject_to_mother_research(tmp_path, monkeypatch):
    from core.brain.mother_research_integration import MotherResearchIntegration, MotherResearchResult
    from core.research.storage import ResearchStorage

    storage = ResearchStorage(tmp_path / "query-normalization.sqlite3")
    research = MotherResearchIntegration(storage=storage)
    seen = {}

    def fake_research(*, query, confirmation=False):
        seen["query"] = query
        return MotherResearchResult(
            success=True,
            query=query,
            status="completed",
            answer="Verified test answer",
            job_id="normalization-job",
            execution_id="normalization-execution",
            verification_status="VERIFIED",
        )

    monkeypatch.setattr(research, "research", fake_research)
    brain = ResearchLearningBrain(research=research)
    result = brain.research_topic("Search the internet for latest AI safety security news today.")

    assert result.success is True
    assert seen["query"] == "latest AI safety security news today"
    storage.close()
