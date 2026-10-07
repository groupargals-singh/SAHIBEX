from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class ExternalAICapability:
    provider: str
    capability: str
    description: str = ""
    evidence: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

class ExternalAICapabilityRegistry:
    """Records externally reported capabilities as untrusted references only."""
    def __init__(self): self._items: list[ExternalAICapability] = []
    def register(self, item: ExternalAICapability) -> None:
        if not item.provider.strip() or not item.capability.strip(): raise ValueError("provider and capability are required")
        self._items.append(item)
    def list(self) -> tuple[ExternalAICapability, ...]: return tuple(self._items)
    def is_authority(self) -> bool: return False
    def grants_permission(self) -> bool: return False
    def executes_external_actions(self) -> bool: return False
