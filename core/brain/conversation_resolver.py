"""Deterministic local responses for basic text-only conversation commands.

These responses keep greetings, capability questions, and status requests usable
without pretending that the small local language model verified those answers.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ConversationResponse:
    intent: str
    answer: str
    response_id: str


_RULES = (
    (
        re.compile(r"(?:नमस्ते|नमस्कार|प्रणाम|हेलो|हाय|hello|hi|hey)(?:\s*[!.।]*)?", re.I),
        ConversationResponse(
            "general_request",
            "नमस्ते! मैं SAHIBEX हूँ। अपना सवाल या टेक्स्ट कमांड लिखिए; मैं उपलब्ध क्षमताओं के अनुसार मदद करूँगा।",
            "CONV-GREETING-001",
        ),
    ),
    (
        re.compile(r"(?:तुम क्या कर सकते हो|आप क्या कर सकते हैं|sahibex क्या कर सकता है|what can you do|what can sahibex do|help|मदद)(?:\s*[?!.।]*)?", re.I),
        ConversationResponse(
            "general_request",
            "अभी आप मुझसे टेक्स्ट में सवाल पूछ सकते हैं, जानकारी/समझाइश माँग सकते हैं, उपलब्ध स्थानीय ज्ञान से जवाब ले सकते हैं, कोड का मसौदा और काम की योजना बनवा सकते हैं। इंटरनेट रिसर्च तभी सफल होगी जब खोज सेवा और नेटवर्क उपलब्ध हों। फ़ाइल बदलने, कमांड चलाने या अन्य सुरक्षित कार्रवाई से पहले लागू अनुमति-जाँच होगी। आवाज़, फोटो और कैमरा अभी इस टेक्स्ट-only चरण में शामिल नहीं हैं।",
            "CONV-CAPABILITIES-001",
        ),
    ),
    (
        re.compile(r"(?:status|/status|सिस्टम की स्थिति|सिस्टम स्टेटस|sahibex status)(?:\s*[?!.।]*)?", re.I),
        ConversationResponse(
            "system_status",
            "SAHIBEX का टेक्स्ट कमांड इंजन और स्थानीय Qwen मॉडल उपलब्ध हैं। यह रनटाइम स्थिति है, पूर्ण क्षमता की गारंटी नहीं। सामान्य प्रश्नों, लाइव वेब रिसर्च और कोड जनरेशन के परिणाम अलग-अलग जाँचने होंगे; सुरक्षित/संरक्षित कार्रवाइयाँ अनुमति के बिना नहीं चलेंगी।",
            "CONV-STATUS-001",
        ),
    ),
)


def resolve_local_conversation(text: str) -> ConversationResponse | None:
    """Resolve only exact, low-risk text interactions; leave other requests to AI."""
    if not isinstance(text, str) or not text.strip():
        return None
    normalized = " ".join(text.strip().split())
    for pattern, response in _RULES:
        if pattern.fullmatch(normalized):
            return response
    return None
