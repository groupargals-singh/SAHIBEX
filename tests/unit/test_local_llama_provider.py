from __future__ import annotations

import json
import os
from io import BytesIO
from unittest.mock import patch

from core.model_gateway.base import ModelRequest
from core.model_gateway.local_llama_provider import LocalLlamaProvider


def _run_provider_with_env(env: dict[str, str]):
    payload_response = {
        "choices": [{"message": {"content": "A concise verified response."}}]
    }
    models_response = BytesIO(json.dumps({"data": [{"id": "loaded-test-model"}]}).encode("utf-8"))
    chat_response = BytesIO(json.dumps(payload_response).encode("utf-8"))
    with patch.dict(os.environ, env, clear=True), patch(
        "urllib.request.urlopen", side_effect=[models_response, chat_response]
    ) as urlopen:
        result = LocalLlamaProvider(endpoint="http://127.0.0.1:8080/v1/chat/completions").generate(
            ModelRequest(prompt="Answer briefly", system_prompt="Be helpful")
        )
    request = urlopen.call_args.args[0]
    return result, json.loads(request.data.decode("utf-8"))


def test_local_provider_uses_mobile_friendly_default_output_limit():
    result, payload = _run_provider_with_env({})

    assert result.success is True
    assert result.text == "A concise verified response."
    assert payload["max_tokens"] == 128
    assert payload["model"] == "loaded-test-model"
    assert payload["chat_template_kwargs"]["enable_thinking"] is False


def test_local_provider_allows_explicit_longer_output_limit():
    result, payload = _run_provider_with_env({"SAHIBEX_LOCAL_LLM_MAX_TOKENS": "256"})

    assert result.success is True
    assert payload["max_tokens"] == 256


def test_local_provider_fails_closed_on_empty_content():
    payload_response = {"choices": [{"message": {"content": "   "}}]}
    models_response = BytesIO(json.dumps({"data": [{"id": "loaded-test-model"}]}).encode("utf-8"))
    chat_response = BytesIO(json.dumps(payload_response).encode("utf-8"))
    with patch("urllib.request.urlopen", side_effect=[models_response, chat_response]):
        result = LocalLlamaProvider(
            endpoint="http://127.0.0.1:8080/v1/chat/completions"
        ).generate(ModelRequest(prompt="Answer briefly"))

    assert result.success is False
    assert result.text == ""
    assert "empty content" in result.error.lower()


class _HttpResponse(BytesIO):
    status = 200


def test_local_provider_uses_request_scoped_timeout():
    models_response = BytesIO(json.dumps({"data": [{"id": "loaded-test-model"}]}).encode("utf-8"))
    chat_response = BytesIO(json.dumps({"choices": [{"message": {"content": "ok"}}]}).encode("utf-8"))
    with patch("urllib.request.urlopen", side_effect=[models_response, chat_response]) as urlopen:
        provider = LocalLlamaProvider(endpoint="http://127.0.0.1:8080/v1/chat/completions", timeout=180)
        result = provider.generate(ModelRequest(prompt="classify", metadata={"timeout_seconds": 12}))
    assert result.success is True
    assert urlopen.call_args.kwargs["timeout"] == 12


def test_local_provider_health_preflight_is_fast_and_truthful():
    with patch("urllib.request.urlopen", return_value=_HttpResponse(b'{"status":"ok"}')) as urlopen:
        provider = LocalLlamaProvider(endpoint="http://127.0.0.1:8080/v1/chat/completions", model="fixed-model")
        assert provider.is_available(timeout=1.0) is True
    assert urlopen.call_args.kwargs["timeout"] == 1.0


def test_local_provider_reports_offline_health_without_waiting_for_inference():
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("offline")):
        provider = LocalLlamaProvider(endpoint="http://127.0.0.1:8080/v1/chat/completions", model="fixed-model")
        assert provider.is_available(timeout=1.0) is False
