import json
from io import BytesIO
from types import SimpleNamespace

from core.brain.translation_adapter import MyMemoryTranslationAdapter


def test_translation_adapter_is_opt_in(monkeypatch):
    monkeypatch.delenv("SAHIBEX_TRANSLATION_PROVIDER", raising=False)
    assert MyMemoryTranslationAdapter.configured() is False


def test_translation_adapter_preserves_numbers_and_urls(monkeypatch):
    monkeypatch.setenv("SAHIBEX_TRANSLATION_PROVIDER", "mymemory")
    payload = {
        "responseStatus": 200,
        "quotaFinished": False,
        "responseData": {
            "translatedText": "भारत की राजधानी 2026 में भी नई दिल्ली है। देखें SAHIBEXURLTOKEN0X"
        },
    }

    class FakeResponse:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return json.dumps(payload).encode()

    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: FakeResponse())
    result = MyMemoryTranslationAdapter().translate(
        "India's capital in 2026 is New Delhi. See https://example.com/source",
        source_language="en",
        target_language="hi",
    )
    assert result is not None
    assert "https://example.com/source" in result.text
    assert "2026" in result.text
    assert result.url_tokens_preserved is True
    assert result.numeric_tokens_preserved is True


def test_translation_adapter_rejects_lost_numeric_evidence(monkeypatch):
    monkeypatch.setenv("SAHIBEX_TRANSLATION_PROVIDER", "mymemory")
    payload = {"responseStatus": 200, "quotaFinished": False,
               "responseData": {"translatedText": "भारत में कोई संख्या नहीं।"}}
    class FakeResponse:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return json.dumps(payload).encode()
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: FakeResponse())
    assert MyMemoryTranslationAdapter().translate(
        "India had 42 incidents.", source_language="en", target_language="hi"
    ) is None


def test_translation_adapter_rejects_unsupported_language_pair(monkeypatch):
    monkeypatch.setenv("SAHIBEX_TRANSLATION_PROVIDER", "mymemory")
    assert MyMemoryTranslationAdapter().translate(
        "Bonjour", source_language="fr", target_language="hi"
    ) is None
