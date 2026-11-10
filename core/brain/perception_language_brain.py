"""Perception and word-knowledge layer for SAHIBEX voice/text input.

This is a local, conservative helper—not an ASR engine or a replacement for an
LLM. It preserves the raw transcript, makes only high-confidence curated
corrections, and keeps uncertain candidates as suggestions for the user.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import threading
import unicodedata

from core.brain.universal_language_brain import UniversalLanguageBrain


@dataclass(frozen=True)
class WordCorrection:
    original: str
    corrected: str
    reason: str
    confidence: float


@dataclass(frozen=True)
class PerceptionResult:
    raw_text: str
    normalized_text: str
    language_code: str
    corrections: tuple[WordCorrection, ...]
    suggestions: tuple[WordCorrection, ...]
    known_terms: tuple[str, ...]


class PerceptionLanguageBrain:
    """Conservative multilingual transcript cleanup and word-library lookup."""

    VERSION = "1.0"
    MAX_TEXT_LENGTH = 8192
    MAX_LIBRARY_ENTRIES = 5000
    _LOCK = threading.RLock()

    # Curated aliases that commonly arise from speech-to-text on this project.
    # Canonical spelling is applied only when the token is clearly a product name.
    _ALIASES = {
        # Explicit project-name variants seen in speech transcripts. This is a
        # closed alias list, not a general fuzzy rewrite of user commands.
        "sahibaks": "SAHIBEX",
        "sahibecs": "SAHIBEX",
        "sahibexx": "SAHIBEX",
        "sahibeks": "SAHIBEX",
        "sahibax": "SAHIBEX",
        "sahibaqs": "SAHIBEX",
        "sahibexs": "SAHIBEX",
        "saahibex": "SAHIBEX",
        "sahebex": "SAHIBEX",
        "saahibaks": "SAHIBEX",
        "sahib e x": "SAHIBEX",
        "sahib ex": "SAHIBEX",
        "sahib x": "SAHIBEX",
        "साहिबेक्स": "SAHIBEX",
        "साहिब एक्स": "SAHIBEX",
        "साहिबेक्स ब्रेन": "SAHIBEX Brain",
        "sahibex brain": "SAHIBEX Brain",
        "sahibaks brain": "SAHIBEX Brain",
        "sahibeks brain": "SAHIBEX Brain",
    }

    # Small, explicit corrections only. Avoid generic fuzzy replacement because
    # changing a name, number, negation, or command can change user intent.
    _SAFE_CORRECTIONS = {
        "autocarect": ("autocorrect", 0.99),
        "autocorect": ("autocorrect", 0.99),
        "autocorrectt": ("autocorrect", 0.99),
        "disnkry": ("dictionary", 0.98),
        "dictionry": ("dictionary", 0.98),
        "dictionairy": ("dictionary", 0.98),
        "dictinary": ("dictionary", 0.98),
        "dictnary": ("dictionary", 0.96),
        "disnary": ("dictionary", 0.96),
        "disnky": ("dictionary", 0.95),
        "libary": ("library", 0.98),
        "librery": ("library", 0.98),
        "langauge": ("language", 0.99),
        "understnad": ("understand", 0.99),
        "listning": ("listening", 0.99),
        "recogniton": ("recognition", 0.98),
        "recogntion": ("recognition", 0.97),
        "speach": ("speech", 0.98),
        "microfone": ("microphone", 0.98),
        "akshr": ("akshar", 0.96),
        "aawaj": ("awaaz", 0.96),
        "awaj": ("awaaz", 0.95),
        "recieve": ("receive", 0.99),
        "teh": ("the", 0.99),
        "thier": ("their", 0.97),
        "becuase": ("because", 0.99),
        "definately": ("definitely", 0.98),
        "seperate": ("separate", 0.98),
        "samjho": ("samjho", 1.0),
        "sahibaks": ("SAHIBEX", 0.96),
        "sahibecs": ("SAHIBEX", 0.96),
        "sahibaqs": ("SAHIBEX", 0.96),
        "galt": ("galat", 0.98),
        "samjh": ("samajh", 0.96),
        "smjh": ("samajh", 0.94),
        "jese": ("jaise", 0.96),
        "jesa": ("jaisa", 0.96),
        "galattt": ("galat", 0.97),
        "pahle": ("pehle", 0.96),
        "kro": ("karo", 0.96),
        "samjhni": ("samajhni", 0.96),
        "samjhna": ("samajhna", 0.96),
    }

    # Starter word library: aliases and frequent bilingual words/commands.
    # This is a seed vocabulary, not a claim of complete dictionary coverage.
    _STARTER_TERMS = {
        "sahibex": "SAHIBEX",
        "sahibex brain": "SAHIBEX Brain",
        "galat": "wrong",
        "samajh": "understand",
        "jaise": "like/as",
        "pehle": "before/first",
        "karo": "do",
        "baat": "talk/statement",
        "samajhni": "to understand",
        "sahi": "correct/right",
        "bat": "bat or spoken Hindi 'baat' (context dependent)",
        "weather": "weather",
        "tomorrow": "tomorrow",
        "please": "please",
        "explain": "explain",
        "topic": "topic",
        "brain": "brain",
        "hindi": "Hindi",
        "hinglish": "Hinglish",
        "english": "English",
        "sunna": "listen",
        "sunne": "listen",
        "samajhna": "understand",
        "samjho": "understand",
        "samjhana": "explain",
        "shabd": "word",
        "shabda": "word (context dependent)",
        "bhasha": "language",
        "bhaasha": "language",
        "bol": "speak/speech",
        "bolna": "to speak",
        "bolo": "speak",
        "boliye": "please speak",
        "awaaz": "voice/sound",
        "aawaz": "voice/sound",
        "awaz": "voice/sound",
        "suno": "listen",
        "sunna": "listen",
        "pehchaan": "recognition/identity",
        "akshar": "letter/character",
        "varnmala": "alphabet",
        "varna": "letter/phoneme (context dependent)",
        "matra": "Devanagari vowel sign",
        "swar": "vowel",
        "vyanjan": "consonant",
        "bhashantar": "translation",
        "anuvad": "translation",
        "jawab": "answer",
        "uttar": "answer",
        "sawal": "question",
        "prashn": "question",
        "dikkat": "problem/difficulty",
        "samasya": "problem",
        "samadhan": "solution",
        "sudhar": "correction/improvement",
        "sudharo": "correct/improve",
        "poora": "complete/full",
        "pura": "complete/full (romanized variant)",
        "adhura": "incomplete",
        "abhi": "now",
        "baad": "later/after",
        "pehle": "before/first",
        "dobara": "again",
        "jaldi": "quickly/soon",
        "dhire": "slowly",
        "dheere": "slowly",
        "theek": "correct/okay",
        "sahi": "correct/right",
        "galat": "wrong",
        "bataiye": "please tell",
        "batana": "to tell",
        "kijiye": "please do",
        "karna": "do",
        "karen": "please do",
        "karoge": "will do",
        "tum": "you (informal)",
        "aap": "you (polite)",
        "hum": "we/us",
        "ham": "we/us (romanized variant)",
        "mere": "my/mine",
        "hamara": "our",
        "hamari": "our",
        "ko": "to/for (postposition)",
        "mein": "in/inside",
        "se": "from/with/by",
        "par": "on/at",
        "aur": "and/more",
        "lekin": "but",
        "agar": "if",
        "tab": "then",
        "kyun": "why",
        "kab": "when",
        "kahan": "where",
        "kaun": "who",
        "kaunsa": "which one",
        "voice": "spoken sound",
        "speech": "spoken language/audio",
        "recognition": "identification from audio/input",
        "transcript": "text produced from speech",
        "transcription": "speech-to-text conversion",
        "microphone": "audio input device",
        "offline": "works without network access",
        "model": "trained parameterized recognition/reasoning system",
        "engine": "software runtime that performs a task",
        "shabdon": "words",
        "akshar": "letter",
        "letters": "letters",
        "dictionary": "dictionary",
        "library": "word library",
        "autocorrect": "automatic spelling correction",
        "kya": "what",
        "kaise": "how",
        "karo": "do",
        "karna": "do",
        "batao": "tell me",
        "samjhao": "explain",
        "nahi": "no/not",
        "nahin": "no/not",
        "hai": "is/are",
        "hain": "are",
        "mujhe": "to me/I need",
        "mera": "my",
        "meri": "my",
        "chahiye": "want/need",
        "है": "is/are",
        "हैं": "are",
        "क्या": "what",
        "मुझे": "to me/I need",
        "नहीं": "no/not",
        "शब्द": "word",
        "शब्दों": "words",
        "अक्षर": "letter",
        "समझो": "understand",
        "बताओ": "tell me",
        "करो": "do",
    }

    def __init__(self, library_path: str | Path | None = None) -> None:
        if library_path is None:
            library_path = (
                Path(__file__).resolve().parents[2]
                / "data" / "knowledge" / "voice_word_library.json"
            )
        self.library_path = Path(library_path)
        self._library = dict(self._STARTER_TERMS)
        self._load_library()

    @staticmethod
    def _fold(text: str) -> str:
        return unicodedata.normalize("NFC", text).casefold().strip()

    @staticmethod
    def _preserve_case(original: str, replacement: str) -> str:
        if original.isupper():
            return replacement.upper()
        if original[:1].isupper():
            return replacement[:1].upper() + replacement[1:]
        return replacement

    def _load_library(self) -> None:
        try:
            if not self.library_path.is_file():
                return
            if self.library_path.stat().st_size > 2_000_000:
                return
            payload = json.loads(self.library_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or payload.get("schema_version") != 1:
                return
            entries = payload.get("entries", {})
            if not isinstance(entries, dict):
                return
            # Load only bounded string-to-string entries; never execute stored data.
            for word, meaning in list(entries.items())[: self.MAX_LIBRARY_ENTRIES]:
                if (isinstance(word, str) and isinstance(meaning, str)
                        and word.strip() and meaning.strip()
                        and len(word) <= 100 and len(meaning) <= 300):
                    self._library[self._fold(word)] = meaning.strip()
        except (OSError, UnicodeError, json.JSONDecodeError, TypeError):
            # A corrupt optional learning library must not block voice input.
            return

    def _save_library(self) -> None:
        self.library_path.parent.mkdir(parents=True, exist_ok=True)
        entries = {
            key: value for key, value in self._library.items()
            if key not in self._STARTER_TERMS or value != self._STARTER_TERMS[key]
        }
        entries = dict(list(entries.items())[-self.MAX_LIBRARY_ENTRIES:])
        payload = {"schema_version": 1, "entries": entries}
        temporary = self.library_path.with_suffix(self.library_path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.library_path)

    def remember_word(self, word: str, meaning: str) -> None:
        """Persist a harmless vocabulary entry when explicitly requested."""
        if not isinstance(word, str) or not isinstance(meaning, str):
            raise TypeError("word and meaning must be strings")
        word, meaning = word.strip(), meaning.strip()
        if not word or not meaning:
            raise ValueError("word and meaning must be non-empty")
        if len(word) > 100 or len(meaning) > 300:
            raise ValueError("word or meaning exceeds the allowed length")
        if any(ord(ch) < 32 for ch in word + meaning):
            raise ValueError("control characters are not allowed")
        with self._LOCK:
            self._library[self._fold(word)] = meaning
            self._save_library()

    def lookup_word(self, word: str) -> str | None:
        if not isinstance(word, str):
            raise TypeError("word must be a string")
        return self._library.get(self._fold(word))

    def _normalize_aliases(self, text: str) -> tuple[str, list[WordCorrection]]:
        result = text
        corrections: list[WordCorrection] = []
        # Longer phrases first, case-insensitively, while preserving surrounding text.
        for alias, canonical in sorted(self._ALIASES.items(), key=lambda item: -len(item[0])):
            def replace_alias(match: re.Match[str], target: str = canonical) -> str:
                if match.group(0) != target:
                    corrections.append(WordCorrection(
                        original=match.group(0),
                        corrected=target,
                        reason="curated_sahibex_name_alias",
                        confidence=0.97,
                    ))
                return target

            result = re.sub(
                rf"(?<![\w]){re.escape(alias)}(?![\w])",
                replace_alias,
                result,
                flags=re.IGNORECASE,
            )
        return result, corrections

    def assess(self, text: str, *, language_code: str | None = None) -> PerceptionResult:
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        raw = unicodedata.normalize("NFC", text)
        if not raw.strip():
            raise ValueError("text must be non-empty")
        if len(raw) > self.MAX_TEXT_LENGTH:
            raise ValueError("text exceeds maximum length")

        normalized = " ".join(raw.strip().split())
        normalized, alias_corrections = self._normalize_aliases(normalized)
        corrections: list[WordCorrection] = list(alias_corrections)
        suggestions: list[WordCorrection] = []

        def replace_word(match: re.Match[str]) -> str:
            token = match.group(0)
            found = self._SAFE_CORRECTIONS.get(self._fold(token))
            if not found:
                return token
            replacement, confidence = found
            replacement = self._preserve_case(token, replacement)
            if token != replacement:
                corrections.append(WordCorrection(
                    original=token, corrected=replacement,
                    reason="curated_high_confidence_spelling", confidence=confidence,
                ))
            return replacement

        normalized = re.sub(r"(?<![\w])[^\W\d_]+(?![\w])", replace_word, normalized, flags=re.UNICODE)
        # Identify known terms but do not reinterpret the user's whole sentence.
        words = re.findall(r"[^\W\d_]+(?:['’][^\W\d_]+)?", normalized.casefold(), flags=re.UNICODE)
        known = tuple(sorted({word for word in words if word in self._library}))
        already_corrected = {item.original.casefold() for item in corrections}
        for token in words:
            if len(token) < 4 or token in self._library or token in already_corrected:
                continue
            candidates = [candidate for candidate in self._library
                          if len(candidate) >= 4 and self._edit_distance_at_most_one(token, candidate)]
            if len(candidates) == 1:
                suggestions.append(WordCorrection(
                    original=token, corrected=candidates[0],
                    reason="single_edit_dictionary_suggestion", confidence=0.72,
                ))
        language = language_code or self._guess_language(normalized)
        return PerceptionResult(
            raw_text=raw,
            normalized_text=normalized,
            language_code=language,
            corrections=tuple(corrections),
            suggestions=tuple(suggestions),
            known_terms=known,
        )

    @staticmethod
    def _edit_distance_at_most_one(left: str, right: str) -> bool:
        if left == right or abs(len(left) - len(right)) > 1:
            return left == right
        i = j = edits = 0
        while i < len(left) and j < len(right):
            if left[i] == right[j]:
                i += 1
                j += 1
                continue
            edits += 1
            if edits > 1:
                return False
            if len(left) > len(right):
                i += 1
            elif len(right) > len(left):
                j += 1
            else:
                i += 1
                j += 1
        if i < len(left) or j < len(right):
            edits += 1
        return edits <= 1

    def analyze_word(self, word: str) -> dict[str, object]:
        """Return a basic letter/script/meaning profile for a single word."""
        if not isinstance(word, str):
            raise TypeError("word must be a string")
        value = unicodedata.normalize("NFC", word.strip())
        if not value or len(value) > 100:
            raise ValueError("word must be non-empty and at most 100 characters")
        units: list[str] = []
        for char in value:
            if units and unicodedata.category(char) in {"Mn", "Mc", "Me"}:
                units[-1] += char
            else:
                units.append(char)
        if any(0x0900 <= ord(char) <= 0x097F for char in value):
            script = "Devanagari"
        elif any(char.isalpha() and ord(char) < 128 for char in value):
            script = "Latin"
        else:
            script = "Mixed or other"
        return {
            "word": value,
            "meaning": self.lookup_word(value),
            "known": self.lookup_word(value) is not None,
            "script": script,
            "letter_units": units,
            "letter_count": sum(1 for char in value if char.isalpha()),
        }

    @staticmethod
    def _guess_language(text: str) -> str:
        # Reuse SAHIBEX's shared multilingual detector. Its Latin-script
        # unknown fallback is refined conservatively for ordinary English/Hinglish.
        assessment = UniversalLanguageBrain().detect(text)
        if assessment.language_code == "und-Latn":
            words = set(re.findall(r"[a-zA-Z]+", text.casefold()))
            hinglish = {"hai", "hain", "kya", "mujhe", "karo", "batao", "nahi", "kaise", "chahiye", "samjho", "samjhao"}
            return "hi-Latn" if words & hinglish else "en"
        return assessment.language_code

    @staticmethod
    def is_read_only_by_default() -> bool:
        return True
