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
        acceptable = bool(result.get("success"))
        failures += 0 if acceptable else 1
        print("QUERY", question, "SECONDS", elapsed, flush=True)
        print("SUCCESS", result.get("success"), "STATUS", result.get("verification_status"), flush=True)
        print("ANSWER", result.get("message"), flush=True)
    except Exception as exc:
        failures += 1
        print("QUERY", question, "SECONDS", round(time.monotonic() - started, 2), flush=True)
        print("REQUEST_ERROR", type(exc).__name__, str(exc)[:240], flush=True)

print("QUALITY_SMOKE_FAILURES", failures, "OF", len(questions), flush=True)
raise SystemExit(1 if failures else 0)
