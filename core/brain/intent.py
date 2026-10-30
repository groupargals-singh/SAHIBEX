from dataclasses import dataclass
import re


@dataclass(frozen=True)
class IntentResult:
    intent: str
    confidence: float
    entities: dict[str, str]


class IntentEngine:
    """Deterministic request classifier; it never authorizes execution."""

    PATTERNS = {
        "system_status": [
            r"\bstatus\b", r"\bhow are you\b", r"\bstate\b",
            r"सिस्टम की स्थिति", r"सिस्टम स्टेटस",
            r"(?:मेरा|अपना|सिस्टम का)\s+(?:स्टेटस|स्थिति)\s*(?:बताओ|बताइए|दिखाओ|दिखाइए)?",
            r"\b(?:sahibex|system)\s+(?:ka|ki|ke)\s+(?:status|stithi)\b",
            r"\b(?:mera|apna|system ka)\s+(?:status|stithi)\s+(?:batao|dikhao|check karo)?\b",
        ],
        "search": [
            r"\bsearch\b", r"\bfind\b", r"\blook up\b",
            r"\bweather\b",
            r"\bforecast\b",
            r"\bnews\b",
            r"\bcurrent weather\b",
            r"\btoday's weather\b",
            r"\blatest news\b",
            r"मौसम का हाल",
            r"मौसम की जानकारी",
            r"मौसम का पूर्वानुमान",
            r"(?:भारत|भोपाल|इंदौर|रायपुर|दिल्ली|मुंबई|लखनऊ|जयपुर).{0,30}मौसम",
            r"आज.{0,20}मौसम",
            r"ताज़ा खबर|ताजा खबर|समाचार",
            r"आज का हाल",
            r"\bweb\b", r"\binternet\b", r"\bresearch\b",
            r"आज.*(?:नया|ताज़ा|ताजा|अपडेट)",
            r"(?:नवीनतम|ताज़ा जानकारी|ताजा जानकारी|लेटेस्ट अपडेट)",
            r"(?:इंटरनेट|वेब) पर (?:खोज|ढूँढ|ढूंढ|देख)",
            r"(?:रिसर्च|शोध) करो",
            r"\b(?:aaj|abhi)\b.{0,40}\b(?:kya naya|latest|taza|taaza|update|news|khabar)\b",
            r"\b(?:latest|taza|taaza)\s+(?:jaankari|jankari|khabar|news|update)\b",
            r"\b(?:aaj ki|aaj ka|aaj ke)\s+(?:news|khabar|samachar|updates?)\b",
            r"\b(?:internet|web)\s+par\s+(?:search|khoj|dhundo|dhoondo|dekho)\b",
            r"\b(?:research|search|google par search)\s+karo\b",
            r"\b(?:mausam|mosam)\s+(?:ka haal|ki jaankari|ka forecast)\b",
            r"ताज़ा जानकारी|ताजा जानकारी|लेटेस्ट न्यूज़|लेटेस्ट न्यूज",
        ],
        "learn": [
            r"\blearn\b", r"\blearning\b", r"\bstudy\b",
            r"\bteach me\b", r"\bhelp me learn\b",
            r"\bhelp me understand\b",
            r"मुझे .* सिखाओ", r"सीखना चाहता", r"सीखना चाहती",
            r"\bmujhe\b.{0,50}\b(?:sikhao|sikhaiye|seekhna|sikhna)\b",
            r"\b(?:seekhna|sikhna)\s+(?:chahta|chahti|chahata|chahati)\b",
            r"\b(?:mujhe|mujhko)\b.{0,40}\b(?:seekhna|sikhna)\s+hai\b",
            r"(?:मुझे|मुझको).{0,40}(?:सीखना|सिखना)\s+(?:है|हैं)",
        ],
        "code": [
            r"\bwrite\s+(?:a\s+)?(?:python|javascript|java|c\+\+|rust|go)\b",
            r"\bcode\b", r"\bprogram\b", r"\bprogramming\b",
            r"\bscript\b", r"\bdebug\b", r"\bpython\b",
            r"\bjavascript\b", r"\bsource code\b",
            r"\b(?:code|program|script)\s+(?:likho|likh do|banao|banado|taiyar karo)\b",
            r"\b(?:python|javascript|java|c\+\+|rust|go)\b.{0,30}\b(?:code|program|script)\b",
            r"\b(?:bug|error)\s+(?:fix|theek|thik)\s+(?:karo|kar do)\b",
            r"\b(?:debug|coding|programming)\s+(?:karo|kar do)\b",
            r"(?:कोड|प्रोग्राम|स्क्रिप्ट)\s*(?:लिखो|लिख दो|बनाओ|तैयार करो)",
            r"(?:बग|एरर)\s*(?:ठीक|फिक्स)\s*(?:करो|कर दो)",
        ],
        "create": [
            r"\bcreate\b", r"\bmake\b", r"\bbuild\b",
            r"\bgenerate\b", r"\bdesign\b",
            r"\b(?:banao|banado|bana do|taiyar karo|design karo|likh kar do)\b",
            r"(?:बनाओ|बना दो|तैयार करो|डिज़ाइन करो|डिजाइन करो|लिखकर दो)",
        ],
        "explain": [
            r"\bexplain\b", r"\bwhat is\b", r"\bhow does\b",
            r"\bwhy\b", r"क्यों", r"क्या है", r"समझाओ",
            r"बताओ",
            r"\b(?:kyun|kyu|kyon|kaise|kya hai|kya hota hai|samjhao|samjhaao|batao|bataiye)\b",
            r"(?:क्या होता है|कैसे काम करता है|क्यों होता है|समझाइए|समझाओ|बताइए)",
        ],
        "file_operation": [
            r"\bfile\b", r"\bfolder\b", r"\bdirectory\b",
            r"\bopen file\b", r"\bread file\b", r"\bview file\b",
            r"\b(?:file|folder|directory)\s+(?:kholo|padho|dikhao|list karo|open karo)\b",
            r"\b(?:file|folder)\s+(?:mein|me)\s+(?:kya hai|dekho)\b",
            r"(?:फ़ाइल|फाइल|फ़ोल्डर|फोल्डर)\s*(?:खोलो|पढ़ो|दिखाओ|खोजो|सूची दिखाओ)",
        ],
    }

    INTENT_PRIORITY = {
        "system_status": 100, "code": 90, "search": 80,
        "file_operation": 70, "explain": 60, "create": 50,
        "learn": 95,
    }

    def detect(self, text: str) -> IntentResult:
        normalized = text.lower().strip()
        if not normalized:
            return IntentResult(intent="empty", confidence=1.0, entities={})

        scores: dict[str, int] = {}
        for intent, patterns in self.PATTERNS.items():
            score = sum(1 for pattern in patterns if re.search(pattern, normalized))
            if score:
                scores[intent] = score

        if not scores:
            return IntentResult(intent="general_request", confidence=0.30, entities={})

        # An explicit search request must not be reclassified as code merely
        # because the subject mentions a language (e.g. "search for Python
        # programming language"). The language/programming keywords below
        # are useful when the user asks to create/debug code, but are too broad
        # to override an explicit retrieval verb on their own.
        explicit_search_request = bool(
            re.search(
                r"\b(?:search|find|look up|research)\b|\b(?:internet|web)\b|"
                r"(?:इंटरनेट|वेब) पर (?:खोज|ढूँढ|ढूंढ|देख)",
                normalized,
            )
        )
        explicit_code_action = bool(
            re.search(
                r"\b(?:write|create|build|make|generate|implement|debug|fix|refactor)\b|"
                r"\b(?:code|program|script)\s+(?:likho|likh do|banao|banado|taiyar karo)\b|"
                r"(?:कोड|प्रोग्राम|स्क्रिप्ट)\s*(?:लिखो|लिख दो|बनाओ|तैयार करो)",
                normalized,
            )
        )
        if explicit_search_request and not explicit_code_action and "search" in scores:
            return IntentResult(
                intent="search",
                confidence=min(0.95, max(0.65, 0.50 + scores["search"] * 0.15)),
                entities={},
            )

        best_intent = max(
            scores,
            key=lambda intent: (scores[intent], self.INTENT_PRIORITY.get(intent, 0)),
        )
        confidence = min(0.95, 0.50 + scores[best_intent] * 0.15)
        return IntentResult(intent=best_intent, confidence=confidence, entities={})
