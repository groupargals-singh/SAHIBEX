from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LocalDeploymentContract:
    endpoint: str
    model: str
    local_only: bool = True

    def validate(self) -> None:
        if not self.endpoint.startswith("http://127.0.0.1:") and not self.endpoint.startswith("http://localhost:"):
            raise ValueError("native deployment must use a local endpoint")
        if not self.model.strip():
            raise ValueError("local model name is required")
        if not self.local_only:
            raise ValueError("native deployment contract must remain local-only")
