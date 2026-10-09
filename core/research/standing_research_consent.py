"""Narrow standing consent for public, read-only research.

This is not a blanket network permission. It applies only to clearly
classified search/learn requests, and never to uploads, downloads, arbitrary
URL fetching, credential use, system changes, or other protected actions.
The consent reflects the user's explicit instruction to avoid per-query
prompts for routine internet learning; the normal protected-action gates stay
in place for everything outside this scope.
"""
from __future__ import annotations

import re


class StandingResearchConsent:
    VERSION = "1.0"
    ALLOWED_INTENTS = frozenset({"search", "learn"})
    BLOCKED_PATTERNS = (
        r"\b(?:upload|send|post|submit)\b",
        r"\b(?:download|install|execute|run command)\b",
        r"\b(?:connect to|log in|login|sign in|credential|password|api key|token)\b",
        r"\b(?:delete|modify|write|overwrite|purchase|pay|transfer money)\b",
        r"https?://",
        r"\bwww\.",
    )

    def allows(self, *, intent: str, action: str, request: str) -> bool:
        if intent not in self.ALLOWED_INTENTS:
            return False
        # Intent/action pairing must match the deterministic classifier.
        # Explicit NETWORK_ACCESS actions are never covered.
        if intent == "search" and action != "research":
            return False
        if intent == "learn" and action != "respond":
            return False
        if not isinstance(request, str) or not request.strip():
            return False
        normalized = request.casefold()
        if any(re.search(pattern, normalized) for pattern in self.BLOCKED_PATTERNS):
            return False
        return True
