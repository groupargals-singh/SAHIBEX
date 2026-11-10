"""Deterministic local responses for basic text-only conversation commands.

These responses handle simple interactions without claiming that unverified
services are online or that an answer has been independently verified.
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
        re.compile(
            r"(?:नमस्ते|नमस्कार|प्रणाम|namaste|namaskar|pranam|हेलो|हाय|hello|hi|hey)"
            r"(?:\s+(?:sahibex|\u0938\u093e\u0939\u093f\u092c\u0947\u0915\u094d\u0938))?"
            r"(?:[,،]?\s*(?:एक छोटे वाक्य में हिंदी में जवाब दो|"
            r"हिंदी में जवाब दो|एक वाक्य में जवाब दो|"
            r"reply in one short sentence))?"
            r"(?:\s*[!.।]*)?",
            re.I,
        ),
        ConversationResponse(
            "general_request",
            "नमस्ते! मैं SAHIBEX हूँ। अपना सवाल या टेक्स्ट कमांड "
            "लिखिए; मैं उपलब्ध क्षमताओं के अनुसार मदद करूँगी।",
            "CONV-GREETING-001",
        ),
    ),
    (
        re.compile(
            r"(?:तुम क्या कर सकते हो|आप क्या कर सकते हैं|"
            r"sahibex क्या कर सकता है|what can you do|"
            r"what can sahibex do|help|मदद)"
            r"(?:\s*[?!.।]*)?",
            re.I,
        ),
        ConversationResponse(
            "general_request",
            "अभी आप मुझसे टेक्स्ट में सवाल पूछें, जानकारी या समझाइश "
            "माँगें, उपलब्ध स्थानीय ज्ञान से जवाब लें, कोड का मसौदा "
            "और काम की योजना बनवाएँ। "
            "इंटरनेट रिसर्च तभी सफल होगी जब खोज सेवा और नेटवर्क उपलब्ध "
            "हों। फ़ाइल बदलने, कमांड चलाने या अन्य संरक्षित कार्रवाई "
            "से पहले लागू अनुमति-जाँच होगी। आवाज़, फोटो और कैमरा अभी "
            "इस टेक्स्ट-only चरण में शामिल नहीं हैं।",
            "CONV-CAPABILITIES-001",
        ),
    ),
    (
        re.compile(
            r"(?:status|/status|sahibex status|"
            r"status\s+(?:batao|बताओ|बताइए|dikhao|दिखाओ)|"
            r"(?:apna|apni|mera|meri)\s+status\s+"
            r"(?:batao|बताओ|बताइए|dikhao|दिखाओ)|"
            r"(?:मेरा|अपना|अपनी)\s+(?:स्टेटस|स्थिति)\s+"
            r"(?:बताओ|बताइए|दिखाओ|दिखाइए)|"
            r"(?:सिस्टम की स्थिति|सिस्टम स्टेटस)|"
            r"(?:तुम|आप)\s+ठीक\s+हो)"
            r"(?:\s*[?!.।]*)?",
            re.I,
        ),
        ConversationResponse(
            "system_status",
            "मैं आपका status अनुरोध पहचान सकती हूँ। यह जवाब सभी "
            "सेवाओं की live health जाँच नहीं करता, इसलिए मैं अभी "
            "यह दावा नहीं कर सकता कि स्थानीय मॉडल, रिसर्च सेवा और "
            "Android bridge चालू हैं। उनकी वास्तविक स्थिति जानने "
            "के लिए health checks चलाने होंगे।",
            "CONV-STATUS-001",
        ),
    ),
    (
        re.compile(
            r"(?:tumhara|tumhara hi|aapka|tera|"
            r"तुम्हारा|आपका|तेरा)\s+"
            r"(?:name|naam|नाम|नाम क्या है)"
            r"(?:\s+kya\s+h(?:ai)?|\s+क्या\s+है)?"
            r"|(?:tum|aap)\s+kaun\s+ho"
            r"|(?:apne|अपने)\s+bare\s+mein\s+batao"
            r"|अपने बारे में बताओ"
            r"|तुम्हारा नाम क्या है"
            r"|आपका नाम क्या है"
            r"|तुम कौन हो"
            r"|आप कौन हैं",
            re.I,
        ),
        ConversationResponse(
            "general_request",
            "मेरा नाम SAHIBEX है। मैं आपकी AI assistant हूँ। "
            "मैं सवालों का जवाब देने, समझाने, योजना बनाने और "
            "उपलब्ध टूल्स से काम करने में मदद कर सकती हूँ। "
            "मेरी वास्तविक क्षमताएँ चालू सेवाओं और उपलब्ध टूल्स "
            "पर निर्भर करती हैं।",
            "CONV-IDENTITY-001",
        ),
    ),
)


def resolve_local_conversation(
    text: str,
) -> ConversationResponse | None:
    """Resolve simple, low-risk text interactions."""
    if not isinstance(text, str) or not text.strip():
        return None

    normalized = " ".join(text.strip().split())

    for pattern, response in _RULES:
        if pattern.fullmatch(normalized):
            return response

    return None
