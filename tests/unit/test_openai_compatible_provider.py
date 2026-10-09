from __future__ import annotations

import json
import os
from io import BytesIO
from unittest.mock import patch

from core.model_gateway.base import ModelRequest
from core.model_gateway.openai_compatible_provider import OpenAICompatibleProvider


def test_remote_provider_uses_configured_endpoint_model_and_bearer_key():
    response = BytesIO(json.dumps({
        "choices": [{"message": {"content": "भारत की राजधानी नई दिल्ली है।"}}]
    }).encode("utf-8"))
    env = {
        "SAHIBEX_REMOTE_LLM_ENDPOINT": "https://example.invalid/v1/chat/completions",
        "SAHIBEX_REMOTE_LLM_MODEL": "strong-reasoner",
        "SAHIBEX_REMOTE_LLM_API_KEY": "test-secret",
    }
    with patch.dict(os.environ, env, clear=True), patch(
        "urllib.request.urlopen", return_value=response
    ) as urlopen:
        result = OpenAICompatibleProvider().generate(
            ModelRequest(prompt="भारत की राजधानी क्या है?", system_prompt="Answer in Hindi.")
        )

    request = urlopen.call_args.args[0]
    assert result.success is True
    assert result.provider == "remote"
    assert result.model == "strong-reasoner"
    assert result.text == "भारत की राजधानी नई दिल्ली है।"
    assert request.get_header("Authorization") == "Bearer test-secret"
    assert json.loads(request.data.decode("utf-8"))["model"] == "strong-reasoner"


def test_remote_provider_fails_closed_when_not_configured():
    with patch.dict(os.environ, {}, clear=True):
        result = OpenAICompatibleProvider().generate(
            ModelRequest(prompt="Hello")
        )

    assert result.success is False
    assert "ENDPOINT is not configured" in (result.error or "")
    assert result.text == ""
