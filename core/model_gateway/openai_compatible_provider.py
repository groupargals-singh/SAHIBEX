from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .base import ModelProvider, ModelRequest, ModelResponse


class OpenAICompatibleProvider(ModelProvider):
    """Optional remote model provider for OpenAI-compatible chat-completions APIs.

    Credentials and endpoint configuration are read only from environment
    variables. No credential is stored in source code or written to logs.
    """

    name = "remote"

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.endpoint = (
            endpoint
            or os.getenv("SAHIBEX_REMOTE_LLM_ENDPOINT", "").strip()
        )
        self.model = (
            model
            or os.getenv("SAHIBEX_REMOTE_LLM_MODEL", "").strip()
        )
        self.api_key = (
            api_key
            if api_key is not None
            else os.getenv("SAHIBEX_REMOTE_LLM_API_KEY", "")
        )
        self.timeout = timeout or float(
            os.getenv("SAHIBEX_REMOTE_LLM_TIMEOUT", "45")
        )

    def generate(self, request: ModelRequest) -> ModelResponse:
        if not self.endpoint:
            return self._failure("SAHIBEX_REMOTE_LLM_ENDPOINT is not configured.")
        if not self.model:
            return self._failure("SAHIBEX_REMOTE_LLM_MODEL is not configured.")

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        payload = {
            "model": request.model or self.model,
            "messages": messages,
            "temperature": request.temperature,
            "stream": False,
        }
        body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = "Bearer " + self.api_key
        http_request = urllib.request.Request(
            self.endpoint,
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(http_request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
            text = data["choices"][0]["message"]["content"]
            if not isinstance(text, str) or not text.strip():
                raise ValueError("Remote model returned empty or non-text content.")
            return ModelResponse(
                text=text.strip(),
                provider=self.name,
                model=request.model or self.model,
                success=True,
                metadata={"engine": "openai_compatible", "remote": True},
            )
        except (
            urllib.error.URLError,
            TimeoutError,
            OSError,
            ValueError,
            KeyError,
            IndexError,
            TypeError,
            json.JSONDecodeError,
        ) as exc:
            return self._failure(
                f"Remote model request failed: {type(exc).__name__}: {exc}"
            )

    def _failure(self, message: str) -> ModelResponse:
        return ModelResponse(
            text="",
            provider=self.name,
            model=self.model or "unconfigured",
            success=False,
            error=message,
            metadata={"engine": "openai_compatible", "remote": True},
        )
