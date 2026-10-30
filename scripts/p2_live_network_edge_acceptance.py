"""Bounded real-network edge acceptance for the direct web acquisition provider.

This uses public httpbin endpoints only. It does not promote fetched content to
verified knowledge; it checks provider behavior, timeout handling, short-page
rejection, and bounded response acquisition.
"""
from __future__ import annotations
import json, time, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.research.acquisition import AcquisitionRequest
from core.research.web_provider import DirectWebResearchProvider, WebProviderConfig

ROOT = Path(__file__).resolve().parents[1]

def acquire(url: str, *, timeout: float = 1.2):
    provider = DirectWebResearchProvider(WebProviderConfig(timeout_seconds=timeout, max_response_bytes=100_000, max_sources=2))
    started = time.monotonic()
    result = provider.acquire(AcquisitionRequest(query="P2 network edge acceptance", max_sources=1, metadata={"url": url}))
    return provider, result, round(time.monotonic() - started, 3)

def main() -> int:
    report = {"task": "P2-live-network-edge-acceptance", "network_permission": "explicit user request for P2 live verification", "checks": {}, "scenarios": {}}
    # A real publisher-like HTML response establishes that direct HTTP fetching works.
    for name, url, expected in [
        ("substantive_html", "https://httpbin.org/html", "acquired"),
        ("inaccessible_404", "https://httpbin.org/status/404", "rejected"),
        ("short_stub", "https://httpbin.org/base64/SGk=", "rejected"),
        ("timeout", "https://httpbin.org/delay/10", "rejected"),
    ]:
        try:
            timeout = 0.7 if name == "timeout" else 1.5
            provider, result, elapsed = acquire(url, timeout=timeout)
            acquired = bool(result.sources)
            errors = list(result.metadata.get("errors", []))
            if expected == "acquired":
                passed = acquired and len(result.sources[0].content.strip()) >= provider.MIN_ARTICLE_CHARS
            elif name == "short_stub":
                passed = not acquired and any("article body too short" in str(error) for error in errors)
            elif name == "timeout":
                passed = not acquired and any("timed out" in str(error).casefold() or "timeout" in str(error).casefold() for error in errors)
            else:
                passed = not acquired and bool(errors)
            report["scenarios"][name] = {"url": url, "expected": expected, "acquired": acquired, "elapsed_seconds": elapsed, "errors": [str(x)[:240] for x in errors], "status": "PASS" if passed else "FAIL"}
        except Exception as exc:
            report["scenarios"][name] = {"url": url, "elapsed_seconds": None, "status": "FAIL", "exception": f"{type(exc).__name__}: {str(exc)[:240]}"}
    checks = report["checks"]
    checks["substantive_page_acquired"] = report["scenarios"].get("substantive_html", {}).get("status") == "PASS"
    checks["http_404_rejected"] = report["scenarios"].get("inaccessible_404", {}).get("status") == "PASS"
    checks["short_stub_rejected"] = report["scenarios"].get("short_stub", {}).get("status") == "PASS"
    checks["network_timeout_bounded_and_rejected"] = report["scenarios"].get("timeout", {}).get("status") == "PASS"
    report["failed_checks"] = [key for key, passed in checks.items() if not passed]
    report["status"] = "PASS" if not report["failed_checks"] else "PARTIAL"
    output = ROOT / "logs" / "p2_matrix_20261017" / "live_network_edge_acceptance.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2

if __name__ == "__main__":
    raise SystemExit(main())
