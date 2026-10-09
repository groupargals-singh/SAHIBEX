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
        self.model = model or os.getenv("SAHIBEX_LOCAL_LLM_MODEL", "Qwen3-1.7B-Q4_K_M.gguf")
        self.timeout = timeout or float(os.getenv("SAHIBEX_LOCAL_LLM_TIMEOUT", "180"))

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

        try:
            with urllib.request.urlopen(http_request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
            text = data["choices"][0]["message"]["content"]
            if not isinstance(text, str):
                raise ValueError("Local model returned non-text content.")
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
