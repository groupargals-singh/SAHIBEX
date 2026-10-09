"""Conservative quality checks for generated conversational answers.

These checks catch obvious failures but cannot prove factual correctness.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class AnswerQuality:
    acceptable: bool
    score: float
    reasons: tuple[str, ...]


def _tokens(text: str) -> list[str]:
    return re.findall(r"[\w]+", text.casefold(), flags=re.UNICODE)


def _has_basic_clause_coverage(question: str, answer_tokens: set[str]) -> bool:
    """Require a minimal lexical signal from each explicit joined request."""
    parts = re.split(
        r"\s+(?:और|तथा|साथ ही|इसके अलावा|and|also|plus)\s+",
        question.casefold(),
        flags=re.IGNORECASE,
    )
    if len(parts) < 2:
        return True

    stop = {
        "क्या", "है", "हैं", "हो", "भी", "बताओ", "बताइए", "समझाओ",
        "करो", "करे", "मुझे", "कैसे", "क्यों", "कौन", "किस", "की",
        "का", "के", "में", "पर", "से", "और", "एक", "the", "is", "are",
        "what", "how", "why", "tell", "me", "about", "please", "the",
        "a", "an", "of", "in", "to", "for", "also", "and",
    }
    for part in parts:
        substantive = {
            token for token in _tokens(part)
            if len(token) >= 3 and token not in stop
        }
        if substantive and not (substantive & answer_tokens):
            return False
    return True


def assess_answer(question: str, answer: str) -> AnswerQuality:
    reasons: list[str] = []
    q = " ".join((question or "").split()).strip()
    a = " ".join((answer or "").split()).strip()
    if not a:
        return AnswerQuality(False, 0.0, ("empty_answer",))

    lowered = a.casefold()
    if any(marker in lowered for marker in (
        "memory data:", "knowledge data:", "intent:", "system prompt:",
        "as an ai language model",
    )):
        reasons.append("instruction_or_context_leak")

    q_token_list = _tokens(q)
    q_tokens = set(q_token_list)
    a_tokens = _tokens(a)
    a_set = set(a_tokens)
    if len(a_tokens) >= 5 and q_tokens:
        overlap = len(q_tokens & a_set) / max(1, len(q_tokens))
        starts_by_echo = (
            len(q_token_list) >= 5
            and a_tokens[:len(q_token_list)] == q_token_list
            and len(a_tokens) <= len(q_token_list) * 4.0
        )
        if starts_by_echo or (
            overlap >= 0.88 and len(a_tokens) <= len(q_tokens) * 1.8
        ):
            reasons.append("question_echo_without_new_content")

    if len(a_tokens) >= 12:
        for n in (3, 4, 5):
            chunks = [tuple(a_tokens[i:i+n]) for i in range(len(a_tokens)-n+1)]
            if chunks and len(set(chunks)) / len(chunks) < 0.55:
                reasons.append("repetitive_output")
                break

    if not _has_basic_clause_coverage(q, a_set):
        reasons.append("possible_missing_question_part")

    # Catch obvious token-limit cuts such as "... founded in 193",
    # unfinished conjunctions, and sentence-ending commas. This is a warning,
    # not a truth test.
    has_terminal_punctuation = bool(
        re.search(r"[.!?।]$|[.!?।][\"'”’)]$", a)
    )
    if a and a.endswith((",", "，", ":", ";", "—", "-")):
        reasons.append("possible_truncated_output")
    elif len(a_tokens) >= 10 and not has_terminal_punctuation:
        reasons.append("possible_truncated_output")
    elif a and not has_terminal_punctuation:
        last = a_tokens[-1] if a_tokens else ""
        if last.isdigit() or last in {
            "और", "लेकिन", "क्योंकि", "कि", "तथा",
            "and", "but", "because", "which", "that", "with", "of", "to",
        }:
            reasons.append("possible_truncated_output")

    score = 1.0 - min(1.0, 0.45 * len(reasons))
    return AnswerQuality(not reasons, round(score, 3), tuple(reasons))


def main() -> None:
    echo = assess_answer(
        "आसमान नीला क्यों दिखाई देता है?",
        "आसमान नीला क्यों दिखाई देता है? यह आसमान के दिन रात के बीच दिखाई देने के लिए",
    )
    assert not echo.acceptable
    assert assess_answer(
        "आसमान नीला क्यों दिखाई देता है?",
        "वायुमंडल के अणु सूर्य के प्रकाश की नीली तरंगों को अधिक बिखेरते हैं।",
    ).acceptable
    assert not assess_answer("Explain this", "Intent: explain. Memory data: none.").acceptable
    assert not assess_answer("Question?", "  ").acceptable
    truncated = assess_answer("भारत की राजधानी और इतिहास बताओ", "नई दिल्ली की स्थापना 193")
    assert not truncated.acceptable
    assert "possible_truncated_output" in truncated.reasons
    comma_cut = assess_answer(
        "भारत की राजधानी और इतिहास बताओ",
        "भारत की राजधानी नई दिल्ली है। इतिहास में नई दिल्ली एक राष्ट्रीय राजधानी थी,",
    )
    assert not comma_cut.acceptable
    missing_part = assess_answer(
        "भारत की राजधानी क्या है और इतिहास भी बताओ?",
        "भारत की राजधानी नई दिल्ली है।",
    )
    assert not missing_part.acceptable
    complete = assess_answer(
        "भारत की राजधानी क्या है और इतिहास भी बताओ?",
        "भारत की राजधानी नई दिल्ली है। इतिहास के अनुसार यह शहर 20वीं सदी में विकसित हुआ।",
    )
    assert complete.acceptable
    print("SAHIBEX ANSWER QUALITY TEST: PASS")


if __name__ == "__main__":
    main()
