from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from core.model_gateway.base import ModelGateway, ModelRequest, ModelResponse

@dataclass(frozen=True)
class FallbackResult:
    response: ModelResponse
    attempts: tuple[str, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

class ModelFallbackExecutor:
    """Safe provider fallback; it never changes permissions or executes tools."""
    def __init__(self, gateway: ModelGateway): self.gateway = gateway
    def generate(self, request: ModelRequest, providers: list[str]) -> FallbackResult:
        if not providers: raise ValueError("providers must not be empty")
        attempts=[]; last=None
        for name in providers:
            if name in attempts: continue
            attempts.append(name)
            try: response=self.gateway.generate(request, provider=name)
            except Exception as exc:
                last=ModelResponse(text="", provider=name, model=request.model or "unknown", success=False, error=str(exc)); continue
            if response.success and response.text.strip():
                return FallbackResult(response=response, attempts=tuple(attempts), metadata={"fallback_used": len(attempts)>1})
            last=response
        assert last is not None
        return FallbackResult(response=last, attempts=tuple(attempts), metadata={"fallback_used": len(attempts)>1})
