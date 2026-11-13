from __future__ import annotations

import base64
import json

import pytest

from core.brain.semantic_vision_provider import SemanticVisionProvider


def _png(path):
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 24)
    return path


def test_semantic_vision_requires_explicit_consent_before_read_or_network(tmp_path, monkeypatch):
    path = _png(tmp_path / "image.png")
    called = []
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: called.append(True))
    provider = SemanticVisionProvider(endpoint="http://127.0.0.1:8080/v1/chat/completions", model="local-vlm")
    with pytest.raises(PermissionError):
        provider.analyze(path, consent=False)
    assert called == []


def test_semantic_vision_posts_bounded_image_and_returns_provenance(tmp_path, monkeypatch):
    path = _png(tmp_path / "image.png")
    captured = {}

    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self, size=-1):
            return json.dumps({"choices": [{"message": {"content": "A red car is parked."}}]}).encode()

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    provider = SemanticVisionProvider(
        endpoint="http://127.0.0.1:8080/v1/chat/completions",
        model="local-vlm",
        timeout=12,
    )
    result = provider.analyze(path, consent=True)
    payload = json.loads(captured["request"].data.decode())
    image_url = payload["messages"][0]["content"][1]["image_url"]["url"]
    assert image_url.startswith("data:image/png;base64,")
    assert base64.b64decode(image_url.split(",", 1)[1]) == path.read_bytes()
    assert result.description == "A red car is parked."
    assert result.remote_transfer is False
    assert len(result.source_sha256) == 64
    assert result.source_bytes == path.stat().st_size
    assert captured["timeout"] == 12


def test_semantic_vision_requires_separate_remote_transfer_consent(tmp_path, monkeypatch):
    path = _png(tmp_path / "image.png")
    called = []
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: called.append(True))
    provider = SemanticVisionProvider(
        endpoint="https://vision.example/v1/chat/completions",
        model="remote-vlm",
    )
    with pytest.raises(PermissionError, match="remote image-transfer"):
        provider.analyze(path, consent=True)
    assert called == []


def test_semantic_vision_rejects_unsupported_image_and_unconfigured_provider(tmp_path):
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not an image at all")
    provider = SemanticVisionProvider(endpoint="http://127.0.0.1:8080/v1/chat/completions", model="local-vlm")
    with pytest.raises(ValueError, match="signatures"):
        provider.analyze(bad, consent=True)
    missing = SemanticVisionProvider()
    with pytest.raises(RuntimeError, match="not configured"):
        missing.analyze(bad, consent=True)


def test_semantic_vision_rejects_symlinks(tmp_path):
    target = _png(tmp_path / "target.png")
    link = tmp_path / "link.png"
    link.symlink_to(target)
    provider = SemanticVisionProvider(endpoint="http://127.0.0.1:8080/v1/chat/completions", model="local-vlm")
    with pytest.raises(ValueError, match="regular non-symlink"):
        provider.analyze(link, consent=True)
