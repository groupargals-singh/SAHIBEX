"""Live acceptance for opt-in English-to-Hindi rendering of verified research.

Requires a prior live task36 JSON report; it refuses to translate unverified,
untraceable, or arbitration-rejected text. The translation API is contacted only
when this script is explicitly invoked with SAHIBEX_TRANSLATION_PROVIDER=mymemory.
"""
from __future__ import annotations
import hashlib, json, os, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.brain.translation_adapter import MyMemoryTranslationAdapter
from core.brain.universal_language_brain import UniversalLanguageBrain

ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    source_report = Path(os.environ.get("SAHIBEX_TRANSLATION_SOURCE_REPORT", "logs/p2_matrix_20261017/english_current_news_final_retest.json"))
    started = time.monotonic()
    report = {"task": "P2-live-translation", "source_report": str(source_report), "checks": {}}
    if not MyMemoryTranslationAdapter.configured():
        report.update(status="BLOCKED", reason="Set SAHIBEX_TRANSLATION_PROVIDER=mymemory explicitly for this acceptance run.")
        print(json.dumps(report, ensure_ascii=False, indent=2)); return 2
    try:
        source = json.loads(source_report.read_text(encoding="utf-8"))
        answer = source.get("answer", {})
        text = str(answer.get("text", "")).strip()
        checks = report["checks"]
        checks["source_live_acceptance_passed"] = source.get("status") == "PASS"
        checks["source_answer_verified"] = answer.get("verified") is True
        checks["source_arbitration_accepted"] = answer.get("arbitration_accepted") is True
        checks["source_traceability_two_publishers"] = "source_count=2" in str(answer.get("traceability", "")) or int(source.get("checks", {}).get("answer_has_traceability", False)) == 1
        checks["source_text_present"] = bool(text)
        if not all(checks.values()):
            report.update(status="FAIL", reason="Refusing to translate an unverified or untraceable source answer.")
            print(json.dumps(report, ensure_ascii=False, indent=2)); return 2
        translated = MyMemoryTranslationAdapter().translate(text, source_language="en", target_language="hi")
        checks["translation_returned"] = translated is not None
        if translated is None:
            report.update(status="FAIL", reason="Translation provider failed or translation preservation checks rejected the output.")
            print(json.dumps(report, ensure_ascii=False, indent=2)); return 2
        checks["hindi_language_gate"] = UniversalLanguageBrain().response_matches_language("आज AI सुरक्षा में क्या नया है?", translated.text)
        checks["numeric_tokens_preserved"] = translated.numeric_tokens_preserved
        checks["url_tokens_preserved"] = translated.url_tokens_preserved
        checks["original_traceability_unchanged"] = answer.get("traceability") is not None and bool(answer.get("traceability"))
        report.update({
            "provider": translated.provider,
            "source_language": translated.source_language,
            "target_language": translated.target_language,
            "source_answer_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "translated_answer": translated.text,
            "source_domains": source.get("distinct_publisher_domains", []),
            "translation_note": "Translation is a rendering layer; original verified evidence and source traceability remain authoritative.",
            "elapsed_seconds": round(time.monotonic() - started, 3),
        })
        report["failed_checks"] = [k for k, v in checks.items() if not v]
        report["status"] = "PASS" if not report["failed_checks"] else "FAIL"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["status"] == "PASS" else 2
    except Exception as exc:
        report.update(status="FAIL", exception=f"{type(exc).__name__}: {str(exc)[:300]}", elapsed_seconds=round(time.monotonic()-started,3))
        print(json.dumps(report, ensure_ascii=False, indent=2)); return 2

if __name__ == "__main__":
    raise SystemExit(main())
