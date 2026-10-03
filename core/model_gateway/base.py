from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ModelRequest:
    prompt: str
    system_prompt: str = ""
    model: str | None = None
    temperature: float = 0.2
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelResponse:
    text: str
    provider: str
    model: str
    success: bool
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelProvider(ABC):
    """
    Common interface for every SAHIBEX AI model provider.

    Providers must implement generate().
    This layer does not execute protected system actions.
    """

    name: str = "unknown"

    @abstractmethod
    def generate(self, request: ModelRequest) -> ModelResponse:
        raise NotImplementedError


class ModelGateway:
    """
    Central gateway for selecting and calling AI model providers.

    MasterBrain should communicate with this gateway rather than
    directly depending on a specific AI provider.
    """

    def __init__(self) -> None:
        self._providers: dict[str, ModelProvider] = {}

    def register_provider(self, provider: ModelProvider) -> None:
        if not provider.name.strip():
            raise ValueError("Provider name cannot be empty.")

        if provider.name in self._providers:
            raise ValueError(
                f"Provider already registered: {provider.name}"
            )

        self._providers[provider.name] = provider

    def providers(self) -> list[str]:
        return sorted(self._providers.keys())

    def get_provider(self, name: str) -> ModelProvider:
        provider = self._providers.get(name)

        if provider is None:
            raise KeyError(f"Unknown model provider: {name}")

        return provider

    def generate(
        self,
        request: ModelRequest,
        *,
        provider: str,
    ) -> ModelResponse:
        selected = self.get_provider(provider)
        return selected.generate(request)
