"""Fast, conservative resolver for a tiny curated local fact set.

This is not a general knowledge engine. Only exact, recognized question families
are answered; all other requests continue through the configured local model.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class LocalFact:
    answer: str
    fact_id: str


_FACTS = (
    (
        re.compile(r"(?:भारत की राजधानी क्या है|भारत की राजधानी बताओ|what is the capital of india|capital of india)(?:[?।.! ]*)$", re.I),
        LocalFact(
            "भारत की राजधानी नई दिल्ली है। नई दिल्ली, दिल्ली के राष्ट्रीय राजधानी क्षेत्र (NCT) में स्थित है; दिल्ली किसी दूसरे राज्य का हिस्सा नहीं है।",
            "IN-CAPITAL-001",
        ),
    ),
    (
        re.compile(r"(?:आसमान नीला क्यों दिखाई देता है|आकाश नीला क्यों दिखता है|why (?:does )?the sky (?:look|appear) blue)(?:[?।.! ]*)$", re.I),
        LocalFact(
            "आसमान नीला दिखाई देता है क्योंकि वायुमंडल के अणु सूर्य के प्रकाश में छोटी तरंगदैर्घ्य वाली नीली रोशनी को लाल रोशनी की तुलना में अधिक बिखेरते हैं।",
            "PHYS-SCATTER-001",
        ),
    ),
    (
        re.compile(r"(?:प्रकाश संश्लेषण क्या है|प्रकाश संश्लेषण कैसे काम करता है|what is photosynthesis|explain photosynthesis(?: in simple hindi)?|photosynthesis in simple hindi)(?:[?।.! ]*)$", re.I),
        LocalFact(
            "प्रकाश संश्लेषण वह प्रक्रिया है जिसमें पौधे सूर्य के प्रकाश की ऊर्जा से पानी और कार्बन डाइऑक्साइड का उपयोग करके अपना भोजन (शर्करा) बनाते हैं और ऑक्सीजन छोड़ते हैं। यह प्रक्रिया मुख्यतः पत्तियों के क्लोरोप्लास्ट में होती है, जहाँ क्लोरोफिल प्रकाश को अवशोषित करता है।",
            "BIO-PHOTOSYNTHESIS-001",
        ),
    ),
    (
        re.compile(r"(?:भारत में मानसून कैसे आता है|मानसून कैसे आता है|how does the monsoon arrive in india)(?:[?।.! ]*)$", re.I),
        LocalFact(
            "भारत में मानसून मुख्यतः मौसमी हवाओं के बदलने से आता है। गर्मियों में भारतीय उपमहाद्वीप की जमीन तेजी से गर्म होती है, जिससे कम दबाव बनता है; अरब सागर और बंगाल की खाड़ी से नमी वाली हवाएँ भूमि की ओर आती हैं। हवा ऊपर उठने और ठंडी होने पर बादल बनते हैं और बारिश होती है; बारिश का समय और मात्रा क्षेत्र के अनुसार बदलते हैं।",
            "CLIMATE-INDIAN-MONSOON-001",
        ),
    ),
)


def resolve_local_fact(question: str) -> LocalFact | None:
    """Return a curated fact only when the entire normalized question matches."""
    if not isinstance(question, str) or not question.strip():
        return None
    normalized = " ".join(question.strip().split())
    # Ignore only trailing answer-format requests; do not remove semantic
    # clauses such as "and tell me its history", which must not partial-match.
    format_suffixes = (
        r"\s+एक\s+वाक्य\s+में\s+जवाब\s+दें[.!।]?$",
        r"\s+एक\s+छोटे\s+वाक्य\s+में\s+जवाब\s+दें[.!।]?$",
        r"\s+संक्षेप\s+में\s+बताएँ[.!।]?$",
        r"\s+answer\s+briefly[.!]?$",
        r"\s+answer\s+in\s+one\s+sentence[.!]?$",
        r"\s+in\s+one\s+sentence[.!]?$",
    )
    for suffix in format_suffixes:
        normalized = re.sub(suffix, "", normalized, flags=re.IGNORECASE).strip()
    for pattern, fact in _FACTS:
        if pattern.fullmatch(normalized):
            return fact
    return None
