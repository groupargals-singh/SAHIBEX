from __future__ import annotations

import json
import os
from urllib import error, request

from core.model_gateway.base import ModelProvider, ModelRequest, ModelResponse
from security.secrets.credential_store import CredentialStore


class OpenAIResponsesProvider(ModelProvider):
    """OpenAI Responses API provider behind the existing SAHIBEX model boundary."""

    name = "openai"
    capabilities = ("text", "reasoning")

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        endpoint: str = "https://api.openai.com/v1/responses",
        timeout: float = 60.0,
    ) -> None:
        self._api_key = (
            api_key.strip()
            if api_key is not None and api_key.strip()
            else None
        )
        self._model = (
            model.strip()
            if model is not None and model.strip()
            else os.getenv("SAHIBEX_OPENAI_MODEL", "gpt-6-luna")
        )
        self._endpoint = endpoint.strip()
        self._timeout = float(timeout)

        if not self._endpoint:
            raise ValueError("OpenAI endpoint cannot be empty.")
        if self._timeout <= 0:
            raise ValueError("OpenAI timeout must be positive.")

    def _credential(self) -> str:
        if self._api_key:
            return self._api_key
        return CredentialStore().require_credential("openai")

    def generate(self, request_data: ModelRequest) -> ModelResponse:
        if not request_data.prompt.strip():
            return ModelResponse(
                text="",
                provider=self.name,
                model=self._model,
                success=False,
                error="Prompt cannot be empty.",
            )

        try:
            api_key = self._credential()
        except RuntimeError as exc:
            return ModelResponse(
                text="",
                provider=self.name,
                model=self._model,
                success=False,
                error=str(exc),
            )

        payload: dict[str, object] = {
            "model": request_data.model or self._model,
            "input": request_data.prompt.strip(),
            "temperature": request_data.temperature,
        }

        if request_data.system_prompt.strip():
            payload["instructions"] = request_data.system_prompt.strip()

        http_request = request.Request(
            self._endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=self._timeout) as response:
                raw = response.read().decode("utf-8")
            body = json.loads(raw)
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            return ModelResponse(
                text="",
                provider=self.name,
                model=self._model,
                success=False,
                error=f"OpenAI HTTP {exc.code}: {detail[:1000]}",
            )
        except (error.URLError, TimeoutError, OSError) as exc:
            return ModelResponse(
                text="",
                provider=self.name,
                model=self._model,
                success=False,
                error=f"OpenAI connection failed: {exc}",
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return ModelResponse(
                text="",
                provider=self.name,
                model=self._model,
                success=False,
                error=f"Invalid OpenAI response: {exc}",
            )

        text = self._extract_text(body)
        model = str(body.get("model") or payload["model"])

        if not text:
            return ModelResponse(
                text="",
                provider=self.name,
                model=model,
                success=False,
                error="OpenAI response contained no output text.",
                metadata={"response_id": body.get("id")},
            )

        return ModelResponse(
            text=text,
            provider=self.name,
            model=model,
            success=True,
            metadata={
                "response_id": body.get("id"),
                "usage": body.get("usage"),
            },
        )

    @staticmethod
    def _extract_text(body: dict[str, object]) -> str:
        output_text = body.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

        output = body.get("output")
        if not isinstance(output, list):
            return ""

        chunks: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    chunks.append(text.strip())

        return "\n".join(chunks).strip()
