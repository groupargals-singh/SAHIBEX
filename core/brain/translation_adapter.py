"""Opt-in external translation for already verified public research answers.

The adapter is deliberately disabled unless SAHIBEX_TRANSLATION_PROVIDER=mymemory
is explicitly configured. It never verifies facts or grants trust; callers must
re-check output language and preserve the original evidence/traceability record.
"""
from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class TranslationResult:
    text: str
    provider: str
    source_language: str
    target_language: str
    url_tokens_preserved: bool
    numeric_tokens_preserved: bool


class MyMemoryTranslationAdapter:
    """Bounded MyMemory API adapter; no credentials or local model required."""

    endpoint = "https://api.mymemory.translated.net/get"
    max_characters = 1000

    def __init__(self, *, timeout_seconds: float = 8.0) -> None:
        if not 0 < timeout_seconds <= 15:
            raise ValueError("timeout_seconds must be between 0 and 15")
        self.timeout_seconds = float(timeout_seconds)

    @staticmethod
    def configured() -> bool:
        return os.environ.get("SAHIBEX_TRANSLATION_PROVIDER", "").strip().casefold() == "mymemory"

    def translate(self, text: str, *, source_language: str, target_language: str) -> TranslationResult | None:
        if not isinstance(text, str) or not text.strip() or len(text) > self.max_characters:
            return None
        source = source_language.split("-")[0].casefold()
        target = target_language.split("-")[0].casefold()
        # Keep initial production scope narrow and auditable. English -> Hindi
        # is the P2 acceptance path; unsupported pairs fail closed.
        if source != "en" or target != "hi":
            return None

        url_pattern = re.compile(r"https?://[^\s)\]>]+", re.IGNORECASE)
        url_tokens: list[str] = []
        protected = url_pattern.sub(lambda m: _stash(url_tokens, m.group(0)), text)
        params = urllib.parse.urlencode({"q": protected, "langpair": "en|hi"})
        request = urllib.request.Request(
            f"{self.endpoint}?{params}",
            headers={"User-Agent": "SAHIBEX/1.0 (opt-in verified-answer translation)"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                if int(getattr(response, "status", 200)) != 200:
                    return None
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            return None

        if payload.get("quotaFinished") is True or str(payload.get("responseStatus", "")) != "200":
            return None
        translated = payload.get("responseData", {}).get("translatedText")
        if not isinstance(translated, str) or not translated.strip():
            return None
        # HTML entities can be returned by translation APIs.
        import html
        translated = html.unescape(translated).strip()
        for index, token in enumerate(url_tokens):
            translated = translated.replace(f"SAHIBEXURLTOKEN{index}X", token)
        url_preserved = all(token in translated for token in url_tokens)
        original_numbers = set(re.findall(r"(?<!\w)\d+(?:[.,]\d+)*(?!\w)", text))
        translated_numbers = set(re.findall(r"(?<!\w)\d+(?:[.,]\d+)*(?!\w)", translated))
        numbers_preserved = original_numbers.issubset(translated_numbers)
        if not url_preserved or not numbers_preserved:
            return None
        return TranslationResult(
            text=translated,
            provider="mymemory",
            source_language=source,
            target_language=target,
            url_tokens_preserved=url_preserved,
            numeric_tokens_preserved=numbers_preserved,
        )


def _stash(tokens: list[str], value: str) -> str:
    index = len(tokens)
    tokens.append(value)
    return f"SAHIBEXURLTOKEN{index}X"
