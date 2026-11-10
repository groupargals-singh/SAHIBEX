from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .base import ModelProvider, ModelRequest, ModelResponse


class LocalLlamaProvider(ModelProvider):
    """Local, self-hosted cognitive engine backed by llama.cpp."""

    name = "local"

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.endpoint = (
            endpoint
            or os.getenv("SAHIBEX_LOCAL_LLM_ENDPOINT", "http://127.0.0.1:8080/v1/chat/completions")
        )
        configured_model = model or os.getenv("SAHIBEX_LOCAL_LLM_MODEL")
        self.model = configured_model or self._discover_active_model() or "Qwen3-4B-Q4_K_M.gguf"
        self.timeout = timeout or float(os.getenv("SAHIBEX_LOCAL_LLM_TIMEOUT", "180"))

    def _api_root(self) -> str:
        return self.endpoint.split("/v1/", 1)[0].rstrip("/")

    def _discover_active_model(self) -> str | None:
        """Use the actually loaded llama.cpp model ID when the server is online."""
        try:
            request = urllib.request.Request(self._api_root() + "/v1/models", method="GET")
            with urllib.request.urlopen(request, timeout=1.0) as response:
                data = json.loads(response.read().decode("utf-8"))
            records = data.get("data") or data.get("models") or []
            if isinstance(records, list):
                for item in records:
                    if isinstance(item, dict):
                        model_id = item.get("id") or item.get("name") or item.get("model")
                        if isinstance(model_id, str) and model_id.strip():
                            return model_id.strip()
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, AttributeError, json.JSONDecodeError):
            return None
        return None

    def is_available(self, *, timeout: float = 1.0) -> bool:
        """Fast health preflight; avoids waiting for a long inference timeout offline."""
        try:
            request = urllib.request.Request(self._api_root() + "/health", method="GET")
            with urllib.request.urlopen(request, timeout=max(0.1, min(float(timeout), 3.0))) as response:
                status = getattr(response, "status", 200)
                return 200 <= status < 300
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            return False

    def generate(self, request: ModelRequest) -> ModelResponse:
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        payload = {
            "model": request.model or self.model,
            "messages": messages,
            "temperature": request.temperature,
            # Mobile CPU inference is slow; concise by default, with an explicit
            # environment override available for longer answers.
            "max_tokens": int(os.getenv("SAHIBEX_LOCAL_LLM_MAX_TOKENS", "384" if "intent: code" in request.prompt.casefold() else "192" if "intent: create" in request.prompt.casefold() else "128")),
            "chat_template_kwargs": {"enable_thinking": False},
            "stream": False,
        }
        body = json.dumps(payload).encode("utf-8")
        http_request = urllib.request.Request(
            self.endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        request_timeout = request.metadata.get("timeout_seconds", self.timeout)
        if (
            isinstance(request_timeout, bool)
            or not isinstance(request_timeout, (int, float))
            or request_timeout <= 0
        ):
            request_timeout = self.timeout
        request_timeout = min(float(request_timeout), self.timeout)

        try:
            with urllib.request.urlopen(http_request, timeout=request_timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
            text = data["choices"][0]["message"]["content"]
            if not isinstance(text, str):
                raise ValueError("Local model returned non-text content.")
            if not text.strip():
                raise ValueError("Local model returned empty content.")
            return ModelResponse(
                text=text,
                provider=self.name,
                model=request.model or self.model,
                success=True,
                metadata={"engine": "llama.cpp", "local": True},
            )
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError, IndexError, json.JSONDecodeError) as exc:
            return ModelResponse(
                text="",
                provider=self.name,
                model=request.model or self.model,
                success=False,
                error=f"Local llama.cpp inference failed: {exc}",
                metadata={"engine": "llama.cpp", "local": True},
            )
