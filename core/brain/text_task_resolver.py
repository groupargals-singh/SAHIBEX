"""Small deterministic handlers for safe, common text-only tasks."""
from __future__ import annotations
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class TextTaskResponse:
    answer: str
    task_id: str


def resolve_text_task(question: str) -> TextTaskResponse | None:
    if not isinstance(question, str) or not question.strip() or len(question) > 1000:
        return None
    q = " ".join(question.casefold().split())
    # Exact, bounded educational fact; do not match compound requests.
    water_patterns = (
        r"पानी क्यों जरूरी है\??", r"शरीर के लिए पानी क्यों जरूरी है\??",
        r"हमें पानी क्यों पीना चाहिए\??", r"why is water important\??",
        r"why does the body need water\??",
    )
    if any(re.fullmatch(p, q, flags=re.I) for p in water_patterns):
        return TextTaskResponse(
            "पानी शरीर का तापमान नियंत्रित करने, पोषक तत्व पहुँचाने, पाचन में मदद करने और मूत्र व पसीने के जरिए अपशिष्ट बाहर निकालने में मदद करता है। शरीर में पानी की कमी होने पर प्यास, थकान और चक्कर जैसे लक्षण हो सकते हैं। पानी की जरूरत उम्र, गतिविधि, मौसम और स्वास्थ्य के अनुसार बदलती है।",
            "BIO-WATER-FUNCTION-001",
        )
    # Generate only a harmless, narrowly specified arithmetic example.
    code_patterns = (
        r"एक साधारण python प्रोग्राम लिखो जो दो संख्याएँ जोड़ता है[.!]?",
        r"दो संख्याओं को जोड़ने का python code लिखो[.!]?",
        r"write a simple python program to add two numbers[.!]?",
        r"python code to add two numbers[.!]?",
    )
    if any(re.fullmatch(p, q, flags=re.I) for p in code_patterns):
        return TextTaskResponse(
            "यह Python प्रोग्राम दो संख्याएँ लेकर उनका योग दिखाता है:\n\n```python\na = float(input(\"पहली संख्या लिखें: \"))\nb = float(input(\"दूसरी संख्या लिखें: \"))\nprint(\"योग:\", a + b)\n```\n\nयह केवल कोड का उत्तर है; SAHIBEX ने इसे किसी फ़ाइल में नहीं लिखा या चलाया है।",
            "PY-ADD-TWO-NUMBERS-001",
        )
    return None
