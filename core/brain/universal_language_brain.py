"""Universal multilingual language brain for SAHIBEX.

Offline-first language/script identification and reply-language policy. It requires
no downloaded model. Script identification is strong where scripts are unique;
languages sharing a script use lexical and orthographic clues and may remain
ambiguous. Fluent generation still depends on the configured language model.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


@dataclass(frozen=True)
class LanguageAssessment:
    language_code: str
    language_name: str
    script: str
    confidence: float
    mixed: bool = False


class UniversalLanguageBrain:
    VERSION = "2.0"
    # (BCP-47-ish code, display name, script, Unicode ranges)
    _SCRIPTS = (
        ("hi", "Hindi", "Devanagari", ((0x0900, 0x097F),)),
        ("bn", "Bengali", "Bengali-Assamese", ((0x0980, 0x09FF),)),
        ("pa", "Punjabi", "Gurmukhi", ((0x0A00, 0x0A7F),)),
        ("gu", "Gujarati", "Gujarati", ((0x0A80, 0x0AFF),)),
        ("or", "Odia", "Odia", ((0x0B00, 0x0B7F),)),
        ("ta", "Tamil", "Tamil", ((0x0B80, 0x0BFF),)),
        ("te", "Telugu", "Telugu", ((0x0C00, 0x0C7F),)),
        ("kn", "Kannada", "Kannada", ((0x0C80, 0x0CFF),)),
        ("ml", "Malayalam", "Malayalam", ((0x0D00, 0x0D7F),)),
        ("si", "Sinhala", "Sinhala", ((0x0D80, 0x0DFF),)),
        ("th", "Thai", "Thai", ((0x0E00, 0x0E7F),)),
        ("lo", "Lao", "Lao", ((0x0E80, 0x0EFF),)),
        ("bo", "Tibetan", "Tibetan", ((0x0F00, 0x0FFF),)),
        ("my", "Burmese", "Myanmar", ((0x1000, 0x109F),)),
        ("ka", "Georgian", "Georgian", ((0x10A0, 0x10FF), (0x2D00, 0x2D2F))),
        ("ko", "Korean", "Hangul", ((0x1100, 0x11FF), (0xAC00, 0xD7AF), (0x3130, 0x318F))),
        ("am", "Amharic", "Ethiopic", ((0x1200, 0x137F),)),
        ("km", "Khmer", "Khmer", ((0x1780, 0x17FF),)),
        ("ja", "Japanese", "Japanese", ((0x3040, 0x30FF), (0x31F0, 0x31FF))),
        ("zh", "Chinese", "Han", ((0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF))),
        ("ru", "Russian", "Cyrillic", ((0x0400, 0x052F),)),
        ("el", "Greek", "Greek", ((0x0370, 0x03FF),)),
        ("he", "Hebrew", "Hebrew", ((0x0590, 0x05FF),)),
        ("ar", "Arabic", "Arabic", ((0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF))),
        ("hy", "Armenian", "Armenian", ((0x0530, 0x058F),)),
        ("fa", "Persian", "Arabic", ((0x0600, 0x06FF),)),
        ("mni", "Manipuri (Meitei)", "Meitei Mayek", ((0xABC0, 0xABFF),)),
        ("sat", "Santali", "Ol Chiki", ((0x1C50, 0x1C7F),)),
    )

    # Lexical fingerprints; deliberately use full words to avoid substring guesses.
    _LATIN_MARKERS = {
        "en": ("the", "what", "please", "hello", "how", "is", "can", "you", "why", "with", "your", "explain", "this", "that", "file", "delete", "open", "show", "close", "run", "execute", "help", "tell", "capital", "from"),
        "hi-Latn": ("kya", "hai", "mujhe", "mujhko", "mera", "meri", "mere", "batao", "kaise", "nahi", "karo", "chahiye", "kyun", "hain", "ko", "mein", "me", "ke", "liye", "banao", "bana", "samajhne", "samajh", "samjho", "samjhao", "wala", "wali", "wale", "sunne", "suno", "sahi", "theek", "thik", "pura", "poora", "abhi", "bahut", "apne", "jaisa", "jese", "dalo", "karna", "karke", "tum", "aap", "kese", "par", "khojo", "khoj", "jankari", "jaankari", "bataiye", "kis", "kaun", "kyunki", "agar", "lekin", "isse", "uske", "iske", "ispar", "isspar", "topic par", "jankari khojo"),
        "es": ("hola", "qué", "como", "gracias", "por", "para", "está", "quiero", "cómo", "usted", "borra", "archivo", "este", "esta", "eliminar", "borrar"),
        "fr": ("bonjour", "merci", "avec", "pour", "est", "vous", "comment", "je", "une", "pas", "supprime", "fichier", "efface", "supprimer"),
        "pt": ("olá", "obrigado", "você", "como", "para", "não", "uma", "que", "por favor"),
        "de": ("hallo", "danke", "und", "ist", "nicht", "wie", "bitte", "ich", "das", "der", "datei", "diese", "entferne"),
        "it": ("ciao", "grazie", "come", "che", "non", "per", "sono", "una", "buongiorno"),
        "id": ("halo", "terima", "kasih", "apa", "saya", "yang", "tidak", "bagaimana", "selamat"),
        "ms": ("apa", "saya", "tidak", "terima", "kasih", "selamat", "boleh", "anda"),
        "tr": ("merhaba", "teşekkür", "nasıl", "için", "değil", "ben", "bir", "lütfen"),
        "vi": ("xin", "chào", "cảm", "ơn", "không", "là", "và", "bạn", "tôi"),
        "sw": ("habari", "asante", "tafadhali", "nini", "kwa", "sana", "karibu"),
        "nl": ("hallo", "dank", "niet", "wat", "hoe", "voor", "een", "het", "jij"),
        "pl": ("cześć", "dziękuję", "jak", "jest", "nie", "proszę", "się"),
        "ro": ("bună", "mulțumesc", "este", "pentru", "nu", "cum", "sunt"),
        "sv": ("hej", "tack", "och", "inte", "hur", "det", "jag"),
        "da": ("hej", "tak", "og", "ikke", "hvordan", "jeg", "det"),
        "no": ("hei", "takk", "og", "ikke", "hvordan", "jeg", "det"),
        "fi": ("hei", "kiitos", "mitä", "ja", "ole", "sinä", "hyvää"),
        "cs": ("ahoj", "děkuji", "jak", "není", "prosím", "dobrý"),
        "hu": ("szia", "köszönöm", "hogy", "nem", "van", "kérem"),
        "tl": ("kumusta", "salamat", "ako", "hindi", "ikaw", "paano", "po"),
        "az": ("salam", "təşəkkür", "necə", "üçün", "mən", "deyil"),
        "uz": ("salom", "rahmat", "qanday", "uchun", "men", "emas"),
        "ha": ("sannu", "na gode", "yaya", "ina", "kai", "don"),
        "yo": ("bawo", "ẹ ṣé", "kini", "báwo", "mo", "ni"),
        "ig": ("ndewo", "daalụ", "kedu", "anyị", "bụ", "ị bụ"),
        "mr-Latn": ("aahe", "mala", "majha", "majhi", "tumhi", "sanga", "krupaya", "nahi"),
        "ne-Latn": ("chha", "chhan", "tapai", "malai", "kasto", "hoina", "dhanyabad", "kripaya"),
        "pa-Latn": ("tusi", "sat sri akaal", "punjabi", "tuhada", "kiven", "dhanvaad"),
        "bn-Latn": ("bhalo", "kemon", "dhonnobad", "ami", "apni", "bangla", "korbo"),
        "ta-Latn": ("vanakkam", "nandri", "ungal", "enna", "tamil", "illai"),
        "te-Latn": ("namaskaram", "dhanyavadalu", "meeru", "telugu", "ledu", "ela"),
        "kn-Latn": ("namaskara", "dhanyavada", "neevu", "kannada", "illa", "hegiddira"),
        "ml-Latn": ("namaskaram", "nanni", "ningal", "malayalam", "alla", "sugham"),
        "gu-Latn": ("kem cho", "aabhar", "tame", "gujarati", "nathi", "maja ma"),
        "or-Latn": ("namaskar", "dhanyabad", "odia", "mu", "tume", "nahin"),
        "as-Latn": ("axomiya", "kenekoi", "moi", "bhal", "dhonyobad", "asu"),
        "kok-Latn": ("konknni", "konkani", "mhaka", "kite", "sang", "asa"),
        "bho-Latn": ("bhojpuri", "hamaar", "raura", "ka haal ba", "kaise bani"),
        "hne-Latn": ("chhattisgarhi", "mor", "tor", "kaabar", "havay", "batavav"),
        "raj-Latn": ("rajasthani", "mhane", "thare", "ghani", "khamma ghani"),
        "bgc-Latn": ("haryanvi", "tanne", "manne", "ghanna", "ke haal se", "konya"),
    }
    _LATIN_NAMES = {
        "en":"English", "hi-Latn":"Hindi (Romanized/Hinglish)", "es":"Spanish",
        "fr":"French", "pt":"Portuguese", "de":"German", "it":"Italian",
        "id":"Indonesian", "ms":"Malay", "tr":"Turkish", "vi":"Vietnamese",
        "sw":"Swahili", "nl":"Dutch", "pl":"Polish", "ro":"Romanian",
        "sv":"Swedish", "da":"Danish", "no":"Norwegian", "fi":"Finnish",
        "cs":"Czech", "hu":"Hungarian", "tl":"Filipino/Tagalog",
        "az":"Azerbaijani", "uz":"Uzbek", "ha":"Hausa", "yo":"Yoruba", "ig":"Igbo",
        "mr-Latn":"Marathi (Romanized)", "ne-Latn":"Nepali (Romanized)",
        "pa-Latn":"Punjabi (Romanized)", "bn-Latn":"Bengali (Romanized)",
        "ta-Latn":"Tamil (Romanized)", "te-Latn":"Telugu (Romanized)",
        "kn-Latn":"Kannada (Romanized)", "ml-Latn":"Malayalam (Romanized)",
        "gu-Latn":"Gujarati (Romanized)", "or-Latn":"Odia (Romanized)",
        "as-Latn":"Assamese (Romanized)", "kok-Latn":"Konkani (Romanized)",
        "bho-Latn":"Bhojpuri (Romanized)", "hne-Latn":"Chhattisgarhi (Romanized)",
        "raj-Latn":"Rajasthani (Romanized)", "bgc-Latn":"Haryanvi (Romanized)",
    }

    # Common word-level signals for Indian languages that share scripts.
    _INDIC_WORDS = {
        "hi": ("है", "हैं", "मुझे", "क्या", "क्यों", "करना", "चाहिए", "बताओ", "नहीं", "और", "यह", "आप", "मेरा", "मेरी", "कृपया", "समझाओ", "नमस्ते"),
        "mr": ("आहे", "आहेत", "मला", "काय", "नाही", "करा", "माझे", "तुम्ही", "आणि", "कसे", "माझं", "कृपया", "सांगा", "मदत", "मराठी", "मराठीत", "भारताची", "कोणती", "द्या", "कृपया"),
        "ne": ("छ", "छन्", "तपाईं", "मलाई", "कस्तो", "होइन", "गर्नु", "धन्यवाद", "नेपाल", "नेपाली", "छैन", "हजुर", "कृपया", "बताउनु"),
        "sa": ("अस्ति", "भवति", "भवन्तः", "किम्", "अहम्", "अहं", "त्वम्", "त्वं", "विद्या", "संस्कृतम्", "संस्कृतं", "पठामि", "नमः", "भवतः", "कथम्", "अस्मि"),
        "mai": ("अछि", "हमर", "अहाँ", "केना", "नहि", "छी", "मैथिली", "अहाँक", "हमरा", "अहाँसभ"),
        "brx": ("बर'", "बड़ो", "दोंसे", "नंगौ", "बड़ो राव", "नोंथां", "खुलुमबाय", "बोडो"),
        "doi": ("तुस", "थुआढ़े", "केह्", "अस्स", "डोगरी", "थुआढ़ा", "करदे", "ओ"),
        "kok": ("आसा", "तुका", "म्हाका", "कितें", "कोंकणी", "हांव", "आमी", "कशें", "आसा"),
        "bho": ("हमार", "रउआ", "बानी", "भोजपुरी", "कइसे", "का हो", "बा"),
        "hne": ("मोला", "तोर", "काबर", "हवय", "छत्तीसगढ़ी", "अउ", "बतावव"),
        "raj": ("म्हाने", "थाने", "घणी", "खम्मा", "राजस्थानी", "केड़ो"),
        "bgc": ("तन्नै", "मन्नै", "घणा", "हरियाणवी", "कोन्या", "के हाल सै"),
        "ks": ("کٲشُر", "کٲشِر", "چھِ", "چھِو", "ژٕ", "کٲشُر زبان", "कॉशुर", "काशुर", "कशीर", "कश्मीरी"),
        "sd": ("سنڌي", "سنڌ", "آهيان", "آھيان", "असां", "आहियूं", "सिंधी"),
        "ur": ("اردو", "ہے", "ہیں", "آپ", "کیا", "نہیں", "مجھے", "اور", "کیسے", "شکریہ", "کرنا"),
        "as": ("আৰু", "মই", "তুমি", "অসমীয়া", "নহয়", "কৰোঁ", "আছে", "ধন্যবাদ", "কেনেকৈ", "আপুনি"),
        "bn": ("আমি", "তুমি", "বাংলা", "কী", "নয়", "করুন", "ধন্যবাদ", "আছে", "কেমন", "ভালো", "আপনি"),

        "pa": ("ਸਤ ਸ੍ਰੀ ਅਕਾਲ", "ਤੁਸੀਂ", "ਕੀ", "ਹਾਂ", "ਨਹੀਂ", "ਪੰਜਾਬੀ", "ਕਿਵੇਂ"),
        "gu": ("છે", "શું", "મને", "નથી", "કરો", "ગુજરાતી", "આભાર"),
        "or": ("ଅଛି", "ମୁଁ", "ତୁମେ", "କଣ", "ନାହିଁ", "ଓଡ଼ିଆ", "ଧନ୍ୟବାଦ"),
        "ta": ("வணக்கம்", "என்ன", "நான்", "நீங்கள்", "இல்லை", "தமிழ்", "நன்றி"),
        "te": ("నమస్కారం", "ఏమిటి", "నేను", "మీరు", "కాదు", "తెలుగు", "ధన్యవాదాలు"),
        "kn": ("ನಮಸ್ಕಾರ", "ಏನು", "ನಾನು", "ನೀವು", "ಇಲ್ಲ", "ಕನ್ನಡ", "ಧನ್ಯವಾದ"),
        "ml": ("നമസ്കാരം", "എന്ത്", "ഞാൻ", "നിങ്ങൾ", "ഇല്ല", "മലയാളം", "നന്ദി"),
        "mni": ("ꯃꯩꯇꯩ", "ꯑꯩ", "ꯅꯪ", "ꯀꯔꯤ"),
        "sat": ("ᱥᱟᱱᱛᱟᱲᱤ", "ᱤᱧ", "ᱟᱢ"),
    }
    _INDIC_NAMES = {
        "hi":"Hindi", "mr":"Marathi", "ne":"Nepali", "sa":"Sanskrit",
        "mai":"Maithili", "doi":"Dogri", "kok":"Konkani", "as":"Assamese",
        "bn":"Bengali", "pa":"Punjabi", "gu":"Gujarati", "or":"Odia",
        "ta":"Tamil", "te":"Telugu", "kn":"Kannada", "ml":"Malayalam",
        "mni":"Manipuri (Meitei)", "sat":"Santali", "sd":"Sindhi", "ks":"Kashmiri",
        "ur":"Urdu", "brx":"Bodo", "bho":"Bhojpuri", "hne":"Chhattisgarhi",
        "raj":"Rajasthani", "bgc":"Haryanvi",
    }

    @staticmethod
    def _words(value: str) -> set[str]:
        # Python's \w excludes many combining marks/matras in Indic scripts;
        # split on punctuation/whitespace instead so full native words survive.
        normalized = unicodedata.normalize("NFC", value.casefold())
        return {word for word in re.split(r"[\s.,!?;:()\[\]{}\"'؟،।॥]+", normalized) if word}

    def _script_counts(self, letters: list[str]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for char in letters:
            point = ord(char)
            for code, _, _, ranges in self._SCRIPTS:
                if any(start <= point <= end for start, end in ranges):
                    counts[code] = counts.get(code, 0) + 1
                    break
        return counts

    def _detect_arabic_script(self, value: str, words: set[str], counts: dict[str, int]) -> LanguageAssessment:
        # Several South Asian languages share the Perso-Arabic script.
        if any(c in value for c in "ڄڳٻڀٿڏڍڦڇ") or words & {"سنڌي", "سنڌ", "सिंधी"}:
            return LanguageAssessment("sd", "Sindhi", "Perso-Arabic", 0.86)
        if any(c in value for c in "ٲٳۆۈۍ") or words & {"کٲشُر", "کٲشِر", "کشمیری"}:
            return LanguageAssessment("ks", "Kashmiri", "Perso-Arabic", 0.80)
        if any(c in value for c in "ٹڈڑںھہےے") or words & {"اردو", "ہے", "ہیں", "آپ", "کیا", "نہیں", "مجھے", "اور"}:
            return LanguageAssessment("ur", "Urdu", "Perso-Arabic", 0.88)
        if any(c in value for c in "پچژگ") or words & {"است", "هست", "برای", "فارسی", "می", "شود", "شما", "چطور"}:
            return LanguageAssessment("fa", "Persian", "Perso-Arabic", 0.82)
        return LanguageAssessment("ar", "Arabic", "Arabic", min(0.78, counts.get("ar", 1) / max(1, sum(counts.values()))))

    def detect(self, text: str) -> LanguageAssessment:
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        value = unicodedata.normalize("NFC", text.strip())
        if not value:
            return LanguageAssessment("und", "Undetermined", "Unknown", 0.0)
        letters = [c for c in value if c.isalpha()]
        if not letters:
            return LanguageAssessment("und", "Undetermined", "Unknown", 0.0)
        words = self._words(value)

        # Meitei and Santali are important Indian-script cases.
        if any(0xABC0 <= ord(c) <= 0xABFF for c in letters):
            return LanguageAssessment("mni", "Manipuri (Meitei)", "Meitei Mayek", 0.98)
        if any(0x1C50 <= ord(c) <= 0x1C7F for c in letters):
            return LanguageAssessment("sat", "Santali", "Ol Chiki", 0.98)

        counts = self._script_counts(letters)
        if counts:
            code, amount = max(counts.items(), key=lambda item: item[1])
            script_info = next(x for x in self._SCRIPTS if x[0] == code)
            name, script = script_info[1], script_info[2]
            total_script = sum(counts.values())
            confidence = amount / max(1, total_script)
            mixed = len(counts) > 1 or amount < len(letters) * 0.75

            if code == "ar":
                return self._detect_arabic_script(value, words, counts)
            if code == "hi":
                scores = {lang: sum(1 for token in markers if token in words or (" " in token and token in value.casefold()))
                          for lang, markers in self._INDIC_WORDS.items()
                          if lang in {"hi", "mr", "ne", "sa", "mai", "doi", "kok", "brx", "ks", "sd", "bho", "hne", "raj", "bgc"}}
                best = max(scores, key=scores.get) if scores else "hi"
                score = scores.get(best, 0)
                if score:
                    return LanguageAssessment(best, self._INDIC_NAMES[best], script,
                                              min(0.96, 0.58 + 0.12 * score), mixed)
                return LanguageAssessment("hi", "Hindi or another Devanagari language", script,
                                          min(0.72, confidence), mixed)
            if code == "bn":
                if any(c in value for c in "ৰৱ"):
                    return LanguageAssessment("as", "Assamese", script, 0.90, mixed)
                scores = {lang: sum(1 for token in markers if token in words or (" " in token and token in value.casefold()))
                          for lang, markers in self._INDIC_WORDS.items() if lang in {"as", "bn"}}
                best = max(scores, key=scores.get)
                if scores[best]:
                    return LanguageAssessment(best, self._INDIC_NAMES[best], script,
                                              min(0.96, 0.58 + 0.12 * scores[best]), mixed)
            if code == "pa" and words & {"ਪੰਜਾਬੀ", "ਸਤ", "ਸ੍ਰੀ", "ਅਕਾਲ"}:
                return LanguageAssessment("pa", "Punjabi", script, 0.96, mixed)
            if code in {"ru"}:
                name = "Russian or another Cyrillic language"
                confidence = min(0.72, confidence)
            if code == "zh" and any(0x3040 <= ord(c) <= 0x30FF for c in letters):
                return LanguageAssessment("ja", "Japanese", "Japanese", 0.96, mixed)
            return LanguageAssessment(code, name, script, min(0.99, confidence), mixed)

        # Latin-script language identification via curated word fingerprints.
        scores = {}
        for lang, markers in self._LATIN_MARKERS.items():
            score = sum(1 for marker in markers if marker in words or (" " in marker and marker in value.casefold()))
            scores[lang] = score
        best = max(scores, key=scores.get)
        score = scores[best]
        active_languages = [lang for lang, value in scores.items() if value >= 2]
        mixed = len(active_languages) > 1
        # Preserve code-switching between Romanized Hindi and English.
        if scores.get("en", 0) > 0 and scores.get("hi-Latn", 0) > 0:
            mixed = True
            if scores["hi-Latn"] >= scores["en"]:
                best = "hi-Latn"
                score = scores[best]
        if score:
            return LanguageAssessment(best, self._LATIN_NAMES[best], "Latin",
                                      min(0.96, 0.48 + score * 0.10), mixed=mixed)
        return LanguageAssessment("und-Latn", "Unidentified Latin-script language", "Latin", 0.25)

    def response_matches_language(self, input_text: str, response_text: str) -> bool:
        """Check whether a response clearly switches away from the user's language.

        Ambiguous/very short responses are not rejected solely by this heuristic.
        This validates language consistency, not factual correctness or fluency.
        """
        expected = self.detect(input_text)
        if expected.language_code in {"und", "und-Latn"}:
            return True
        if not isinstance(response_text, str) or not response_text.strip():
            return False
        actual = self.detect(response_text)
        if actual.language_code in {"und", "und-Latn"}:
            return True
        expected_base = expected.language_code.split("-")[0]
        actual_base = actual.language_code.split("-")[0]
        return expected_base == actual_base

    def reply_instruction(self, text: str) -> str:
        assessment = self.detect(text)
        if assessment.language_code == "und":
            return "Reply in the language most clearly requested by the user; if unclear, ask briefly."
        if assessment.language_code == "und-Latn":
            return ("The user's language is uncertain. Match the user's wording; do not assume English. "
                    "If the user's language cannot be identified, ask which language they prefer.")
        return (f"Reply in {assessment.language_name} (language code: {assessment.language_code}). "
                "Use the user's language and normal script; preserve their natural code-switching. "
                "Do not translate into English unless asked. Use natural, fluent phrasing, not word-for-word "
                "translation. If a language is ambiguous, ask a short clarification instead of guessing. "
                "If you cannot confidently answer in that language, say so honestly.")
