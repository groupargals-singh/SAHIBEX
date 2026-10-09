"""Conservative direct answers for explicitly requested personal-memory recall.

Only narrowly structured, high-confidence user_context memories are eligible.
This module never treats memory text as instructions or execution authority.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class MemoryFactAnswer:
    answer: str
    memory_id: str
    fact_type: str


_CODENAME_QUESTION = re.compile(
    r"(?:what is|what's|tell me|remind me|do you remember)\s+"
    r"(?:my\s+)?(?:project\s+)?codename\??|"
    r"(?:मेरा|मेरे)\s+(?:प्रोजेक्ट\s+)?कोडनेम\s+(?:क्या\s+है|बताओ|याद\s+है)\??",
    re.IGNORECASE,
)
_CODENAME_VALUE = re.compile(
    r"(?:project\s+)?codename\s*(?:is|:|=)\s*([A-Za-z0-9_-]{3,80})",
    re.IGNORECASE,
)


def resolve_memory_fact(
    question: str,
    memories: Iterable[object],
) -> MemoryFactAnswer | None:
    """Resolve only an exact codename recall from one unambiguous memory."""
    if not isinstance(question, str) or not question.strip():
        return None
    if not _CODENAME_QUESTION.fullmatch(" ".join(question.strip().split())):
        return None

    candidates: dict[str, str] = {}
    for memory in memories:
        if getattr(memory, "memory_type", None) != "user_context":
            continue
        if float(getattr(memory, "confidence", 0.0)) < 0.85:
            continue
        if float(getattr(memory, "importance", 0.0)) < 0.70:
            continue
        content = getattr(memory, "content", "")
        if not isinstance(content, str):
            continue
        match = _CODENAME_VALUE.search(content)
        if not match:
            continue
        value = match.group(1).strip(" .,:;!?\"'`")
        if value:
            candidates[value] = str(getattr(memory, "memory_id", ""))

    if len(candidates) != 1:
        return None

    value, memory_id = next(iter(candidates.items()))
    if not memory_id:
        return None
    return MemoryFactAnswer(
        answer=f"आपकी saved memory के अनुसार project codename {value} है।",
        memory_id=memory_id,
        fact_type="project_codename",
    )
