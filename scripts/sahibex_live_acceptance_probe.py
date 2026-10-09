from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:38742"

def main() -> int:
    with urllib.request.urlopen(BASE + "/health", timeout=3) as response:
        health = json.loads(response.read())
    if not health.get("success"):
        print("BRIDGE_HEALTH=FAIL")
        return 1
    token = (ROOT / "data" / "android_companion_media_token").read_text(encoding="utf-8").strip()
    payload = json.dumps({"text": "Hello Sahibex. Reply in one short sentence."}).encode("utf-8")
    request = urllib.request.Request(
        BASE + "/voice",
        data=payload,
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read())
            print("BRIDGE_HEALTH=PASS")
            print("BRAIN_HTTP_STATUS=", response.status)
            print("BRAIN_SUCCESS=", result.get("success"))
            print("BRAIN_VERIFICATION=", result.get("verification_status"))
            print("RESPONSE_CHARS=", len(result.get("message", "")))
            return 0 if response.status == 200 and result.get("success") else 2
    except Exception as exc:
        print("BRAIN_E2E=FAIL", type(exc).__name__, str(exc)[:240])
        return 3

if __name__ == "__main__":
    raise SystemExit(main())
