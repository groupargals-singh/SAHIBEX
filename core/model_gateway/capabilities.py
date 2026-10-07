from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from core.model_gateway.base import ModelProvider

@dataclass(frozen=True)
class ModelCapability:
    name: str
    supported: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

class ModelCapabilityRegistry:
    """Read-only capability view over registered model providers."""
    def __init__(self, providers: dict[str, ModelProvider]):
        self._providers = providers
    def capabilities(self, provider: str) -> tuple[ModelCapability, ...]:
        p = self._providers.get(provider)
        if p is None: raise KeyError(f"Unknown model provider: {provider}")
        raw = getattr(p, "capabilities", ())
        return tuple(x if isinstance(x, ModelCapability) else ModelCapability(str(x)) for x in raw)
    def supports(self, provider: str, capability: str) -> bool:
        return any(c.name == capability and c.supported for c in self.capabilities(provider))
