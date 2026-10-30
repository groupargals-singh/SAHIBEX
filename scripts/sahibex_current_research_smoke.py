"""One-query live smoke test for SAHIBEX current-news research."""
import json
import pathlib
import time
import urllib.request

root = pathlib.Path(__file__).resolve().parents[1]
token = (root / "data" / "android_companion_media_token").read_text().strip()
question = "आज AI सुरक्षा में क्या नया है?"
body = json.dumps({"text": question}, ensure_ascii=False).encode()
request = urllib.request.Request(
    "http://127.0.0.1:38742/voice",
    data=body,
    headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
    method="POST",
)
started = time.monotonic()
try:
    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.loads(response.read())
    elapsed = round(time.monotonic() - started, 2)
    status = str(result.get("verification_status", "")).upper()
    success = result.get("success") is True
    print("QUERY", question, "SECONDS", elapsed, flush=True)
    print("OUTCOME", "VERIFIED_RESEARCH" if success and status == "VERIFIED" else "RESEARCH_ACCEPTANCE_FAILED", "SUCCESS", success, "STATUS", status, flush=True)
    print("ANSWER", str(result.get("message", ""))[:1200], flush=True)
    diagnostics = result.get("research_diagnostics", {})
    print("RESEARCH_DIAGNOSTICS", json.dumps(diagnostics if isinstance(diagnostics, dict) else {}, ensure_ascii=False, default=str)[:6000], flush=True)
    raise SystemExit(0 if success and status == "VERIFIED" else 1)
except Exception as exc:
    print("QUERY", question, "SECONDS", round(time.monotonic() - started, 2), flush=True)
    print("REQUEST_ERROR", type(exc).__name__, str(exc)[:240], flush=True)
    raise
