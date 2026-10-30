from __future__ import annotations

import json
from pathlib import Path
import tempfile

from core.brain.perception_language_brain import PerceptionLanguageBrain


def main() -> None:
    with tempfile.TemporaryDirectory() as temp:
        brain = PerceptionLanguageBrain(Path(temp) / "words.json")

        result = brain.assess("Hey sahibaks, add autocarect and disnkry support")
        assert result.raw_text == "Hey sahibaks, add autocarect and disnkry support"
        assert "SAHIBEX" in result.normalized_text
        assert "autocorrect" in result.normalized_text
        assert "dictionary" in result.normalized_text
        assert result.language_code == "en"
        assert {c.original for c in result.corrections} == {"sahibaks", "autocarect", "disnkry"}

        hinglish = brain.assess("SAHIBEX mujhe samjho kya hai")
        assert hinglish.language_code == "hi-Latn"
        gujarati = brain.assess("હું તમને મદદ કરી શકું છું")
        assert gujarati.language_code == "gu"
        assert "SAHIBEX" in hinglish.normalized_text
        # Closed bilingual aliases repair common ASR spellings of the project name.
        for spoken_variant in (
            "sahibaks", "sahibeks", "sahibax", "sahibexx",
            "sahib e x", "साहिबेक्स", "साहिब एक्स",
        ):
            assert brain.assess(spoken_variant).normalized_text == "SAHIBEX", spoken_variant
        assert brain.assess("sahibeks brain").normalized_text == "SAHIBEX Brain"
        hinglish_typos = brain.assess("galt samjhni h, gpt jese samjho")
        assert "galat" in hinglish_typos.normalized_text.casefold()
        assert "samajhni" in hinglish_typos.normalized_text.casefold()
        assert "jaise" in hinglish_typos.normalized_text.casefold()
        # Similar-looking unrelated words are not rewritten by a fuzzy matcher.
        assert brain.assess("weather forecast").normalized_text == "weather forecast"
        assert brain.lookup_word("samjho") == "understand"
        assert brain.lookup_word("SHABD") == "word"
        spoken_ai_words = brain.assess("sahibex disnary speach recogntion aawaj")
        assert "dictionary" in spoken_ai_words.normalized_text
        assert "speech" in spoken_ai_words.normalized_text
        assert "recognition" in spoken_ai_words.normalized_text
        assert "awaaz" in spoken_ai_words.normalized_text
        assert brain.lookup_word("bhasha") == "language"
        assert brain.lookup_word("microphone") == "audio input device"
        assert brain.analyze_word("है")["script"] == "Devanagari"
        suggestion = brain.assess("please add dictioary")
        assert any(item.original == "dictioary" and item.corrected == "dictionary"
                   for item in suggestion.suggestions)
        assert "dictioary" in suggestion.normalized_text  # uncertain spellings are not silently changed
        word_profile = brain.analyze_word("है")
        assert word_profile["script"] == "Devanagari"
        assert word_profile["known"] is True
        assert word_profile["letter_units"]

        # Preserve negation, numbers, unknown words, and the original transcript.
        safety = brain.assess("sahibex delete mat karna 42 xqz")
        assert safety.normalized_text == "sahibex delete mat karna 42 xqz"
        assert safety.raw_text == "sahibex delete mat karna 42 xqz"

        # Explicitly learned vocabulary survives a new instance/restart.
        brain.remember_word("termux", "Android terminal environment")
        brain.remember_word("samjho", "user-defined meaning")
        restored = PerceptionLanguageBrain(Path(temp) / "words.json")
        assert restored.lookup_word("Termux") == "Android terminal environment"
        assert restored.lookup_word("samjho") == "user-defined meaning"
        payload = json.loads((Path(temp) / "words.json").read_text(encoding="utf-8"))
        assert payload["schema_version"] == 1

        for invalid in ("", "   "):
            try:
                brain.assess(invalid)
            except ValueError:
                pass
            else:
                raise AssertionError("empty text must be rejected")

        assert brain.is_read_only_by_default() is True

    print("SAHIBEX PERCEPTION LANGUAGE BRAIN TEST: PASS")


if __name__ == "__main__":
    main()


def test_perception_language_brain_contract() -> None:
    main()
