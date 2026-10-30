from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class ContentFilterDecision:
    accepted: bool
    reason: str
    normalized_text: str


class ResearchContentFilter:
    """Conservative deterministic filter for obvious page chrome/noise.

    This filter does not decide truth. It removes only strong, explicit
    navigation/promotional boilerplate before candidate claims are stored.
    Uncertain text is retained for the separate verification pipeline.
    """

    VERSION = "1.0"
    MIN_CHARS = 5
    _BOILERPLATE_PATTERNS = (
        re.compile(r"^click here[.!]*$", re.I),
        re.compile(r"\bjoin our whatsapp channel\b", re.I),
        re.compile(r"\bsubscribe to (our|the) newsletter\b", re.I),
        re.compile(r"\bclick here to subscribe\b", re.I),
        re.compile(r"\bread more (stories|articles|news)\b", re.I),
        re.compile(r"\brelated stories\b", re.I),
        re.compile(r"\btrending (now|stories|news)\b", re.I),
        re.compile(r"\bshare this (article|story|page)\b", re.I),
        re.compile(r"\bfollow us on (facebook|x|twitter|instagram|linkedin)\b", re.I),
        re.compile(r"\ball rights reserved\b", re.I),
        re.compile(r"\baccept all cookies\b", re.I),
        re.compile(r"\bprivacy policy\s*[|•]\s*terms of use\b", re.I),
        re.compile(r"^skip to content\b", re.I),
        re.compile(r"^advertisement\b", re.I),
        re.compile(r"\bmake us preferred source on google\b", re.I),
        re.compile(r"\b(?:whatsapp|facebook|reddit|twitter|instagram)\b.*\bprint\b", re.I),
        re.compile(r"\bstory continues below this ad\b", re.I),
        re.compile(r"^also read\s*[|:]?", re.I),
        re.compile(r"^by:\s*[^.]{1,80}\b\d+\s*min(?:ute)?s? read\b", re.I),
    )

    _INLINE_NOISE_PATTERNS = (
        re.compile(r"\bskip to content\s+advertisement\b", re.I),
        re.compile(r"^advertisement\b", re.I),
        re.compile(r"\bskip to content\b", re.I),
        re.compile(r"\bmake us preferred source on google\b", re.I),
        re.compile(r"\bwhatsapp\s+twitter\s+facebook\s+reddit\s+print\b", re.I),
        re.compile(r"\bstory continues below this ad\b", re.I),
        re.compile(r"\balso read\s*[|:]\s*[^.!?।॥]*", re.I),
        re.compile(r"\bby:\s*[^.]{1,80}\b\d+\s*min(?:ute)?s? read\b", re.I),
    )

    def evaluate(self, text: str) -> ContentFilterDecision:
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        normalized = " ".join(text.split()).strip()
        if not normalized:
            return ContentFilterDecision(False, "empty", normalized)

        # Strip recognizable inline page chrome before evaluating the remaining
        # sentence; otherwise an otherwise useful claim can carry navigation,
        # advertising, or social-share text into the knowledge graph.
        for pattern in self._INLINE_NOISE_PATTERNS:
            normalized = pattern.sub(" ", normalized)
        normalized = " ".join(normalized.split()).strip()

        if not normalized:
            return ContentFilterDecision(False, "page_boilerplate", normalized)
        if len(normalized) < self.MIN_CHARS:
            return ContentFilterDecision(False, "too_short_for_claim", normalized)
        for pattern in self._BOILERPLATE_PATTERNS:
            if pattern.search(normalized):
                return ContentFilterDecision(False, "page_boilerplate", normalized)
        return ContentFilterDecision(True, "candidate_content", normalized)
