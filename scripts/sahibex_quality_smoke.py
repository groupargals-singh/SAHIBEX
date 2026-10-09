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
for question in questions:
    body = json.dumps({"text": question}, ensure_ascii=False).encode()
    request = urllib.request.Request(
        "http://127.0.0.1:38742/voice",
        data=body,
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        method="POST",
    )
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.loads(response.read())
    print("QUERY", question, "SECONDS", round(time.monotonic() - started, 2))
    print("SUCCESS", result.get("success"), "STATUS", result.get("verification_status"))
    print("ANSWER", result.get("message"))
