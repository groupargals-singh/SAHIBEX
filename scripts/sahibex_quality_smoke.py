import json
import pathlib
import time
import urllib.request

root = pathlib.Path(__file__).resolve().parents[1]
token = (root / "data" / "android_companion_media_token").read_text().strip()
questions = [
    "आसमान नीला क्यों दिखाई देता है?",
    "भारत की राजधानी क्या है और इतिहास भी बताओ?",
    "आज AI सुरक्षा में क्या नया है?",
]
failures = 0
for question in questions:
    body = json.dumps({"text": question}, ensure_ascii=False).encode()
    request = urllib.request.Request(
        "http://127.0.0.1:38742/voice",
        data=body,
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        method="POST",
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.loads(response.read())
        elapsed = round(time.monotonic() - started, 2)
        success = result.get("success") is True
        verification_status = str(result.get("verification_status", "")).upper()
        message = str(result.get("message", ""))
        is_current_research = question.startswith("आज AI सुरक्षा")
        if is_current_research:
            # A current-news answer may be unavailable when corroboration fails.
            # The safe outcome is an explicit NOT_VERIFIED response with source
            # leads, not a fabricated success. Do not confuse that with verified research.
            safe_fail_closed = (
                result.get("success") is False
                and verification_status in {"NOT_VERIFIED", "INSUFFICIENT_EVIDENCE"}
                and any(marker in message for marker in ("सत्यापित", "स्रोत", "verified", "source"))
            )
            # Safe fail-closed is a security PASS, but it is not a research-quality
            # PASS. Keep the outcome visible and make the quality smoke fail until
            # the current-news query returns an actually verified answer.
            acceptable = success and verification_status == "VERIFIED"
            outcome = "VERIFIED_RESEARCH" if acceptable else (
                "SAFE_FAIL_CLOSED" if safe_fail_closed else "RESEARCH_ACCEPTANCE_FAILED"
            )
        else:
            acceptable = success and verification_status in {"STRUCTURALLY_VALID", "VERIFIED"}
            outcome = "PASS" if acceptable else "EXPECTED_ANSWER_FAILED"
        failures += 0 if acceptable else 1
        print("QUERY", question, "SECONDS", elapsed, flush=True)
        print("OUTCOME", outcome, "SUCCESS", success, "STATUS", verification_status, flush=True)
        print("ANSWER", message, flush=True)
        if is_current_research:
            diagnostics = result.get("research_diagnostics", {})
            if not isinstance(diagnostics, dict):
                diagnostics = {}
            print("RESEARCH_DIAGNOSTICS", json.dumps(diagnostics, ensure_ascii=False, default=str)[:5000], flush=True)
    except Exception as exc:
        failures += 1
        print("QUERY", question, "SECONDS", round(time.monotonic() - started, 2), flush=True)
        print("REQUEST_ERROR", type(exc).__name__, str(exc)[:240], flush=True)

print("QUALITY_SMOKE_FAILURES", failures, "OF", len(questions), flush=True)
raise SystemExit(1 if failures else 0)
